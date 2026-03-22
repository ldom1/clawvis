#!/usr/bin/env bash
# Sync OpenClaw config (openclaw.json, cron/jobs.json, agents/) → openclaw-dombot repo.
# Skills → clawvis/hub-ldom (not backed up here).
# Memory → hub-ldom/instances/ldom/memory (not backed up here).
set -euo pipefail
trap 'e=$?; [ $e -ne 0 ] && uv run --directory ~/.openclaw/skills/logger/core dombot-log "ERROR" "cron:git-sync" "system" "sync:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

OPENCLAW="$HOME/.openclaw"
WORKSPACE="$OPENCLAW/workspace"
SKILLS="$OPENCLAW/skills"
REPO_NAME="${GIT_SYNC_REPO:-openclaw-dombot}"
REPO_DIR="$HOME/$REPO_NAME"
LAB="$HOME/Lab"

log() { echo "[git-sync] $*"; }

# ═══════════════════════════════════════════════════════════════
# PART 1: OpenClaw workspace + skills → openclaw-dombot repo
# ═══════════════════════════════════════════════════════════════

RSYNC_OPTS=(--delete-excluded --exclude='.git' --exclude='.openclaw/' --exclude='.pi/' --exclude='.venv/' --exclude='venv/' --exclude='node_modules/' --exclude='__pycache__/' --exclude='*.pyc' --exclude='.env' --exclude='.env.*' --exclude='*.key' --exclude='auth*.json' --exclude='**/secrets/' --exclude='**/credentials/')

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

sync_into_repo() {
  # Only sync OpenClaw runtime config — NOT skills (→ clawvis/hub-ldom) NOR memory (→ hub-ldom)
  log "Copying OpenClaw config into $REPO_NAME..."

  if [[ -f "$OPENCLAW/openclaw.json" ]]; then
    cp "$OPENCLAW/openclaw.json" "$REPO_DIR/openclaw.json"
  fi

  if [[ -f "$OPENCLAW/cron/jobs.json" ]]; then
    mkdir -p "$REPO_DIR/cron"
    cp "$OPENCLAW/cron/jobs.json" "$REPO_DIR/cron/jobs.json"
  fi

  if [[ -d "$OPENCLAW/agents" ]]; then
    mkdir -p "$REPO_DIR/agents"
    if command -v rsync >/dev/null 2>&1; then
      rsync -a --delete "${RSYNC_OPTS[@]}" "$OPENCLAW/agents/" "$REPO_DIR/agents/"
    else
      rm -rf "$REPO_DIR/agents"
      cp -r "$OPENCLAW/agents" "$REPO_DIR/agents"
    fi
  fi
}

do_push() {
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    git push -u origin HEAD 2>/dev/null || git push || log "push failed"
  else
    git push || log "push failed"
  fi
}

ensure_gh_remote() {
  cd "$REPO_DIR"
  git remote -v | grep -q . && return 0
  command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1 || { log "No remote, no gh"; return 1; }
  gh repo create "$REPO_NAME" --private --source=. --remote=origin 2>/dev/null || { log "Repo may exist, link manually"; return 1; }
  log "Created GitHub repo $REPO_NAME (private)"
}

sync_openclaw() {
  log "=== OpenClaw config sync (skills/memory excluded — in clawvis/hub-ldom) ==="
  ensure_repo
  sync_into_repo

  cd "$REPO_DIR"
  [[ -d .git ]] || { git init -b main; log "Initialized $REPO_DIR"; }
  git remote -v | grep -q . || ensure_gh_remote || true

  git add -A
  if git diff --staged --quiet 2>/dev/null; then
    log "No changes"
  else
    git commit -m "sync $(date '+%Y-%m-%d %H:%M')"
    log "Committed"
  fi
  git remote -v | grep -q . && { do_push; log "Pushed"; }
}

# ═══════════════════════════════════════════════════════════════
# PART 2: Lab repos (hub, projects, pocs, quartz)
# ═══════════════════════════════════════════════════════════════

sync_lab() {
  log "=== Lab repos sync ==="
  if [[ -x "$LAB/git-sync.sh" ]]; then
    bash "$LAB/git-sync.sh"
  else
    log "Lab git-sync.sh not found, skipping"
  fi
}

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

sync_openclaw
sync_lab
log "All done."
uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:git-sync" "system" "sync:complete" "Git sync finished" 2>/dev/null || true
