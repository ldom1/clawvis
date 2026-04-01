#!/usr/bin/env bash
# skill-tester — run all Python unit tests for OpenClaw skills
# Usage:
#   test-all.sh              # test all skills with core/tests/
#   test-all.sh logger       # test a single skill
#   test-all.sh --list       # list testable skills
#
# Roots (first match wins defaults):
#   SKILL_TEST_ROOTS="path1 path2"  — explicit list of dirs containing skill subfolders
#   CLAWVIS_ROOT + INSTANCE_NAME    — adds .../skills and .../instances/$INSTANCE/skills
#   Else: ~/.openclaw/skills if non-empty, else ~/Lab/clawvis/skills (+ instances/dombot/skills)
#
# Logger (dombot-log): LOGGER_CORE_OVERRIDE or first existing .../logger/core under roots / Lab / .openclaw
set -uo pipefail

SKILL_FILTER="${1:-}"
PASS=0
FAIL=0
SKIP=0
REPORT=()

green() { printf '\033[32m%s\033[0m\n' "$*"; }
red()   { printf '\033[31m%s\033[0m\n' "$*"; }
yellow(){ printf '\033[33m%s\033[0m\n' "$*"; }
bold()  { printf '\033[1m%s\033[0m\n' "$*"; }

resolve_logger_core() {
  local r c
  if [[ -n "${LOGGER_CORE_OVERRIDE:-}" && -d "${LOGGER_CORE_OVERRIDE}" ]]; then
    printf '%s' "${LOGGER_CORE_OVERRIDE}"
    return 0
  fi
  for r in "${SKILL_ROOTS_ARR[@]}"; do
    c="${r%/}/logger/core"
    [[ -d "$c" ]] && { printf '%s' "$c"; return 0; }
  done
  for c in \
    "${HOME}/Lab/clawvis/skills/logger/core" \
    "${HOME}/.openclaw/skills/logger/core"
  do
    [[ -d "$c" ]] && { printf '%s' "$c"; return 0; }
  done
  return 1
}

build_skill_roots() {
  SKILL_ROOTS_ARR=()
  if [[ -n "${SKILL_TEST_ROOTS:-}" ]]; then
    read -r -a SKILL_ROOTS_ARR <<< "${SKILL_TEST_ROOTS}"
    return 0
  fi
  if [[ -n "${CLAWVIS_ROOT:-}" ]]; then
    CR="${CLAWVIS_ROOT%/}"
    [[ -d "${CR}/skills" ]] && SKILL_ROOTS_ARR+=("${CR}/skills")
    IN="${INSTANCE_NAME:-dombot}"
    [[ -n "${IN}" && -d "${CR}/instances/${IN}/skills" ]] && SKILL_ROOTS_ARR+=("${CR}/instances/${IN}/skills")
    [[ ${#SKILL_ROOTS_ARR[@]} -gt 0 ]] && return 0
  fi
  if compgen -G "${HOME}/.openclaw/skills/*/" &>/dev/null; then
    SKILL_ROOTS_ARR+=("${HOME}/.openclaw/skills")
    return 0
  fi
  LC="${HOME}/Lab/clawvis"
  [[ -d "${LC}/skills" ]] && SKILL_ROOTS_ARR+=("${LC}/skills")
  [[ -d "${LC}/instances/dombot/skills" ]] && SKILL_ROOTS_ARR+=("${LC}/instances/dombot/skills")
}

LOGGER_CORE=""
build_skill_roots
if LOGGER_CORE="$(resolve_logger_core)"; then
  export LOGGER_CORE
  trap 'e=$?; [ $e -ne 0 ] && uv run --directory "$LOGGER_CORE" dombot-log "ERROR" "system:skill-tester" "system" "tests:fail" "Skill tests failed (exit $e)" 2>/dev/null || true; exit $e' EXIT
else
  trap 'exit $?' EXIT
fi

# ── list mode ────────────────────────────────────────────────────────────────

if [ "$SKILL_FILTER" = "--list" ]; then
  bold "Skills with Python tests:"
  for SK_ROOT in "${SKILL_ROOTS_ARR[@]}"; do
    [[ -d "$SK_ROOT" ]] || continue
    for skill_dir in "${SK_ROOT}"/*/; do
      [[ -d "$skill_dir" ]] || continue
      name=$(basename "$skill_dir")
      if [ -d "$skill_dir/core/tests" ] && ls "$skill_dir/core/tests/test_"*.py &>/dev/null 2>&1; then
        echo "  ✅ ${SK_ROOT%/}/$name"
      fi
    done
  done
  exit 0
fi

# ── test runner ──────────────────────────────────────────────────────────────

bold "═══════════════════════════════════════"
bold " OpenClaw Skill Test Runner"
bold " $(date '+%Y-%m-%d %H:%M')"
bold "═══════════════════════════════════════"
echo
if [[ ${#SKILL_ROOTS_ARR[@]} -eq 0 ]]; then
  yellow "No skill roots found. Set CLAWVIS_ROOT, SKILL_TEST_ROOTS, or symlink ~/.openclaw/skills"
  exit 1
fi
echo "Roots: ${SKILL_ROOTS_ARR[*]}"
echo

if [[ -n "${LOGGER_CORE}" ]]; then
  uv run --directory "$LOGGER_CORE" \
    dombot-log "INFO" "system:skill-tester" "system" "tests:start" "Skill tests started" 2>/dev/null || true
fi

for SK_ROOT in "${SKILL_ROOTS_ARR[@]}"; do
  [[ -d "$SK_ROOT" ]] || continue
  for skill_dir in "${SK_ROOT}"/*/; do
    [[ -d "$skill_dir" ]] || continue
  name=$(basename "$skill_dir")
  core_dir="$skill_dir/core"
  tests_dir="$core_dir/tests"

  if [ -n "$SKILL_FILTER" ] && [ "$SKILL_FILTER" != "--list" ] && [ "$name" != "$SKILL_FILTER" ]; then
    continue
  fi

  if [ ! -d "$tests_dir" ] || ! ls "$tests_dir/test_"*.py &>/dev/null 2>&1; then
    if [ -n "$SKILL_FILTER" ]; then
      yellow "⚠️  $name: no tests found in $tests_dir"
    fi
    ((SKIP++)) || true
    continue
  fi

  echo -n "Testing $name ... "

  if [ ! -f "$core_dir/pyproject.toml" ]; then
    yellow "SKIP (no pyproject.toml)"
    REPORT+=("⚠️  SKIP  $name (no pyproject.toml)")
    ((SKIP++)) || true
    continue
  fi

  if ! command -v uv &>/dev/null; then
    yellow "SKIP (uv not found)"
    REPORT+=("⚠️  SKIP  $name (uv not installed)")
    ((SKIP++)) || true
    continue
  fi

  if grep -q 'optional-dependencies' "$core_dir/pyproject.toml" 2>/dev/null && \
     grep -q '"dev"' "$core_dir/pyproject.toml" 2>/dev/null; then
    output=$(uv run --directory "$core_dir" --extra dev pytest tests/ -q --tb=short 2>&1)
  else
    output=$(uv run --directory "$core_dir" --with pytest pytest tests/ -q --tb=short 2>&1)
  fi
  exit_code=$?

  if [ $exit_code -eq 0 ]; then
    summary=$(echo "$output" | grep -E "passed|failed|error" | tail -1)
    green "✅ PASS — $summary"
    REPORT+=("✅ PASS  $name — $summary")
    ((PASS++)) || true
  else
    red "❌ FAIL"
    echo "$output" | tail -20 | sed 's/^/    /'
    REPORT+=("❌ FAIL  $name")
    ((FAIL++)) || true
  fi
  done
done

# ── Slack connectivity check (optional) ──────────────────────────────────

echo
bold "── Slack connectivity ──────────────────"
slack_found=0
for SK_ROOT in "${SKILL_ROOTS_ARR[@]}"; do
  if [[ -f "${SK_ROOT}/logger/scripts/slack-check.sh" ]]; then
    slack_found=1
    output=$(bash "${SK_ROOT}/logger/scripts/slack-check.sh" 2>&1)
    if echo "$output" | grep -q "OK\|configured"; then
      green "✅ Slack config OK"
      REPORT+=("✅ Slack config OK")
    else
      yellow "⚠️  Slack: $(echo "$output" | head -2)"
      REPORT+=("⚠️  Slack not fully configured")
    fi
    break
  fi
done
if [[ "$slack_found" -eq 0 ]]; then
  yellow "⚠️  logger skill not found under roots"
fi

# ── Summary ────────────────────────────────────────────────────────────────

echo
bold "═══════════════════════════════════════"
bold " Results: $PASS passed · $FAIL failed · $SKIP skipped"
bold "═══════════════════════════════════════"

for line in "${REPORT[@]}"; do
  echo "  $line"
done

echo

if [ "$FAIL" -gt 0 ]; then
  red "❌ $FAIL skill(s) failing — check logs above"
  [[ -n "${LOGGER_CORE}" ]] && uv run --directory "$LOGGER_CORE" \
    dombot-log "ERROR" "system:skill-tester" "system" "tests:summary" "Skill tests finished with failures (fail=$FAIL, pass=$PASS, skip=$SKIP)" 2>/dev/null || true
  exit 1
else
  green "✅ All tested skills passing"
  [[ -n "${LOGGER_CORE}" ]] && uv run --directory "$LOGGER_CORE" \
    dombot-log "INFO" "system:skill-tester" "system" "tests:summary" "Skill tests finished successfully (pass=$PASS, skip=$SKIP)" 2>/dev/null || true
  exit 0
fi
