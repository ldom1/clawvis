# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

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
- `docs/playwright-persona.md` — Persona 6 covers full chat test journey.

### Brain / Quartz integration (2026-03-24)
- `scripts/setup-quartz.sh` — clone, patch content path, and first-build Quartz in one command.
- `clawvis setup quartz` — wired in both bash `clawvis` script and `clawvis-cli/cli.mjs`.
- `scripts/build-quartz.sh` — `QUARTZ_AVAILABLE` flag: Quartz owns display layer when installed; Python renderer is edit-only fallback.
- `kanban_api/core.py` — `_quartz_public_dir()` prefers `quartz/public/` over Python-generated HTML at runtime.

### CLI — setup-runtime & fixes (2026-03-24)
- `scripts/setup-runtime.sh` — configure any AI provider in `.env` from CLI: `clawvis setup provider --provider claude --key <key>`.
- `clawvis setup quartz` and `clawvis setup provider` now routed correctly in the bash fallback script.
- `clawvis update --channel stable|beta` — replaced `rg` with `grep` (non-standard tool, was CI failure on vanilla Ubuntu).

### Docs (2026-03-24)
- `docs/playwright-persona.md` — comprehensive 7-persona test guide: onboarding, kanban lifecycle, project CRUD, Brain/Quartz, Settings, Chat, health check.

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

