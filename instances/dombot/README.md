# Instance `dombot` (lab.dombot.tech)

## Principe produit (prioritaire)

- **Clawvis doit rester simple à utiliser** : le moins de scripts et de chemins « ops » possibles dans cette instance.
- **Cible** : un utilisateur ne devrait **pas avoir à cloner le dépôt Git** pour installer, mettre à jour ou utiliser le Hub — installation packagée ou release (wizard / image / installeur), pas une collection de `.sh` à maintenir à la main.
- Ce qui est décrit ci-dessous est du **maintien actuel** (devbox / transition). Tout nouveau script ici est une **dette** à faire disparaître vers ce modèle.

---

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
