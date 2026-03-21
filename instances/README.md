# Instances

Each deployment of Clawvis is an "instance" — a copy of Clawvis customized for one user/org.

## Create your instance

```bash
cp -r instances/example instances/ldom   # use your name
echo "instances/ldom/.env.local" >> .gitignore
```

For a private fork (recommended):
```bash
git clone https://github.com/lgiron/clawvis hub-ldom
cd hub-ldom
git remote rename origin upstream
git remote add origin git@github.com:YOURNAME/hub-ldom.git
cp -r instances/example instances/ldom
echo "instances/ldom/.env.local" >> .gitignore
git push -u origin main
```

## What goes where

| Item | Location | Why |
|------|----------|-----|
| nginx config (personal) | `instances/ldom/nginx/nginx.conf` | Your routes |
| Authelia | `instances/ldom/authelia/` | Your SSO |
| Scripts | `instances/ldom/scripts/` | Your ops scripts |
| Served content | `instances/ldom/public/` | Your dashboard HTML |
| API keys | `instances/ldom/.env.local` | Never committed |
| Generic hub code | `hub/`, `hub-core/`, `kanban/` | Shared — contribute back |
