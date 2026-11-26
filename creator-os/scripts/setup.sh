#!/usr/bin/env bash
# One-time setup on the creator's Mac (or any machine with the media on it).
set -euo pipefail
cd "$(dirname "$0")/.."
command -v ffmpeg >/dev/null || { echo "Install ffmpeg first:  brew install ffmpeg"; exit 1; }
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip -q
pip install -r scripts/requirements.txt -q
if [[ "${1:-}" == "--semantic" ]]; then pip install open_clip_torch torch -q; fi
echo "Creator OS ready. Activate with:  source .venv/bin/activate   then run:  claude"
