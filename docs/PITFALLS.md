# docs/PITFALLS.md

> Known bugs, technical debt, and documented friction points.
> Updated after each significant debug session.
> For architecture → `docs/ARCHITECTURE.md`

---

## Production pitfalls (ADR 0004)

| # | Symptom | Cause | Fix |
|---|---------|-------|-----|
| 1 | 500 Kanban/Memory | Broken Docker symlink | Explicit volume override in `docker-compose.override.yml` |
| 2 | Black page | Vite `/assets/` not routed by nginx | `location /assets/` block BEFORE `/hub/` |
| 3 | Logo 404 | `hub/public/` root files not routed | nginx regex location for root statics |
| 4 | nginx HUP silent | `envsubst` without export + without scope | `export` + explicit scope |
| 5 | Black page (again) | Container not rebuilt after JS changes | `build` + `up --force-recreate` |
| 6 | 0 logs | `Path.home()` = `/` if `HOME` missing | `HOME=/home/lgiron` + openclaw logs volume |
| 7 | 0 projects | `projects_root` = non-existent path | Fix path + volume mount |
| 8 | `/chat/` inaccessible | Hash routing vs pathname SPA | Proxy `location /chat/` → clawvis_hub |
| 9 | OpenClaw Node v22+ | `setup_20.x` unsupported | `setup_22.x` in Dockerfile |
| 10 | EACCES UID 1000 | Host state files | `user: root` + identical mount |
| 11 | Port 8092 conflict | `spendlens_api` on 8092 | `AGENT_PORT=8093` in `.env` |
| 12 | Chat `[CLAWVIS:AUTH]` | OAuth tokens, not API keys | `preferred_provider=openclaw` in agent-config.json |
| 13 | `/project/<slug>` 404 | Missing nginx `location /project/` | Added in template 2026-03-28 |
| 14 | Containers without override | `docker compose up` without override → broken symlink | Always run with `-f instances/ldom/docker-compose.override.yml` |
| 15 | Cron `Channel is required` | No default channel | `"channel": "telegram"` in job delivery |
| 16 | Runtime banner always visible | SPA ignored backend state | Collapsible green chip when configured |
| 17 | Nginx orphan route after project delete | `_cleanup_nginx_route()` inactive without env var | Active if `NGINX_PROJECTS_D` set |
| 18 | Kanban / Logs / Settings SPA unchanged | `location /kanban/` + `/settings/` as `alias` to `instances/dombot/public/` | `nginx/nginx.conf`: `proxy_pass` Hub + `include …/snippets/spa-hub-prefixes.conf` (`^~` on SPA prefixes, **before** `projects.d`); `scripts/render-nginx.sh` |
| 19 | `500` on `/hub/` | Old `location /hub/` + `alias` or invalid path; UI is at `/` | `spa-hub-prefixes.conf` + `hub/nginx.conf`: `^~ /hub/` → 301 redirect to `/` or `/…`; remove any residual `alias` in `projects.d` |
| 20 | OpenClaw crons (e.g. hub-refresh 1h) not firing | **`openclaw-gateway`** failing (restart loop) — invalid config after CLI upgrade | `journalctl --user -u openclaw-gateway.service`; `PATH=~/.npm-global/bin:$PATH openclaw doctor --fix`; verify `systemctl --user status openclaw-gateway` **active (running)** stable |
| 21 | `doctor`: *Skipping skill path that resolves outside its configured root* (repeated) | Symlinks `~/.openclaw/skills/<name>` → `Lab/clawvis/...`: managed root is `~/.openclaw/skills`, OpenClaw ignores targets outside root | **`clawvis skills sync`** (`scripts/sync-openclaw-skills-dirs.sh`): `jq` + absolute paths `skills/` + `instances/<INSTANCE>/skills/`, removes managed symlinks, then **`openclaw gateway restart`**, **`openclaw skills list`**, **`openclaw doctor`**. Crons: absolute repo paths (not `~/.openclaw/skills/…`) |
| 22 | `collect.sh` / skill crons: *Command not allowed* (OpenClaw) | Execution policy / **tools** or **shell** allowlist on gateway blocking `uv`, `curl`, `bash`, paths off list | Check `openclaw doctor` and cron **tools** config (OpenClaw 2026.x); prefer **`exec`** jobs / direct shell script on machine rather than full agent round-trip if policy is strict |
| 23 | `skill-tester`: 0 tests, `~/.openclaw/skills` empty | After **`clawvis skills sync`** (extraDirs), no copies/symlinks under `~/.openclaw/skills` | Run with **`CLAWVIS_ROOT=$HOME/Lab/clawvis INSTANCE_NAME=dombot`** (or **`SKILL_TEST_ROOTS="…/skills …/instances/dombot/skills"`**): `bash skills/skill-tester/scripts/test-all.sh` |
| 24 | **500** on whole lab (`lab.dombot.tech` / `:8088`) | **`auth_request` Authelia → 400**: `X-Original-URL` is **`http://`** while TLS is at reverse proxy (local nginx sees `$scheme` = http) | Template `instances/dombot/nginx/nginx.conf`: force **`https`** for Authelia + **`map`** `lab_x_forwarded_proto` to Hub; `render-nginx.sh --reload` |
| 25 | **500** after fix #24; Authelia logs **« authelia url lookup failed »** | **AuthRequest** no longer infers portal URL if **`session.cookies[]` + `authelia_url`** missing (upgrade 4.38+) | **`configuration.yml`**: `session.cookies` with `authelia_url: https://lab.dombot.tech/authelia/`; **or** nginx: `proxy_pass …/auth-request?authelia_url=https://$host/authelia/;` (already in template) |
| 26 | **OpenClaw crons `exec denied`** — `security=allowlist ask=on-miss askFallback=deny` | Default allowlist mode: crons cannot wait for interactive approval, `askFallback=deny` blocks any script off allowlist | In `~/.openclaw/openclaw.json` → `tools.exec: {security: "full", ask: "off"}`; in `~/.openclaw/exec-approvals.json` → `defaults: {security: "full", ask: "off"}`; then `openclaw gateway restart`. Verified: `openclaw approvals get --gateway` shows `security=full, ask=off` |
| 27 | **`kanban/Dockerfile` — `uv sync --no-dev` fails** with `dombot-hub-core is not a workspace member` | `kanban/Dockerfile` copied `hub-core/` and `kanban/` but not root `pyproject.toml` + `uv.lock` that define the uv workspace | Add `COPY pyproject.toml ./` and `COPY uv.lock ./` BEFORE `COPY hub-core/ ./hub-core/` in `kanban/Dockerfile` |
| 28 | **kanban-api / hub-memory-api containers exit (255)** — `exec /clawvis/kanban/.venv/bin/uvicorn: no such file or directory` | With uv workspace, venv is created at repo root `/clawvis/.venv`, not `/clawvis/kanban/.venv` | Replace all `/clawvis/kanban/.venv/bin/` paths with `/clawvis/.venv/bin/` in `docker-compose.yml` and `kanban/Dockerfile` CMD |
| 29 | **White page on `lab.dombot.tech`** — Authelia portal empty, JS bundles do not load (`upstream prematurely closed connection`) | VPS nginx without `proxy_buffering`: streaming mode; Authelia JS bundles (~314 KB) and Hub assets drop via Tailscale DERP relay. HTML (2 KB) passes, large files do not. | VPS `/etc/nginx/sites-enabled/lab.dombot.tech`: `proxy_buffering on; proxy_buffer_size 128k; proxy_buffers 8 256k; proxy_busy_buffers_size 512k; proxy_read_timeout 120s;` then `nginx -s reload` |
| 30 | **White page on `lab.dombot.tech`** — Authelia JS truncated ~43 KB, nginx-error-http.log: `open() "/var/lib/nginx/proxy/…" failed (13: Permission denied) while reading upstream` | Devbox nginx runs as user `lgiron` without rights on `/var/lib/nginx/proxy/`. When a large file (> RAM buffers) must spill to disk, nginx cuts the connection → partial transfer. | `instances/dombot/nginx/nginx.conf`, `http {}` block: global `proxy_buffering off;`. Regenerate: `render-nginx.sh --reload`. |
| 31 | **Black page after auth** — Hub JS (`/assets/index-*.js`) truncated, same `Permission denied` — though pitfall #30 was supposed to fix | Fix #30 was `proxy_buffering off` *per location* (`/authelia/`) only. Local `nginx-reload.sh` wrote `nginx-generated.conf` while master reads `nginx-active.conf` → reloads applied nothing. Then nginx restart re-enabled buffering on `/assets/`. | Move `proxy_buffering off` to `http {}` block (global inheritance). Replace local `nginx-reload.sh` with tracked wrapper (`instances/dombot/scripts/nginx-reload.sh`) delegating to `render-nginx.sh --reload`. |
| 32 | **Hub shows 0 projects** despite projects_root configured | PROJECTS_ROOT in root `.env` pointed at host path (/home/lgiron/Lab/project) inaccessible in container; only ./instances is bind-mounted. Kanban API scans that folder to list projects. | 1) Volume `/home/lgiron/Lab/project:/clawvis/project` in kanban-api override.yml 2) PROJECTS_ROOT=/clawvis/project in root `.env` 3) hub_settings.json.projects_root=/clawvis/project |
| 33 | **Blank white `/apps/<slug>/`** in hub nginx | Dev `index.html` wins before `dist/index.html`, or Vite assets use `base: '/'` | Hub `nginx.conf`: `try_files` prefers `$uri/dist/index.html`; [re]build each app with `base: '/apps/<slug>/'` in `vite.config` |
---

## Fixed bugs — 2026-03-28 session

1. **hub-core pylint E0211**: `setup_runtime.py:21` — `get_providers()` missing `@staticmethod` → fixed
2. **Hub Prettier**: `src/main.js`, `src/style.css`, `vite.config.js` not formatted → fixed (`yarn --cwd hub format`)
3. **install.sh — non-standard `rg`**: `migrate_memory_if_needed` used `rg` → replaced with `find`
4. **install.sh — Docker unhelpful error**: Vague error → clear message with install link + `docker info`
5. **install.sh — Node version**: No check → Node >= 18 guard added
6. **install.sh — missing yarn in dev mode**: No fallback → automatic `corepack enable`
7. **docker-compose.yml — obsolete label**: `app=clawpilot` → `app=clawvis`
8. **hub/src/main.js — service counter**: `/openclaw/` counted "down" → marked `optional: true`
9. **hub/src/main.js — i18n FR accents**: `"Parametres"` → `"Paramètres"`, `"A configurer"` → `"À configurer"`, etc.

---

## Unresolved friction (priority)

### Critical — blocks Franc mode

**Kanban API missing from docker-compose**
In `docker` mode (Franc mode), the Kanban board is unusable: all `/api/kanban/*` calls return 404.
→ Fix: add `kanban-api` service based on `hub-core` to docker-compose + nginx proxy in hub container.

### Important

**Quartz Brain build**
`scripts/build-quartz.sh` depends on an optional submodule. If missing, Brain shows nothing without a clear error.
→ Fix: graceful degradation — show lightweight Python renderer if Quartz absent.

**`clawvis setup provider` not implemented**
Post-install CLI command to set provider from terminal. Mentioned in CLAUDE.md but missing.
→ Fix: implement in `clawvis-cli/` as post-install command.

### Minor

**`clawvis skills sync` (Phase 2A.7)**
OpenClaw skill symlinks not auto-synced. Should make skills available in chat.
→ Next step before Phase 2B.

---

## Technical audit — 2026-03-24

> Excerpt from technical findings on architecture debt.

**Gap vs real stack:**
- Dev mode: Vite on `HUB_PORT`, Vite proxy `/api/kanban/*` → Kanban API uvicorn (8090)
- Docker mode: nginx serves `hub/dist/`. **Kanban API not in docker-compose** — critical gap
- Brain = Logseq web app (`ghcr.io/logseq/logseq-webapp`) on `MEMORY_PORT` — iframe embed

**Tooling rules not to forget:**
- Hub → Yarn Berry 4 only (`yarn --cwd hub`) — never npm
- CLI → npm (`npm ci`)
- Kanban API + hub-core → uv only — never pip
- CI gate → `bash tests/ci-all.sh` exits 0 before any merge

---

## Template: add a pitfall

```markdown
| N | <observable symptom> | <root cause> | <fix applied or to apply> |
```

Rule: one documented pitfall = symptom + cause + fix. No "to investigate" without at least a suspected cause.
