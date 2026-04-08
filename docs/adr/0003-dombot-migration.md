# ADR-0003 — Dombot migration: Clawpilot → Clawvis

**Date:** 2026-03-27  
**Status:** Pre-migration snapshot (historical) — for current public routing (**`lab.dombot.tech`** vs landing **`clawvis.fr`**) and **`HUB_HOST`**, see **[guides/dombot-edge-routing.md](../guides/dombot-edge-routing.md)**.  
**Author:** automated audit Phase 1.5.1

## Context

The Dombot server (`lab.dombot.tech`) runs `hub-ldom`, a Clawpilot instance (legacy name) with nginx, Authelia, and several Python APIs. The goal is to migrate this instance to `clawvis/instances/ldom/` to use the Clawvis update cycle while preserving routes, credentials, and existing memory data. This document captures the exact system state before any change.

## 1. Active services (pre-migration)

| Port | Bind | Process / Image | State | Role |
|------|------|-----------------|-------|------|
| 8088 | 0.0.0.0 | nginx (user lgiron) | active | Hub ldom (hub-ldom nginx) |
| 9091 | 127.0.0.1 | authelia/authelia:latest (Docker) | Up 4 days (healthy) | Auth gateway |
| 18789 | 127.0.0.1 + ::1 | openclaw-gateway (systemd user) | active running | OpenClaw Gateway v2026.3.11 |
| 18791 | 127.0.0.1 | openclaw-gateway | active running | same (worker) |
| 18792 | 127.0.0.1 | openclaw-gateway | active running | same (worker) |
| 8090 | 127.0.0.1 | python3 uvicorn | active | kanban_api |
| 8000 | 127.0.0.1 | python3 | active | optimizer_api |
| 8092 | 127.0.0.1 | python | active | spendlens_api |
| 8501 | 127.0.0.1 | python3 | active | messidor |
| 5175 | 0.0.0.0 | node (Vite dev server) | active | brain-pulse (likely) |
| 3010 | * | next-server | active | debate app |
| 16152 | 0.0.0.0 | Tailscale | active | private network |
| 80 | 0.0.0.0 | system nginx (root) | active | HTTP entrypoint |

**Only active Docker container:** `lab-authelia` (authelia/authelia:latest).

**Notable systemd user service:** `openclaw-gateway.service` — loaded active running, OpenClaw Gateway v2026.3.11.

## 2. nginx routes

### dombot.tech (public, no auth)

| Path | Type | Destination |
|------|------|-------------|
| `/` | static | `~/Lab/clawvis-landing/dist` |
| `/assets/` | static | `~/Lab/clawvis-landing/dist` |
| `/docs/` | static | `~/Lab/clawvis-landing/dist` |

### lab.dombot.tech (behind Authelia)

| Path | Type | Destination | Migration notes |
|------|------|-------------|-----------------|
| `/` | static | `hub-ldom/instances/ldom/public/` | → `clawvis/instances/ldom/public/` |
| `/memory/` | static | `/home/lgiron/Lab/quartz/public/` | Quartz Brain build — unchanged |
| `/brain-pulse/` | static | `~/Lab/project/brain-pulse/dist/` | separate project |
| `/plume/` | static | `hub-ldom/instances/ldom/public/plume/` | → `clawvis/instances/ldom/public/plume/` |
| `/real-estate/` | static | `~/Lab/project/real-estate/frontend/` | separate project |
| `/debate/` | proxy | `debate_api` → 127.0.0.1:3010 (Next.js) | independent service |
| `/poems/` | static | `~/Lab/poc/vitrine-poeme/dist/` | separate project |
| `/techspend/` | static + proxy | `spendlens_api` → 127.0.0.1:8092 for `/api/` | independent service |
| `/optimizer/` | static | `hub-ldom/instances/ldom/public/optimizer/` | → `clawvis/instances/ldom/public/optimizer/` |
| `/greet/` | static | `hub-ldom/instances/ldom/public/greet/` | → `clawvis/instances/ldom/public/greet/` |
| `/adele-icecream/` | static | `hub-ldom/instances/ldom/public/adele-icecream/` | → `clawvis/instances/ldom/public/adele-icecream/` |
| `/kanban/` | static | `hub-ldom/instances/ldom/public/kanban/` | legacy static Kanban → replaced by Hub SPA |
| `/logs/` | static | `clawvis/core-tools/logger/` | already Clawvis ✅ |
| `/settings/` | static | `hub-ldom/instances/ldom/public/settings/` | legacy static Settings → replaced by Hub SPA |
| `/tutti-frottie/` | static | `~/Lab/poc/tutti-frottie/` | separate project |
| `/openclaw/` | proxy | `openclaw` → 127.0.0.1:18789 | gateway token required |
| `/api/kanban/` | proxy | `kanban_api` → 127.0.0.1:8090 | → same port post-migration |
| `/api/` | proxy | `debate_api` → 127.0.0.1:3010 | independent service |
| `/optimizer/api/` | proxy | `optimizer_api` → 127.0.0.1:8000 | independent service |
| `/messidor/` | proxy | `messidor` → 127.0.0.1:8501 | independent service |
| `/poetic-shield/` | proxy | `poetic_shield` → 127.0.0.1:8503 | independent service |
| `/api/tokens.json` | static (auth) | `hub-ldom/instances/ldom/public/api/tokens.json` | → `clawvis/instances/ldom/public/api/` |
| `/api/system.json` | static (auth) | `hub-ldom/instances/ldom/public/api/system.json` | same |
| `/api/providers.json` | static (auth) | same | same |
| `/api/status.json` | static (auth) | same | same |
| `/authelia/` | proxy | authelia Docker → 127.0.0.1:9091 | unchanged |

**Defined nginx upstreams:**

```nginx
upstream debate_api    { server 127.0.0.1:3010; }
upstream optimizer_api { server 127.0.0.1:8000; }
upstream messidor      { server 127.0.0.1:8501; }
upstream poetic_shield { server 127.0.0.1:8503; }
upstream kanban_api    { server 127.0.0.1:8090; }
upstream spendlens_api { server 127.0.0.1:8092; }
upstream authelia      { server 127.0.0.1:9091; }
upstream openclaw      { server 127.0.0.1:18789; }
```

## 3. nginx variables (envsubst)

| Variable | Current resolution | Computation |
|----------|-------------------|-------------|
| `${HUB_ROOT}` | `~/Lab/hub-ldom/instances/ldom` | computed in `nginx-reload.sh` |
| `${LAB}` | `~/Lab` | 4× dirname from `scripts/` |
| `${OPENCLAW_GATEWAY_TOKEN}` | from `~/.openclaw/.env` or `openclaw.json .gateway.auth.token` | secret — do not commit |

**Critical trap — `LAB` variable:** `LAB` is computed by going up 4 directory levels from `scripts/` (scripts → ldom → instances → hub-ldom → Lab). If only 3× dirname is used, `LAB` is `hub-ldom/` and **all static routes silently return 404**. Verify this calculation after any tree change.

## 4. Authelia

| Parameter | Value |
|-----------|--------|
| Config | `hub-ldom/instances/ldom/authelia/configuration.yml` |
| Users | `hub-ldom/instances/ldom/authelia/users_database.yml` |
| Domain | `dombot.tech` |
| Session expiration | 12h, inactivity 45min |
| Auth method | two_factor (TOTP, issuer: dombot.tech) |
| Storage | SQLite (`/config/data/db.sqlite3` in container) |
| User | `ldom` (email: ldom@dombot.tech, group: admins) |
| Container files | `/config/` |

**Post-migration:** Authelia config files must move to `clawvis/instances/ldom/authelia/` and the Docker volume updated accordingly.

## 5. Skills — current state and migration target

**Note:** skills are partially migrated (symlinks). All 12 core skills already point to `clawvis/skills/`. Only 4 private skills still point to `hub-ldom`.

| Skill | Current state | Points to (current) | Post-migration target |
|-------|---------------|----------------------|------------------------|
| brain-maintenance | symlink ✅ | `~/Lab/clawvis/skills/brain-maintenance` | unchanged |
| git-sync | symlink ✅ | `~/Lab/clawvis/skills/git-sync` | unchanged |
| kanban-implementer | symlink ✅ | `~/Lab/clawvis/skills/kanban-implementer` | unchanged |
| knowledge-consolidator | symlink ✅ | `~/Lab/clawvis/skills/knowledge-consolidator` | unchanged |
| logger | symlink ✅ | `~/Lab/clawvis/skills/logger` | unchanged |
| morning-briefing | symlink ✅ | `~/Lab/clawvis/skills/morning-briefing` | unchanged |
| proactive-innovation | symlink ✅ | `~/Lab/clawvis/skills/proactive-innovation` | unchanged |
| qmd | symlink ✅ | `~/Lab/clawvis/skills/qmd` | unchanged |
| reverse-prompt | symlink ✅ | `~/Lab/clawvis/skills/reverse-prompt` | unchanged |
| ruflo | symlink ✅ | `~/Lab/clawvis/skills/ruflo` | unchanged |
| self-improvement | symlink ✅ | `~/Lab/clawvis/skills/self-improvement` | unchanged |
| skill-tester | symlink ✅ | `~/Lab/clawvis/skills/skill-tester` | unchanged |
| brain-pulse | symlink ⚠️ | `~/Lab/hub-ldom/instances/ldom/skills/brain-pulse` | `clawvis/instances/ldom/skills/brain-pulse` |
| dombot-mail | symlink ⚠️ | `~/Lab/hub-ldom/instances/ldom/skills/dombot-mail` | `clawvis/instances/ldom/skills/dombot-mail` |
| hub-refresh | symlink ⚠️ | `~/Lab/hub-ldom/instances/ldom/skills/hub-refresh` | `clawvis/instances/ldom/skills/hub-refresh` |
| system-restart | symlink ⚠️ | `~/Lab/hub-ldom/instances/ldom/skills/system-restart` | `clawvis/instances/ldom/skills/system-restart` |

**Required action:** copy the 4 private skills (`brain-pulse`, `dombot-mail`, `hub-refresh`, `system-restart`) to `clawvis/instances/ldom/skills/`, then update the 4 symlinks.

## 6. Memory

**Current symlink:**
```
~/.openclaw/workspace/memory -> /home/lgiron/Lab/hub-ldom/instances/ldom/memory
```

**Vault structure (unchanged after migration):**
```
memory/
  archive/
  breadcrumbs.md
  caps/
  consolidation/
  daily/
  DomBot-brain.md
  index.md
  kanban/
  projects/
  resources/
  todo/
```

**Post-migration:** update symlink to point to `~/Lab/clawvis/instances/ldom/memory`. Internal structure stays the same (move, not copy).

## 7. hub-ldom scripts

Scripts in `hub-ldom/instances/ldom/scripts/`:

| Script | Presumed role |
|--------|----------------|
| `healthcheck.sh` | Service health checks |
| `hub_update_loop.sh` | Hub update loop (polling) |
| `nginx-reload.sh` | Recompute envsubst vars + nginx reload |
| `restart.sh` | Stack restart |
| `session-end-tracker.sh` | OpenClaw session end tracking |
| `start.sh` | Stack start |
| `stop.sh` | Stack stop |
| `system_audit.sh` | System audit (generates system.json or equivalent) |
| `transcribe-audio.sh` | OpenClaw / local Whisper transcription (`scripts/` in Clawvis) |
| `update-projects-and-reload.sh` | Project update + nginx reload |

**Post-migration:** copy or port these to `clawvis/instances/ldom/scripts/`. Hardcoded paths to `hub-ldom/` must be updated.

## 8. OpenClaw config

| Parameter | Value |
|-----------|--------|
| Version | 2026.3.11 |
| Agent primary model | `anthropic/claude-haiku-4-5` |
| Subagents model | `mistral/mistral-small-3.2-24b-instruct` (via MammouthAI `https://api.mammouth.ai/v1`) |
| Max concurrent subagents | 8 |
| Workspace | `~/.openclaw/workspace` |
| Config | `openclaw.json` (credentials excluded from this document) |

## 9. Migration decisions

Migration runs in Phase 1.5.x steps:

| Phase | Action | Impact |
|-------|--------|--------|
| 1.5.1 | Full pre-migration audit (this document) | None — read-only |
| 1.5.2 | Copy `instances/ldom/` from hub-ldom to `clawvis/instances/ldom/` | Creates target without breaking existing |
| 1.5.3 | Update 4 private skill symlinks | Private skills point to clawvis |
| 1.5.4 | Update memory symlink | Memory points to clawvis |
| 1.5.5 | Update `nginx-reload.sh` + `HUB_ROOT` variable | nginx serves from clawvis |
| 1.5.6 | Full smoke test + disable hub-ldom | Migration validated |

## 10. Watch points

- **`LAB` variable trap (4× dirname):** If the tree changes or `nginx-reload.sh` is ported without adapting the calculation, all static routes return 404. Always verify `echo $LAB` after changes.
- **`OPENCLAW_GATEWAY_TOKEN`:** Read from `~/.openclaw/.env` or `openclaw.json`. Never commit. Ensure `clawvis/instances/ldom/.env.local` is in `.gitignore`.
- **Authelia Docker volumes:** Container mounts `/config/` as volume. When moving config files, recreate container (`docker rm lab-authelia`) so the new path applies.
- **4 private skill symlinks to update:** `brain-pulse`, `dombot-mail`, `hub-refresh`, `system-restart` — still on hub-ldom, migrate manually.
- **`HUB_PORT=5678` in `clawvis/.env`:** Legacy from old name (Clawpilot). Unused in production. Remove or fix to avoid confusion with real port 8088.
- **`/kanban/` and `/settings/` static routes:** These serve legacy static Kanban and Settings. After Hub SPA migration, replace or redirect to main Hub (`/`).
- **`poetic_shield` on port 8503:** Defined in nginx upstreams but not in `ss -tlnp` → service likely stopped or intermittent. Verify before migrating nginx config.
- **brain-pulse Vite dev server (port 5175):** Runs in dev mode (`node`). Check whether it should be built as static or kept as proxy in production.
