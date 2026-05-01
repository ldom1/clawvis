#!/usr/bin/env python3
"""
session-janitor.py — Clears openclaw sessions stuck as 'running'.

A session is considered orphaned when ALL of these are true:
  1. status == "running"
  2. startedAt is older than TTL_MINUTES ago  (default 90)
  3. The session's JSONL file is either missing or the session has no messages

Run via cron every 30 min:
  */30 * * * * /usr/bin/python3 /path/to/session-janitor.py >> ~/.openclaw/logs/session-janitor.log 2>&1
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

SESSIONS_PATH = os.path.expanduser("~/.openclaw/agents/main/sessions/sessions.json")
LOG_PREFIX = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] session-janitor"
TTL_MINUTES = int(os.environ.get("JANITOR_TTL_MINUTES", "90"))
DRY_RUN = "--dry-run" in sys.argv

now_ms = int(time.time() * 1000)
ttl_ms = TTL_MINUTES * 60 * 1000

with open(SESSIONS_PATH) as f:
    sessions = json.load(f)

fixed = []
skipped_recent = []

for key, session in sessions.items():
    if session.get("status") != "running":
        continue

    started_at = session.get("startedAt", now_ms)
    age_ms = now_ms - started_at

    if age_ms < ttl_ms:
        skipped_recent.append(key)
        continue

    # Check if JSONL file exists and has content
    jsonl_path = session.get("sessionFile", "")
    jsonl_missing = not jsonl_path or not os.path.exists(jsonl_path)

    if not jsonl_missing:
        # File exists — only clear if it's empty (0 messages means never started)
        try:
            with open(jsonl_path) as jf:
                content = jf.read().strip()
            if content:
                # Has content → might still be running legitimately, skip
                continue
        except OSError:
            jsonl_missing = True

    age_min = age_ms / 60000
    label = session.get("label", key)

    if DRY_RUN:
        print(f"{LOG_PREFIX} [DRY-RUN] would clear: {label!r} (age={age_min:.0f}m, jsonl_missing={jsonl_missing})")
    else:
        session["status"] = "done"
        session["endedAt"] = now_ms
        if "runtimeMs" not in session:
            session["runtimeMs"] = now_ms - started_at
        fixed.append((label, age_min))

if not DRY_RUN and fixed:
    with open(SESSIONS_PATH, "w") as f:
        json.dump(sessions, f, indent=2)
    for label, age in fixed:
        print(f"{LOG_PREFIX} cleared: {label!r} (was stuck {age:.0f}m)")
elif not fixed and not skipped_recent:
    print(f"{LOG_PREFIX} nothing to clear")
elif not fixed:
    print(f"{LOG_PREFIX} nothing to clear ({len(skipped_recent)} running sessions within TTL)")
