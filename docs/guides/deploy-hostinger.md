# Deploying Clawvis on Hostinger VPS

> For non-technical users. No command line required after the first connection.

---

## Prerequisites

- A Hostinger VPS with **Docker** pre-installed ("Docker" template in hPanel)
- OpenClaw already deployed on the same VPS (or reachable via external URL)
- The Clawvis repo is **public** on GitHub

---

## Recommended method — Docker Manager in hPanel

Hostinger provides a visual **Docker Manager** in hPanel. No terminal required.

### Step 1 — Open Docker Manager

1. Log in to [hPanel](https://hpanel.hostinger.com)
2. Select your VPS → **Docker**
3. Click **New project**
4. Choose **Compose from URL**

### Step 2 — Point to Clawvis docker-compose

In the URL field, paste:

```
https://raw.githubusercontent.com/YOUR_USERNAME/clawvis/main/docker-compose.yml
```

> Replace `YOUR_USERNAME` with your GitHub username.

### Step 3 — Configure environment variables

In Docker Manager, add:

| Variable | Value | Description |
|----------|--------|-------------|
| `INSTANCE_NAME` | `my-instance` | Your instance name (no spaces) |
| `OPENCLAW_BASE_URL` | `http://host.docker.internal:3333` | OpenClaw URL on the same VPS |
| `OPENCLAW_API_KEY` | _(your key)_ | OpenClaw API key (if configured) |
| `PRIMARY_AI_PROVIDER` | `openclaw` | Use OpenClaw as provider |
| `HOST_UID` | `1000` | VPS user UID |
| `HOST_GID` | `1000` | VPS user GID |

> **OpenClaw on the same VPS:** use `http://host.docker.internal:3333`.
> Docker resolves this automatically to the host.
>
> **OpenClaw on another server:** use the full URL, e.g. `https://openclaw.mydomain.com`.

### Step 4 — Start the project

Click **Deploy**. Docker Manager pulls images and starts containers.

Open the Hub at: `http://<YOUR-VPS-IP>:8088`

---

## Advanced method — GitHub Actions (automatic deployment)

So every `git push` triggers a redeploy.

### Extra prerequisites

- Hostinger account with API access
- Your Hostinger **VM ID** (hPanel → VPS → API)
- Your **Hostinger API key** (hPanel → Profile → API Keys)

### Configuration

Add these secrets in your GitHub repo (**Settings → Secrets → Actions**):

| Secret | Value |
|--------|--------|
| `HOSTINGER_API_KEY` | Your Hostinger API key |
| `HOSTINGER_VM_ID` | Your VPS ID |

The `.github/workflows/deploy-hostinger.yml` workflow is included in Clawvis. It runs on each push to `main`.

---

## Architecture on the VPS

```
Internet
    │
    ▼
[VPS Hostinger]
    ├── Port 8088 (or 80 with reverse proxy)
    │       └── Hub nginx ─────────────────────────────┐
    │              ├── /api/hub/kanban/*  → kanban-api  │
    │              ├── /api/hub/memory/*  → memory-api  │
    │              └── /api/hub/chat/*    → kanban-api  │
    │                                          │        │
    │                                          ▼        │
    │                                      OpenClaw     │
    │                                    (port 3333)    │
    │                                                   │
    └── Port 3333 — OpenClaw (internal, not exposed)  ◄──┘
```

The OpenClaw port is **not** exposed externally — only the Hub (8088/80) is reachable.

---

## Add a domain name

To use `https://clawvis.mydomain.com` instead of an IP:

1. In hPanel → **Domains** → point a subdomain to the VPS IP
2. Install nginx as reverse proxy on the VPS:

```bash
# SSH to VPS
ssh root@<VPS-IP>

# Install nginx
apt install nginx -y

# Create config (replace clawvis.mydomain.com)
cat > /etc/nginx/sites-available/clawvis <<'CONF'
server {
    listen 80;
    server_name clawvis.mydomain.com;
    location / {
        proxy_pass http://127.0.0.1:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
CONF

ln -s /etc/nginx/sites-available/clawvis /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# SSL (Let's Encrypt)
apt install certbot python3-certbot-nginx -y
certbot --nginx -d clawvis.mydomain.com
```

---

## Verify deployment

After startup, verify:

```bash
# From your machine (replace IP)
curl http://<VPS-IP>:8088/api/hub/chat/status
# Expected: {"provider":"openclaw","openclaw_configured":true,...}

curl http://<VPS-IP>:8088/api/hub/kanban/hub/projects
# Expected: {"projects":[...]}

curl http://<VPS-IP>:8088/api/hub/memory/settings
# Expected: {"projects_root":...}
```

---

## Upgrade

To upgrade Clawvis to a new version:

**Docker Manager:** Open project → **Update** → manager pulls and restarts.

**GitHub Actions:** push to `main` — redeploy is automatic.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Chat does not respond | OpenClaw unreachable | Check `OPENCLAW_BASE_URL`, test `curl http://host.docker.internal:3333/v1/models` from container |
| Kanban empty | `INSTANCE_NAME` not set | Check variable in hPanel Docker Manager |
| Brain does not load | Quartz not built | `docker exec <hub-memory-api> bash scripts/build-quartz.sh` |
| Port 8088 unreachable | VPS firewall | hPanel → VPS → Firewall → allow port 8088 |
