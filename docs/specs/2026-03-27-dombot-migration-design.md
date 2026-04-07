# Design spec — Phase 1.5: Dombot migration (Clawpilot → Clawvis)

**Date:** 2026-03-27  
**Status:** Approved — pending implementation  
**Scope:** Production Clawvis deployment on Dombot server, replacing hub-ldom

---

## Context

Dombot is a personal home server running a "Clawpilot" instance (hub-ldom) — the architecture that preceded Clawvis. OpenClaw is installed on this server (`~/.openclaw/`) with its own skills and shared memory via symlink.

The goal is to migrate cleanly to Clawvis, validating install and production deployment under real conditions.

### Current architecture (before migration)

```
~/Lab/hub-ldom/                  ← private instance (dombot-lab-hub git repo)
  instances/ldom/
    nginx/                        ← nginx config (dombot.tech + lab.dombot.tech)
    authelia/                     ← SSO behind lab.dombot.tech
    memory/                       ← ldom memory vault
    skills/                       ← 4 private skills
    public/, scripts/, src/...

~/Lab/clawvis/                   ← clawvis core (public), NOT active
  instances/example/              ← template only

~/.openclaw/
  workspace/
    memory -> hub-ldom/instances/ldom/memory/   ← symlink
  skills/                         ← 16 skills (mixed public/private, real dirs)
```

**Network:**
```
Internet → VPS OVH nginx (lab.dombot.tech) → Tailscale 100.64.162.103:8088
→ Dombot nginx (hub-ldom nginx) → services behind Authelia
```

No Clawvis Hub, kanban-api, or memory-api containers are running yet.

---

## Target philosophy

> **Clawvis = OpenClaw control tower.**  
> Skills and memory have a single source of truth in Clawvis.  
> OpenClaw points to Clawvis, not the reverse.

---

## Target architecture

### Layout

```
~/Lab/clawvis/
  skills/                             ← PUBLIC skills (core Clawvis, upstream)
    logger/
    kanban-implementer/
    git-sync/
    skill-tester/
    ...
  instances/
    ldom/                             ← created by clawvis install, git = dombot-lab-hub
      docker-compose.override.yml     ← real production override
      .env.local                      (gitignored — secrets)
      memory/                         ← ldom vault (single source of truth)
      nginx/nginx.conf                ← nginx config migrated from hub-ldom
      authelia/                       ← authelia config migrated
      skills/                         ← PRIVATE ldom skills
        brain-pulse/
        dombot-mail/
        hub-refresh/
        system-restart/
      public/
      scripts/

~/Lab/hub-ldom/                      ← DEPRECATED, archived after migration

~/.openclaw/
  workspace/
    memory -> ~/Lab/clawvis/instances/ldom/memory/  ← updated symlink
  skills/
    # Public skills → symlinks to clawvis/skills/
    logger        -> ~/Lab/clawvis/skills/logger/
    kanban-*      -> ~/Lab/clawvis/skills/kanban-*/
    git-sync      -> ~/Lab/clawvis/skills/git-sync/
    skill-tester  -> ~/Lab/clawvis/skills/skill-tester/
    brain-maintenance -> ~/Lab/clawvis/skills/brain-maintenance/
    knowledge-consolidator -> ~/Lab/clawvis/skills/knowledge-consolidator/
    morning-briefing -> ~/Lab/clawvis/skills/morning-briefing/
    proactive-innovation -> ~/Lab/clawvis/skills/proactive-innovation/
    qmd           -> ~/Lab/clawvis/skills/qmd/
    reverse-prompt -> ~/Lab/clawvis/skills/reverse-prompt/
    ruflo         -> ~/Lab/clawvis/skills/ruflo/
    self-improvement -> ~/Lab/clawvis/skills/self-improvement/
    # Private skills → symlinks to instances/ldom/skills/
    brain-pulse   -> ~/Lab/clawvis/instances/ldom/skills/brain-pulse/
    dombot-mail   -> ~/Lab/clawvis/instances/ldom/skills/dombot-mail/
    hub-refresh   -> ~/Lab/clawvis/instances/ldom/skills/hub-refresh/
    system-restart -> ~/Lab/clawvis/instances/ldom/skills/system-restart/
```

### Target network flow

```
Internet
  -> VPS OVH nginx (lab.dombot.tech, fixed IP)
    -> proxy_pass Tailscale 100.64.162.103:8088
      -> Dombot nginx (instances/ldom/nginx/)   [port 8088]
          /              -> Clawvis Hub SPA (hub container)
          /api/hub/*     -> kanban-api + hub-memory-api
          /memory/       -> Obsidian remote (kept)
          /brain-pulse/  -> brain-pulse service (kept)
          /authelia/     -> Authelia (kept)
          /plume/, /real-estate/, /debate/, /poems/, /techspend/  (kept)
```

### Production docker-compose

```bash
# Production deploy command
docker compose \
  -f ~/Lab/clawvis/docker-compose.yml \
  -f ~/Lab/clawvis/instances/ldom/docker-compose.override.yml \
  up -d
```

The ldom `docker-compose.override.yml` defines:
- Real ports (`HUB_PORT=8088`, `KANBAN_API_PORT=8090`, `HUB_MEMORY_API_PORT=8091`)
- Volumes: nginx config, authelia, memory vault
- Extra services: kanban-api, hub-memory-api, authelia, nginx
- Networks: nginx bridge with existing services (brain-pulse, plume, etc.)

---

## Auto-symlink for new skills

### Principle

When a new skill is created (in `clawvis/skills/` or `instances/ldom/skills/`), it must be available in OpenClaw without manual steps.

### Command

```bash
clawvis skills sync
```

Behavior:
1. Scan `~/Lab/clawvis/skills/*/` → create public symlinks in `~/.openclaw/skills/`
2. Scan `~/Lab/clawvis/instances/ldom/skills/*/` → create private symlinks
3. If `~/.openclaw/skills/<name>` is a real directory (old install) → `WARN: manual dir found, skipping`
4. Never remove existing symlinks (append only)

### Git hooks

`.githooks/post-merge` in `clawvis/` and in `instances/ldom/` (dombot-lab-hub):
```bash
#!/bin/bash
# Auto-sync skill symlinks after git pull
clawvis skills sync
```

Setup: `git config core.hooksPath .githooks` (already in place for commit-msg).

---

## Phase 1.5 steps

### 1.5.1 — Audit & snapshot of hub-ldom

- Document all active services, ports, env vars (no secrets)
- Save generated nginx config
- Skills inventory: which is in hub-ldom vs ~/.openclaw only
- Deliverable: `docs/adr/0003-dombot-migration.md`

### 1.5.2 — `clawvis install` on Dombot

- Run Clawvis wizard with `INSTANCE_NAME=ldom` on the server
- Validate `instances/ldom/` structure (real flow test)
- Initialize `instances/ldom/` as git repo with remote `dombot-lab-hub`
- First commit: standard template structure

### 1.5.3 — Migrate hub-ldom → instances/ldom/

Content to migrate:
- `nginx/nginx.conf` → adjust `proxy_pass` to Clawvis containers
- `authelia/` → direct copy
- `memory/` → keep in place (already correct structure)
- `skills/` (4 private skills) → copy into `instances/ldom/skills/`
- `docker-compose.override.yml` → rewrite for real Clawvis production
- `.env.local` → migrate variables (no tracked secrets)

### 1.5.4 — OpenClaw symlinks

Update `~/.openclaw/workspace/memory`:
```bash
rm ~/.openclaw/workspace/memory
ln -s ~/Lab/clawvis/instances/ldom/memory ~/.openclaw/workspace/memory
```

Clear old skill dirs and create symlinks:
```bash
clawvis skills sync  # first manual run
```

Install post-merge git hook on both repos.

### 1.5.5 — Production deployment

```bash
cd ~/Lab/clawvis
docker compose \
  -f docker-compose.yml \
  -f instances/ldom/docker-compose.override.yml \
  up -d
```

Validation:
- `curl http://localhost:8088/` → Hub SPA responds
- `curl http://localhost:8090/api/kanban/projects` → kanban-api responds
- `curl http://localhost:8091/api/hub/memory/tree` → memory-api responds
- `lab.dombot.tech/` → Clawvis Hub reachable from browser via VPS

### 1.5.6 — OpenClaw wired validation

- Hub Settings → AI Runtime → select OpenClaw, URL `http://localhost:3333`
- `GET /api/hub/chat/status` → `{"openclaw_configured": true}`
- Send message from `/chat/` → reply received
- Verify OpenClaw skills load from symlinks

---

## Exit criteria

- [ ] `clawvis install` created `instances/ldom/` correctly (real-world flow validated)
- [ ] `hub-ldom` is deprecated and archived
- [ ] `~/.openclaw/skills/*` = 100% symlinks (no real directories)
- [ ] `~/.openclaw/workspace/memory` → `clawvis/instances/ldom/memory/`
- [ ] `clawvis skills sync` works and new skills auto-symlink
- [ ] `docker compose -f ... -f instances/ldom/docker-compose.override.yml up` deploys everything
- [ ] `lab.dombot.tech/` shows Clawvis Hub SPA
- [ ] Authelia still works on `lab.dombot.tech`
- [ ] Existing services (memory, brain-pulse, etc.) still reachable
- [ ] OpenClaw responds via Hub Chat

---

## Architecture decisions

**ADR-0003:** `instances/ldom/` in `clawvis/` (Option B) — dombot-lab-hub clone placed manually, gitignored by clawvis core, `upstream=clawvis` kept in dombot-lab-hub for optional `git fetch upstream`.

**Why not submodule:** Submodule management in prod is fragile (forgotten init/update). The instance is gitignored and managed independently, matching the Clawvis contract.

**Why recreate via `clawvis install`:** Validates the install flow under real conditions. End-to-end test of Phase 1 on a real machine.
