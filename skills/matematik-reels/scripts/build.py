#!/usr/bin/env python3
"""Turn plan.json into a frame-accurate timeline, refusing anything that would ship wrong.

Usage: build.py JOB        (reads jobs/JOB/plan.json, writes jobs/JOB/timeline.json)
Errors stop the render. Warnings are for the author to judge against the rendered frames.
"""
import difflib
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

RUNTIME = Path(os.environ.get("MATEMATIK_REELS_HOME", Path.home() / ".local/share/matematik-reels"))
TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)

# ig-reel's safe zone for 1080x1920: clear of the top bar, the caption and the action rail.
SAFE = {"x0": 40, "x1": 850, "y0": 230, "y1": 1440}
SLOTS = {
    "top": (40, 230, 810, 400),
    "upper-left": (40, 230, 400, 400),
    "upper-right": (450, 230, 400, 400),
    "left": (40, 560, 400, 520),
    "right": (450, 560, 400, 520),
    "middle": (40, 500, 810, 480),
    "bottom": (40, 880, 810, 340),
    "stage": (40, 300, 810, 900),
}
ANCHOR_KEYS = {"at", "until", "strike_at", "right_at", "answer_at"}
BANNED_ASKS = re.compile(r"\b(dm|özelden|ozelden|mesaj at|anahtar kelimeyi)\b", re.I)
FEAR = re.compile(r"(sınıfta kal|aptal|salak|unut gitsin|lgs'?yi unut|son şans|hemen izle|kaybedersin|geride kalırsın)", re.I)
ALLOWED_TYPES = {"hook", "text", "formula", "steps", "compare", "quiz", "numberline", "graph", "shape",
                 "fractionbars", "camera", "broll"}


def tr_lower(text):
    return text.replace("İ", "i").replace("I", "ı").lower()


def norm(text):
    return re.sub(r"[^\wçğıöşü]+", "", tr_lower(text), flags=re.U)


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


class Anchors:
    """Locates spoken phrases in the transcript. Whisper spelling drifts, so matching is fuzzy but reported."""

    def __init__(self, words, report):
        self.words, self.report = words, report
        self.tokens = [norm(w["w"]) for w in words]

    def find(self, phrase, occ, where):
        target = [norm(t) for t in phrase.split() if norm(t)]
        if not target:
            self.report.err(f"{where}: boş ifade '{phrase}'")
            return None
        joined = "".join(target)
        hits = []
        n = len(target)
        # An exact phrase always beats a near one, or "yani parantez" also matches every "parantez".
        for i in range(0, len(self.tokens) - n + 1):
            if self.tokens[i:i + n] == target:
                hits.append((i, n, 1.0))
        for size in () if hits else {max(1, n - 1), n, n + 1}:
            for i in range(0, len(self.tokens) - size + 1):
                score = difflib.SequenceMatcher(None, joined, "".join(self.tokens[i:i + size])).ratio()
                if score >= 0.8:
                    hits.append((i, size, score))
        best = {}
        for i, size, score in hits:
            if i not in best or score > best[i][1]:
                best[i] = (size, score)
        # Neighbouring starts are one spoken instance, keep the strongest of each cluster.
        instances = []
        for i in sorted(best):
            size, score = best[i]
            if instances and i <= instances[-1][0] + instances[-1][1] - 1:
                if score > instances[-1][2]:
                    instances[-1] = (i, size, score)
            else:
                instances.append((i, size, score))
        if not instances:
            close = difflib.get_close_matches(joined, self.tokens, n=3, cutoff=0.5)
            self.report.err(f"{where}: '{phrase}' konuşmada bulunamadı. Yakın kelimeler: {close}")
            return None
        if len(instances) > 1 and occ is None:
            times = ", ".join(f"{self.words[i]['s']:.1f}s" for i, _, _ in instances)
            self.report.err(f"{where}: '{phrase}' {len(instances)} kez geçiyor ({times}). occ ile hangisi olduğunu seç.")
            return None
        index = (occ or 1) - 1
        if index >= len(instances):
            self.report.err(f"{where}: '{phrase}' için occ={occ} yok, {len(instances)} kez geçiyor.")
            return None
        i, size, _ = instances[index]
        return self.words[i]["s"], self.words[i + size - 1]["e"]


def run_checks(plan, report):
    """Every claim the video shows gets recomputed. A teacher's account cannot carry a wrong sum."""
    results = []
    for c in plan.get("checks", []):
        try:
            left = parse_expr(c["left"], transformations=TRANSFORMS, evaluate=True)
            right = parse_expr(c["right"], transformations=TRANSFORMS, evaluate=True)
            holds = sp.simplify(left - right) == 0
        except Exception as err:  # noqa: BLE001  any parse failure means the claim is unverified
            report.err(f"kontrol okunamadı: {c} ({err})")
            continue
        expected = c.get("holds", True)
        label = f"{c['left']} = {c['right']}"
        if holds != expected:
            report.err(f"MATEMATİK HATASI: {label} {'doğru' if holds else 'yanlış'} çıktı, plan tersini söylüyor.")
        results.append(f"{label}: {'doğru' if holds else 'yanlış'}")
    return results


def sample_curve(expr_text, xmin, xmax, ymin, ymax):
    x = sp.Symbol("x")
    fn = sp.lambdify(x, parse_expr(expr_text, transformations=TRANSFORMS), "numpy")
    xs = np.linspace(xmin, xmax, 240)
    ys = np.broadcast_to(np.asarray(fn(xs), dtype=float), xs.shape)
    margin = (ymax - ymin) * 0.05
    return [[round(float(a), 4), None if not np.isfinite(b) or b < ymin - margin or b > ymax + margin
             else round(float(b), 4)] for a, b in zip(xs, ys)]


def overlap(a, b):
    w = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    h = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    return max(0, w) * max(0, h)


def build(job):
    report = Report()
    plan = json.loads((job / "plan.json").read_text(encoding="utf-8"))
    meta = json.loads((job / "probe.json").read_text(encoding="utf-8"))
    words = json.loads((job / "words.json").read_text(encoding="utf-8"))
    fps, total = meta["fps"], meta["duration"]
    frames = round(total * fps)
    lead = plan.get("lead", 0.1)  # lands on the word: the spring needs a beat to read as arriving

    for w in words:
        key = norm(w["w"])
        for wrong, right in plan.get("corrections", {}).items():
            if key == norm(wrong):
                w["w"] = right
    anchors = Anchors(words, report)

    def time_of(obj, key, where, use_end=False):
        value = obj.get(key)
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        found = anchors.find(value, obj.get(f"{key}_occ"), where)
        if not found:
            return None
        return found[1] if use_end else found[0]

    def to_frame(seconds):
        return max(0, min(frames - 1, round(seconds * fps)))

    events, cameras, brolls = [], [], []
    face = plan.get("teacher", {}).get("face")

    def add_event(ev, index, in_broll=False):
        kind = ev.get("type")
        where = f"olay #{index} ({kind})"
        if kind not in ALLOWED_TYPES:
            report.err(f"{where}: bilinmeyen tip")
            return
        start = 0.0 if kind == "hook" and ev.get("at") is None else time_of(ev, "at", where)
        if start is None:
            if ev.get("at") is None:
                report.err(f"{where}: 'at' gerekli")
            return
        start = max(0.0, start - (0 if kind == "hook" else lead))

        if kind == "camera":
            cameras.append({"from": to_frame(start), "scale": ev.get("scale", 1), "x": ev.get("x", 0), "y": ev.get("y", 0)})
            return

        end = time_of(ev, "until", where, use_end=True)
        if end is None:
            end = start + ev.get("dur", 3.0)
        end = min(total, end + ev.get("hold", 0.25))

        if kind == "broll":
            brolls.append({"from": to_frame(start), "to": to_frame(end), "pip": ev.get("pip", True),
                           **({"focus": [face[0] + face[2] / 2, face[1] + face[3] / 2]} if face else {}),
                           **({"src": ev["src"]} if ev.get("src") else {}),
                           **({"title": ev["title"]} if ev.get("title") else {})})
            for j, child in enumerate(ev.get("scene", [])):
                add_event({"slot": "stage", **child, "_parent_end": end}, f"{index}.{j}", True)
            return

        if ev.get("_parent_end"):
            end = min(end, ev["_parent_end"])
        slot = ev.get("slot", "top")
        if isinstance(slot, list):
            box = dict(zip("xywh", slot))
        elif slot in SLOTS:
            box = dict(zip("xywh", SLOTS[slot]))
        else:
            report.err(f"{where}: bilinmeyen yer '{slot}'")
            return
        if box["x"] < SAFE["x0"] or box["x"] + box["w"] > SAFE["x1"] or box["y"] < SAFE["y0"] or box["y"] + box["h"] > SAFE["y1"]:
            report.err(f"{where}: Instagram arayüzünün altında kalıyor ({box})")

        out = {k: v for k, v in ev.items() if k not in ANCHOR_KEYS and not k.endswith("_occ") and not k.startswith("_")}
        out.update(id=f"e{index}", from_=to_frame(start), to=min(frames, to_frame(end) + 1), box=box, in_broll=in_broll)
        out["from"] = out.pop("from_")
        out.pop("slot", None)

        for key, target in (("strike_at", "strike_f"), ("right_at", "right_f"), ("answer_at", "answer_f")):
            t = time_of(ev, key, where)
            if t is not None:
                out[target] = to_frame(t - lead)
        for key in ("steps", "bars", "hops", "points", "items", "curves"):
            for j, child in enumerate(ev.get(key, []) or []):
                t = time_of(child, "at", f"{where}.{key}[{j}]")
                resolved = {k: v for k, v in child.items() if k != "at" and not k.endswith("_occ")}
                resolved["f"] = to_frame((t if t is not None else start) - (lead if t is not None else 0))
                if key == "curves":
                    try:
                        resolved["samples"] = sample_curve(child["fn"], ev["xmin"], ev["xmax"], ev["ymin"], ev["ymax"])
                    except Exception as err:  # noqa: BLE001
                        report.err(f"{where}: fonksiyon çizilemedi {child.get('fn')}: {err}")
                        return
                out[key] = out.get(key, [])
                if j == 0:
                    out[key] = []
                out[key].append(resolved)
        if kind == "compare" and "right_f" not in out:
            report.err(f"{where}: 'right_at' gerekli")
        if kind == "quiz":
            out.setdefault("seconds", 3)
            if "answer" in out and "answer_f" not in out:
                report.err(f"{where}: 'answer' için 'answer_at' gerekli")

        text = ev.get("text") or ""
        if text and len(text.split()) > 6:
            report.warn(f"{where}: ekranda {len(text.split())} kelime. Bir bakışta okunması için en fazla 6.")
        if FEAR.search(text):
            report.err(f"{where}: korku veya aşağılama dili: '{text}'")
        if (out["to"] - out["from"]) / fps < 1.0:
            report.warn(f"{where}: ekranda {(out['to'] - out['from']) / fps:.1f}s kalıyor, okunmaz.")
        events.append(out)

    for i, ev in enumerate(plan.get("events", [])):
        add_event(ev, i)

    cameras.sort(key=lambda c: c["from"])
    brolls.sort(key=lambda b: b["from"])
    events.sort(key=lambda e: e["from"])

    def in_broll_at(frame):
        return any(b["from"] <= frame < b["to"] for b in brolls)

    def camera_at(frame):
        pose = {"scale": 1, "x": 0, "y": 0}
        for c in cameras:
            if c["from"] <= frame:
                pose = c
        return pose

    hooks = [e for e in events if e["type"] == "hook"]
    if not hooks:
        report.warn("Hook kartı yok. İlk karede okunacak bir yazı izleyiciyi tutar.")
    elif hooks[0]["from"] > 0:
        report.err("Hook kartı ilk karede başlamalı.")

    for i, a in enumerate(events):
        box_a = (a["box"]["x"], a["box"]["y"], a["box"]["w"], a["box"]["h"])
        for b in events[i + 1:]:
            if b["from"] >= a["to"] - 8:  # exit spring overlap is fine
                continue
            box_b = (b["box"]["x"], b["box"]["y"], b["box"]["w"], b["box"]["h"])
            if overlap(box_a, box_b) > 0:
                report.err(f"{a['id']} ({a['type']}) ile {b['id']} ({b['type']}) üst üste biniyor. Yer veya süre değiştir.")
        if face and not a.get("in_broll") and not in_broll_at(a["from"]):
            cam = camera_at(a["from"])
            s = cam["scale"]
            # transform-origin 50% 45% in Reel.tsx
            cx, cy = 540, 864
            moved = (cx + (face[0] - cx) * s + cam["x"], cy + (face[1] - cy) * s + cam["y"], face[2] * s, face[3] * s)
            share = overlap(box_a, moved) / max(1, moved[2] * moved[3])
            if share > 0.15:
                report.err(f"{a['id']} ({a['type']}) yüzünün %{share * 100:.0f}'ini kapatıyor. Başka yer seç veya camera ile kaydır.")

    # Long stretches with nothing changing are where viewers leave.
    marks = {0, frames} | {e["from"] for e in events} | {c["from"] for c in cameras} | {b["from"] for b in brolls}
    for e in events:
        for key in ("steps", "bars", "hops", "points", "items", "curves"):
            marks |= {x["f"] for x in e.get(key, [])}
        marks |= {e[k] for k in ("strike_f", "right_f", "answer_f") if k in e}
    marks = sorted(marks)
    for a, b in zip(marks, marks[1:]):
        if (b - a) / fps > 6:
            report.warn(f"{a / fps:.1f}-{b / fps:.1f}s arası {(b - a) / fps:.1f}s görsel değişim yok.")

    if not 15 <= total <= 90:
        report.warn(f"Süre {total:.1f}s. Reels ve Shorts için hedef 30-50 sn.")

    # Words spoken far faster than a 12-year-old can follow.
    if words:
        speech = max(1e-3, words[-1]["e"] - words[0]["s"])
        wpm = len(words) / speech * 60
        if wpm > 170:
            report.warn(f"Konuşma hızı {wpm:.0f} kelime/dk. Ortaokul için yüksek, adımlar arasına duraklama koy.")

    captions = []
    if plan.get("captions", True):
        group = []
        def flush():
            if not group:
                return
            captions.append({
                "f0": to_frame(group[0]["s"]),
                "f1": min(frames, to_frame(group[-1]["e"]) + 2),
                "words": [{"w": w["w"].strip(".,;:"), "f0": to_frame(w["s"]), "f1": max(to_frame(w["s"]) + 1, to_frame(w["e"]))} for w in group],
            })
            group.clear()
        for w in words:
            joined = " ".join(x["w"] for x in group + [w])
            if group and (len(joined) > 26 or len(group) >= 5 or w["s"] - group[-1]["e"] > 0.35):
                flush()
            group.append(w)
            if w["w"][-1] in ".?!":
                flush()
        flush()
        for c, nxt in zip(captions, captions[1:]):
            c["f1"] = min(c["f1"], nxt["f0"])

    results = run_checks(plan, report)
    if not plan.get("checks"):
        report.err("checks boş. Videodaki her işlem SymPy ile kontrol edilmeli.")

    source =meta["source"] if meta["video"] else None
    timeline = {"fps": fps, "width": 1080, "height": 1920, "durationFrames": frames, "src": source,
                "captions": captions, "events": events, "cameras": cameras, "brolls": brolls,
                "audio": meta["source"] if not meta["video"] else None}
    if not meta["video"] and sum(b["to"] - b["from"] for b in brolls) < frames * 0.95:
        report.err("Yalnız ses var: broll tüm süreyi kaplamalı, yoksa ekran boş kalır.")
    (job / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False), encoding="utf-8")

    print(f"{len(events)} olay, {len(cameras)} kamera, {len(brolls)} b-roll, {len(captions)} altyazı grubu, {total:.1f}s")
    for line in results:
        print(f"  işlem: {line}")
    for w in report.warnings:
        print(f"  UYARI: {w}")
    for e in report.errors:
        print(f"  HATA: {e}")
    return 1 if report.errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(build(RUNTIME / "jobs" / sys.argv[1]))
