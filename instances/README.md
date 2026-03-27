# Instances

Each deployment of Clawvis is an "instance" — a copy of Clawvis customized for one user/org.

## Create your instance

```bash
./install.sh
# installer asks your instance name and renames:
# instances/example -> instances/<your_name>
```

For a private fork (recommended):
```bash
git clone https://github.com/ldom1/clawvis hub-ldom
cd hub-ldom
git remote rename origin upstream
git remote add origin git@github.com:YOURNAME/hub-ldom.git
# run installer and set your instance name
./install.sh
git push -u origin main
```

## What goes where

| Item | Location | Why |
|------|----------|-----|
| nginx config (personal) | `instances/ldom/nginx/nginx.conf` | Your routes |
| Authelia | `instances/ldom/authelia/` | Your SSO |
| Scripts | `instances/ldom/scripts/` | Your ops scripts |
| Instance memory | `instances/<name>/memory/` | Canonical Brain + project SoT |
| API keys | `instances/ldom/.env.local` | Never committed |
| Generic hub code | `hub/`, `hub-core/`, `kanban/` | Shared — contribute back |
