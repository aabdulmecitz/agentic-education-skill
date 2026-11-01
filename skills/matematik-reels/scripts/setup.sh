#!/usr/bin/env bash
# Installs everything the skill needs. Safe to run repeatedly.
# Runtime lives outside the skill folder so node_modules and models stay out of it.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME="${MATEMATIK_REELS_HOME:-$HOME/.local/share/matematik-reels}"
mkdir -p "$RUNTIME/engine" "$RUNTIME/jobs"

command -v ffmpeg >/dev/null || { echo "ffmpeg yok: sudo apt install ffmpeg" >&2; exit 1; }
command -v node >/dev/null || { echo "Node yok" >&2; exit 1; }

if [ ! -x "$RUNTIME/venv/bin/python" ]; then
  python3 -m venv "$RUNTIME/venv"
fi
"$RUNTIME/venv/bin/pip" install -q --upgrade pip
"$RUNTIME/venv/bin/pip" install -q faster-whisper sympy numpy
if command -v nvidia-smi >/dev/null && nvidia-smi -L >/dev/null 2>&1; then
  "$RUNTIME/venv/bin/pip" install -q nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*" \
    || echo "UYARI: CUDA kutuphaneleri kurulamadi, yazi dokumu CPU'da calisir." >&2
fi

cp -a "$SKILL_DIR/engine/." "$RUNTIME/engine/"
cd "$RUNTIME/engine"
npm install --no-audit --no-fund --loglevel=error
npx remotion browser ensure >/dev/null
echo "Kurulum tamam: $RUNTIME"
