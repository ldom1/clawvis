#!/usr/bin/env bash
# Write a log entry (dombot.log + dombot.jsonl) and route to Slack if pattern matches.
# Usage: dombot-log.sh LEVEL PROCESS MODEL ACTION MESSAGE [METADATA_JSON]
# Example: dombot-log.sh INFO "cron:self-improvement" system cron:complete "Review finished"
# Example with metadata: dombot-log.sh ERROR cron:job "" job:fail "Script failed" '{"exit_code":1}'

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CORE_DIR="$(cd "$SCRIPT_DIR/../core" && pwd)"

exec uv run --directory "$CORE_DIR" dombot-log "$@"
