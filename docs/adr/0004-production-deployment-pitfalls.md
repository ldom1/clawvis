# 0004 — Production Deployment Pitfalls (Dombot first deploy 2026-03-28)

## Status
Accepted

## Context

First real production deployment of Clawvis on Dombot (lab.dombot.tech). Three classes of failures emerged that were not caught in CI or local testing. This ADR documents them as permanent safeguards.

---

## Pitfall 1 — Broken symlink inside Docker containers

### Problem
`instances/ldom` in the clawvis repo is a symlink to `/home/lgiron/Lab/hub-ldom/instances/ldom`. Docker bind-mounts the `./instances` directory and includes the symlink — but the symlink target is outside the container's namespace. Result: `FileExistsError: [Errno 17] File exists: '/clawvis/instances/ldom'` when kanban-api and hub-memory-api try to `mkdir(parents=True, exist_ok=True)` on any path under `instances/ldom/`.

### Decision
In `instances/ldom/docker-compose.override.yml`, explicitly mount the real instance directory at the path the symlink points to:

```yaml
kanban-api:
  volumes:
    - /home/lgiron/Lab/hub-ldom/instances/ldom:/clawvis/instances/ldom

hub-memory-api:
  volumes:
    - /home/lgiron/Lab/hub-ldom/instances/ldom:/clawvis/instances/ldom
```

Docker resolves both mounts; the more specific `/clawvis/instances/ldom` shadows the broken symlink from the parent mount `./instances:/clawvis/instances`.

### Rule
**Any instance that uses a symlink to an external directory MUST add an explicit volume override for each container that reads from that path.**

---

## Pitfall 2 — Vite builds assets at absolute `/assets/` path

### Problem
Vite (no `base` config) builds to `dist/assets/index-HASH.js`. When nginx proxies `/hub/` to the hub container, the browser receives HTML with `<script src="/assets/index-HASH.js">` — an absolute path. nginx only had a `/hub/` location block, so `/assets/` returned 404 (not even a redirect). The page loaded as a black screen: CSS (dark theme) applied, JS never executed.

### Decision
Add a dedicated `location /assets/` block in the nginx template **before** the `/hub/` block:

```nginx
location /assets/ {
    auth_request /_authelia_auth;
    proxy_pass http://clawvis_hub/assets/;
    proxy_set_header Host $host;
    add_header Cache-Control 'public, max-age=31536000, immutable';
}
```

### Rule
**Any Vite SPA served under a subpath (e.g., `/hub/`) requires an explicit nginx location for `/assets/`. The `/assets/` block must come before the subpath block.**

---

## Pitfall 3 — Static root files (public/) served at absolute paths

### Problem
`hub/public/clawvis-mascot.svg` is copied to `dist/` root by Vite and referenced as `/clawvis-mascot.svg` in main.js. nginx had no location for this path — the logo returned 404 in production even though `http://hub-container/clawvis-mascot.svg` returns 200.

### Decision
Add a regex location for known root static files in the nginx template:

```nginx
location ~ ^/(clawvis-mascot\.svg|favicon\.ico|favicon\.png)$ {
    auth_request /_authelia_auth;
    proxy_pass http://clawvis_hub$request_uri;
    proxy_set_header Host $host;
    add_header Cache-Control "public, max-age=86400";
}
```

### Rule
**Any file placed in `hub/public/` and referenced with an absolute path in main.js MUST have an explicit nginx location block. Alternatively: configure `base: '/hub/'` in vite.config.js (long-term fix) to eliminate all absolute-root references.**

---

## Pitfall 4 — `envsubst` without export and without variable scope

### Problem (two sub-issues)

**4a — No `export`:** Variables set with `VAR=value` (no export) are not visible to child processes like `envsubst`. When running `HUB_ROOT=... envsubst '${HUB_ROOT}...'`, `envsubst` substitutes the variable list with env values — but only exported variables are in the env. Result: `${HUB_ROOT}` → empty → `pid /logs/nginx.pid` instead of `pid /path/to/logs/nginx.pid`. Nginx's HUP reload then silently fails because the PID file path is wrong.

**4b — No scope:** Running `envsubst < nginx.conf` without a variable list substitutes ALL `$VAR` patterns, including nginx variables like `$http_upgrade`, `$connection_upgrade`, `$host`, `$uri`. This corrupts `map` directives and `proxy_set_header` lines.

### Decision
The canonical regenerate command (also in `start.sh`) is:

```bash
export HUB_ROOT=/home/lgiron/Lab/hub-ldom/instances/ldom
export LAB=/home/lgiron/Lab
export OPENCLAW_GATEWAY_TOKEN=$(jq -r '.gateway.auth.token // empty' ~/.openclaw/openclaw.json 2>/dev/null || echo "")
envsubst '${HUB_ROOT} ${LAB} ${OPENCLAW_GATEWAY_TOKEN}' \
  < instances/ldom/nginx/nginx.conf \
  > instances/ldom/logs/nginx-generated.conf
kill -HUP $(cat instances/ldom/logs/nginx.pid)
```

Note: `nginx -t -c` will warn about the pid path — this is a false positive from testing without the nginx prefix. The actual HUP reload works correctly.

### Rule
**Always `export` variables before `envsubst`. Always scope `envsubst` with an explicit variable list matching the shell variables used in the template.**

---

## Pitfall 5 — Container not rebuilt after source changes

### Problem
After modifying `hub/src/main.js` (changing `/api/hub/chat` → `/api/hub/agent/`), `docker compose up -d` did NOT rebuild the hub container because the image layer cache was still valid. The deployed container continued serving the old JavaScript, causing API calls to fail silently on page load (black screen again).

### Decision
After any source code change to a service, explicitly rebuild:

```bash
docker compose -f docker-compose.yml -f instances/ldom/docker-compose.override.yml build <service>
docker compose -f docker-compose.yml -f instances/ldom/docker-compose.override.yml up -d --force-recreate <service>
```

### Rule
**`docker compose up -d` does not rebuild. After source changes: always `build` then `up --force-recreate`. Verify the deployed JS contains the expected strings before declaring success.**

---

---

## Pitfall 6 — `Path.home()` returns `/` in container (HOME not set)

### Problem
`logs_api.py` uses `Path.home() / ".openclaw" / "logs" / "dombot.jsonl"` to find the log file. Inside Docker, if `HOME` is not set in the container environment, `Path.home()` returns `/` — the log path becomes `/.openclaw/logs/dombot.jsonl` which doesn't exist. Result: the Logs view always shows "0 logs found".

### Fix
In `instances/ldom/docker-compose.override.yml`, add to kanban-api:

```yaml
kanban-api:
  volumes:
    - /home/lgiron/.openclaw/logs:/home/lgiron/.openclaw/logs:ro
  environment:
    - HOME=/home/lgiron
```

### Rule
**Any container that uses `Path.home()` or reads host user files MUST have `HOME` explicitly set in its environment and the relevant host paths mounted.**

---

## Pitfall 7 — `hub_settings.json projects_root` points to non-existent container path

### Problem
`hub_settings.json` contained `"projects_root": "/clawvis/instances/ldom/projects"` — a path inside the container that was never created. `list_projects()` silently returns `[]` when `projects_root` doesn't exist. Result: the Hub Projects view shows 0 projects even though real project directories exist on the host.

On Dombot, the actual project directories live at `/home/lgiron/Lab/project/` (brain-pulse, debate-arena, messidor, optimizer-arena, plume, real-estate, techspend).

### Fix
Update `instances/ldom/memory/kanban/hub_settings.json` with the real host path, and mount it in the kanban-api container:

```json
{"projects_root": "/home/lgiron/Lab/project", "instances_external_root": "", "linked_instances": []}
```

```yaml
kanban-api:
  volumes:
    - /home/lgiron/Lab/project:/home/lgiron/Lab/project:ro
```

### Rule
**After any `clawvis install`, verify `hub_settings.json projects_root` points to a real path accessible inside the container. Default value (`/clawvis/instances/ldom/projects`) is a placeholder — update it during instance setup.**

---

## Pitfall 8 — Direct URL access to Hub SPA sub-paths returns nginx 404

### Problem
The Hub SPA routes internally via hash (`/hub/#/chat`, `/hub/#/logs`, etc.). Users or external links hitting `https://lab.dombot.tech/chat/` directly get a nginx 404 because no location block exists for `/chat/`. This is a common surprise after a successful deployment — everything works from the Hub home, but direct URLs fail.

### Fix
Add redirect location blocks in the nginx template for each SPA sub-path that might be accessed directly:

```nginx
location = /chat  { return 301 /hub/#/chat; }
location = /chat/ { return 301 /hub/#/chat; }
```

### Rule
**For every SPA route that may be linked externally, add a nginx redirect to the Hub hash route. Add them to the nginx template at deploy time, not reactively.**

---

## Consequences

- `instances/ldom/docker-compose.override.yml` now contains explicit volume mounts for kanban-api and hub-memory-api
- kanban-api has `HOME=/home/lgiron` + openclaw logs + project dir mounts
- nginx template has location blocks for `/assets/`, root static files, and `/chat/` redirect
- `hub_settings.json projects_root` must be set to real host path during instance setup
- `envsubst` usage in all scripts must use `export` + explicit variable list
- Deploy checklist (see `docs/guides/deploy-checklist.md`) must include a rebuild step

## Summary table (all pitfalls)

| # | Symptom | Cause | Fix |
|---|---------|-------|-----|
| 1 | 500 Kanban/Memory | Broken Docker symlink | Volume override direct mount |
| 2 | Black page | Vite `/assets/` not routed by nginx | `location /assets/` before `/hub/` |
| 3 | Logo 404 | `hub/public/` root files not routed | nginx regex location for root statics |
| 4 | nginx HUP silent fail | envsubst without export + without scope | `export` + scoped envsubst |
| 5 | Black page (again) | Container not rebuilt after JS changes | `build` + `up --force-recreate` |
| 6 | 0 logs | `Path.home()` = `/` in container | `HOME=/home/lgiron` + openclaw logs mount |
| 7 | 0 projects | `projects_root` path doesn't exist | Update `hub_settings.json` + mount real dir |
| 8 | `/chat/` 404 | No nginx location for SPA sub-paths | nginx redirect `location /chat/ → /hub/#/chat` |
