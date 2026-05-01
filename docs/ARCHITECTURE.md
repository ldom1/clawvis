# docs/ARCHITECTURE.md

> Clawvis technical architecture. Source of truth for implementation decisions.
> For product vision → `docs/GOAL.md`
> For dev rules → `CLAUDE.md` (summary) · `docs/CLAUDE-REFERENCE.md` (detail)
> For data model → `docs/DATA-MODEL.md`
> For setup (installer wizard, modes, memory) → `docs/SETUP.md`

---

## Overview

```
User
    │
    ├── Telegram / Discord  (external channels)
    │
    └── Hub UI  (localhost:8088 or lab.dombot.tech)
            │
            ├── /hub/          → Project dashboard
            ├── /kanban/       → Task board
            ├── /memory/       → Brain (Quartz iframe)
            ├── /logs/         → Real-time log stream
            ├── /chat/         → Agent chat
            └── /settings/     → Runtime AI config, workspace

    Hub UI ──► Kanban API      (port 8090)
           ──► Memory API      (port 8091)
           ──► Agent Service   (port 8092, env: AGENT_PORT)
           ──► OpenClaw        (port 18789)
```

---

## Core Principles

> **The Brain is the single source of truth.**  
> All project data, metadata, and documentation must originate from and be synchronized with the Brain.  
> The filesystem is secondary.

- If a project exists in the Brain (`memory/projects/<slug>.md`), it appears everywhere in the UI — regardless of whether a local folder exists.
- Never hardcode project lists — always derive them from the Brain.
- Archive is reversible; delete is permanent and always requires confirmation.

---

## Stack — entry points

| Layer | Technology | Entry point |
|--------|-------------|-------------|
| Hub SPA | Vite + vanilla JS | `hub/src/main.js` |
| Kanban API | FastAPI (uvicorn) | `kanban/kanban_api/server.py` |
| Memory API | FastAPI (uvicorn) | `hub-core/hub_core/memory_api.py` |
| Agent Service | Python | `services/agent/agent_service/main.py` |
| Brain display | Quartz static (iframe) | `scripts/build-quartz.sh` |
| Docker proxy | nginx | `hub/nginx.conf` |
| OpenClaw | Node.js | port 18789 |

---

## Services

| Service | Port | Tech | Role |
|---------|------|------|------|
| **Hub** | 8088 | Vite SPA + nginx | Single interface — dashboard, kanban, brain, logs, chat, settings |
| **Kanban API** | 8090 | FastAPI (hub-core) | Projects/tasks, memory sync, settings |
| **Memory API** | 8091 | FastAPI (hub-core) | Brain tree, Quartz, instance linking |
| **Agent Service** | 8092 (`AGENT_PORT`) | Python | Streaming LLM, OpenClaw sessions, provider routing |
| **OpenClaw** | 18789 | Node.js | Agent runtime, skill crons, Telegram/Discord channels |

**`GET /api/hub/agent/config`** (and `GET …/config` on the agent) matches **`docs/examples/agent-config-get-response.json`**: **`preferred_provider`**, **`primary_provider`** (wizard / `PRIMARY_AI_PROVIDER`: OpenClaw vs Claude Code), **`providers`** (`anthropic`, `openrouter`, `mammouth`, `openclaw` with **`models.default`**). **`PATCH /config`** still reads/writes **`agent-config.json`** (`anthropic_model`, `mammouth_model`, …). Use **`GET /status`** for LLM routing / readiness flags.

---

## Startup modes

### Franc — Docker (default user)

```bash
docker compose -f docker-compose.yml -f instances/<n>/docker-compose.override.yml up
```

- nginx serves `hub/dist/` (built SPA)
- nginx proxies `/api/hub/kanban/*` → kanban-api
- nginx proxies `/api/hub/memory/*` → hub-memory-api
- Brain = Quartz static served via iframe

**`HUB_HOST`** in `docker-compose.yml` controls the bind:

```yaml
ports:
  - "${HUB_HOST:-127.0.0.1}:${HUB_PORT:-8088}:80"
```

- `HUB_HOST=127.0.0.1` (default) → loopback only, safe for Docker Desktop and setups with a host reverse proxy
- `HUB_HOST=0.0.0.0` → container accepts non-loopback connections (without a host reverse proxy)

**Health:** `docker-compose.yml` defines `healthcheck` on `hub`, `kanban-api`, and `hub-memory-api`. For host-side diagnostics (mapped ports, text or `--json` output), use `bash scripts/hub-healthcheck.sh` (variables `HUB_PORT`, `KANBAN_API_PORT`, `HUB_MEMORY_API_PORT`, `NGINX_PORT` as appropriate).

### Mérovingien — VPS / server

Same as Franc but deployment via `clawvis deploy` (rsync + remote build).
VPS nginx reverse proxy → local stack via Tailscale or directly.

### Soissons — Local dev

```bash
clawvis start  # or scripts/start.sh
```

- Vite dev server on `HUB_PORT` (8088)
- Vite proxy `/api/kanban/*` → uvicorn Kanban API (8090)
- Vite proxy `/api/hub/memory/*` → uvicorn Memory API (8091)
- `system.json` = static file in `hub/public/api/`, updated by cron via hub-core

---

## Hub routing (SPA)

All routes are handled by `hub/src/main.js` via the History API.

Static assets in `hub/public/` are copied verbatim into `hub/dist/` at build:

| File | Role |
|------|------|
| `hub/public/settings/index.html` | Static Docker settings page — served on `/settings/` by nginx |
| `hub/public/optional-app-placeholder/index.html` | "App not deployed" fallback |
| `hub/public/api/*.json` | Static stubs used in dev and prod |

**Critical nginx rule:** the `location /assets/` block must come **before** `/hub/` — Vite emits absolute paths `/assets/index-HASH.js` that otherwise return 404. See pitfall #2 in `docs/PITFALLS.md`.

---

## API contract — separate domains

```
/api/hub/kanban/*    → Kanban API (FastAPI, port 8090)
/api/hub/memory/*    → Memory API (FastAPI, port 8091)
/api/hub/logs/*      → Logs (hub-core)
/api/hub/chat/*      → Agent Service (port 8092)
```

**Absolute rule:** Brain/Quartz endpoints never live under the Kanban API surface.

### Main endpoints

```
GET  /api/kanban/hub/settings
PUT  /api/kanban/hub/settings
GET  /api/kanban/hub/projects?kind=project|poc
POST /api/kanban/hub/projects          # { description, template }
GET  /api/kanban/hub/projects/{slug}
GET  /api/hub/chat/status              # → { openclaw_configured: bool }
```

### Project creation (backend)

`POST /api/kanban/hub/projects` creates in sequence:
1. Repo folder under `projects_root` or `pocs_root`
2. Memory doc `memory/projects/<slug>.md`
3. Metadata file `.clawvis-project.json`
4. Kanban tasks from the chosen template

---

## Brain — active memory and Quartz

### Resolving the memory root

Resolved by `hub_core.brain_memory.active_brain_memory_root(settings)`:

1. List `linked_instances` — if `<path>/memory` exists → candidate
2. If `MEMORY_ROOT` == a candidate → that candidate wins
3. Otherwise → first candidate after lexicographic sort
4. If no linked instance has `memory/` → direct `MEMORY_ROOT`

`GET /hub/settings` returns `active_brain_memory` for UI transparency.
Tests: `hub-core/tests/test_brain_memory.py`.

### Quartz — service and `<base>` tag

The Quartz build (`quartz/public/`) is served at:

```
/api/hub/memory/quartz-static/{path}
```

The Memory API injects a `<base>` tag in each HTML page so relative assets resolve at any URL depth:

```
quartz/public/
  index.html           → <base href="/api/hub/memory/quartz-static/">
  projects/slug.html   → <base href="/api/hub/memory/quartz-static/">
  index.css            → served directly
```

If Quartz is missing (submodule not initialized), the lightweight Python renderer takes over — graceful degradation, no blank page.

### Brain editing scope

- In-Hub editing: `memory/projects/*.md` only
- Quartz preview: `memory/projects/*.html`
- Other folders (`resources/`, `daily/`): readable on disk, not exposed to in-Hub editing unless explicitly extended

---

## Dombot pattern — multi-vhost edge routing

For homelab setups (one IP, several domains):

```
Internet
  → VPS nginx (lab.dombot.tech, HTTPS termination)
    → Tailscale / proxy → Dombot :8088
      → nginx host (generated from instances/<n>/nginx/nginx.conf)
          server_name www.clawvis.fr   → static clawvis-landing/dist/
          server_name lab.dombot.tech  → Hub container (127.0.0.1:8089) + Authelia
```

**Why `HUB_HOST=0.0.0.0` alone is not enough:** if the Hub container is published directly on `0.0.0.0:8088`, every vhost sees the Hub SPA — you cannot serve the landing on the same port.

**Correct pattern:**
- `HUB_HOST=127.0.0.1`, Hub bound to `127.0.0.1:8089` (internal port)
- Host nginx on `0.0.0.0:8088`, dispatch by `server_name`

`clawvis start` (Vite dev) does **not** implement this pattern — production only.
→ See `docs/guides/dombot-edge-routing.md` for operational detail.

---

## Repository layout

```
clawvis/
  hub/                    # Vite SPA frontend + nginx Docker image
    src/                  # Dev source (main.js, style.css)
    public/               # Static assets, built SPA prod
    dist/                 # Build output (gitignored)
  hub-core/               # Shared Python lib — Memory API, transcribe, brain_memory helpers
  services/
    agent/                # AI agent service (port 8092)
    kanban/               # Kanban + hub API (port 8090)
    scheduler/            # Cron job runner (port 8095)
    telegram/             # Telegram bot (port 8094)
  skills/                 # Preconfigured Clawvis skills
    project-init/
      templates/          # New project templates (python, vite, empty)
  clawvis-cli/            # Unified CLI (npm) — clawvis start/deploy/update/backup
  scripts/                # Scripts (start, deploy, upgrade, build-quartz, hub-healthcheck…)
  instances/
    example/              # Instance template (copied on install)
    <instance_name>/      # Real instance data (gitignored except structure)
  docs/                   # Technical documentation
  tests/                  # CI — ci-all.sh, ci-skills.sh
  .github/workflows/      # CI/CD GitHub Actions
```

---

## OpenClaw — skills integration

OpenClaw runs on port 18789. Clawvis connects via `OPENCLAW_BASE_URL`.

Clawvis skills are OpenClaw crons defined in `skills/` (and `instances/<instance>/skills/`) — **`clawvis skills sync`** updates `~/.openclaw/openclaw.json` (`skills.load.extraDirs`) and restarts the gateway — without symlinks under `~/.openclaw/skills/`.

Discord channel configuration in `hub_settings.json`:

```json
{
  "discord_channels": {
    "innovation": "#innovation",
    "projects":   "#projects",
    "logs":       "#logs",
    "ops":        "#ops"
  }
}
```

---

## Update lifecycle

```
1. Pin release     → tag vYYYY-MM-dd
2. Upgrade prep    → fetch changelog, migration checks compose/env/memory
3. Apply           → update core to target tag, instances/ unchanged
4. Validate        → smoke tests (Hub, Brain, Logs, Kanban, project creation)
5. Promote         → redeploy only after green checks
```

---

## CI

```bash
bash tests/ci-all.sh    # main gate — must exit 0
bash tests/ci-skills.sh # includes skill-tester
```

| Workflow | Trigger | Role |
|----------|---------|------|
| `ci.yml` | PR / push | Shell syntax, hub format+tests+build, Python compile |
| `license.yml` | PR | Validates MIT |
| `release-dry-run.yml` | PR | Validates tag format |
| `release.yml` | Tag `vYYYY-MM-dd` | Publishes GitHub Release |

---

## ADRs — major decisions

| ADR | Title | Link |
|-----|-------|------|
| 0001 | Docker as default install mode (Franc) | `docs/adr/0001-docker-as-default-mode.md` |
| 0002 | Instance-scoped memory — never at repo root | `docs/adr/0002-instance-scoped-memory.md` |
| 0003 | Dombot migration (Clawpilot → Clawvis) | `docs/adr/0003-dombot-migration.md` |
| 0004 | First production deployment pitfalls | `docs/adr/0004-production-deployment-pitfalls.md` |

### Key principles

- `project_slug == memory_page_slug == kanban_project_key` — single canonical identity
- Memory is never owned by core — always instance-scoped
- Instance → core symlinks are managed by `clawvis skills sync`
- `docker-compose.override.yml` per instance for prod/dev separation
