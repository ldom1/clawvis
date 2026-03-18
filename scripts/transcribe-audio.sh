#!/usr/bin/env bash
# Transcribe audio via Lab hub_core (Faster Whisper, local, no API key).
# Used by OpenClaw for Telegram voice notes when tools.media.audio.models uses this CLI.
# Usage: transcribe-audio.sh <path-to-audio>
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE_DIR="$SCRIPT_DIR/../core"
[[ -n "${1:-}" ]] || { echo "Usage: $0 <audio-file>" >&2; exit 1; }
cd "$CORE_DIR" && uv run python -m hub_core transcribe "$1" -l fr
