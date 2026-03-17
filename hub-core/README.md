## dombot-hub-core

Core Python package for the LabOS hub.

- Fetches provider data (MammouthAI credits, Claude usage via `openclaw status`)
- Tracks CPU/RAM, token usage, system metrics
- Aggregates everything into Pydantic models (`HubState`, `CpuRam`, etc.)
- Writes JSON snapshots for a static/NGINX dashboard (`providers.json`, `system.json`, `tokens.json`, `status.json`)
- Logs structured events to `~/.openclaw/logs/dombot.log` (text) and `dombot.jsonl` (JSONL)

---

## Structure

```
hub_core/
├── agents/          # Agent adapters (OpenClaw local, MammouthAI remote, registry)
├── security/        # Identity (RBAC roles), network policy, capability decorators
├── fetch/           # Provider data fetching (MammouthAI credits, etc.)
├── track/           # System metrics (CPU/RAM, token usage via openclaw status)
├── update/          # Status + system_metrics aggregators
├── mammouth/        # MammouthAI HTTP client
├── transcribe/      # Optional transcription (requires faster_whisper)
├── services/        # Service manager (proxy services status)
├── config.py        # Paths and constants (LAB_DIR, HUB_API_DIR, etc.)
├── models.py        # Pydantic models (HubState, CpuRam, ProvidersResponse, …)
├── dombot_log.py    # Structured DomBot logger → ~/.openclaw/logs/
├── api_fallback.py  # Auto-fallback Claude → MammouthAI at 75% usage
└── main.py          # Entry point: get_hub_state(), get_simple_state()
```

---

## Setup

```bash
# 1. Copy env and fill in your MammouthAI key
cp .env.example .env

# 2. Install dependencies
uv sync

# 3. Run
uv run python -m hub_core.main
```

Or from Python:

```python
from hub_core.main import get_simple_state

state = get_simple_state(write_json=True)
print(state)
```

---

## Configuration (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `MAMMOUTH_API_KEY` | — | **Required.** MammouthAI gateway key (get it at mammouth.ai) |
| `AGENT_ID` | `hub-core` | Agent identifier logged to dombot.log |
| `AGENT_ROLE` | `AGENT` | RBAC role: `ORCHESTRATOR`, `AGENT`, or `VIEWER` |
| `AGENT_MODEL` | `claude-haiku-4-5` | Model used for logging context |
| `NETWORK_MODE` | `restricted` | `unrestricted`, `restricted`, or `allowlist` |
| `NETWORK_ALLOWLIST` | — | Comma-separated allowed hosts (if `allowlist` mode) |
| `LAB_DIR` | `~/Lab` | Override if your Lab root is elsewhere |

---

## Deployment — Connect hub-core to OpenClaw

Hub-core is designed to run as a cron inside OpenClaw and write JSON files consumed by the Hub dashboard.

### 1. Configure the `.env`

```bash
cp .env.example .env
# Set MAMMOUTH_API_KEY, AGENT_ID=hub-core, AGENT_ROLE=AGENT
```

### 2. Add a cron in OpenClaw

In `~/.openclaw/workspace/crons/` (or via the `CronCreate` tool):

```json
{
  "name": "hub-refresh",
  "schedule": "*/5 * * * *",
  "command": "cd ~/Lab/dombot-labos/hub-core && uv run python -m hub_core.main",
  "description": "Refresh hub state every 5 minutes"
}
```

### 3. Verify logs appear in DomBot log

```bash
tail -f ~/.openclaw/logs/dombot.log
```

You should see lines like:
```
[2026-03-17T13:00:00] [INFO] [hub-core] [claude-haiku-4-5] hub:refresh — Fetching hub state (agent=hub-core@labos.local)
[2026-03-17T13:00:01] [INFO] [hub-core] [claude-haiku-4-5] hub:complete — Hub state ready (cpu=12.3, ram=41.5, mammouth_credits=87.5)
```

### 4. Verify JSON outputs

```bash
ls ~/Lab/hub/public/api/
# providers.json  status.json  system.json  tokens.json  session-tokens.json
```

### 5. Expose via NGINX (optional)

If the hub dashboard is served by NGINX, ensure the `api/` folder is served as static JSON:

```nginx
location /api/ {
    root /home/lgiron/Lab/hub/public/;
    add_header Cache-Control "no-cache";
}
```

---

## Tests

```bash
# All tests (skip real API tests if key invalid)
uv run pytest tests/ --ignore=tests/test_transcriber.py -q

# Integration (identity/RBAC/network policy/openclaw adapter)
AGENT_ID=labos-orchestrator AGENT_ROLE=ORCHESTRATOR \
uv run pytest tests/test_integration.py -v

# Real provider tests (requires valid MAMMOUTH_API_KEY)
uv run pytest tests/test_real_providers.py -v
```
