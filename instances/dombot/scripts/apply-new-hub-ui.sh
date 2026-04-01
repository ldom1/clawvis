#!/usr/bin/env bash
# Déploie la SPA Hub à jour (Kanban / Logs / Chat markdown) sur Dombot :
# 1) nginx hôte → plus d'alias statique /kanban|/settings, tout vers clawvis_hub
# 2) rebuild image Docker hub + up -d
#
# Prérequis : docker compose, nginx, gettext (envsubst), .env clawvis avec INSTANCE_NAME=dombot, HUB_PORT cohérent.
set -euo pipefail

SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTANCE="$(cd "${SCRIPTS}/.." && pwd)"
CLAWVIS="$(cd "${INSTANCE}/../.." && pwd)"

cd "${CLAWVIS}"
export LAB="${LAB:-$(cd "${CLAWVIS}/.." && pwd)}"

echo "==> 1/3 render nginx (lab SPA → upstream 127.0.0.1:8089)"
bash "${SCRIPTS}/render-nginx.sh"

echo "==> 2/3 docker compose build hub"
docker compose -f docker-compose.yml -f instances/dombot/docker-compose.override.yml build hub

echo "==> 3/3 docker compose up -d hub"
docker compose -f docker-compose.yml -f instances/dombot/docker-compose.override.yml up -d hub

echo "==> OK — recharge nginx hôte si besoin (ex. kill -HUP \$(cat instances/dombot/logs/nginx.pid))"
echo "    Puis ouvre https://lab.dombot.tech/kanban/ en navigation privée (anti-cache)."
