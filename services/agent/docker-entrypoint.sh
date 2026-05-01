#!/bin/sh
# Restore .claude.json when absent — the direct file bind-mount is fragile on
# WSL Docker Desktop; the backup lives inside the directory mount (~/.claude/).
if [ -n "$HOME" ] && [ ! -f "$HOME/.claude.json" ]; then
    backup=$(ls -t "$HOME/.claude/backups/.claude.json.backup."* 2>/dev/null | head -1)
    if [ -n "$backup" ]; then
        cp "$backup" "$HOME/.claude.json"
    fi
fi

exec "$@"
