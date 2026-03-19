# dombot-logger — Hub tool

Viewer for OpenClaw/DomBot structured logs. Served by the Lab Hub at `/logs/`.

- **API:** Hub proxies `/api/kanban/logs` to Kanban API (FastAPI :8090), which reads `~/.openclaw/logs/dombot.jsonl`.
- **Source:** This folder is the single source for the logs UI; hub nginx serves it via `alias ${HUB_ROOT}/core-tools/logger/`.
- **Project:** `memory/projects/dombot-logger.md`
