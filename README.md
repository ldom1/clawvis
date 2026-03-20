# ClawPilot

> Your personal AI agent OS — Matrix-grade orchestration, on your machine.
> Open Source · Self-Hosted · AI-Native

Deploy your own autonomous AI agent infrastructure in minutes.
Hub, Kanban, multi-agent routing (OpenClaw / Claude / Gemini), shared PARA memory. On your machine.

## Quick Start

```bash
git clone https://github.com/lgiron/dombot-labos
cd dombot-labos
cp .env.example .env
# Add your API keys in .env
docker-compose up -d
# Dashboard at http://localhost:8088
```

## What's Inside

| Directory | Purpose |
|-----------|---------|
| `landing/` | Marketing landing page (Vite.js → dombot.tech) |
| `hub/` | Central dashboard + Nginx reverse proxy |
| `kanban/` | Task board with confidence scoring |
| `openclaw/` | Self-hosted agent runtime |
| `skills/` | Pre-configured agent skills |
| `vault-template/` | Obsidian PARA vault template |

## Architecture

**Layer 1 — Operational:** Hub + Kanban + Logs with confidence scoring (Kahneman-inspired)

**Layer 2 — Strategic:** Multi-agent orchestration — route tasks to best agent by cost & quality

## License

MIT
