## hub-core

Core Python package for the Clawvis Hub: metrics, providers, tokens, Memory API, and optional CLI tools.

- Fetches provider data (MammouthAI credits, Claude usage via `openclaw status`)
- Tracks CPU/RAM, token usage, system metrics
- Aggregates everything into Pydantic models (`HubState`, `CpuRam`, etc.)
- Writes JSON snapshots for a static/NGINX dashboard (`providers.json`, `system.json`, `tokens.json`, `status.json`)
- Logs structured events to `~/.openclaw/logs/dombot.log` (text) and `dombot.jsonl` (JSONL)

---

## Structure

```
hub_core/
├── brain_memory.py  # Active memory root resolution (used by Kanban + Memory API)
├── memory_api.py    # FastAPI Brain / Quartz endpoints (separate service)
├── security/        # Identity only (AGENT_ID / AGENT_ROLE)
├── fetch/           # Provider data (MammouthAI credits)
├── track/           # Token stats + system metrics
├── update/          # Status + CPU/RAM aggregators
├── transcribe/      # Optional transcription (requires faster_whisper)
├── config.py        # Paths and constants (LAB_DIR, HUB_API_DIR, etc.)
├── models.py        # Pydantic models (HubState, CpuRam, ProvidersResponse, …)
├── dombot_log.py    # Structured DomBot logger → ~/.openclaw/logs/
└── main.py          # Entry point: get_hub_state(), get_simple_state()
```

### Packaging — workspace and Memory API layering

- **UV workspace**: resolve `hub-core` and `kanban` from the **repo root** (`pyproject.toml` + `uv.lock` there). A `uv sync` only inside `hub-core/` without the workspace is not supported.
- **Strategy B (current)**: `memory_api` reuses implementation in `kanban_api.core` so Brain settings/projects/Quartz stay in one place. `hub-core` declares `kanban-api`; both packages are workspace members. **Strategy A** (future) would move Brain helpers fully into `hub-core` and drop this dependency direction.

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
| `MAMMOUTH_API_KEY` | — | MammouthAI gateway key (optional if unused) |
| `AGENT_ID` | `hub-core` | Agent identifier logged to dombot.log |
| `AGENT_ROLE` | `AGENT` | Role: `ORCHESTRATOR`, `AGENT`, or `VIEWER` |
| `AGENT_MODEL` | `claude-haiku-4-5` | Model used for logging context |
| `NETWORK_ALLOWLIST` | — | Optional comma-separated hosts (identity metadata) |
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
  "command": "cd ~/Lab/clawvis/hub-core && uv run python -m hub_core.main",
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
# Gate utilisé en CI (voir tests/ci-hub-core.sh)
uv run pytest tests/ -k "not real_providers and not transcriber_real_audio" -q
```
