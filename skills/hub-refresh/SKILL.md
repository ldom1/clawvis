---
name: hub-refresh
description: "Run hub_core.main as dombot ORCHESTRATOR with RBAC env (AGENT_ID, AGENT_ROLE). Use when cron hub-refresh or when Ldom asks to refresh Hub / orchestrator context via hub_core."
---

# Hub Refresh

## When to use

- Cron **hub-refresh** (or manual equivalent).
- Request to execute a **Hub refresh** / `hub_core` orchestrator pass with dombot identity.

## Run

```bash
${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/hub-refresh/scripts/run.sh
```

Optional args are forwarded to `python -m hub_core.main` (see script).

## What it does

1. Resolves repo root via `CLAWVIS_ROOT`, or `$HOME/lab/clawvis`, or `$HOME/Lab/clawvis` (must contain `hub-core/`).
2. Uses `UV_PROJECT_ENVIRONMENT` (default `$HOME/.venvs/hub-core`) and `UV_PYTHON` (default `/usr/bin/python3.11`) for a stable venv.
3. `cd` into `hub-core` and runs `timeout 300 uv run python -m hub_core.main "$@"`.
4. Appends logs to `~/.openclaw/logs/hub-refresh-<timestamp>.log` and `/tmp/hub-refresh.log`.
5. Sets `AGENT_ID=dombot`, `AGENT_ROLE=ORCHESTRATOR`, `NETWORK_MODE=allowlist` (see script for allowlist).
6. On exit, calls **dombot-log** via `skills/logger/core` (`cron:hub-refresh`).

## Requirements

- `uv`, `timeout`, `hub-core` install runnable with `uv run`.
- Logger skill at `${CLAWVIS_ROOT}/skills/logger/core` for the completion line.

## Troubleshooting

- **Wrong repo path:** export `CLAWVIS_ROOT=/path/to/clawvis` (the directory that contains `hub-core` and `skills/`).
