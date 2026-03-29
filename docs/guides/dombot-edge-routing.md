# Dombot-style public routing (landing vs lab)

This documents the **production** pattern used on the homelab host **Dombot**: one reverse proxy entry port on the LAN/Tailscale side (`8088`) with **multiple `server` blocks** by `server_name`.

It is **not** the same as local dev (`clawvis start` / `scripts/start.sh`).

## What `lab.dombot.tech` hits

| Layer | Role |
|-------|------|
| Public DNS + TLS | Typically a VPS (nginx) terminates HTTPS and forwards to the home host (often via **Tailscale**). |
| Home host `:8088` | **`/usr/sbin/nginx`** with **`instances/dombot/logs/nginx-active.conf`**, generated from **`instances/dombot/nginx/nginx.conf`** using **`envsubst '${HUB_ROOT} ${LAB} ${OPENCLAW_GATEWAY_TOKEN}'`**. |
| Host nginx `server_name lab.dombot.tech` | Proxies to **`upstream clawvis_hub`** (container Hub on **`127.0.0.1:8089`**) and enforces **Authelia** (`auth_request` → **`127.0.0.1:9091`**, Docker container `lab-authelia`). |
| Docker stack | `docker compose -f docker-compose.yml -f instances/dombot/docker-compose.override.yml up -d` from **`Lab/clawvis`**. |

**`clawvis start`** starts **Vite + uvicorn** on the host for development; it does **not** implement this vhost split and is **not** what serves `lab.dombot.tech` in this production layout.

## What `www.clawvis.fr` hits

Same host port **8088**, different **`server` block**: static **`$LAB/clawvis-landing/dist`** (marketing site). Do **not** route this hostname straight to the Hub container, or both domains will show the Hub SPA.

The marketing `server` block should **not** expose Authelia unless you intentionally want auth on the public site.

## Why Hub must not grab `0.0.0.0:8088` alone

If the Hub container is published as `0.0.0.0:8088->80`, every hostname pointing at that port gets the **Hub SPA** only — **no** per-host landing.

Patterns:

- **Edge nginx on 8088** + Hub bound to **`127.0.0.1:${HUB_PORT}`** (e.g. `8089`) — recommended for Dombot.
- **Hub only**: set **`HUB_HOST=0.0.0.0`** (see root **`docker-compose.yml`**) if you deliberately expose the container without host nginx (single-site / no landing split).

## Core repo: `HUB_HOST`

In **`docker-compose.yml`**:

```yaml
ports:
  - "${HUB_HOST:-127.0.0.1}:${HUB_PORT:-8088}:80"
```

Copy **`HUB_HOST`** from **`.env.example`**. Default **`127.0.0.1`** is safe for laptop/Docker Desktop; use **`0.0.0.0`** only when the container must accept non-loopback connections without a host reverse proxy.

## Operational notes

- After reboot, **regenerate** `nginx-active.conf` and start host nginx if you rely on it (user-run master is common); **`lab-authelia`** can use Docker **`restart: unless-stopped`**.
- Front proxy must send **`X-Forwarded-Proto: https`** when Authelia issues redirects, or login redirects may show `http://` links.

## See also

- [ADR 0003](../adr/0003-dombot-migration.md) — historical pre-migration snapshot (ports/routes evolved).
- [Production pitfalls](../adr/0004-production-deployment-pitfalls.md)
- [Architecture overview](../architecture.md)
