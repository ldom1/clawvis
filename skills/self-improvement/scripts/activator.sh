#!/bin/bash
# Self-Improvement Activator Hook

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_clawvis_env.sh"
clawvis_env_load || LOGGER_CORE=""

trap 'e=$?; [ $e -ne 0 ] && dombot_log_uv dombot-log "ERROR" "hook:self-improvement" "system" "hook:activator:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

cat << 'EOF'
<self-improvement-reminder>
After completing this task, evaluate if extractable knowledge emerged:
- Non-obvious solution discovered through investigation?
- Workaround for unexpected behavior?
- Project-specific pattern learned?
- Error required debugging to resolve?

If yes: Log to .learnings/ using the self-improvement skill format.
If high-value (recurring, broadly applicable): Consider skill extraction.
</self-improvement-reminder>
EOF
dombot_log_uv dombot-log "INFO" "hook:self-improvement" "system" "hook:activator" "Self-improvement reminder shown" 2>/dev/null || true
