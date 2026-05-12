# Clawvis + skills

- **Repo root**: set **`CLAWVIS_ROOT`** to the directory that contains `hub-core/` and `skills/`.
- **Shared helpers**: `skills/_clawvis_env.sh` — sources `clawvis_env_load` for `LOGGER_CORE`, `LOG_DIR`.
- **Logger**: `${CLAWVIS_ROOT}/skills/logger/core` — `dombot-log` + Discord bridge; logs default to `${CLAWVIS_ROOT}/logs/` when `CLAWVIS_LOG_DIR` is unset.
- **Telegram from cron/shell**: `POST ${TELEGRAM_URL}/send` with JSON `{"text":"…"}` (see `services/telegram`).
- **Bootstrap hook** (optional): `skills/self-improvement/hooks/agent-bootstrap/handler.js` — generic reminder; wire it according to your agent runtime (not Clawvis-specific).
