"""
CLI entry point documentation for kanban-implementer.

The actual CLI is implemented in __main__.py and invoked via:
  python -m kanban_implementer <command>

Commands:
  select [--project PROJECT]  — Select next eligible task for DomBot
  update TASK_ID STATUS       — Update task status
  list                        — List all eligible tasks

STATUS values: Backlog | To Start | In Progress | Blocked | Review | Done

Quick start (via uv):
  uv run --directory /home/lgiron/Lab/clawvis/skills/kanban-implementer/core python -m kanban_implementer select
  uv run --directory /home/lgiron/Lab/clawvis/skills/kanban-implementer/core python -m kanban_implementer update TASK_ID 'In Progress'

See __main__.py for implementation. See SKILL.md for full workflow.
"""
from kanban_implementer.__main__ import main

__all__ = ["main"]
