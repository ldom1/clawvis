<p align="center">
  <img src="./hub/public/clawvis-mascot.svg" alt="Clawvis" width="120" />
</p>

<h1 align="center">Clawvis</h1>

<p align="center">
  Self-hosted control center for your AI agents — Hub, Kanban, Memory, Skills.
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

**Clawvis is that place.** One `docker compose up` gives you:

| Service | URL | What it does |
|---------|-----|--------------|
| **Hub** | `localhost:8088` | Dashboard — system status, agent activity, projects |
| **Kanban** | `localhost:8088/kanban/` | Task board with confidence scoring and memory sync |
| **Brain** | `localhost:8088/memory/` | Project knowledge base (markdown → searchable pages) |
| **Logs** | `localhost:8088/logs/` | Real-time log stream from all your agents |
| **Settings** | `localhost:8088/settings/` | AI runtime config, workspace paths, linked instances |

Your data stays in `instances/<your-name>/` — never touched by core updates.

---

## Prerequisites

### Mode Franc — default (Docker)

Everything runs inside containers. You only need:

| Tool | Why | Install |
|------|-----|---------|
| **Docker** Engine 24+ or Desktop | runs the full stack | [docs.docker.com](https://docs.docker.com/get-docker/) |
| **Git** | clones the repo (`get.sh` handles this) | pre-installed on most systems |

That's it. Yarn, npm, uv and all build tools run **inside Docker** — you don't install them.

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

It works out of the box — no Quartz installation needed. A lightweight Python renderer converts your `.md` files to HTML automatically. If you want the full Quartz static site experience, clone Quartz to `quartz/` in the repo root and run `clawvis start`.

---

## What's inside

| Directory | Purpose |
|-----------|---------|
| `hub/` | Vite SPA frontend + nginx Docker image |
| `hub-core/` | Python lib — identity, RBAC, AI adapters |
| `kanban/` | Task board FastAPI — tasks, projects, memory sync |
| `skills/` | Pre-configured agent skills (kanban, logger, brain…) |
| `instances/` | Your instance data — never overwritten by updates |
| `project-templates/` | Starter templates for new projects |

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
./install.sh  # choose mode 3 (Soissons)
clawvis start
```

---

## License

MIT
