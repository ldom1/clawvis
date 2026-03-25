# Clawvis Architecture

> Authoritative source: **CLAUDE.md** — this file is a quick-reference addendum.

## Stack

| Layer | Technology | Entry point |
|---|---|---|
| Hub SPA | Vite + vanilla JS | `hub/src/main.js` |
| Kanban API | FastAPI (uvicorn) | `kanban/kanban_api/server.py` |
| Memory API | FastAPI (uvicorn) | `hub-core/hub_core/memory_api.py` |
| Brain display | Quartz static (iframe) | `scripts/build-quartz.sh` |
| Docker proxy | nginx | `hub/nginx.conf` |

## API domains (`/api/hub/*`)

| Prefix | Service | Examples |
|---|---|---|
| `/api/hub/kanban/` | Kanban API | tasks, projects, stats, logs |
| `/api/hub/memory/` | Memory API | settings, instances, brain, quartz |
| `/api/hub/chat/` | Chat runtime | streaming responses |

## Hub routing (SPA)

All routes are handled by `hub/src/main.js` via `History API`.
Static assets in `hub/public/` are copied verbatim to `hub/dist/` during build:

- `hub/public/settings/index.html` — Docker-only static settings page (served at `/settings/` by nginx)
- `hub/public/optional-app-placeholder/index.html` — "App not deployed" fallback
- `hub/public/api/*.json` — static stubs used in dev and prod

## Project lifecycle

```
POST /api/hub/kanban/hub/projects  →  creates:
  - instances/<name>/memory/projects/<slug>.md
  - .clawvis-project.json in project repo
  - Kanban tasks from template
```

## Memory sources (Brain)

Active brain memory root is resolved by `hub_core.brain_memory.active_brain_memory_root`.
Priority: instance whose `memory/` dir matches `MEMORY_ROOT` → first instance alphabetically → fallback to `MEMORY_ROOT`.

Quartz build output (`quartz/public/`) is served via `/api/hub/memory/quartz-static/{path}` with `<base>` tag injection for correct relative asset resolution.
