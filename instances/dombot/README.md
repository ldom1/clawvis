# Instance `dombot` (lab.dombot.tech)

## Obtenir les **nouvelles** pages Hub (Kanban, Logs, Chat markdown, …)

Une commande depuis la racine du dépôt `clawvis` :

```bash
cd ~/Lab/clawvis
export LAB=/home/lgiron/Lab
chmod +x instances/dombot/scripts/apply-new-hub-ui.sh
./instances/dombot/scripts/apply-new-hub-ui.sh
```

Puis **recharge nginx** si ton master n’utilise pas encore `instances/dombot/logs/nginx-active.conf` :

```bash
nginx -t -c ~/Lab/clawvis/instances/dombot/logs/nginx-active.conf
kill -HUP "$(cat ~/Lab/clawvis/instances/dombot/logs/nginx.pid)"
```

Ou démarre nginx une fois avec ce `-c`. Ouvre **`/kanban/`** et **`/logs/`** en **navigation privée** (vider le cache JS).

## Nginx : Kanban / Logs = SPA Docker

Les routes **`/kanban/`**, **`/logs/`**, **`/settings/`** doivent être servies par le **conteneur Hub** (même upstream que `/`), pas par `alias` vers `public/kanban/` (vieux statique).

- Génération seule : `./instances/dombot/scripts/render-nginx.sh` (idem avec `export LAB=...`).
- `nginx -t -c instances/dombot/logs/nginx-active.conf` avant reload.

## Docker Hub

`apply-new-hub-ui.sh` fait déjà `build hub` + `up -d`. Sinon manuellement :

`docker compose -f docker-compose.yml -f instances/dombot/docker-compose.override.yml build hub && ... up -d hub`
