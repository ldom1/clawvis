# Clawvis

<p align="center">
  <img src="./hub/public/clawvis-mascot.svg" alt="Clawvis mascot" width="160" />
</p>

<p align="center">
  <strong>Your personal AI workspace — Hub, Kanban, Memory, Skills. One command to start.</strong>
</p>

<p align="center">
  <a href="https://github.com/lgiron/clawvis/actions/workflows/ci.yml"><img src="https://github.com/lgiron/clawvis/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/lgiron/clawvis/actions/workflows/release.yml"><img src="https://github.com/lgiron/clawvis/actions/workflows/release.yml/badge.svg" alt="Release"></a>
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT">
</p>

---

Clawvis gives you a self-hosted control center for your AI agents: a dashboard Hub, a Kanban board with confidence scoring, a searchable memory Brain, and a pluggable skills system — all wired to your preferred AI runtime (Claude, Mistral, or self-hosted OpenClaw).

Your customizations stay in `instances/<your-name>/` and are never touched by core updates.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/lgiron/clawvis/main/get.sh | bash
```

That's it. The installer handles the symlink, PATH, and guides you through the setup wizard.

After install, reload your shell and verify:

```bash
source ~/.bashrc   # or source ~/.zshrc
clawvis doctor
```

**With git:**

```bash
git clone https://github.com/lgiron/clawvis && cd clawvis && ./install.sh
```

**Non-interactive (CI / scripted):**

```bash
./install.sh --non-interactive --instance myname --provider claude --claude-api-key "sk-ant-..." --mode docker
```

## What you get

| Service | URL (default) | Description |
|---------|--------------|-------------|
| Hub | `http://localhost:8088` | Dashboard — agent activity, logs, status |
| Kanban | `http://localhost:8088/kanban/` | Task board with Kahneman-style confidence scoring |
| Brain | `http://localhost:8088/memory/` | Searchable PARA memory vault |
| Logs | `http://localhost:8088/logs/` | Live SSE log stream |

## Daily use

```bash
clawvis start          # start the stack
clawvis doctor         # health check all services
clawvis update wizard  # interactive upgrade
clawvis backup create  # snapshot your instance before updates
```

## Stay up to date

Core updates never touch your instance data:

```bash
clawvis update status
clawvis update --tag v2026-03-23
# or
clawvis update --channel stable
```

Rollback anytime:

```bash
clawvis backup list
clawvis restore <backup-id>
```

## Providers

Choose your AI runtime during install — switch anytime in `.env`:

| Provider | Variable |
|----------|----------|
| Claude (Anthropic) | `CLAUDE_API_KEY` |
| Mistral | `MISTRAL_API_KEY` |
| OpenClaw (self-hosted) | `OPENCLAW_BASE_URL` + `OPENCLAW_API_KEY` |

## Private instance (fork pattern)

Run your own private fork that stays upgradeable from upstream:

```bash
git clone https://github.com/lgiron/clawvis hub-myname
cd hub-myname
git remote rename origin upstream
git remote add origin git@github.com:YOURNAME/hub-myname.git
./install.sh
```

All your customizations go in `instances/myname/` — merge upstream updates freely.

## What's inside

| Directory | Purpose |
|-----------|---------|
| `hub/` | Vite frontend + nginx production image |
| `hub-core/` | Python library — identity, RBAC, adapters, registry |
| `kanban/` | Task board API with confidence scoring |
| `skills/` | Pre-configured agent skills |
| `openclaw/` | OpenClaw wrapper + config |
| `instances/` | Your instance config — never overwritten by updates |

## License

MIT
