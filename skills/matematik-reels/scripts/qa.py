#!/usr/bin/env python3
"""Check a rendered reel against upload specs and pull one still per event for visual review.

Usage: qa.py JOB   writes jobs/JOB/qa/*.jpg and qa/sheet.jpg; exits 1 if the file is out of spec.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

RUNTIME = Path(os.environ.get("MATEMATIK_REELS_HOME", Path.home() / ".local/share/matematik-reels"))


def main(name):
    job = RUNTIME / "jobs" / name
    video = job / "out.mp4"
    timeline = json.loads((job / "timeline.json").read_text(encoding="utf-8"))
    info = json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)]))
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    expected = timeline["durationFrames"] / timeline["fps"]
    problems = []
    if (v["width"], v["height"]) != (1080, 1920):
        problems.append(f"boyut {v['width']}x{v['height']}")
    if v["codec_name"] != "h264" or v["pix_fmt"] != "yuv420p":
        problems.append(f"kodek {v['codec_name']}/{v['pix_fmt']}")
    if a is None:
        problems.append("ses yok")
    if abs(dur - expected) > 0.2:
        problems.append(f"süre {dur:.2f}s, beklenen {expected:.2f}s")
    if a is not None and abs(float(a["duration"]) - float(v["duration"])) > 0.15:
        problems.append(f"ses {a['duration']}s, görüntü {v['duration']}s: senkron kayabilir")

    loud = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-af", "volumedetect", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    peak = re.search(r"max_volume: (-?[\d.]+)", loud)
    mean = re.search(r"mean_volume: (-?[\d.]+)", loud)
    if mean and float(mean.group(1)) < -35:
        problems.append(f"ses çok düşük ({mean.group(1)} dB)")

    qa = job / "qa"
    shutil.rmtree(qa, ignore_errors=True)
    qa.mkdir()
    fps = timeline["fps"]
    moments = []
    for e in timeline["events"]:
        latest = [e["from"] + min(22, max(1, (e["to"] - e["from"]) // 2))]
        for key in ("steps", "bars", "hops", "points", "items", "curves"):
            if e.get(key):
                latest.append(max(x["f"] for x in e[key]) + 22)
        for key in ("strike_f", "right_f", "answer_f"):
            if key in e:
                latest.append(e[key] + 22)
        moments.append((min(max(latest), e["to"] - 11, timeline["durationFrames"] - 1), e["id"], e["type"]))
    if not moments:
        moments = [(timeline["durationFrames"] // 2, "orta", "video")]
    for f, eid, kind in moments:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{max(f, 0) / fps:.3f}", "-i", str(video), "-frames:v", "1",
                        "-vf", "scale=540:-2", "-q:v", "3", str(qa / f"{max(f, 0):05d}_{eid}_{kind}.jpg")], check=True)
    cols = min(6, max(1, len(moments)))
    rows = max(1, -(-len(moments) // cols))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-pattern_type", "glob", "-i", str(qa / "*.jpg"),
                    "-vf", f"scale=270:-2,tile={cols}x{rows}", "-frames:v", "1", "-q:v", "3", str(qa / "sheet.jpg")],
                   check=True)

    size = video.stat().st_size / 1e6
    print(f"QA: {v['width']}x{v['height']} {v['codec_name']} {dur:.2f}s {size:.1f} MB, "
          f"tepe {peak.group(1) if peak else '?'} dB, ortalama {mean.group(1) if mean else '?'} dB")
    print(f"QA kareleri: {qa} ({len(moments)} kare, özet: {qa / 'sheet.jpg'})")
    for p in problems:
        print(f"  HATA: {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
