"""
implement — load task context and optionally update status.

Usage:
  python -m implement                          → auto-select task + print context
  python -m implement --project PROJECT        → auto-select from specific project
  python -m implement --list [--project P]     → list eligible tasks
  python -m implement --task-id <id>           → load specific task via API
  python -m implement --task-id <id> --set-status "In Progress"
  python -m implement --task-id <id> --mark-done
"""
from __future__ import annotations

import argparse
import sys

from implement.api import get_task, update_status
from implement.config import MAX_EFFORT, PRIORITY_PROJECT
from implement.selector import ELIGIBLE_STATUSES, format_task_context, load_tasks, select_task


def _print_task_from_api(task_id: str) -> None:
    try:
        ctx = get_task(task_id)
    except RuntimeError as e:
        print(f"[implement] Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"TASK_ID={ctx.id}")
    print(f"TASK_TITLE={ctx.title}")
    print(f"TASK_PROJECT={ctx.project}")
    print(f"TASK_STATUS={ctx.status}")
    print(f"TASK_PRIORITY={ctx.priority}")
    print(f"TASK_EFFORT={ctx.effort_hours}")
    print(f"BRAIN_NOTE={ctx.brain_note}")
    print()
    print("--- TASK DESCRIPTION ---")
    print(ctx.description or "(no description)")
    if ctx.brain_content:
        print()
        print("--- BRAIN NOTE ---")
        print(ctx.brain_content)


def main() -> None:
    parser = argparse.ArgumentParser(prog="implement", description="Load task context for implementation")
    parser.add_argument("--task-id", help="Task ID from kanban (skip auto-select)")
    parser.add_argument("--project", "-p", help="Priority project for auto-select")
    parser.add_argument("--list", action="store_true", help="List eligible tasks and exit")
    parser.add_argument("--set-status", metavar="STATUS", help="Update task status (requires --task-id)")
    parser.add_argument("--mark-done", action="store_true", help="Mark task as Done (requires --task-id)")
    args = parser.parse_args()

    # Status mutations require an explicit task-id
    if args.set_status or args.mark_done:
        if not args.task_id:
            print("[implement] --set-status / --mark-done require --task-id", file=sys.stderr)
            sys.exit(1)
        status = "Done" if args.mark_done else args.set_status
        update_status(args.task_id, status)
        print(f"[implement] {args.task_id} → {status}", file=sys.stderr)
        return

    # List mode
    if args.list:
        tasks = load_tasks()
        eligible = [t for t in tasks if t.is_eligible]
        if not eligible:
            print("Aucune tâche éligible.")
            return
        proj = args.project
        if proj:
            eligible = [t for t in eligible if t.project == proj] or eligible
        print(f"{'ID':<18} {'PRIO':<8} {'EFFORT':<7} {'PROJET':<25} TITRE")
        print("-" * 90)
        for t in sorted(eligible, key=lambda x: (x.priority_rank, x.effort_hours)):
            print(f"{t.id:<18} {t.priority:<8} {t.effort_hours:<7.1f} {t.project[:24]:<25} {t.title[:40]}")
        return

    # Explicit task-id: load via API
    if args.task_id:
        _print_task_from_api(args.task_id)
        return

    # Auto-select from tasks.json
    task = select_task(priority_project=args.project)
    if task is None:
        print("⚠️  Aucune tâche éligible trouvée.")
        print(f"   Critères : assignee=DomBot, status∈{ELIGIBLE_STATUSES}, effort≤{MAX_EFFORT}h")
        if PRIORITY_PROJECT:
            print(f"   Projet prioritaire : {PRIORITY_PROJECT}")
        sys.exit(0)

    print(format_task_context(task))
    print(f"\n---\nPROJET_PRIORITAIRE={args.project or PRIORITY_PROJECT or '(none)'}")
    print(f"TASK_ID={task.id}")
    print(f"IS_AMBIGUOUS={'true' if task.is_ambiguous else 'false'}")


if __name__ == "__main__":
    main()
