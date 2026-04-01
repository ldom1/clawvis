#!/usr/bin/env bash
# Wire Clawvis skill trees into OpenClaw via skills.load.extraDirs (no symlinks under ~/.openclaw/skills).
# Env: ROOT_DIR, INSTANCE_NAME (optional), OPENCLAW_CONFIG (optional), NO_RESTART=1 to skip gateway/doctor.
# Needs: jq (merge JSON). openclaw on PATH or ~/.npm-global/bin.
set -euo pipefail

ROOT_DIR="${ROOT_DIR:?ROOT_DIR required}"
INSTANCE_NAME="${INSTANCE_NAME:-example}"
OPENCLAW_CONFIG="${OPENCLAW_CONFIG:-${HOME}/.openclaw/openclaw.json}"
MANAGED_SKILLS="${HOME}/.openclaw/skills"
export PATH="${HOME}/.npm-global/bin:${PATH}"

log() { printf "==> %s\n" "$1"; }
warn() { printf "[warn] %s\n" "$1"; }
die() { printf "[error] %s\n" "$1" >&2; exit 1; }

if [[ ! -f "${OPENCLAW_CONFIG}" ]]; then
  log "No OpenClaw config at ${OPENCLAW_CONFIG} — skip (nothing to update)."
  exit 0
fi

command -v jq >/dev/null 2>&1 || die "jq is required (e.g. apt install jq / brew install jq) to patch openclaw.json"

declare -a dirs=()
_core="${ROOT_DIR}/skills"
_inst="${ROOT_DIR}/instances/${INSTANCE_NAME}/skills"
[[ -d "${_core}" ]] && dirs+=("$(cd "${_core}" && pwd)")
[[ -d "${_inst}" ]] && dirs+=("$(cd "${_inst}" && pwd)")
[[ ${#dirs[@]} -eq 0 ]] && die "No skill dirs: ${_core} or ${_inst}"

_extra_json="$(jq -n '$ARGS.positional' --args "${dirs[@]}")"
_tmp="${OPENCLAW_CONFIG}.$$.$RANDOM"
jq --argjson extra "${_extra_json}" \
  '.skills = (.skills // {}) | .skills.load = (.skills.load // {}) | .skills.load.extraDirs = $extra' \
  "${OPENCLAW_CONFIG}" >"${_tmp}"
mv "${_tmp}" "${OPENCLAW_CONFIG}"

log "Updated ${OPENCLAW_CONFIG} — skills.load.extraDirs:"
for d in "${dirs[@]}"; do printf '    %s\n' "$d"; done

if [[ -d "${MANAGED_SKILLS}" ]]; then
  shopt -s nullglob
  for f in "${MANAGED_SKILLS}"/*; do
    [[ -L "${f}" ]] || continue
    log "Removing symlink ${f}"
    rm -f "${f}"
  done
  shopt -u nullglob
fi

if [[ "${NO_RESTART:-0}" == "1" ]]; then
  log "NO_RESTART=1 — run: openclaw gateway restart && openclaw skills list && openclaw doctor"
  exit 0
fi

if ! command -v openclaw >/dev/null 2>&1; then
  warn "openclaw not found (PATH / ~/.npm-global/bin) — run: openclaw gateway restart && openclaw skills list && openclaw doctor"
  exit 0
fi

log "openclaw skills list…"
openclaw skills list || warn "openclaw skills list failed"

log "openclaw doctor…"
openclaw doctor || warn "openclaw doctor failed"

log "openclaw gateway restart…"
openclaw gateway restart || warn "openclaw gateway restart failed"
