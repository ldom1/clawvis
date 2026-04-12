# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Hub + Playwright — bulk project delete and suite teardown (2026-04-12)
- **Hub projects grid**: added per-card selection checkboxes and a **Delete selected** CTA that appears only when at least one project is selected.
- **Bulk delete flow** uses native `window.confirm("Delete X project(s)? This cannot be undone.")`, deletes each selected project via `DELETE /api/hub/kanban/hub/projects/{slug}`, then re-fetches and re-renders the grid.
- **Playwright project lifecycle suite** now tracks created slugs and includes `afterAll` teardown deleting remaining test-created projects only, with per-slug deletion logs for traceability.
- **Playwright UI coverage**: added a dedicated home-grid bulk-delete scenario selecting two cards, accepting the native confirm dialog, and asserting both cards disappear.
- **Kanban API route** `DELETE /hub/projects/{project_slug}` already exists and remains backward-compatible (no route change needed).
- **CLI root resolution**: running `clawvis restart` from inside a Clawvis git checkout now targets that checkout (instead of always using the install path behind `~/.local/bin/clawvis`), so local code changes are picked up.

### Hub — launch detection + workspace root + GitNexus cleanup (2026-04-12)
- **Project launch CTA** now uses a backend launch-status resolver instead of a blind `HEAD /apps/<slug>/` probe. The Hub distinguishes `launchable`, `buildable`, and genuinely missing projects, preserving the existing not-deployed fallback only for real misses.
- **Build & Launch** is available for buildable frontend Vite projects: the Kanban API derives the build command from the repo on disk, runs `npm install` if needed, then builds with `--base=/apps/<slug>/` before opening the app.
- **Workspace settings precedence fixed**: saved `projects_root` from Settings now overrides stale `PROJECTS_ROOT` env defaults, so launch detection and repo discovery honor the path actively chosen in the Hub.
- **GitNexus removed from repo-owned guidance**: cleaned `AGENTS.md`, `CLAUDE.md`, docs references, `.gitignore`, and deleted generated `graphify-out` artifacts that still embedded GitNexus-derived context.

### Docker — project creation on kanban-api (2026-04-12)
- **`docker-compose.yml` (kanban-api)**: **`PROJECTS_ROOT`** bind mount **`ro` → `rw`** so **`POST /hub/projects`** can create directories and files on the host path (read-only produced **500** and the Hub alert **Creation impossible**).
- **`tests/playwright/tests/personas/projects.spec.ts`**: assert the create-project **POST** response is **OK** (fail fast with response body).

### Docs — pitfall #37 (2026-04-12)
- **`docs/PITFALLS.md`**: **`~/.clawvis`** vs **`lab/clawvis`** — agent Docker image bakes **`~/.clawvis/agent/`**; sync + rebuild **`agent-service`** after editing the lab tree.

### Agent — `GET /config` matches example JSON (2026-04-12)
- **`GET /config`**: body is only **`preferred_provider`**, **`primary_provider`**, **`providers`** (same shape as `docs/examples/agent-config-get-response.json`). Dropped flat duplicates; use **`GET /status`** for `effective_provider` / `runtime_ready` / `*_configured`.

### Agent service — Hub banner + dev/Docker wiring (2026-04-12)
- **`docker-compose.yml`**: **`hub`** now **`depends_on`** **`agent-service`** with **`service_healthy`** so nginx can reach `GET /api/hub/agent/config` after a normal `compose up`.
- **`scripts/start.sh`**: starts **agent** uvicorn on **`AGENT_PORT`** (default 8092); skip with **`CLAWVIS_SKIP_AGENT=1`** (**`scripts/start-for-e2e.sh`** sets it for Playwright).
- **`docs/PITFALLS.md`**: pitfall **#36** — wizard vs agent-service split.
- **`clawvis` restart / `install.sh` / `tests/ci-docker.sh` / CLI hints**: **`docker compose up`** now includes **`agent-service`** explicitly so **`PRIMARY_AI_PROVIDER`** in `.env` (written by the setup wizard via kanban-api) is visible to the Hub after restart — the wizard never started the Python agent by itself.
- **`docker-compose.yml` (agent-service)**: healthcheck uses **`curl`** instead of **`wget`** (agent image installs curl only) so the container can report **healthy** correctly.

### Playwright — writable project root for auto-started stack (2026-04-11)
- **`scripts/start-for-e2e.sh`** sets **`CLAWVIS_E2E_ISOLATE=1`**; **`scripts/start.sh`** then forces **`MEMORY_ROOT`** / **`PROJECTS_ROOT`** to **`.e2e-memory/`** and **`.e2e-projects/`** under the repo (after loading `.env`) and **`LINKED_INSTANCES=""`** so the Brain does not follow **linked instances** to an unreadable path. Both dirs are **gitignored**.
- **`get_hub_settings`**: if **`LINKED_INSTANCES`** is set in the environment (including empty), it **replaces** file-based `linked_instances` — empty env clears links (fixes `[] or file` keeping stale links).
- **`scripts/init-memory.sh`**: **`MEMORY_ROOT`** absolute paths are no longer prefixed with **`ROOT_DIR`** (e2e isolate dirs initialize correctly).

### Hub — Activate project visible on cards (2026-04-11)
- Home project cards: **Activate project** / **Activer le projet** full-width button under the card (not only in the ⋮ menu) for projects whose Brain `status` is not `active`.

### Agent — runtime UI after setup wizard (2026-04-11)
- **`PRIMARY_AI_PROVIDER`** for `GET /agent/config` (Hub home banner, `/runtime`, Settings pill) is read from the **repo `.env` on disk** when mounted (`./.env` → `/clawvis/.env`, `CLAWVIS_DOTENV_PATH`), so the wizard no longer requires restarting **agent-service** to show “Connected” / configured.
- **`agent_service.provider`**: `primary_ai_provider_raw()`, `_read_dotenv_key`, `_dotenv_paths`.

### MCP — host `server.js` path + working Node server (2026-04-11)
- **`claude.json` MCP `args`**: use **`CLAWVIS_REPO_HOST_PATH` / `mcp/server.js` on the host** (not `/clawvis/mcp/...` inside Docker) so Claude Code can spawn `node` successfully. Optional override **`CLAWVIS_MCP_SERVER_JS`**.
- **`mcp/package.json`**: `@modelcontextprotocol/sdk` + `zod`; **`mcp/server.js`** rewritten for **`McpServer` + `StdioServerTransport`** (old `StdioServer` export removed in current SDK).
- **Setup success page** (`hub/public/setup/runtime/`): shows **MCP script (host)** path + one-time `npm install` under `mcp/`.

### Docker + Claude Code — host `~/.claude` (2026-04-11)
- **`docker-compose.yml` (kanban-api)**: bind-mount `${HOME}/.claude` → `/clawvis-host-claude`, set `CLAWVIS_HOST_CLAUDE_DIR` and `CLAWVIS_REPO_HOST_PATH=${PWD}` so setup writes `claude.json`, `LocalBrain.md`, and the `skills` symlink for **Claude Code on the host**, not the container filesystem.
- **`hub_core.setup_sync`**: `claude_mcp_config_path`, `claude_local_sync_dir`, `claude_skills_symlink_target_abs`; `find_claude_on_path` honors **`CLAWVIS_HOST_CLAUDE_CLI`** (file may be host-mounted and non-executable in-container). `/api/hub/setup/context` exposes `claude_host_claude_dir` and `claude_repo_host_path`.

### Hub — Set active project (2026-04-11)
- **Home project cards** (⋮ menu): **Set active** / **Définir actif** calls `POST /api/hub/kanban/hub/projects/{slug}/brain-status` with `{ "status": "active" }`, which writes YAML frontmatter `status: active` on the project memory `.md` (same field the grid uses for `brain_status`).
- **Kanban API**: `_upsert_brain_frontmatter_status`, `set_project_brain_status`; resolves `memory_path` when the note lives outside instance `memory/projects/` (brain-only listings).

### Setup — Claude Code MCP sync (2026-04-11)
- **`/setup/runtime` + `POST /api/hub/setup/claude-code-sync`**: registering MCP in `~/.claude/claude.json` only needs `node`; the wizard no longer fails when `claude` is missing from the **API process** PATH (common with Docker/systemd vs an interactive shell).
- **`find_claude_on_path`**: searches `CLAUDE_CLI_PATH`, then `~/.local/bin`, `~/bin`, `/usr/local/bin`, `/opt/homebrew/bin`, then `PATH`.
- Response may include `warning` when the CLI is not visible server-side; setup page shows it on success.

### Hub — Prettier (2026-04-11)
- `yarn prettier --write` sur `src/main.js` et `src/style.css` pour faire passer `prettier --check` en CI.

### Installer — `get.sh` piped bootstrap (2026-04-11)
- **Piped `curl … | bash`**: avoid `set -u` failure when `BASH_SOURCE[0]` is unset; treat empty script path as non–local-dev so the GitHub clone path stays correct.
- **Post-clone check**: exit with a clear error if `install.sh` is missing under `CLAWVIS_DIR`.

### Installer — brain path normalization (2026-04-11)
- **`install.sh` symlink memory**: normalize `--brain-path` / interactive input (BOM, CR, outer quotes, `~`, `wslpath` for `C:\…`, `/mnt/c/…` ↔ `/c/…`) before the existence check; clearer hint when the path still cannot be opened from the current environment (WSL vs Git Bash, OneDrive online-only).
- **`.env` / `source`**: `upsert_env` shell-quotes values that are not “simple” tokens so paths with spaces (e.g. `…/Local Brain`) do not break `load_env_file` / Quartz (`Brain: command not found`).

### Hub — Runtime IA page (2026-04-04)
- **Page `/chat` remplacée par `/runtime`** : nouvelle page dédiée au runtime IA avec info panel (provider, modèle, statut live), bouton de test de connexion (ping `/api/hub/agent/chat`), et accès OpenClaw (lien externe + iframe embed toggle). Route `/chat` conservée comme alias legacy.
- **Section runtime retirée de Settings** : la gestion du provider est centralisée sur `/runtime`. Le health banner "Runtime config" dans Settings est maintenant un lien cliquable vers `/runtime`.
- **Dot de statut pulsant** sur la tile "Runtime IA" de la home : vert (backend OK), orange (config locale non confirmée côté backend), rouge (rien de configuré / API inaccessible). Animé via CSS `@keyframes`.
- `hub/__tests__/runtime.test.js` créé : 10 tests couvrant la baseline `escapeHtml`, la structure DOM de la page runtime, les patterns d'erreur CLAWVIS, la logique d'état du dot.

### Phase 1.5 — Dombot migration complete (2026-03-27)
- **Clawvis stack deployed on Dombot** (hub:8089, kanban-api:8090, hub-memory-api:8091 — all bound to 127.0.0.1).
- `docker-compose.yml`: all service ports now bound to `127.0.0.1` by default — prevents accidental exposure on `0.0.0.0` and fixes port-conflict bug when `docker-compose.override.yml` redeclares the same ports (compose merges port arrays, causing duplicate bind failures).
- `instances/ldom/docker-compose.override.yml`: simplified — ports removed (inherited from base), only env overrides and ldom-specific volumes remain.
- `instances/ldom/nginx/nginx.conf`: nginx ldom updated with `upstream clawvis_hub { server 127.0.0.1:8089; }`, redirect `/ → /hub/`, proxy `/hub/` and `/api/hub/` → Clawvis hub container (Authelia-protected).
- **OpenClaw connected**: `GET /api/hub/chat/status` → `{"openclaw_configured": true}` from hub container.
- `docs/adr/0003-dombot-migration.md`: pre-migration audit snapshot (13 services, nginx routes, skills reconciliation, 6 pitfalls).

### install.sh + CLI — `--no-start` flag for server deployments (2026-03-27)
- `--no-start` flag added to `install.sh`: creates instance structure, initialises memory and Quartz, then stops without launching Docker services.
- Mode **2) Mérovingien** in the CLI wizard now passes `--no-start` automatically — correct behaviour for servers where nginx already listens on the target port.
- CLI completion box for Mérovingien mode shows a yellow "Instance ready" panel with the manual `docker compose up` command instead of Hub URLs.
- `README.md` — Mérovingien section rewritten with concrete `--no-start` examples and the override compose command.

### Hub — AI Runtime prominence & business KPIs (2026-03-24)
- **AI Runtime banner** added to the Hub home page: visible status badge (Connected / Not configured), provider name, and CTA to configure — no longer hidden in Settings only.
- **Business KPIs row** in System Status: Projects count, Active tasks, Done tasks, Brain notes — loaded live from the Kanban API.
- **Home page compact layout**: topbar redesigned as a slim horizontal nav bar (logo 28px, inline title), reducing wasted vertical space and bringing Core tools and Projects into immediate view.
- Removed "key stored in browser" messaging everywhere (intro, runtimeInfo, wizard step 2). Replaced with actionable copy pointing to `.env` for server usage.
- Settings AI runtime card now shows active provider name and status badge inline.
- Chat tile added to the Core tools section on home.

### Chat core-tool — AI conversation interface (2026-03-24)
- New route `/chat/` in the SPA with streaming chat UI (bubbles, auto-resizing textarea, Enter to send).
- Backend: `kanban_api/chat_api.py` — POST `/chat` streams from Claude / Mistral / OpenClaw based on `.env` config.
- Provider status endpoint: GET `/chat/status` — returns which provider is configured.
- Chat accessible from home tools bar tile and topbar (future).
### Brain / Quartz integration (2026-03-24)
- `scripts/setup-quartz.sh` — clone, patch content path, and first-build Quartz in one command.
- `clawvis setup quartz` — wired in both bash `clawvis` script and `clawvis-cli/cli.mjs`.
- `scripts/build-quartz.sh` — `QUARTZ_AVAILABLE` flag: Quartz owns display layer when installed; Python renderer is edit-only fallback.
- `kanban_api/core.py` — `_quartz_public_dir()` prefers `quartz/public/` over Python-generated HTML at runtime.

### CLI — setup-runtime & fixes (2026-03-24)
- `scripts/setup-runtime.sh` — configure any AI provider in `.env` from CLI: `clawvis setup provider --provider claude --key <key>`.
- `clawvis setup quartz` and `clawvis setup provider` now routed correctly in the bash fallback script.
- `clawvis update --channel stable|beta` — replaced `rg` with `grep` (non-standard tool, was CI failure on vanilla Ubuntu).

### Hub — production-grade redesign (`hub/public/index.html`)
- Aligned hub template with the production design from hub-ldom: dark theme, Inter font, indigo accent.
- Added Clawvis mascot logo centred in the header.
- Added 5 top-right icon shortcuts: OpenClaw, Logs, Kanban, Brain, Settings.
- System stats card with live fetch: CPU, RAM, Disk, Mammouth credits (progress bars, colour thresholds).
- Core tools section: Kanban, OpenClaw, Brain — styled tiles with left accent bar and chips.
- Projects and Experiments (POC) sections with empty-state placeholders, collapsible via localStorage.
- Theme (dark/light) persisted in localStorage, applied on load.
- Fixed prettier formatting in `src/main.js` (was failing CI format check).

### CLI (`clawvis-cli`)
- Fixed critical bug: binary was registered as `clawvisx` instead of `clawvis` — was uninstallable.
- Redesigned install modes to prioritise accessibility:
  - Mode 1 **Simple (Recommended)**: one-command Docker setup, no port/path prompts, automatic defaults.
  - Mode 2 **Server / Advanced (Docker)**: for VPS or server deployments, allows manual port/path configuration.
  - Mode 3 **Dev (contribution)**: full npm + uv stack for contributors.
  - Mode 4 **Dev light**: explore without configuring an AI runtime.
- Port prompts now shown only for modes 2, 3, 4 (not mode 1).
- `skipPrimary` logic made explicit per mode instead of relying on docker/dev string.

### CI
- Merged `license.yml` into `ci.yml` — single workflow instead of two running in parallel.
- Replaced `rg` (ripgrep, unavailable on ubuntu-latest) with `grep` for the MIT licence check.

### Docs
- Added **Adoptability First** design philosophy to `CLAUDE.md`: install must be one command, plain language, no technical jargon for end users by default.

- Hub migrated to Vite app (`hub/src`) with shared onboarding navigation and mascot branding.
- Added onboarding pages for Logs, Brain, Kanban in Hub, including logs empty-state visibility.
- Added interactive project-scoped Kanban board in Hub with inline status updates.
- Added project tags support and display in project cards.
- Project creation now enforces memory page creation and uses memory page as project source of truth.
- Brain runtime integrated through Docker (`memory` service) with instance-scoped memory root support.
- Added memory initialization script with canonical structure (`projects/resources/daily/archive/todo`) and template seeds.
- Installer (`install.sh`) now provides guided setup for OpenClaw, Claude, or Mistral, plus instance naming.
- Added versioned upgrade workflow via `upgrade.sh <tag>` with smoke checks.
- Start/deploy workflows now rebuild Hub with Yarn before run/deploy.
- Added frontend formatter/test tooling in `hub/` (`prettier`, `jest`, and initial test).

