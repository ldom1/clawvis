from __future__ import annotations

from collections.abc import Callable


def _enrich_tasks(args: str) -> str:
    action = args.strip() or "list all tasks"
    return (
        "You are managing the Clawvis task board via the Kanban API. "
        f"The user wants to: {action}. "
        "Execute the appropriate Kanban task action now and confirm with the task ID and title."
    )


def _enrich_projects(args: str) -> str:
    action = args.strip() or "list all projects"
    return (
        "You are managing Clawvis projects via the Kanban API. "
        f"The user wants to: {action}. "
        "Execute the appropriate project action now and confirm with the project slug and name."
    )


def _enrich_status(_args: str) -> str:
    return (
        "The user wants to know the current status of the Clawvis agent. "
        "Describe your current operational state: which AI provider is active, "
        "which model is in use, and whether you are ready to process requests."
    )


_DISPATCH: dict[str, Callable[[str], str]] = {
    "tasks": _enrich_tasks,
    "projects": _enrich_projects,
    "status": _enrich_status,
}


def enrich(command: str, args: str) -> str | None:
    fn = _DISPATCH.get(command)
    if fn is None:
        return None
    return fn(args)
