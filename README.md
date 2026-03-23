# Clawvis

<p align="center">
  <img src="./hub/public/clawvis-mascot.svg" alt="Clawvis mascot" width="160" />
</p>

[![CI](https://github.com/lgiron/clawvis/actions/workflows/ci.yml/badge.svg)](https://github.com/lgiron/clawvis/actions/workflows/ci.yml)
[![Release](https://github.com/lgiron/clawvis/actions/workflows/release.yml/badge.svg)](https://github.com/lgiron/clawvis/actions/workflows/release.yml)
[![Release Dry Run](https://github.com/lgiron/clawvis/actions/workflows/release-dry-run.yml/badge.svg)](https://github.com/lgiron/clawvis/actions/workflows/release-dry-run.yml)
[![License Check](https://github.com/lgiron/clawvis/actions/workflows/license.yml/badge.svg)](https://github.com/lgiron/clawvis/actions/workflows/license.yml)
![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)

> Shared core platform for instance-scoped Clawvis deployments.
> Keep core updatable. Keep user customizations in `instances/<instance_name>/`.

Clawvis provides the core Hub + Kanban + Brain runtime contract, while each user deployment is isolated in its own instance folder and memory root.

## Install (recommended)

```bash
git clone https://github.com/lgiron/clawvis
cd clawvis
chmod +x clawvis
mkdir -p ~/.local/bin
ln -sf "$PWD/clawvis" ~/.local/bin/clawvis
export PATH="$HOME/.local/bin:$PATH"
clawvis install
```

`clawvis install` guides:
- instance naming (`instances/<name>`)
- provider selection (OpenClaw / Claude / Mistral)
- memory initialization (instance-scoped)
- run mode (docker or local dev)

## Quick Start

```bash
clawvis install --non-interactive --instance demo --provider claude --claude-api-key "sk-ant-..." --mode docker
clawvis doctor
```

Main URLs (defaults):
- Hub: `http://localhost:8088`
- Logs: `http://localhost:8088/logs/`
- Kanban: `http://localhost:8088/kanban/`
- Brain: `http://localhost:8088/memory/` (runtime on `http://localhost:3099`)

## Update lifecycle

Versioned updates:

```bash
clawvis update status
clawvis update wizard
# or
clawvis update --tag v2026-03-23
```

Backup / restore:

```bash
clawvis backup create --json
clawvis backup list
clawvis restore <backup-id>
```

## Architecture behavior

- Work instance-specific only under `instances/<name>/`.
- Keep core reusable in root (`hub`, `kanban`, `hub-core`, `skills`).
- Memory source of truth is instance-scoped (`MEMORY_ROOT`, default `instances/<name>/memory`).

## What's Inside

| Directory | Purpose |
|-----------|---------|
| `hub/` | Vite frontend + nginx production image |
| `hub-core/` | Python library — identity, RBAC, adapters, registry |
| `kanban/` | Task board API with confidence scoring |
| `skills/` | Pre-configured agent skills |
| `openclaw/` | OpenClaw wrapper + config |
| `vault-template/` | Obsidian PARA vault template |
| `instances/` | Per-instance config (fork `instances/example/`) |

## Private Instance (hub-ldom pattern)

```bash
git clone https://github.com/lgiron/clawvis hub-ldom
cd hub-ldom
git remote rename origin upstream
git remote add origin git@github.com:YOURNAME/hub-ldom.git
clawvis install
```

## Architecture

**Layer 1 — Operational:** Hub + Kanban + Logs with confidence scoring (Kahneman-inspired)

**Layer 2 — Orchestration:** Multi-agent routing — route tasks to best agent by cost & quality

**Layer 3 — Accessibility:** One-click deploy, Web UI setup, no CLI required

## License

MIT
