---
name: matematik-reels
description: >-
  Turn a math teacher's vertical video or voice recording into a finished Instagram Reel and YouTube
  Short: word-by-word transcription, math animations placed beside the teacher and timed to their
  voice, full-screen animated b-roll where it helps, burned-in captions, plus caption, title and
  description. Also writes the hook and script when nothing is recorded yet. Use whenever the user
  sends a video or audio file to animate, or says things like "animasyonlu video yap", "bu videoya
  animasyon ekle", "yanıma animasyon koy", "b-roll ekle", "reels yap", "shorts yap", "bu kazanımı
  videoya çevir", "şu konuyu anlatan video", even if they don't mention Remotion or this skill.
---

# matematik-reels

The user is a Turkish middle school math teacher, starting with 8th grade and LGS. Talk to them in
Turkish, in plain language. Their voice leads the video and every animation follows it.

Paths: `S=~/.claude/skills/matematik-reels`, `PY=~/.local/share/matematik-reels/venv/bin/python`.
`render.sh` prints the delivery folder; its root comes from `$MATEMATIK_REELS_OUT` or the
`~/.local/share/matematik-reels/out_dir` file, otherwise `./videolar/`.

If `$PY` is missing, run `$S/scripts/setup.sh` first.

## Pick the path

- **Video sent:** follow the full flow below.
- **Voice recording only:** same flow. `prepare.py` detects it, and `broll` scenes must cover the
  whole length, because there is no teacher on screen.
- **Topic or kazanım only:** nothing can be synced yet, and generating a fake teacher voice is not
  what they asked for. Write the script (step "No recording yet") and wait for the recording.

## Full flow

### 1. Prepare

Use a short ASCII job name, like `uslu-eksi-kare`.

```bash
$PY $S/scripts/prepare.py "/path/video.mp4" --job NAME --tighten 0.45
```

`--tighten` removes pauses, which is most of what makes a talking video feel fast. Skip it if the
teacher uses silence on purpose, such as a "durdur ve çöz" pause. Add `--cut 12.4-15.0` to remove a
retake (original-recording seconds), after reading a first transcript if needed.

### 2. Understand the video

Read `jobs/NAME/transcript.txt` and view `jobs/NAME/contact.jpg`; view single frames from `frames/`
when the layout is unclear. Establish:

- The one idea being taught and the misconception behind it.
- Where the face and hands are, and where the free space is. Frames are 360px wide, so multiply by
  3 to get 1080-space coordinates for `teacher.face`.
- Whether the math the teacher says is correct. If they misspeak, stop and tell them; do not paper
  over it with a correct animation or ship the error.

Whisper mishears math. Fix wrong words through `corrections` in the plan, and if a number or formula
is uncertain, ask rather than guess.

### 3. Write the plan

Read `references/plan-format.md`, then write `jobs/NAME/plan.json`. Read `references/teaching.md`
for what to show and when. The choices that matter most:

- **Beside the teacher by default.** Use a slot clear of the face, moving the teacher with `camera`
  when there is no room.
- **Show on the word.** Anchor each thing to the phrase that introduces it, so the viewer hears and
  sees it together.
- **B-roll when the teacher's face adds nothing:** a graph being drawn, a geometric construction, a
  long calculation. Keep each one 3-8 seconds. Going back to the face rebuilds the connection.
- **Something changes every 2-4 seconds,** but only if it carries meaning. Decoration competes with
  the math for the attention of a 13-year-old.
- **List every shown calculation in `checks`,** including deliberately wrong claims with
  `"holds": false`.

### 4. Build, fix, render

```bash
$PY $S/scripts/build.py NAME     # fix every HATA, judge every UYARI
$S/scripts/render.sh NAME        # also runs qa.py
```

### 5. Look at what rendered

View `jobs/NAME/qa/sheet.jpg`, then individual `qa/*.jpg` wherever anything looks off. The build
checks boxes, not pixels, so this is where real problems show: a formula covering a hand, unreadable
text on a bright background, a broken formula, a transcript error in the captions. Fix the plan and
rebuild until the frames are clean. Say honestly that you checked sampled frames rather than watching
the video.

### 6. Write the post package

Follow `references/package.md`, using the existing `ig-*` and `yt-*` skills, and save
`paket.md` beside the video.

### 7. Hand over

Report the delivery folder, the length, what the math check verified, and anything you could not
confirm. Nothing gets published by this skill: the teacher reviews the video and posts it. After they
approve, append date, hook and topic to `~/.claude/instagram/log.md`, so `/ig-audit` has a history.

## No recording yet

1. Ask only for what is missing: the kazanım, the grade and the mistake students usually make. If they
   don't give the mistake, propose one and let them correct it.
2. Read `references/teaching.md`, then `~/.claude/skills/ig-reel/hooks.json`. Write three hooks and the
   30-50 second script using the structure in `teaching.md`.
3. Time it: `python3 ~/.claude/skills/ig-reel/beats.py script.txt --target 40`. Use the score from
   `hookscore.py` only as a rough signal, since its word lists are built for English, and judge the
   Turkish yourself.
4. Give the script with shooting notes: which side to stand on, where animations will appear, and
   formulas spelled out as spoken ("x kare eksi dokuz").
5. Say that you will add the animations once the recording arrives.

## When this needs more than the plan

The components cover most lessons. If a topic needs a visual they can't express, add a component to
`$S/engine/src/events.tsx`, using springs or cubic-bezier easing and never linear motion, and register
it in `ALLOWED_TYPES` in `build.py`. `render.sh` copies the engine source on every run.
