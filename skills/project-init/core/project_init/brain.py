"""Brain note writer for project-init."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from project_init.config import MEMORY_ROOT


PARA_TEMPLATE = """\
---
title: {name}
created: {date}
tags:
  - project
status: active
---
# {name}

> {description}

---

## Contexte

_(à compléter par l'agent après analyse)_

## Objectif

_{description}_

## Ressources

- Hub : {hub_url}/project/{slug}
- Kanban : {hub_url}/kanban/

## Archive

_(décisions, versions précédentes)_
"""


def write_project_note(slug: str, name: str, description: str, hub_url: str) -> Path:
    projects_dir = MEMORY_ROOT / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    note_path = projects_dir / f"{slug}.md"
    content = PARA_TEMPLATE.format(
        name=name,
        date=date.today().isoformat(),
        description=description,
        slug=slug,
        hub_url=hub_url,
    )
    note_path.write_text(content, encoding="utf-8")
    return note_path
