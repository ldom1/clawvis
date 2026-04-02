#!/usr/bin/env bash
# OpenClaw tools.media.audio : stdout = transcript.  --config → hub_core openclaw-audio-config
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
cd "${ROOT}/hub-core"

if [ "${1:-}" = "--config" ]; then
  shift
  extra=()
  for a in "$@"; do [ "$a" = "--apply" ] && extra+=(--apply); done
  [ ! -x "${SELF}" ] && [ -f "${SELF}" ] && chmod +x "${SELF}" || true
  export OPENCLAW_JSON="${OPENCLAW_JSON:-${HOME}/.openclaw/openclaw.json}"
  exec uv run python -m hub_core openclaw-audio-config --wrapper "${SELF}" "${extra[@]}"
fi

MEDIA="${1:?usage: $0 <audio-file> | $0 --config [--apply]}"
exec uv run python -m hub_core transcribe "${MEDIA}" \
  -l "${TRANSCRIBE_LANG:-fr}" -m "${TRANSCRIBE_MODEL:-base}"
