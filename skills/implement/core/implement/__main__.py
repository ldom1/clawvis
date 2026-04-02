"""
implement — load task context and optionally update status.

Usage:
  python -m implement --task-id <id>
      → Print task context (for LLM to implement)

  python -m implement --task-id <id> --set-status "In Progress"
      → Update task status

  python -m implement --task-id <id> --mark-done
      → Mark task as Done
"""
from __future__ import annotations

import argparse
import sys

from implement.api import get_task, update_status


def main() -> None:
    parser = argparse.ArgumentParser(prog="implement", description="Load task context for implementation")
    parser.add_argument("--task-id", required=True, help="Task ID from kanban")
    parser.add_argument("--set-status", metavar="STATUS", help="Update task status")
    parser.add_argument("--mark-done", action="store_true", help="Mark task as Done")
    args = parser.parse_args()

    # Status update only
    if args.set_status:
        update_status(args.task_id, args.set_status)
        print(f"[implement] {args.task_id} → {args.set_status}", file=sys.stderr)
        return

    if args.mark_done:
        update_status(args.task_id, "Done")
        print(f"[implement] {args.task_id} → Done", file=sys.stderr)
        return

    # Load and print task context
    try:
        ctx = get_task(args.task_id)
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


if __name__ == "__main__":
    main()
