# Clawvis setup

## Prerequisites

Before running Clawvis, your agent must already be operational:

- **OpenClaw**: your OpenClaw instance runs on your server
- **Claude Code**: Claude Code is installed on your machine (`claude` available on PATH)

Clawvis does not manage any API keys. Credential management belongs to your agent, not Clawvis.

## Configuration

In your `.env` file, choose your provider:

```bash
PRIMARY_AI_PROVIDER=openclaw   # or: claude
```

This is the only connection parameter. No URL, no key.

The wizard **Setup** in the Hub (`/setup/runtime/`) writes this line to the Clawvis repo `.env`. Restart services (agent, Docker, etc.) so processes pick up the new value.

## Starting

```bash
clawvis start
```

Clawvis detects the configured provider and connects to the agent that is already running.

## Related API

- `POST /api/hub/setup/provider` — body `{ "provider": "openclaw" | "claude" }`: updates `PRIMARY_AI_PROVIDER` in `.env`.
- `GET /api/hub/agent/config` — field `primary_provider` (`openclaw` \| `claude` \| `null`) read from the agent service environment.

## Skills and memory (outside the wizard)

Skills / Brain memory synchronization (scripts, `clawvis start`, dedicated endpoints) remains independent of the provider choice above. See [Architecture](ARCHITECTURE.md).
