#!/usr/bin/env bash
# Backup Clawvis project config (.claude, env templates) → GIT_SYNC_REPO under $HOME.
# Lab multi-repo sync stays optional (~/Lab/git-sync.sh).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$(cd "$SCRIPT_DIR/../.." && pwd)/_clawvis_env.sh"

trap 'e=$?; [ $e -ne 0 ] && dombot_log_uv dombot-log "ERROR" "cron:git-sync" "system" "sync:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

if ! clawvis_env_load; then
  echo "git-sync: set CLAWVIS_ROOT or checkout clawvis under ~/lab/clawvis" >&2
  exit 1
fi

REPO_NAME="${GIT_SYNC_REPO:-clawvis-config-mirror}"
REPO_DIR="$HOME/$REPO_NAME"
LAB="$HOME/Lab"

log() { echo "[git-sync] $*"; }

RSYNC_OPTS=(--delete-excluded --exclude='.git' --exclude='.pi/' --exclude='.venv/' --exclude='venv/' --exclude='node_modules/' --exclude='__pycache__/' --exclude='*.pyc' --exclude='.env' --exclude='.env.*' --exclude='*.key' --exclude='auth*.json' --exclude='**/secrets/' --exclude='**/credentials/')

ensure_repo() {
  mkdir -p "$REPO_DIR"
  if [[ ! -f "$REPO_DIR/.gitignore" ]]; then
    cat > "$REPO_DIR/.gitignore" << 'GITIGNORE'
*.log
.DS_Store
GITIGNORE
    log "Created .gitignore"
  fi
}

sync_clawvis_mirror() {
  log "=== Clawvis tree → $REPO_NAME (subset, no secrets) ==="
  ensure_repo
  mkdir -p "$REPO_DIR/clawvis-claude"
  if [[ -d "$CLAWVIS_ROOT/.claude" ]]; then
    if command -v rsync >/dev/null 2>&1; then
      rsync -a "${RSYNC_OPTS[@]}" "$CLAWVIS_ROOT/.claude/" "$REPO_DIR/clawvis-claude/"
    else
      rm -rf "${REPO_DIR:?}/clawvis-claude"
      cp -r "$CLAWVIS_ROOT/.claude" "$REPO_DIR/clawvis-claude"
    fi
  else
    log "No .claude at CLAWVIS_ROOT — skip"
  fi
  for f in .env.example .clawvis-project.json; do
    if [[ -f "$CLAWVIS_ROOT/$f" ]]; then
      cp "$CLAWVIS_ROOT/$f" "$REPO_DIR/$f"
    fi
  done
  if [[ -f "$SCRIPT_DIR/../assets/README-clawvis-backup.md" ]]; then
    cp "$SCRIPT_DIR/../assets/README-clawvis-backup.md" "$REPO_DIR/README.md"
  fi

  cd "$REPO_DIR"
  [[ -d .git ]] || { git init -b main; log "Initialized $REPO_DIR"; }
  git remote -v | grep -q . || true

  git add -A
  if git diff --staged --quiet 2>/dev/null; then
    log "No changes"
  else
    git commit -m "sync $(date '+%Y-%m-%d %H:%M')"
    log "Committed"
  fi
  if git remote -v | grep -q .; then
    if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
      git push -u origin HEAD 2>/dev/null || git push || log "push failed"
    else
      git push || log "push failed"
    fi
    log "Pushed"
  fi
}

sync_lab() {
  log "=== Lab repos sync ==="
  if [[ -x "$LAB/git-sync.sh" ]]; then
    bash "$LAB/git-sync.sh"
  else
    log "Lab git-sync.sh not found, skipping"
  fi
}

sync_clawvis_mirror
sync_lab || log "Lab git-sync finished with errors (non-fatal)"
log "All done."
dombot_log_uv dombot-log "INFO" "cron:git-sync" "system" "sync:complete" "Git sync finished" 2>/dev/null || true
