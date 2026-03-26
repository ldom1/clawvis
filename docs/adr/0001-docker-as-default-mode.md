# 0001 — Docker as default install mode (Franc)

## Status
Accepted

## Context
Clawvis is a multi-service platform (Hub SPA, Kanban API, Memory API, Brain). Early versions required users to install Node.js, yarn, uv, and Python manually before they could run anything. This created a high-friction onboarding experience incompatible with the "1 command install" goal.

## Decision
Docker is the default and recommended install mode ("Franc"). All build tools (yarn, uv, npm) run inside Docker images. The only host dependencies are `git`, `docker`, and `python3` (pre-installed on all modern Linux/macOS).

`install.sh` defaults to `--mode docker` and runs `docker compose up` as the final step.

## Alternatives considered

- **Local dev as default (Soissons):** Rejected — requires Node 18+, yarn, uv. Too many prerequisites for non-technical users.
- **Single binary install (like OpenClaw):** Rejected — Clawvis is a platform with multiple services; a single binary would require bundling a full runtime or using something like Tauri/Electron, which adds significant complexity.

## Consequences
- Non-technical users need only Docker to run Clawvis.
- `docker/test.Dockerfile` validates the bootstrap in a clean Ubuntu environment.
- Dev contributors (mode Soissons) still need the full local stack but this is explicitly opt-in.
- Docker images must stay small and startup time must be acceptable (target: Hub responding within 10s of `docker compose up`).
