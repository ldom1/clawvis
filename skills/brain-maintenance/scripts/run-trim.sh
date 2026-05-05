#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CORE_BRAIN="$SKILL_ROOT/core"
# shellcheck disable=SC1091
source "$(cd "$SKILL_ROOT/.." && pwd)/_clawvis_env.sh"
clawvis_env_load || true

ENV_LOCAL="${HUB_ROOT:-$HOME/Lab/hub-ldom/instances/ldom}/.env.local"
[ -f "$ENV_LOCAL" ] && set -a && . "$ENV_LOCAL" && set +a

trap 'e=$?; [ $e -ne 0 ] && [ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && clawvis_uv_run_dir "$LOGGER_CORE" dombot-log "ERROR" "cron:brain-maintenance" "system" "trim:fail" "Brain maintenance trim failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

[ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && clawvis_uv_run_dir "$LOGGER_CORE" \
  dombot-log "INFO" "cron:brain-maintenance" "system" "trim:start" "Brain maintenance trim started" 2>/dev/null || true

if ! clawvis_uv_run_dir "$CORE_BRAIN" python -m brain_maintenance trim; then
  SUMMARY=$(clawvis_uv_run_dir "$CORE_BRAIN" \
    python -c "
from brain_maintenance.trim import audit_l1_files, L1_TOTAL_BUDGET
r = audit_l1_files()
print(f'L1 Budget dépassé : {r[\"total_tokens\"]}/{L1_TOTAL_BUDGET} tokens. Trop de contenu dans les fichiers SOUL/AGENTS/MEMORY. A nettoyer.')
" 2>/dev/null)
  if [ -n "$SUMMARY" ]; then
    _tg="${TELEGRAM_URL:-http://127.0.0.1:8094}"
    payload=$(REPORT="$SUMMARY" python3 -c 'import json, os; print(json.dumps({"text": "🔴 Trim " + os.environ["REPORT"]}))')
    curl -fsS -X POST "${_tg%/}/send" -H "Content-Type: application/json" -d "$payload" 2>/dev/null || true
  fi
  [ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && clawvis_uv_run_dir "$LOGGER_CORE" \
    dombot-log "WARNING" "cron:brain-maintenance" "system" "trim:over" "L1 budget exceeded — Telegram alert sent" 2>/dev/null || true
  exit 0
fi

[ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && clawvis_uv_run_dir "$LOGGER_CORE" \
  dombot-log "INFO" "cron:brain-maintenance" "system" "trim:complete" "Brain maintenance trim finished — budget OK" 2>/dev/null || true
