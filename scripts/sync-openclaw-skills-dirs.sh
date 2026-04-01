#!/usr/bin/env bash
# Wire Clawvis skill trees into OpenClaw via skills.load.extraDirs (no symlinks under ~/.openclaw/skills).
# Env: ROOT_DIR (clawvis repo), INSTANCE_NAME (optional), OPENCLAW_CONFIG (optional), NO_RESTART=1 to skip systemd.
set -euo pipefail

ROOT_DIR="${ROOT_DIR:?ROOT_DIR required}"
INSTANCE_NAME="${INSTANCE_NAME:-example}"
export ROOT_DIR INSTANCE_NAME
OPENCLAW_CONFIG="${OPENCLAW_CONFIG:-${HOME}/.openclaw/openclaw.json}"
export OPENCLAW_CONFIG
MANAGED_SKILLS="${HOME}/.openclaw/skills"

log() { printf "==> %s\n" "$1"; }
warn() { printf "[warn] %s\n" "$1"; }

if [[ ! -f "${OPENCLAW_CONFIG}" ]]; then
  log "No OpenClaw config at ${OPENCLAW_CONFIG} — skip (nothing to update)."
  exit 0
fi

mapfile -t dirs < <(python3 <<'PY'
import json
import os
import sys
from pathlib import Path

root = Path(os.environ["ROOT_DIR"])
inst_name = os.environ["INSTANCE_NAME"]
cfg_path = Path(os.environ["OPENCLAW_CONFIG"])

out: list[str] = []
core = root / "skills"
ins = root / "instances" / inst_name / "skills"
if core.is_dir():
    out.append(str(core.resolve()))
if ins.is_dir():
    out.append(str(ins.resolve()))
if not out:
    sys.stderr.write(
        "no Clawvis skill directories found (skills/ or instances/<INSTANCE>/skills/)\n"
    )
    raise SystemExit(1)

data = json.loads(cfg_path.read_text(encoding="utf-8"))
skills = data.setdefault("skills", {})
load = skills.setdefault("load", {})
load["extraDirs"] = out
cfg_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
for d in out:
    print(d)
PY
)

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
  log "NO_RESTART=1 — start OpenClaw gateway yourself if needed."
  exit 0
fi

if command -v systemctl >/dev/null 2>&1 && systemctl --user show openclaw-gateway.service &>/dev/null; then
  if systemctl --user is-active openclaw-gateway.service &>/dev/null; then
    log "Restarting openclaw-gateway (user)…"
    systemctl --user restart openclaw-gateway.service
  else
    log "Starting openclaw-gateway (user)…"
    systemctl --user start openclaw-gateway.service || warn "systemctl start failed"
  fi
else
  warn "No user systemd unit openclaw-gateway.service — restart gateway manually."
fi
