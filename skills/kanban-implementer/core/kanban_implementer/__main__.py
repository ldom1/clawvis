"""
Entry point for kanban-implementer.

Usage:
  python -m kanban_implementer select [--project PROJECT]
      → Print the selected task context (for DomBot to implement)

  python -m kanban_implementer update TASK_ID STATUS
      → Update task status in tasks.json
      → STATUS: Backlog | To Start | In Progress | Blocked | Review | Done

  python -m kanban_implementer list
      → List all eligible tasks (DomBot-assigned, Backlog/To Start)
"""
from __future__ import annotations

import sys

from kanban_implementer.config import PRIORITY_PROJECT, MAX_EFFORT
from kanban_implementer.selector import load_tasks, select_task, format_task_context, ELIGIBLE_STATUSES
from kanban_implementer.status import update_task_status


def main_select() -> None:
    """CLI entrypoint: kanban-select [--project PROJECT]"""
    args = sys.argv[1:]
    project: str | None = None

    i = 0
    while i < len(args):
        if args[i] in ("--project", "-p") and i + 1 < len(args):
            project = args[i + 1]
            i += 2
        else:
            i += 1

    task = select_task(priority_project=project)
    if task is None:
        print("⚠️  Aucune tâche éligible trouvée.")
        print(f"   Critères : assignee=DomBot, status∈{ELIGIBLE_STATUSES}, effort≤{MAX_EFFORT}h")
        if PRIORITY_PROJECT:
            print(f"   Projet prioritaire : {PRIORITY_PROJECT}")
        sys.exit(0)

    print(format_task_context(task))
    print(f"\n---\nPROJET_PRIORITAIRE={project or PRIORITY_PROJECT or '(none)'}")
    print(f"TASK_ID={task.id}")
    print(f"IS_AMBIGUOUS={'true' if task.is_ambiguous else 'false'}")


def main_update() -> None:
    """CLI entrypoint: kanban-update TASK_ID STATUS"""
    args = sys.argv[1:]
    if len(args) < 2:
        print("Usage: kanban-update <task-id> <status>")
        print("Status: Backlog | To Start | In Progress | Blocked | Review | Done")
        sys.exit(1)
    task_id, new_status = args[0], args[1]
    ok = update_task_status(task_id, new_status)
    sys.exit(0 if ok else 1)


def main_list() -> None:
    """List eligible tasks."""
    tasks = load_tasks()
    eligible = [t for t in tasks if t.is_eligible]
    if not eligible:
        print("Aucune tâche éligible.")
        return
    print(f"{'ID':<18} {'PRIO':<8} {'EFFORT':<7} {'PROJET':<25} TITRE")
    print("-" * 90)
    for t in sorted(eligible, key=lambda x: (x.priority_rank, x.effort_hours)):
        print(f"{t.id:<18} {t.priority:<8} {t.effort_hours:<7.1f} {t.project[:24]:<25} {t.title[:40]}")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        main_select()
        return
    cmd = args[0]
    sys.argv = [sys.argv[0]] + args[1:]
    if cmd == "select":
        main_select()
    elif cmd == "update":
        main_update()
    elif cmd == "list":
        main_list()
    else:
        print(f"Unknown command: {cmd}. Use: select | update | list")
        sys.exit(1)


if __name__ == "__main__":
    main()
