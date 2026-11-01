#!/usr/bin/env python3
"""Normalize a teacher's video or voice recording, transcribe it word by word, sample frames.

Usage: prepare.py INPUT --job NAME [--model large-v3-turbo] [--language tr] [--tighten 0.45] [--cut 3.2-5.0]...

Writes to the job folder: source.mp4, words.json, transcript.txt, frames/, probe.json.
--tighten removes pauses longer than the given seconds; --cut removes retakes. Times are in the
original recording. Both rewrite word timings, so a plan is always written against the result.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

RUNTIME = Path(os.environ.get("MATEMATIK_REELS_HOME", Path.home() / ".local/share/matematik-reels"))
VOCAB = (
    "Ortaokul matematik dersi. üslü ifadeler, kareköklü ifadeler, özdeşlikler, çarpanlar ve katlar, "
    "EBOB, EKOK, kesir, payda, pay, tam sayılar, eksi, artı, çarpı, bölü, üzeri, karekök, x kare, "
    "denklem, eşitsizlik, olasılık, doğru grafiği, eğim, üçgen, LGS."
)
AUDIO_EXT = {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac", ".opus"}


def reexec_with_cuda_libs():
    """ctranslate2 finds pip-installed CUDA libraries only through LD_LIBRARY_PATH at process start."""
    libs = sorted(str(p) for p in (RUNTIME / "venv/lib").glob("python*/site-packages/nvidia/*/lib"))
    current = os.environ.get("LD_LIBRARY_PATH", "")
    missing = [p for p in libs if p not in current]
    if missing:
        os.environ["LD_LIBRARY_PATH"] = ":".join(libs + ([current] if current else []))
        os.execv(sys.executable, [sys.executable] + sys.argv)


def run(*cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def probe(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
    )
    return json.loads(out)


def duration(path):
    return float(probe(path)["format"]["duration"])


def normalize(src, dst, fps):
    """Cover-crop to 1080x1920 at constant frame rate, so phone HEVC, rotation and VFR stop mattering."""
    info = probe(src)
    has_video = any(s["codec_type"] == "video" and s.get("disposition", {}).get("attached_pic") != 1
                    for s in info["streams"])
    if not any(s["codec_type"] == "audio" for s in info["streams"]):
        sys.exit("Bu dosyada ses yok. Animasyonlar sese göre zamanlandığı için sesli kayıt gerekiyor.")
    audio = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
             "-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]
    if has_video and src.suffix.lower() not in AUDIO_EXT:
        vf = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps={fps},setsar=1"
        run("ffmpeg", "-y", "-i", str(src), "-vf", vf, "-map", "0:v:0", "-map", "0:a:0",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", *audio, str(dst))
        return True
    run("ffmpeg", "-y", "-i", str(src), "-map", "0:a:0", "-vn", *audio, str(dst.with_suffix(".m4a")))
    return False


def transcribe(media, model_name, language):
    import numpy as np
    from faster_whisper import WhisperModel

    # Decode with ffmpeg: faster-whisper's PyAV path breaks across PyAV releases.
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(media), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         check=True, stdout=subprocess.PIPE).stdout
    audio = np.frombuffer(pcm, dtype=np.float32)
    model = None
    for device, compute in (("cuda", "float16"), ("cpu", "int8")):
        try:
            model = WhisperModel(model_name, device=device, compute_type=compute,
                                 download_root=str(RUNTIME / "models"))
            segments, info = model.transcribe(
                audio, language=language, word_timestamps=True, vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 250, "speech_pad_ms": 120},
                initial_prompt=VOCAB, beam_size=5, condition_on_previous_text=False,
            )
            words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3),
                      "p": round(w.probability, 3)}
                     for seg in segments for w in seg.words if w.word.strip()]
            # Whisper splits Turkish suffixes after digits ("2", "'nin"); captions and anchors need one word.
            merged = []
            for w in words:
                if merged and w["w"][0] in "'’":
                    merged[-1].update(w=merged[-1]["w"] + w["w"], e=w["e"], p=min(merged[-1]["p"], w["p"]))
                else:
                    merged.append(w)
            print(f"yazı dökümü: {model_name} / {device}, {len(merged)} kelime")
            return merged
        except (RuntimeError, ValueError, OSError) as err:
            print(f"{device} kullanılamadı ({str(err)[:110]}), sıradakine geçiliyor")
    sys.exit("Yazı dökümü başarısız oldu.")


def keep_ranges(words, total, gap, cuts):
    """Spans to keep: pauses longer than `gap` and explicit cuts are dropped, 0.12s of air stays around speech."""
    pad = 0.12
    spans = []
    if gap is None:
        spans = [[0.0, total]]
    else:
        for w in words:
            s, e = max(0, w["s"] - pad), min(total, w["e"] + pad)
            if spans and s - spans[-1][1] <= gap:
                spans[-1][1] = max(spans[-1][1], e)
            else:
                spans.append([s, e])
    for c0, c1 in cuts:
        next_spans = []
        for s, e in spans:
            if e <= c0 or s >= c1:
                next_spans.append([s, e])
                continue
            if s < c0:
                next_spans.append([s, c0])
            if e > c1:
                next_spans.append([c1, e])
        spans = next_spans
    return [s for s in spans if s[1] - s[0] > 0.05]


def apply_cuts(src, dst, spans, is_video):
    parts = []
    labels = ""
    for i, (s, e) in enumerate(spans):
        if is_video:
            parts.append(f"[0:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS[v{i}]")
            labels += f"[v{i}]"
        parts.append(f"[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.012,afade=t=out:st={max(0, e - s - 0.012):.3f}:d=0.012[a{i}]")
        labels += f"[a{i}]"
    n = len(spans)
    if is_video:
        parts.append(f"{labels}concat=n={n}:v=1:a=1[v][a]")
        maps = ["-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                "-pix_fmt", "yuv420p"]
    else:
        parts.append(f"{labels}concat=n={n}:v=0:a=1[a]")
        maps = ["-map", "[a]"]
    run("ffmpeg", "-y", "-i", str(src), "-filter_complex", ";".join(parts), *maps,
        "-c:a", "aac", "-b:a", "192k", str(dst))


def remap(words, spans):
    out = []
    offset = 0.0
    for s, e in spans:
        for w in words:
            mid = (w["s"] + w["e"]) / 2
            if s <= mid < e:
                out.append({**w, "s": round(max(w["s"], s) - s + offset, 3),
                            "e": round(min(w["e"], e) - s + offset, 3)})
        offset += e - s
    return out


def frames(video, out_dir, every):
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True)
    run("ffmpeg", "-y", "-i", str(video), "-vf", f"fps=1/{every},scale=360:-2", "-q:v", "4",
        str(out_dir / "t%03d.jpg"))
    run("ffmpeg", "-y", "-i", str(video), "-vf",
        f"fps=1/{every},scale=270:-2,drawtext=text='%{{pts\\:hms}}':x=8:y=8:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6,"
        "tile=6x3", "-frames:v", "1", "-q:v", "4", str(out_dir.parent / "contact.jpg"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("--job", required=True)
    ap.add_argument("--model", default="large-v3-turbo")
    ap.add_argument("--language", default="tr")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--tighten", type=float, default=None)
    ap.add_argument("--cut", action="append", default=[])
    args = ap.parse_args()
    reexec_with_cuda_libs()

    if not args.input.exists():
        sys.exit(f"Dosya bulunamadı: {args.input}")
    job = RUNTIME / "jobs" / args.job
    job.mkdir(parents=True, exist_ok=True)

    raw = job / "raw.mp4"
    is_video = normalize(args.input, raw, args.fps)
    media = raw if is_video else raw.with_suffix(".m4a")
    words = transcribe(media, args.model, args.language)
    if not words:
        sys.exit("Kayıtta konuşma bulunamadı.")

    cuts = [tuple(float(x) for x in c.split("-")) for c in args.cut]
    final = job / ("source.mp4" if is_video else "source.m4a")
    if args.tighten is not None or cuts:
        spans = keep_ranges(words, duration(media), args.tighten, cuts)
        apply_cuts(media, final, spans, is_video)
        before = duration(media)
        words = remap(words, spans)
        print(f"kısaltma: {before:.1f}s -> {duration(final):.1f}s, {len(spans)} parça")
    else:
        shutil.copy(media, final)

    (job / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=0), encoding="utf-8")
    lines, line = [], []
    for w in words:
        line.append(w)
        if w["w"][-1] in ".?!" or len(line) >= 14:
            lines.append(f"[{line[0]['s']:6.2f}] " + " ".join(x["w"] for x in line))
            line = []
    if line:
        lines.append(f"[{line[0]['s']:6.2f}] " + " ".join(x["w"] for x in line))
    (job / "transcript.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    unsure = [f"{w['w']} @{w['s']:.1f}s" for w in words if w["p"] < 0.5]
    total = duration(final)
    if is_video:
        frames(final, job / "frames", 2 if total <= 36 else 3)
    (job / "probe.json").write_text(json.dumps(
        {"fps": args.fps, "duration": total, "video": is_video, "source": final.name}, indent=1), encoding="utf-8")

    print(f"iş klasörü: {job}\nsüre: {total:.2f}s  görüntü: {'var' if is_video else 'yok (yalnız ses)'}")
    if total > 90:
        print("UYARI: 90 saniyeden uzun. Tek fikirlik Reels için 30-50 sn hedefle ya da seriye böl.")
    if unsure:
        print("Emin olunmayan kelimeler (matematik terimiyse plan.corrections ile düzelt): " + ", ".join(unsure[:30]))


if __name__ == "__main__":
    main()
