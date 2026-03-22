#!/usr/bin/env bash
# skill-tester — run all Python unit tests for OpenClaw skills
# Usage:
#   test-all.sh              # test all skills with core/tests/
#   test-all.sh logger       # test a single skill
#   test-all.sh --list       # list testable skills
set -uo pipefail

trap 'e=$?; [ $e -ne 0 ] && uv run --directory ~/.openclaw/skills/logger/core dombot-log "ERROR" "system:skill-tester" "system" "tests:fail" "Skill tests failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

SKILLS_DIR="$HOME/.openclaw/skills"
SKILL_FILTER="${1:-}"
PASS=0
FAIL=0
SKIP=0
REPORT=()

# ── helpers ──────────────────────────────────────────────────────────────────

green() { printf '\033[32m%s\033[0m\n' "$*"; }
red()   { printf '\033[31m%s\033[0m\n' "$*"; }
yellow(){ printf '\033[33m%s\033[0m\n' "$*"; }
bold()  { printf '\033[1m%s\033[0m\n' "$*"; }

# ── list mode ────────────────────────────────────────────────────────────────

if [ "$SKILL_FILTER" = "--list" ]; then
  bold "Skills with Python tests:"
  for skill_dir in "$SKILLS_DIR"/*/; do
    name=$(basename "$skill_dir")
    if [ -d "$skill_dir/core/tests" ] && ls "$skill_dir/core/tests/test_"*.py &>/dev/null 2>&1; then
      echo "  ✅ $name"
    fi
  done
  exit 0
fi

# ── test runner ──────────────────────────────────────────────────────────────

bold "═══════════════════════════════════════"
bold " OpenClaw Skill Test Runner"
bold " $(date '+%Y-%m-%d %H:%M')"
bold "═══════════════════════════════════════"
echo

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "system:skill-tester" "system" "tests:start" "Skill tests started" 2>/dev/null || true

for skill_dir in "$SKILLS_DIR"/*/; do
  name=$(basename "$skill_dir")
  core_dir="$skill_dir/core"
  tests_dir="$core_dir/tests"

  # Filter if specific skill requested
  if [ -n "$SKILL_FILTER" ] && [ "$SKILL_FILTER" != "--list" ] && [ "$name" != "$SKILL_FILTER" ]; then
    continue
  fi

  # Skip if no Python tests
  if [ ! -d "$tests_dir" ] || ! ls "$tests_dir/test_"*.py &>/dev/null 2>&1; then
    if [ -n "$SKILL_FILTER" ]; then
      yellow "⚠️  $name: no tests found in $tests_dir"
    fi
    ((SKIP++)) || true
    continue
  fi

  echo -n "Testing $name ... "

  # Check uv + pyproject.toml
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

  # Run pytest via uv (try --extra dev first, fallback without)
  if grep -q 'optional-dependencies' "$core_dir/pyproject.toml" 2>/dev/null && \
     grep -q '"dev"' "$core_dir/pyproject.toml" 2>/dev/null; then
    output=$(uv run --directory "$core_dir" --extra dev pytest tests/ -q --tb=short 2>&1)
  else
    output=$(uv run --directory "$core_dir" pytest tests/ -q --tb=short 2>&1)
  fi
  exit_code=$?

  if [ $exit_code -eq 0 ]; then
    # Extract pass count from pytest output
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

# ── Slack connectivity check (optional) ──────────────────────────────────────

echo
bold "── Slack connectivity ──────────────────"
if [ -f "$SKILLS_DIR/logger/scripts/slack-check.sh" ]; then
  output=$(bash "$SKILLS_DIR/logger/scripts/slack-check.sh" 2>&1)
  if echo "$output" | grep -q "OK\|configured"; then
    green "✅ Slack config OK"
    REPORT+=("✅ Slack config OK")
  else
    yellow "⚠️  Slack: $(echo "$output" | head -2)"
    REPORT+=("⚠️  Slack not fully configured")
  fi
else
  yellow "⚠️  logger skill not found"
fi

# ── Summary ──────────────────────────────────────────────────────────────────

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
  uv run --directory ~/.openclaw/skills/logger/core \
    dombot-log "ERROR" "system:skill-tester" "system" "tests:summary" "Skill tests finished with failures (fail=$FAIL, pass=$PASS, skip=$SKIP)" 2>/dev/null || true
  exit 1
else
  green "✅ All tested skills passing"
  uv run --directory ~/.openclaw/skills/logger/core \
    dombot-log "INFO" "system:skill-tester" "system" "tests:summary" "Skill tests finished successfully (pass=$PASS, skip=$SKIP)" 2>/dev/null || true
  exit 0
fi
