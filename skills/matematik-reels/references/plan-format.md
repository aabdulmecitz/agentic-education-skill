# plan.json

```json
{
  "topic": "Üslü ifadelerde parantez",
  "teacher": {"face": [340, 300, 400, 480]},
  "corrections": {"üsü": "üssü"},
  "captions": true,
  "lead": 0.1,
  "checks": [
    {"left": "(-2)^2", "right": "4"},
    {"left": "-2^2", "right": "4", "holds": false}
  ],
  "events": []
}
```

- `teacher.face`: `[x, y, w, h]` in 1080x1920. `build.py` rejects cards covering over 15% of it.
- `corrections`: wrong Whisper word to the right word. Also corrects burned-in captions.
- `lead`: seconds an animation starts before its word. The default suits nearly everything.
- `checks`: `left`, `right` in Python-math notation (`^` allowed), `holds` defaults to true.

## Timing fields

- `at`: phrase the teacher says, copied from the transcript, or a number of seconds. Prefer phrases,
  which survive re-tightening.
- `until`: phrase whose end closes the event, or use `dur` in seconds (default 3). `hold` adds tail
  (default 0.25).
- If a phrase occurs more than once, `build.py` stops and lists the times; pick with `at_occ`,
  `until_occ`, `strike_at_occ` and so on (1-based).
- Keep phrases to 2-4 distinctive words. A single common word like "eksi" matches everywhere.

## Slots

`slot` is a name or `[x, y, w, h]`. Everything must stay inside x 40-850, y 230-1440, because Instagram
and Shorts interface covers the rest. Captions occupy y 1250-1430 (hide with `"captions": false`).

| Slot | x, y, w, h | Use |
|---|---|---|
| `top` | 40, 230, 810, 400 | Teacher lower in frame |
| `upper-left`, `upper-right` | 40 or 450, 230, 400, 400 | Beside the head |
| `left`, `right` | 40 or 450, 560, 400, 520 | Beside the body, gestures toward it |
| `middle` | 40, 500, 810, 480 | Teacher moved away or in b-roll |
| `bottom` | 40, 880, 810, 340 | Teacher high in frame |
| `stage` | 40, 300, 810, 900 | B-roll default |

## Events

`tone` is `wrong`, `right` or `accent` wherever it appears. LaTeX strings need JSON-escaped backslashes.

```jsonc
// First-frame hook. No "at" needed. Six words at most. "accent" colours those letters.
{"type": "hook", "text": "Bu soruda herkes yanılıyor", "accent": "herkes", "until": "yanılıyor", "slot": "top"}

// Short sentence on a card.
{"type": "text", "text": "Parantez her şeyi değiştirir", "at": "parantez", "dur": 2.5, "tone": "accent"}

// One formula. strike_at draws a red line through it on a spoken phrase.
{"type": "formula", "latex": "-2^2 = 4", "tone": "wrong", "at": "çoğu kişi", "strike_at": "bu yanlış", "until": "bu yanlış", "slot": "right"}

// Solution revealed line by line, on the teacher's words. Older lines dim.
{"type": "steps", "at": "önce açalım", "until": "sonuç dört", "slot": "top",
 "steps": [{"latex": "(-2)^2", "at": "önce açalım"},
           {"latex": "(-2)\\cdot(-2)", "at": "iki kere"},
           {"latex": "= 4", "at": "sonuç dört", "tone": "right"}]}

// Mistake crossed out, correct version below.
{"type": "compare", "wrong": "(a-b)^2 = a^2-b^2", "right": "(a-b)^2 = a^2-2ab+b^2",
 "at": "çoğu öğrenci", "strike_at": "bu yanlış", "right_at": "doğrusu", "until": "doğrusu şu", "slot": "top"}

// Pause-and-solve with countdown ring. answer and answer_at are optional.
{"type": "quiz", "label": "Durdur ve çöz", "latex": "(-3)^2 = ?", "seconds": 3, "at": "şimdi sen", "dur": 3.5,
 "answer": "9", "answer_at": "cevap dokuz", "slot": "middle"}

// Number line with points and hops.
{"type": "numberline", "min": -5, "max": 5, "step": 1, "at": "sayı doğrusunda", "dur": 6, "slot": "middle",
 "points": [{"v": -2, "label": "A", "at": "eksi iki"}],
 "hops": [{"start": -2, "end": 3, "label": "+5", "at": "beş ileri"}]}

// Function curves. fn is Python-math in x, sampled by SymPy, so the curve is exact.
{"type": "graph", "xmin": -4, "xmax": 4, "ymin": -2, "ymax": 8, "at": "grafiğe bakalım", "dur": 6, "slot": "stage",
 "curves": [{"fn": "2*x + 1", "at": "grafiğe bakalım", "tone": "accent"}],
 "points": [{"x": 0, "y": 1, "label": "(0, 1)", "at": "y eksenini"}]}

// Geometry in your own coordinate space. kind: poly, line, circle, label. Each item has its own "at".
{"type": "shape", "view": [100, 100], "at": "kareyi çizelim", "dur": 7, "slot": "stage",
 "items": [{"kind": "poly", "pts": [[0,0],[100,0],[100,100],[0,100]], "at": "kareyi çizelim"},
           {"kind": "poly", "pts": [[0,0],[70,0],[70,70],[0,70]], "fill": true, "tone": "right", "at": "küçük kare"},
           {"kind": "line", "pts": [[70,0],[70,100]], "tone": "wrong", "at": "kenarı"},
           {"kind": "circle", "cx": 50, "cy": 50, "r": 20, "at": "çember"},
           {"kind": "label", "x": 35, "y": 40, "text": "a²", "at": "küçük kare"}]}

// Fraction bars, one per fraction.
{"type": "fractionbars", "at": "hangisi büyük", "dur": 6, "slot": "middle",
 "bars": [{"n": 3, "d": 4, "at": "dörtte üç"}, {"n": 5, "d": 7, "at": "yedide beş"}]}

// Move or push in on the teacher; holds until the next camera event. Moves are springs.
{"type": "camera", "at": "dikkat edin", "scale": 1.18, "x": 0, "y": 120}
{"type": "camera", "at": "şimdi", "scale": 1, "x": -180, "y": 200}

// Full-screen b-roll. pip keeps the teacher in a small circle. src is an optional silent video file
// the user has rights to, copied into the job folder. scene holds normal events, default slot "stage".
{"type": "broll", "at": "alan modeli", "until": "iki ab gelir", "pip": true, "title": "Alan modeli",
 "scene": [{"type": "shape", "view": [100, 100], "at": "alan modeli", "items": []}]}
```

Events in the same place and time are rejected. Stack them in separate slots or give them separate
time ranges. Leave `at` on every sub-item that should appear on a word; without one it appears when
the parent does.
