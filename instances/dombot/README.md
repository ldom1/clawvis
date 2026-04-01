# Instance `dombot` (lab.dombot.tech)

## Nginx : Kanban / Logs = SPA Docker

Les routes **`/kanban/`**, **`/logs/`**, **`/settings/`** doivent être servies par le **conteneur Hub** (même upstream que `/`), pas par `alias` vers `public/kanban/` (vieux statique).

1. Variables puis génération :
   ```bash
   cd /chemin/vers/clawvis
   export LAB="$(dirname "$(pwd)")"   # ex. /home/lgiron/Lab
   ./instances/dombot/scripts/render-nginx.sh
   ```
2. Vérifier : `nginx -t -c instances/dombot/logs/nginx-active.conf`
3. Démarrer ou recharger le master nginx qui pointe vers ce fichier (souvent `nginx -c .../logs/nginx-active.conf` puis `kill -HUP $(cat instances/dombot/logs/nginx.pid)`).

Option : `./instances/dombot/scripts/render-nginx.sh --reload` si le pid file existe.

## Docker Hub

Après changement du frontend : `docker compose -f docker-compose.yml -f instances/dombot/docker-compose.override.yml build hub && docker compose ... up -d hub`
