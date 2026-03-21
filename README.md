# Clawvis

> Your personal AI agent OS — multi-agent orchestration, on your machine.
> Open Source · Self-Hosted · AI-Native

Transform OpenClaw into an accessible platform for everyone. Hub dashboard, Kanban, multi-agent routing (OpenClaw / Claude / MammouthAI / Gemini), shared PARA memory.

## Quick Start

```bash
git clone https://github.com/lgiron/clawvis
cd clawvis
cp .env.example .env
# Add your API keys in .env
docker-compose up -d
# Dashboard at http://localhost:8088
```

## What's Inside

| Directory | Purpose |
|-----------|---------|
| `hub/` | Template frontend (nginx + HTML) |
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
cp -r instances/example instances/ldom
echo "instances/ldom/.env.local" >> .gitignore
```

## Architecture

**Layer 1 — Operational:** Hub + Kanban + Logs with confidence scoring (Kahneman-inspired)

**Layer 2 — Orchestration:** Multi-agent routing — route tasks to best agent by cost & quality

**Layer 3 — Accessibility:** One-click deploy, Web UI setup, no CLI required

## License

MIT
