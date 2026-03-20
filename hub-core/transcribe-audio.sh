#!/usr/bin/env bash
# Transcribe audio via local hub_core (Faster Whisper, no API key required).
#
# Usage: transcribe-audio.sh <path-to-audio>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

[[ -n "${1:-}" ]] || { echo "Usage: $0 <audio-file>" >&2; exit 1; }

cd "$SCRIPT_DIR"
uv run python -m hub_core transcribe "$1" -l fr

