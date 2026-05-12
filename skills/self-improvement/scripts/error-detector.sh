#!/bin/bash
# Self-Improvement Error Detector Hook

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_clawvis_env.sh"
clawvis_env_load || LOGGER_CORE=""

trap 'e=$?; [ $e -ne 0 ] && dombot_log_uv dombot-log "ERROR" "hook:self-improvement" "system" "hook:error-detector:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

OUTPUT="${CLAUDE_TOOL_OUTPUT:-}"

ERROR_PATTERNS=(
  "error:"
  "Error:"
  "ERROR:"
  "failed"
  "FAILED"
  "command not found"
  "No such file"
  "Permission denied"
  "fatal:"
  "Exception"
  "Traceback"
  "npm ERR!"
  "ModuleNotFoundError"
  "SyntaxError"
  "TypeError"
  "exit code"
  "non-zero"
)

contains_error=false
for pattern in "${ERROR_PATTERNS[@]}"; do
  if [[ "$OUTPUT" == *"$pattern"* ]]; then
    contains_error=true
    break
  fi
done

if [ "$contains_error" = true ]; then
  cat << 'EOF'
<error-detected>
A command error was detected. Consider logging this to .learnings/ERRORS.md if:
- The error was unexpected or non-obvious
- It required investigation to resolve
- It might recur in similar contexts
- The solution could benefit future sessions

Use the self-improvement skill format: [ERR-YYYYMMDD-XXX]
</error-detected>
EOF
  dombot_log_uv dombot-log "WARNING" "hook:self-improvement" "system" "hook:error-detected" "Command error detected, reminder shown" 2>/dev/null || true
fi
