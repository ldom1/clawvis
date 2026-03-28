#!/usr/bin/env bash
# Clawvis — health check
# Tests Docker services (direct ports) + optional nginx endpoint check.
#
# Usage:
#   ./hub-healthcheck.sh                  # human output
#   ./hub-healthcheck.sh --json           # machine-readable JSON
#   NGINX_PORT=8088 ./hub-healthcheck.sh  # also check nginx gateway
#
# Environment variables:
#   HUB_PORT         Hub container host port (default 8089)
#   KANBAN_API_PORT  Kanban API host port    (default 8090)
#   HUB_MEMORY_PORT  Memory API host port    (default 8091)
#   AGENT_PORT       Agent service host port (default 8093)
#   NGINX_PORT       nginx gateway port (optional — skip if unset)

[ -z "${BASH_VERSION:-}" ] && exec bash "$0" "$@"

HUB_PORT="${HUB_PORT:-8089}"
KANBAN_API_PORT="${KANBAN_API_PORT:-8090}"
HUB_MEMORY_PORT="${HUB_MEMORY_PORT:-8091}"
AGENT_PORT="${AGENT_PORT:-8093}"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'; BOLD='\033[1m'
pass=0; fail=0; results=()

check() {
  local name="$1" url="$2" expect="${3:-2xx}" timeout="${4:-5}"
  local status
  status=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$url" 2>/dev/null)
  if [[ "$status" == "$expect" || ( "$expect" == "2xx" && "$status" =~ ^2 ) ]]; then
    echo -e "  ${GREEN}✓${NC} ${name} → ${status}"
    results+=("{\"name\":\"$name\",\"url\":\"$url\",\"status\":$status,\"ok\":true}")
    ((pass++))
  else
    echo -e "  ${RED}✗${NC} ${name} → ${status:-timeout}"
    results+=("{\"name\":\"$name\",\"url\":\"$url\",\"status\":${status:-0},\"ok\":false}")
    ((fail++))
  fi
}

check_json() {
  local name="$1" url="$2" contains="${3:-}" timeout="${4:-5}"
  local body status
  body=$(curl -s --max-time "$timeout" -w "\n%{http_code}" "$url" 2>/dev/null)
  status="${body##*$'\n'}"; body="${body%$'\n'*}"
  if [[ ! "$status" =~ ^2 ]]; then
    echo -e "  ${RED}✗${NC} ${name} → HTTP ${status:-timeout}"
    results+=("{\"name\":\"$name\",\"url\":\"$url\",\"status\":${status:-0},\"ok\":false}")
    ((fail++)); return
  fi
  if ! echo "$body" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    echo -e "  ${RED}✗${NC} ${name} → 200 non-JSON"
    results+=("{\"name\":\"$name\",\"url\":\"$url\",\"status\":$status,\"ok\":false}")
    ((fail++)); return
  fi
  if [[ -n "$contains" && "$body" != *"$contains"* ]]; then
    echo -e "  ${RED}✗${NC} ${name} → JSON sans «$contains»"
    results+=("{\"name\":\"$name\",\"url\":\"$url\",\"status\":$status,\"ok\":false}")
    ((fail++)); return
  fi
  echo -e "  ${GREEN}✓${NC} ${name} → ${status} JSON"
  results+=("{\"name\":\"$name\",\"url\":\"$url\",\"status\":$status,\"ok\":true}")
  ((pass++))
}

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}🦅 Clawvis — Health Check${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo ""
echo -e "${YELLOW}● Hub container (:${HUB_PORT})${NC}"
check     "Hub SPA (index.html)"      "http://localhost:${HUB_PORT}/"                    "2xx" 5
check     "Hub /setup/runtime/"       "http://localhost:${HUB_PORT}/setup/runtime/"      "2xx" 5

echo ""
echo -e "${YELLOW}● Kanban API (:${KANBAN_API_PORT})${NC}"
check     "Kanban API /docs"          "http://localhost:${KANBAN_API_PORT}/docs"          "2xx" 5
check_json "Kanban /tasks"            "http://localhost:${KANBAN_API_PORT}/tasks"         "\"tasks\"" 5
check_json "Kanban /hub/projects"     "http://localhost:${KANBAN_API_PORT}/hub/projects"  "\"projects\"" 5
check_json "Kanban /stats"            "http://localhost:${KANBAN_API_PORT}/stats"         "" 5
check_json "Kanban /logs/summary"     "http://localhost:${KANBAN_API_PORT}/logs/summary"  "\"total\"" 5

echo ""
echo -e "${YELLOW}● Hub Memory API (:${HUB_MEMORY_PORT})${NC}"
check     "Memory API /docs"          "http://localhost:${HUB_MEMORY_PORT}/docs"          "2xx" 5

echo ""
echo -e "${YELLOW}● Agent Service (:${AGENT_PORT})${NC}"
check_json "Agent /health"            "http://localhost:${AGENT_PORT}/health"             "\"ok\"" 5
check_json "Agent /status"            "http://localhost:${AGENT_PORT}/status"             "\"provider\"" 5
check_json "Agent /config"            "http://localhost:${AGENT_PORT}/config"             "\"preferred_provider\"" 5

if [[ -n "${NGINX_PORT:-}" ]]; then
  echo ""
  echo -e "${YELLOW}● nginx gateway (:${NGINX_PORT}) — auth-protected (expect 404 from localhost)${NC}"
  # Protected by Authelia — 404 from localhost is expected (no session cookie).
  # A 200 from a real browser session confirms the route exists.
  check "nginx /hub/"            "http://localhost:${NGINX_PORT}/hub/"             "404" 5
  check "nginx /setup/runtime/"  "http://localhost:${NGINX_PORT}/setup/runtime/"   "404" 5
  check "nginx /assets/ (probe)" "http://localhost:${NGINX_PORT}/assets/index.js"  "404" 5
fi

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
total=$((pass + fail))
if [[ $fail -eq 0 ]]; then
  echo -e "${GREEN}${BOLD}✓ All checks passed (${pass}/${total})${NC}"
else
  echo -e "${RED}${BOLD}✗ ${fail} failure(s) / ${total} checks${NC}"
fi
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [[ "$1" == "--json" ]]; then
  joined=$(IFS=,; echo "${results[*]}")
  echo "{\"pass\":$pass,\"fail\":$fail,\"total\":$total,\"results\":[$joined]}"
fi

exit $fail
