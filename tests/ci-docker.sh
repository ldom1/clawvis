#!/usr/bin/env bash
# ci-docker.sh — Phase 1.3 smoke test: real docker compose services + Playwright E2E
#
# Usage:
#   bash tests/ci-docker.sh              # build + start + test + teardown
#   bash tests/ci-docker.sh --no-build   # skip build (reuse existing images)
#   bash tests/ci-docker.sh --keep-up    # don't teardown after (for debugging)
#
# Requires: docker, docker compose, curl
# Optional: node + npm (for Playwright E2E — skipped if not available)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

HUB_PORT="${HUB_PORT:-8088}"
BASE_URL="http://localhost:${HUB_PORT}"
TIMEOUT_SECS=120
BUILD_FLAG="--build"
KEEP_UP=0
FAILURES=0

for arg in "$@"; do
  case "$arg" in
    --no-build) BUILD_FLAG="" ;;
    --keep-up)  KEEP_UP=1 ;;
  esac
done

# ── helpers ──────────────────────────────────────────────────────────────────

ok()   { printf "  [PASS] %s\n" "$1"; }
fail() { printf "  [FAIL] %s\n" "$1"; FAILURES=$((FAILURES + 1)); }
info() { printf "\n==> %s\n" "$1"; }

curl_check() {
  local label="$1" url="$2" expected_status="${3:-200}"
  local actual
  actual=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${BASE_URL}${url}" 2>/dev/null || echo "000")
  if [ "${actual}" = "${expected_status}" ]; then
    ok "${label} (${url} → ${actual})"
  else
    fail "${label} (${url} → expected ${expected_status}, got ${actual})"
  fi
}

json_check() {
  local label="$1" url="$2" key="$3"
  local body
  body=$(curl -s --max-time 10 "${BASE_URL}${url}" 2>/dev/null || echo "{}")
  if echo "${body}" | python3 -c "import sys,json; d=json.load(sys.stdin); assert '${key}' in d" 2>/dev/null; then
    ok "${label} (${url} has key '${key}')"
  else
    fail "${label} (${url} missing key '${key}' — got: ${body:0:120})"
  fi
}

wait_for_hub() {
  info "Waiting for Hub on ${BASE_URL} (up to ${TIMEOUT_SECS}s)"
  local elapsed=0
  until curl -sf --max-time 3 "${BASE_URL}/" >/dev/null 2>&1; do
    if [ "${elapsed}" -ge "${TIMEOUT_SECS}" ]; then
      echo "  [ERROR] Hub did not respond within ${TIMEOUT_SECS}s"
      docker compose logs hub | tail -20
      exit 1
    fi
    sleep 3
    elapsed=$((elapsed + 3))
    printf "  waiting... %ds\r" "${elapsed}"
  done
  printf "  Hub ready after %ds            \n" "${elapsed}"
}

wait_for_memory_api() {
  info "Waiting for Memory API on ${BASE_URL}/api/hub/memory/settings (up to 30s)"
  local elapsed=0
  until curl -sf --max-time 3 "${BASE_URL}/api/hub/memory/settings" >/dev/null 2>&1; do
    if [ "${elapsed}" -ge 30 ]; then
      echo "  [WARN] Memory API not ready after 30s — tests may fail"
      return
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  printf "  Memory API ready after %ds      \n" "${elapsed}"
}

teardown() {
  if [ "${KEEP_UP}" -eq 0 ]; then
    info "Teardown"
    docker compose down --remove-orphans --timeout 10 2>/dev/null || true
  else
    info "Services kept up (--keep-up). Run: docker compose down"
  fi
}

# ── main ─────────────────────────────────────────────────────────────────────

# Ensure .env exists (needed by docker compose)
if [ ! -f "${ROOT_DIR}/.env" ]; then
  cp "${ROOT_DIR}/.env.example" "${ROOT_DIR}/.env"
  # Set a minimal INSTANCE_NAME so memory mounts work
  echo "INSTANCE_NAME=e2e" >> "${ROOT_DIR}/.env"
fi

info "Starting services (docker compose up -d${BUILD_FLAG:+ --build})"
# shellcheck disable=SC2086
docker compose up -d ${BUILD_FLAG} hub kanban-api hub-memory-api

trap teardown EXIT

wait_for_hub
wait_for_memory_api

# Prime projects_root to a path that exists inside the container.
# The default (~/Lab/projects) resolves to /Lab/projects when HOME=/ (Docker),
# which is not writable by the container user. Override to the mounted volume.
info "Priming projects_root (container-safe path)"
INSTANCE_NAME_VAL=$(grep -E '^INSTANCE_NAME=' "${ROOT_DIR}/.env" | cut -d= -f2 | tr -d '[:space:]' || echo "example")
PROJECTS_ROOT_DOCKER="/clawvis/instances/${INSTANCE_NAME_VAL}/projects"
curl -s -X PUT "${BASE_URL}/api/hub/memory/settings" \
  -H "Content-Type: application/json" \
  -d "{\"projects_root\": \"${PROJECTS_ROOT_DOCKER}\"}" >/dev/null 2>&1 && \
  ok "projects_root set to ${PROJECTS_ROOT_DOCKER}" || \
  fail "could not prime projects_root"

# ── CURL SMOKE TESTS ──────────────────────────────────────────────────────────

echo ""
echo "=== Curl smoke tests ==="
echo ""

# Static assets / SPA
curl_check "Hub index (SPA root)"           "/"            200
curl_check "Hub /kanban/ route"             "/kanban/"     200
curl_check "Hub /logs/ route"               "/logs/"       200
curl_check "Hub /settings/ (static)"        "/settings/"   200
curl_check "Hub /chat/ route"               "/chat/"       200
curl_check "System JSON stub"               "/api/system.json" 200

# Kanban API (via nginx proxy)
curl_check "Kanban tasks list"              "/api/hub/kanban/tasks"        200
curl_check "Kanban projects list"           "/api/hub/kanban/hub/projects" 200
curl_check "Kanban stats"                   "/api/hub/kanban/stats"        200
curl_check "Chat status endpoint"           "/api/hub/chat/status"         200

# Memory API (via nginx proxy)
curl_check "Memory projects list"           "/api/hub/memory/projects"     200
curl_check "Memory settings"                "/api/hub/memory/settings"     200

# JSON shape checks
json_check "Kanban tasks is array"          "/api/hub/kanban/tasks"        "tasks"
json_check "Chat status has provider field" "/api/hub/chat/status"         "provider"
json_check "Memory settings shape"          "/api/hub/memory/settings"     "projects_root"

echo ""
printf "Curl results: %d failed\n" "${FAILURES}"

# ── PLAYWRIGHT E2E ────────────────────────────────────────────────────────────

PW_DIR="${ROOT_DIR}/tests/playwright"
PW_FAILURES=0

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo ""
  echo "==> [SKIP] Playwright: node/npm not available"
else
  echo ""
  echo "=== Playwright E2E against docker stack ==="
  echo ""

  npm ci --prefix "${PW_DIR}" --silent

  if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    (cd "${PW_DIR}" && npx playwright install --with-deps chromium 2>/dev/null)
  else
    (cd "${PW_DIR}" && npx playwright install chromium 2>/dev/null)
  fi

  set +e
  (
    cd "${PW_DIR}"
    PLAYWRIGHT_BASE_URL="${BASE_URL}" \
    PW_NO_WEBSERVER=1 \
    CI=true \
      npx playwright test --project=chromium --reporter=list
  )
  PW_FAILURES=$?
  set -e

  if [ "${PW_FAILURES}" -eq 0 ]; then
    echo ""
    echo "==> [OK] Playwright: all tests passed"
  else
    echo ""
    echo "==> [FAIL] Playwright: some tests failed (exit ${PW_FAILURES})"
    FAILURES=$((FAILURES + 1))
  fi
fi

# ── FINAL RESULT ──────────────────────────────────────────────────────────────

echo ""
if [ "${FAILURES}" -eq 0 ]; then
  echo "==> Phase 1.3 PASSED: all curl + E2E checks green"
  exit 0
else
  echo "==> Phase 1.3 FAILED: ${FAILURES} check(s) failed"
  exit 1
fi
