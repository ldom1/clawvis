# Logger Skill

## ⚡ Quick start

```bash
# Log + Discord routing
${CLAWVIS_ROOT}/skills/logger/scripts/dombot-log.sh INFO "cron:xxx" system cron:complete "Message"

# Discord only
${CLAWVIS_ROOT}/skills/logger/scripts/discord-send.sh ops "Message"

# Discord diagnostics
${CLAWVIS_ROOT}/skills/logger/scripts/discord-check.sh --test
```

Unified structured logging for all DomBot agents.

## Scripts (`scripts/`)

Launch from anywhere; no need to `cd` into core.

| Script | Purpose |
|--------|--------|
| `dombot-log.sh` | Write log entry (dombot.log + jsonl) and route to Discord if pattern matches |
| `discord-send.sh` | Send a message to Discord only (no log file) |
| `discord-check.sh` | Diagnose config (env + openclaw.json); use `--test` to send a test message |

**dombot-log (log + optional Discord):**
```bash
${CLAWVIS_ROOT}/skills/logger/scripts/dombot-log.sh LEVEL PROCESS MODEL ACTION MESSAGE [METADATA_JSON]
# Example
${CLAWVIS_ROOT}/skills/logger/scripts/dombot-log.sh INFO "cron:self-improvement" system cron:complete "Review finished"
```

**discord-send (Discord only):**
```bash
${CLAWVIS_ROOT}/skills/logger/scripts/discord-send.sh [TARGET] MESSAGE
# TARGET: channel ID, or general|logs|projects|ops|alerts|dm|innovations
${CLAWVIS_ROOT}/skills/logger/scripts/discord-send.sh ops "Cron completed"
${CLAWVIS_ROOT}/skills/logger/scripts/discord-send.sh "Single arg → sent to general"
```

**Why am I not receiving anything on Discord?**
1. Run `${CLAWVIS_ROOT}/skills/logger/scripts/discord-check.sh` to see current config.
2. Set **at least one** of:
   - **Env:** `export DISCORD_BOT_TOKEN="..."` and `export DISCORD_CHANNEL_ID_OPS="YOUR_CHANNEL_ID"` (or another `DISCORD_CHANNEL_ID_*`)
   - **Config:** In `${CLAWVIS_ROOT}/config.json` under `channels.discord` set `token` as env SecretRef (`id: DISCORD_BOT_TOKEN`)
   (Get the channel ID by enabling Developer Mode in Discord → right-click channel → Copy Channel ID.)
3. Run `discord-check.sh --test` to send a test message.

### Discord CLI — create / delete channels (bot)

From `skills/logger/core` (or `${CLAWVIS_ROOT}/skills/logger/core` on an instance):

```bash
uv run discord-cli create-channels --channels logs,innovations,projects,ops
uv run discord-cli delete-channels --channels channel-name
# Multiple names: --channels foo,bar
# Optional: --guild-id, --channel-id (reference), --store-path (default: .local/discord_channels.json)
```

**Requirements:** `DISCORD_BOT_TOKEN`, `DISCORD_GUILD_ID`, and a reference channel (`DISCORD_CHANNEL_ID_GENERAL` or `--channel-id`). The bot needs the **Manage Channels** permission to create or delete.

- **`create-channels`:** allowed names match the logger config (`general`, `logs`, `innovations`, `projects`, `ops`, `alerts`, etc.); updates the store file with channel IDs.
- **`delete-channels`:** any **text channel** name (Discord slug: lowercase with hyphens); removes matching keys from the store when present.

---

## Usage (core)

Before any significant action (task start, task complete, cron execute, error), log it:

```bash
cd ${CLAWVIS_ROOT}/skills/logger/core
uv run dombot-log "INFO" "agent:main" "claude-haiku-4-5" "task:start" "Starting task: Build API endpoints" '{"task_id": "task-abc123"}'
```

## Log Levels

- **DEBUG**: Verbose internals (parsing steps, API calls)
- **INFO**: Normal operations (task started, cron executed, sync completed)
- **WARNING**: Unexpected but recoverable (API retry, missing file, slow operation)
- **ERROR**: Failed operations (parse failure, API error, task blocked)
- **CRITICAL**: System-level failures (disk full, auth expired, service down)

## Process Identifiers

Format: `type:name`

- `agent:main` — Primary DomBot agent
- `cron:morning-briefing` — Cron job
- `cron:knowledge-consolidator` — Cron job
- `subagent:curiosity` — Subagent
- `parser:kanban` — Kanban parser
- `api:kanban` — Kanban API

## Log Files

- `${CLAWVIS_ROOT}/logs/dombot.log` — Human-readable text format
- `${CLAWVIS_ROOT}/logs/dombot.jsonl` — Machine-readable JSON lines

## Integration — When the logger MUST run

The logger **must** be invoked after **every**:

1. **Action triggered by a Telegram or Discord message** — After handling the message (reply, task, script), log what was done. Process: `agent:main`, `channel:telegram`, or `channel:discord`.
2. **Cron run** — At start (`cron:start`) and at end (`cron:complete` or `cron:fail`) of each job. Process: `cron:<job-name>`.
3. **Agent or subagent significant action** — Session start/end, task create/update/archive, sync, deploy, errors. Process: `agent:main`, `subagent:<name>`, `parser:kanban`, etc.

See `AGENTS.md` and `MEMORY.md` for the full traceability policy. **No silent work.**

---

## Python skills: use dombot_logger in code

Skills that run Python (e.g. `dombot-mail`, `self-improving-agent`) **should** log via the central logger so entries appear in `${CLAWVIS_ROOT}/logs/dombot.jsonl` and `dombot.log`, and **each log is also sent to Discord** on the relevant channel (when `DISCORD_BOT_TOKEN` and `DISCORD_CHANNEL_ID_*` are set).

**Pattern** (no hard dependency on logger package; fallback if unavailable):

1. Add the logger core path to `sys.path`:
   `Path(__file__).resolve().parents[2] / "logger" / "core"` (from a file under `skills/<skill>/scripts/` or `skills/<skill>/core/`).
2. Try `from dombot_logger import get_logger` then
   `log = get_logger(process="cron:<job>" | "skill:<name>", model="")`.
3. On `ImportError`, use a no-op or `loguru` fallback so the skill still runs.
4. Call `log.info(action, message, **meta)` at key events (start, complete, error).

**Reference:** `${CLAWVIS_ROOT}/skills/dombot-mail/core/dombot_mail/service.py` and `${CLAWVIS_ROOT}/skills/self-improving-agent/scripts/self-improvement.py`.

**Shell scripts:** At the end of each script (on success, or before exit on failure), call the logger so runs are traceable:

```bash
uv run --directory ${CLAWVIS_ROOT}/skills/logger/core \
  dombot-log "INFO" "cron:<job>" "system" "cron:complete" "Short message" 2>/dev/null || true
```

Use `cron:fail` and level `ERROR` when the script exits with failure. Process names: `cron:git-sync`, `cron:knowledge-consolidator`, `cron:self-improvement`, `system-restart`, `hook:self-improvement`, `skill:self-improving-agent`.
