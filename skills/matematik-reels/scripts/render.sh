#!/usr/bin/env bash
# Renders a built job, samples QA frames at each event, and copies the result to OUT_DIR.
# Usage: render.sh JOB [OUT_DIR]
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME="${MATEMATIK_REELS_HOME:-$HOME/.local/share/matematik-reels}"
JOB="$RUNTIME/jobs/$1"
# Default delivery root is machine-specific: set it with $MATEMATIK_REELS_OUT or $RUNTIME/out_dir.
OUT_ROOT="${MATEMATIK_REELS_OUT:-$(cat "$RUNTIME/out_dir" 2>/dev/null || echo "$PWD/videolar")}"
OUT_DIR="${2:-$OUT_ROOT/$1}"
[ -f "$JOB/timeline.json" ] || { echo "Önce build.py çalıştır: $JOB/timeline.json yok" >&2; exit 1; }

# The skill folder is the source of truth for engine code.
cp -a "$SKILL_DIR/engine/src/." "$RUNTIME/engine/src/"
cd "$RUNTIME/engine"

COMMON=(--props="$JOB/timeline.json" --public-dir="$JOB" --log=error)
npx remotion render src/index.ts Reel "$JOB/out.mp4" "${COMMON[@]}" \
  --codec=h264 --crf=18 --pixel-format=yuv420p --audio-bitrate=192k

# Cover frame: the hook fully landed.
npx remotion still src/index.ts Reel "$JOB/kapak.png" "${COMMON[@]}" --frame=20

"$RUNTIME/venv/bin/python" "$SKILL_DIR/scripts/qa.py" "$1"

mkdir -p "$OUT_DIR"
cp "$JOB/out.mp4" "$OUT_DIR/video.mp4"
cp "$JOB/kapak.png" "$OUT_DIR/kapak.png"
cp "$JOB/plan.json" "$JOB/transcript.txt" "$OUT_DIR/"
echo "Teslim klasörü: $OUT_DIR"
