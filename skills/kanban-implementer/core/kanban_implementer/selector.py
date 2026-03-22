"""Task selection logic from Kanban JSON."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from kanban_implementer.config import TASKS_JSON, PRIORITY_PROJECT, MAX_EFFORT, WORKSPACE, MIN_CONFIDENCE


PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}
ELIGIBLE_STATUSES = {"To Start", "Backlog"}
AGENT_ASSIGNEES = {"DomBot"}
_VAGUE_RE = re.compile(
    r"\b(?:vague|various|variously|misc|miscellaneous|cleanup|clarify|refonte|audit|tbd|wip|"
    r"divers|quelques|améliorer|clarifier|etc\.?)\b",
    re.I,
)


@dataclass
class Task:
    id: str
    title: str
    project: str
    status: str
    priority: str
    effort_hours: float
    assignee: str
    source_file: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    confidence: float | None = None

    @property
    def priority_rank(self) -> int:
        return PRIORITY_ORDER.get(self.priority, 99)

    @property
    def confidence_effective(self) -> float:
        """1.0 for humans, task.confidence ?? 0.5 for agents."""
        if self.assignee not in AGENT_ASSIGNEES:
            return 1.0
        return self.confidence if self.confidence is not None else 0.5

    @property
    def is_eligible(self) -> bool:
        return (
            self.status in ELIGIBLE_STATUSES
            and self.assignee == "DomBot"
            and self.effort_hours <= MAX_EFFORT
            and self.confidence_effective >= MIN_CONFIDENCE
        )

    @property
    def is_ambiguous(self) -> bool:
        blob = f"{self.title} {self.description}".lower()
        return bool(_VAGUE_RE.search(blob))

    @property
    def source_path(self) -> Path | None:
        if not self.source_file:
            return None
        p = WORKSPACE / self.source_file
        return p if p.exists() else None


def load_tasks() -> list[Task]:
    if not TASKS_JSON.exists():
        return []
    with open(TASKS_JSON, encoding="utf-8") as f:
        data = json.load(f)
    tasks = []
    for t in data.get("tasks", []):
        tasks.append(Task(
            id=t.get("id", ""),
            title=t.get("title", ""),
            project=t.get("project", ""),
            status=t.get("status", ""),
            priority=t.get("priority", "Medium"),
            effort_hours=float(t.get("effort_hours") or 0.0),
            assignee=t.get("assignee", ""),
            source_file=t.get("source_file", ""),
            description=t.get("description", ""),
            tags=t.get("tags", []),
            notes=t.get("notes", ""),
            confidence=t.get("confidence"),
        ))
    return tasks


def select_task(priority_project: str | None = None) -> Task | None:
    """
    Select the best task to implement.

    Selection rules (in order):
    1. Eligible: status in {To Start, Backlog}, assignee = DomBot, effort <= MAX_EFFORT
    2. If priority_project set → tasks from that project first
    3. Sort by priority rank (High=0 < Medium=1 < Low=2), then effort_hours asc
    """
    tasks = load_tasks()
    eligible = [t for t in tasks if t.is_eligible]

    if not eligible:
        return None

    proj = priority_project or PRIORITY_PROJECT

    def sort_key(t: Task) -> tuple:
        in_priority_proj = 0 if (proj and t.project == proj) else 1
        return (in_priority_proj, t.priority_rank, t.effort_hours)

    eligible.sort(key=sort_key)
    return eligible[0]


def format_task_context(task: Task) -> str:
    """Return a markdown summary of the task for DomBot."""
    lines = [
        f"## Tâche sélectionnée : {task.id}",
        f"- **Titre** : {task.title}",
        f"- **Projet** : {task.project}",
        f"- **Priorité** : {task.priority}",
        f"- **Effort estimé** : {task.effort_hours}h",
        f"- **Statut actuel** : {task.status}",
    ]
    if task.description:
        lines.append(f"- **Description** : {task.description}")
    if task.notes:
        lines.append(f"- **Notes** : {task.notes}")
    if task.tags:
        lines.append(f"- **Tags** : {', '.join(task.tags)}")
    if task.source_file:
        lines.append(f"- **Fichier projet** : {task.source_file}")

    # Load source context
    src = task.source_path
    if src:
        content = src.read_text(encoding="utf-8")
        # Truncate to ~2000 chars for context
        if len(content) > 2000:
            content = content[:2000] + "\n[... tronqué ...]"
        lines += ["", "### Contexte projet (source_file)", "```markdown", content, "```"]

    return "\n".join(lines)
