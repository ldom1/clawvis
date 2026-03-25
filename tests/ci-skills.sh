#!/usr/bin/env bash
set -euo pipefail

# Skills quality gate:
# Discover each skill core project (skills/*/core/pyproject.toml)
# and run lint/tests consistently.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
mkdir -p "${ROOT_DIR}/.tmp"

for pyproject in skills/*/core/pyproject.toml; do
  [ -f "${pyproject}" ] || continue
  core_dir="$(dirname "${pyproject}")"
  echo "==> skills core: ${core_dir}"
  export PYLINTHOME="${ROOT_DIR}/.tmp/pylint-$(echo "${core_dir}" | tr '/.' '__')"
  mkdir -p "${PYLINTHOME}"

  # Ruff fatal/lint errors only (keeps CI stable across legacy style differences).
  uv run --directory "${core_dir}" --with ruff ruff check . --select F

  # Pylint on package dir(s) if present.
  for pkg in "${core_dir}"/*; do
    if [ -d "${pkg}" ] && [ -f "${pkg}/__init__.py" ]; then
      if [ -d "${core_dir}/tests" ]; then
        uv run --directory "${core_dir}" --with pylint pylint --disable=all --enable=E,F --disable=E1101 --ignored-modules=pytest "$(basename "${pkg}")" tests
      else
        uv run --directory "${core_dir}" --with pylint pylint --disable=all --enable=E,F --disable=E1101 --ignored-modules=pytest "$(basename "${pkg}")"
      fi
    fi
  done

  # Run tests only when tests directory exists.
  if [ -d "${core_dir}/tests" ]; then
    uv run --directory "${core_dir}" --with pytest pytest -q tests
  fi
done

echo "==> skill tester"
skill_tester="${ROOT_DIR}/skills/skill-tester/scripts/test-all.sh"
if [ -f "${skill_tester}" ]; then
  chmod +x "${skill_tester}" || true
  tester_home="${ROOT_DIR}/.tmp/skill-tester-home"
  mkdir -p "${tester_home}/.openclaw"
  ln -sfn "${ROOT_DIR}/skills" "${tester_home}/.openclaw/skills"
  HOME="${tester_home}" bash "${skill_tester}"
else
  echo "[warn] skill-tester not found at ${skill_tester}"
fi
