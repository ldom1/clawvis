#!/usr/bin/env bash
# Morning workflow: process newsletters (Medium + TLDR) then send daily briefing.
# Step 1 — email-sync (filtered): only archives matching senders; others stay in INBOX.
# Step 2 — morning-briefing: reads fresh curiosity notes written in step 1.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
KC_CORE="${SKILLS_ROOT}/knowledge-consolidator/core"

# shellcheck disable=SC1091
source "${SKILLS_ROOT}/_clawvis_env.sh"
clawvis_env_load || true

LOG_DIR="${LOG_DIR:-${TMPDIR:-/tmp}/clawvis-logs}"
mkdir -p "$LOG_DIR"

_log() { echo "[$(date '+%H:%M:%S')] $*"; }

# Step 1 — newsletter email sync
_log "email-sync: processing Medium + TLDR newsletters"
MAIL_NEWSLETTER_SENDERS="${MAIL_NEWSLETTER_SENDERS:-@medium.com,@tldrnewsletter.com}" \
  UV_PROJECT_ENVIRONMENT="${TMPDIR:-/tmp}/clawvis-venvs/knowledge-consolidator-core" \
  uv run --directory "$KC_CORE" python -m knowledge_consolidator mail \
  && _log "email-sync: done" \
  || _log "email-sync: failed (non-fatal, briefing continues)"

# Step 2 — morning briefing
_log "morning-briefing: starting"
bash "$SCRIPT_DIR/run.sh"
_log "morning-briefing: done"
