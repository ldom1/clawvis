#!/usr/bin/env bash
# Resolve Clawvis repo root + logger paths (shared by skills/scripts).
# shellcheck shell=bash

clawvis_resolve_root() {
  if [ -n "${CLAWVIS_ROOT:-}" ] && [ -d "${CLAWVIS_ROOT}/hub-core" ]; then
    printf '%s\n' "${CLAWVIS_ROOT}"
    return 0
  fi
  for _p in "${HOME}/lab/clawvis" "${HOME}/Lab/clawvis"; do
    if [ -d "${_p}/hub-core" ]; then
      printf '%s\n' "${_p}"
      return 0
    fi
  done
  return 1
}

# Sets CLAWVIS_ROOT, LOGGER_CORE, LOG_DIR; returns 0 if repo found.
clawvis_env_load() {
  local root _primary_log
  root="$(clawvis_resolve_root)" || return 1
  CLAWVIS_ROOT="$root"
  export CLAWVIS_ROOT
  LOGGER_CORE="${CLAWVIS_ROOT}/skills/logger/core"
  _primary_log="${CLAWVIS_ROOT}/logs"
  if mkdir -p "$_primary_log" 2>/dev/null && [ -w "$_primary_log" ]; then
    LOG_DIR="$_primary_log"
  else
    LOG_DIR="${TMPDIR:-/tmp}/clawvis-logs"
    mkdir -p "$LOG_DIR" 2>/dev/null || true
  fi
  export LOGGER_CORE LOG_DIR
  return 0
}

# Wraps `uv run --directory <dir>` with a writable venv in /tmp.
# Derives venv slug from parent-dir + dir name (e.g. logger-core, morning-briefing-core).
clawvis_uv_run_dir() {
  local dir="$1"; shift
  local slug
  slug="$(basename "$(dirname "$dir")")-$(basename "$dir")"
  UV_PROJECT_ENVIRONMENT="${TMPDIR:-/tmp}/clawvis-venvs/${slug}" \
    VIRTUAL_ENV="" \
    uv run --directory "$dir" "$@"
}

dombot_log_uv() {
  [ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] || return 0
  clawvis_uv_run_dir "$LOGGER_CORE" "$@"
}
