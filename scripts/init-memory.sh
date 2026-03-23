#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTANCE_NAME="${INSTANCE_NAME:-example}"
MEMORY_ROOT="${MEMORY_ROOT:-instances/${INSTANCE_NAME}/memory}"
MEM_DIR="${ROOT_DIR}/${MEMORY_ROOT}"

mkdir -p \
  "${MEM_DIR}/projects" \
  "${MEM_DIR}/resources" \
  "${MEM_DIR}/daily" \
  "${MEM_DIR}/archive" \
  "${MEM_DIR}/todo" \
  "${MEM_DIR}/kanban"

mkdir -p "${MEM_DIR}/.obsidian" 2>/dev/null || true

if [ ! -f "${MEM_DIR}/.obsidian/app.json" ]; then
  echo "{}" > "${MEM_DIR}/.obsidian/app.json" 2>/dev/null || true
fi

if [ ! -f "${MEM_DIR}/.obsidian/workspace.json" ]; then
  echo "{}" > "${MEM_DIR}/.obsidian/workspace.json" 2>/dev/null || true
fi

# Do not write through container fallback: it can create root/nobody-owned files on host bind mounts.
if [ ! -f "${MEM_DIR}/.obsidian/app.json" ] || [ ! -f "${MEM_DIR}/.obsidian/workspace.json" ]; then
  echo "[warn] Cannot initialize ${MEM_DIR}/.obsidian files with current permissions."
  echo "[warn] Fix ownership once: sudo chown -R ${USER}:${USER} \"${MEM_DIR}\""
fi

if [ ! -f "${MEM_DIR}/projects/_template.md" ]; then
  cat > "${MEM_DIR}/projects/_template.md" <<'EOF'
# Project Template

## Objective

## Context

## Kanban
- Project slug:
- Stage:

## Links
- Repository:
- Brain page:

## Notes
EOF
fi

if [ ! -f "${MEM_DIR}/projects/clawvis.md" ]; then
  cat > "${MEM_DIR}/projects/clawvis.md" <<'EOF'
# Clawvis

## Objective
Build a project-centric AI hub where memory is the single source of truth.

## Kanban
- Project slug: clawvis
- Stage: MVP

## Notes
- Use this page as canonical project context.
EOF
fi

if [ ! -f "${MEM_DIR}/projects/example-project.md" ] && [ -w "${MEM_DIR}/projects" ]; then
  cat > "${MEM_DIR}/projects/example-project.md" <<'EOF'
# Example Project

## Objective
Run a quick Clawvis demo with one Kanban task and one log line.

## Kanban
- Project slug: example-project
- Stage: PoC

## Notes
- This page is created automatically for local demo onboarding.
EOF
fi

for folder in resources daily archive todo; do
  if [ ! -f "${MEM_DIR}/${folder}/README.md" ]; then
    cat > "${MEM_DIR}/${folder}/README.md" <<EOF
# ${folder^}

This folder is part of the Brain structure.
EOF
  fi
done

TASKS_JSON="${MEM_DIR}/kanban/tasks.json"
if [ ! -f "${TASKS_JSON}" ]; then
  cat > "${TASKS_JSON}" <<EOF
{"tasks":[],"generated":"$(date -u +"%Y-%m-%dT%H:%M:%SZ")","meta":{},"stats":{},"kanban":{}}
EOF
fi

# Seed minimal demo task/project only when tasks list is empty.
python3 - "${TASKS_JSON}" <<'PY' || true
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    raise SystemExit(0)

try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(0)
tasks = data.get("tasks", [])
if tasks:
    raise SystemExit(0)

now = datetime.now(timezone.utc).isoformat() + "Z"
task = {
    "id": "task-demo-001",
    "title": "Prepare mini demo board",
    "description": "Show one task lifecycle from To Start to Done.",
    "project": "example-project",
    "status": "To Start",
    "priority": "High",
    "effort_hours": 1,
    "timeline": "Today",
    "start_date": None,
    "end_date": None,
    "assignee": "DomBot",
    "dependencies": [],
    "tags": ["example", "onboarding"],
    "comments": [],
    "progress": 0.0,
    "source_file": "",
    "notes": "Auto-seeded example task.",
    "confidence": 0.92,
    "created_by": "system",
    "created": now,
    "updated": now,
    "archived_at": None,
}
data["tasks"] = [task]
data["generated"] = now
data["meta"] = data.get("meta") or {}
data["stats"] = {
    "total_tasks": 1,
    "by_status": {"Backlog": 0, "To Start": 1, "In Progress": 0, "Blocked": 0, "Review": 0, "Done": 0, "Archived": 0},
    "by_priority": {"Critical": 0, "High": 1, "Medium": 0, "Low": 0},
    "effort_remaining_hours": 1,
    "completion_rate": 0.0,
}
data["kanban"] = {
    "Backlog": [],
    "To Start": ["task-demo-001"],
    "In Progress": [],
    "Blocked": [],
    "Review": [],
    "Done": [],
    "Archived": [],
}
try:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
except Exception:
    raise SystemExit(0)
PY

# Seed one demo log line only when logger file is missing/empty.
LOG_FILE="${HOME}/.openclaw/logs/dombot.jsonl"
mkdir -p "$(dirname "${LOG_FILE}")" || true
if [ -d "$(dirname "${LOG_FILE}")" ] && [ ! -s "${LOG_FILE}" ]; then
  printf '%s\n' "{\"ts\":\"$(date -u +"%Y-%m-%d %H:%M:%S")\",\"level\":\"INFO\",\"process\":\"demo:bootstrap\",\"model\":\"system\",\"action\":\"example:init\",\"message\":\"Example seeded (project=example-project, task=task-demo-001)\"}" >> "${LOG_FILE}" || true
fi

if [ -f "${ROOT_DIR}/project-template.html" ]; then
  cp -f "${ROOT_DIR}/project-template.html" "${MEM_DIR}/projects/project-template.html"
fi
if [ -f "${ROOT_DIR}/clawvis.html" ]; then
  cp -f "${ROOT_DIR}/clawvis.html" "${MEM_DIR}/projects/clawvis.html"
fi

echo "Memory initialized at ${MEM_DIR}"
