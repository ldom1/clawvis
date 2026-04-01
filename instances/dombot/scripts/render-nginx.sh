#!/usr/bin/env bash
# Generate instances/dombot/logs/nginx-active.conf from nginx/nginx.conf via envsubst.
# Usage:
#   ./instances/dombot/scripts/render-nginx.sh           # test + write active conf
#   ./instances/dombot/scripts/render-nginx.sh --reload  # nginx -t then HUP master (needs pid file)
set -euo pipefail

SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTANCE="$(cd "${SCRIPTS}/.." && pwd)"
CLAWVIS="$(cd "${INSTANCE}/../.." && pwd)"

export HUB_ROOT="${INSTANCE}"
export LAB="${LAB:-$(cd "${CLAWVIS}/.." && pwd)}"
export OPENCLAW_GATEWAY_TOKEN="${OPENCLAW_GATEWAY_TOKEN:-}"
if [ -f "${HOME}/.openclaw/openclaw.json" ] && [ -z "${OPENCLAW_GATEWAY_TOKEN}" ]; then
  OPENCLAW_GATEWAY_TOKEN="$(jq -r '.gateway.auth.token // empty' "${HOME}/.openclaw/openclaw.json" 2>/dev/null || true)"
  export OPENCLAW_GATEWAY_TOKEN
fi

mkdir -p "${HUB_ROOT}/logs"
command -v envsubst >/dev/null || {
  echo "install gettext-base (envsubst)" >&2
  exit 1
}

envsubst '${HUB_ROOT} ${LAB} ${OPENCLAW_GATEWAY_TOKEN}' \
  < "${HUB_ROOT}/nginx/nginx.conf" \
  > "${HUB_ROOT}/logs/nginx-active.conf"

nginx -t -c "${HUB_ROOT}/logs/nginx-active.conf"
echo "==> wrote ${HUB_ROOT}/logs/nginx-active.conf"

if [ "${1:-}" = "--reload" ]; then
  pid_file="${HUB_ROOT}/logs/nginx.pid"
  if [ -f "${pid_file}" ]; then
    kill -HUP "$(cat "${pid_file}")"
    echo "==> sent HUP to nginx (pid $(cat "${pid_file}"))"
  else
    echo "[warn] no ${pid_file}; start nginx with: nginx -c ${HUB_ROOT}/logs/nginx-active.conf" >&2
  fi
fi
