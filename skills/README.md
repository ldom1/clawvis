# Skills (Clawvis)

Skills live under **`${CLAWVIS_ROOT}/skills/`** (and optionally `instances/<name>/skills/`).

Shared path resolution: **`skills/_clawvis_env.sh`** — `clawvis_env_load` sets `CLAWVIS_ROOT`, `LOGGER_CORE`, `LOG_DIR`.

Register with your agent via **`clawvis skills sync`** (Claude Code / `.claude`) so tools resolve skills from the repo — no symlink farm required.
