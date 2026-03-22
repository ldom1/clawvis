#!/usr/bin/env bash
set -euo pipefail

# Load instance secrets (TELEGRAM_TARGET_ID)
ENV_LOCAL="${HUB_ROOT:-$HOME/Lab/hub-ldom/instances/ldom}/.env.local"
[ -f "$ENV_LOCAL" ] && set -a && . "$ENV_LOCAL" && set +a

trap 'e=$?; [ $e -ne 0 ] && uv run --directory ~/.openclaw/skills/logger/core dombot-log "ERROR" "cron:brain-maintenance" "system" "trim:fail" "Brain maintenance trim failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:brain-maintenance" "system" "trim:start" "Brain maintenance trim started" 2>/dev/null || true

# Run trim — exit 1 if budget exceeded
if ! uv run --directory ~/.openclaw/skills/brain-maintenance/core python -m brain_maintenance trim; then
  # Budget dépassé : lire le total depuis stdout (déjà imprimé) et alerter directement
  SUMMARY=$(uv run --directory ~/.openclaw/skills/brain-maintenance/core \
    python -c "
from brain_maintenance.trim import audit_l1_files, L1_TOTAL_BUDGET
r = audit_l1_files()
print(f'L1 Budget dépassé : {r[\"total_tokens\"]}/{L1_TOTAL_BUDGET} tokens. Trop de contenu dans les fichiers SOUL/AGENTS/MEMORY. A nettoyer.')
" 2>/dev/null)
  if [ -n "${TELEGRAM_TARGET_ID:-}" ] && [ -n "$SUMMARY" ]; then
    openclaw message send --channel telegram --target "$TELEGRAM_TARGET_ID" \
      --message "🔴 Trim $SUMMARY" 2>/dev/null || true
  fi
  uv run --directory ~/.openclaw/skills/logger/core \
    dombot-log "WARNING" "cron:brain-maintenance" "system" "trim:over" "L1 budget exceeded — Telegram alert sent" 2>/dev/null || true
  exit 0  # Ne pas faire échouer le cron, l'alerte est envoyée
fi

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:brain-maintenance" "system" "trim:complete" "Brain maintenance trim finished — budget OK" 2>/dev/null || true

