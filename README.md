<p align="center">
  <img src="./hub/public/clawvis-mascot.svg" alt="Clawvis" width="120" />
</p>

<h1 align="center">Clawvis</h1>

<p align="center">
  The french king of AI agents. Hub, Kanban, Memory, Skills. Self-hosted. Simple.
</p>

<p align="center">
  <a href="https://github.com/ldom1/clawvis/actions/workflows/ci.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/ldom1/clawvis/ci.yml?branch=main&label=CI&style=flat-square" alt="CI" />
  </a>
  <a href="https://github.com/ldom1/clawvis/actions/workflows/release.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/ldom1/clawvis/release.yml?label=Release&style=flat-square" alt="Release" />
  </a>
  <img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License: MIT" />
</p>

**One-liner install:** `curl -fsSL https://raw.githubusercontent.com/ldom1/clawvis/main/get.sh | bash`

---

## Install

**One command — no setup required:**

```bash
curl -fsSL https://raw.githubusercontent.com/ldom1/clawvis/main/get.sh | bash
```

Clones the repo to `~/.clawvis`, runs the interactive wizard, and starts the stack.

**With git (control where it lives):**

```bash
git clone https://github.com/ldom1/clawvis && cd clawvis && ./install.sh
```

**Non-interactive (CI / scripted):**

```bash
./install.sh --non-interactive --instance myname --mode docker
```

After install, open **`http://localhost:8088`** and configure your AI runtime in **Settings → AI Runtime**.

---

## What is Clawvis?

You run AI agents — Claude, Mistral, or your own OpenClaw instance. But you have no single place to see what they're doing, manage their tasks, or keep project notes alongside them.

**Clawvis is that place.** One `docker compose up` to rull them all.

| Service | URL | What it does |
|---------|-----|--------------|
| **Hub** | `localhost:8088` | Dashboard — system status, agent activity, projects |
| **Agent service** | proxied as `/api/hub/agent/*` | Streaming chat and runtime config for the Hub banner |
| **Kanban** | `localhost:8088/kanban/` | Task board with confidence scoring and memory sync |
| **Brain** | `localhost:8088/memory/` | Project knowledge base (markdown → searchable pages) |
| **Logs** | `localhost:8088/logs/` | Real-time log stream from all your agents |
| **Settings** | `localhost:8088/settings/` | AI runtime config, workspace paths, linked instances |

Your data stays in `instances/<your-name>/` — never touched by core updates.

Projects on the Hub home support single delete from the card menu and bulk delete by selecting multiple cards then clicking **Delete selected**.

---

## Prerequisites

### Mode Franc — default (Docker)

Everything runs inside containers. You only need:

| Tool | Why | Install |
|------|-----|---------|
| **Docker** Engine 24+ or Desktop | runs the full stack | [docs.docker.com](https://docs.docker.com/get-docker/) |
| **Git** | clones the repo (`get.sh` handles this) | pre-installed on most systems |

That's it.

### Mode Soissons — dev / contribution

Running the stack locally (outside Docker) requires:

| Tool | Version | Why |
|------|---------|-----|
| **Node.js** | >= 18 | Vite dev server + CLI wizard |
| **npm** | bundled with Node | CLI dependencies |
| **Yarn** (via corepack) | 4.x | Hub frontend build (`corepack enable` installs it automatically) |
| **uv** | latest | Kanban API + hub-core — `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

### Mode Mérovingien — VPS / server deploy

Choose **2) Mérovingien** in the wizard for deployments where nginx or another reverse-proxy is already running on the target port. The installer creates the instance structure and `.env` **without launching Docker**, so you keep full control of startup:

```bash
# Non-interactive equivalent:
./install.sh --non-interactive --instance myname --mode docker --no-start

# Then start manually (with instance override):
docker compose \
  -f docker-compose.yml \
  -f instances/myname/docker-compose.override.yml \
  up -d
```

---

## Daily use

```bash
clawvis start       # start the stack (dev mode)
clawvis doctor      # health check — shows what's up and what's not
clawvis shutdown    # graceful stop
clawvis restart     # stop + start
```

When `clawvis` is installed globally (`~/.local/bin/clawvis`) and you run commands inside another Clawvis checkout, `start`/`restart` now use the current checkout so local updates are applied.

**Cron + Telegram:** `docker compose up` (and `clawvis restart` in Docker mode) start `telegram` and `scheduler` with the rest of the stack. Without `TELEGRAM_BOT_TOKEN`, the telegram service runs in **stub mode** (HTTP `/send` only — logs deliveries, no Telegram API). Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env` for a real bot. `TELEGRAM_CHAT_ID` must be the target chat/channel id (not the bot id), otherwise `/test` and scheduler notifications are rejected. Cron definitions: `services/scheduler/definitions/jobs/*.yaml` and workflows in `services/scheduler/definitions/workflows/*.yaml`.

---

## AI Runtime

No API key is required at install time. Configure post-install:

**Option A — Browser (recommended):**
Go to `http://localhost:8088/settings/` → AI Runtime section.
Keys are stored in your browser's localStorage.

**Option B — .env file (backend / persistent):**
Edit `.env` and restart:
```bash
CLAUDE_API_KEY=sk-ant-...        # Anthropic Claude
MISTRAL_API_KEY=...              # Mistral
OPENCLAW_BASE_URL=http://host    # Self-hosted OpenClaw
OPENCLAW_API_KEY=...             # OpenClaw key (optional)
```

---

## Stay up to date

Core updates never touch your instance data:

```bash
clawvis update status
clawvis update --tag v2026-03-23
clawvis update --channel stable
```

Backup and restore:

```bash
clawvis backup create
clawvis backup list
clawvis restore <backup-id>
```

---

## Deploy to a server (Hostinger / VPS)

**1. Set deploy target in `.env`:**
```bash
DEPLOY_HOST=your-vps-ip
DEPLOY_USER=ubuntu
DEPLOY_PATH=/opt/clawvis
DEPLOY_SSH_PORT=22
```

**2. Deploy:**
```bash
clawvis deploy
```

See [`docs/guides/deploy-hostinger.md`](docs/guides/deploy-hostinger.md) for the full guide.

---

## Brain (Knowledge base)

The Brain shows your project markdown files from `instances/<name>/memory/projects/`.

On the Hub home, each project that is not the home “active” row has an **Activate project** button (and a ⋮ menu for archive/delete). It sets YAML frontmatter `status: active` on that project’s memory note so the card moves to the main grid (others stay under “Show all projects” until activated).

**Claude Code in Docker:** the Kanban API mounts your host `~/.claude` and sets `CLAWVIS_HOST_CLAUDE_DIR` / `CLAWVIS_REPO_HOST_PATH` (see `docker-compose.yml`) so runtime setup updates the same files Claude Code reads on the machine, not paths inside the container. **`claude.json` points `node` at `<repo>/mcp/server.js` on the host** (not `/clawvis/...`). One-time: `cd mcp && npm install` so the MCP SDK is available, then `claude refresh`. Optionally mount the host `claude` binary and set `CLAWVIS_HOST_CLAUDE_CLI` for wizard detection.

It works out of the box — no Quartz installation needed. A lightweight Python renderer converts your `.md` files to HTML automatically. If you want the full Quartz static site experience, clone Quartz to `quartz/` in the repo root and run `clawvis start`.

---

## What's inside

| Directory | Purpose |
|-----------|---------|
| `hub/` | Vite SPA frontend + nginx Docker image |
| `hub-core/` | Python lib — identity, RBAC, AI adapters |
| `services/kanban/` | Task board FastAPI — tasks, projects, memory sync |
| `services/agent/` | AI agent service — streaming chat, runtime config |
| `services/scheduler/` | Cron job runner |
| `services/telegram/` | Telegram bot |
| `skills/` | Pre-configured agent skills (kanban, logger, brain…) |
| `skills/project-init/templates/` | Starter templates for new projects |
| `instances/` | Your instance data — never overwritten by updates |

---

## Troubleshooting

**Hub shows blank page:**
The Kanban API may not be running. Check: `clawvis doctor` or `docker compose ps`.

**`clawvis: command not found` after install:**
Reload your shell: `source ~/.zshrc` (or `~/.bashrc`).

**Docker not running:**
Start Docker Desktop, or: `sudo systemctl start docker`.

**Port already in use:**
Change `HUB_PORT` in `.env` (e.g. to `8089`), then restart.

**AI runtime shows "not configured":**
Go to `localhost:8088/settings/` and configure your provider.

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).
Mode Soissons (contribution) in the installer sets up your dev environment.

```bash
./install.sh  # choose mode: dev
clawvis start
```

---

## License

MIT
