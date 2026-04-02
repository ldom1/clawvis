"""
project-init — bootstrap a Clawvis project from slug/name/description.

Usage:
  python -m project_init --slug <slug> --name <name> --description <desc>
  python -m project_init --slug <slug> --name <name> --description <desc> --dry-run
"""
from __future__ import annotations

import argparse
import sys

from project_init.config import HUB_URL
from project_init.api import ProjectPayload, create_project
from project_init.brain import write_project_note


def main() -> None:
    parser = argparse.ArgumentParser(prog="project_init", description="Bootstrap a Clawvis project")
    parser.add_argument("--slug", required=True, help="kebab-case project identifier")
    parser.add_argument("--name", required=True, help="Display name")
    parser.add_argument("--description", required=True, help="One-sentence problem statement")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be created without calling APIs")
    args = parser.parse_args()

    slug: str = args.slug.lower().replace(" ", "-")

    if args.dry_run:
        print(f"[dry-run] Would create project: {slug!r} ({args.name})")
        print(f"[dry-run] Brain note: $MEMORY_ROOT/projects/{slug}.md")
        print(f"[dry-run] Hub URL: {HUB_URL}/project/{slug}")
        return

    # 1. Create project in Kanban API
    p = ProjectPayload(slug=slug, name=args.name, description=args.description)
    try:
        result = create_project(p)
        print(f"[project-init] Project created: {result.get('slug', slug)}", file=sys.stderr)
    except RuntimeError as e:
        print(f"[project-init] Warning: Kanban API error — {e}", file=sys.stderr)

    # 2. Write Brain note
    note_path = write_project_note(slug=slug, name=args.name, description=args.description, hub_url=HUB_URL)
    print(f"[project-init] Brain note written: {note_path}", file=sys.stderr)

    # 3. Print env-style output for the LLM orchestrator to read
    print(f"PROJECT_SLUG={slug}")
    print(f"PROJECT_NAME={args.name}")
    print(f"PROJECT_URL={HUB_URL}/project/{slug}")
    print(f"BRAIN_NOTE={note_path}")


if __name__ == "__main__":
    main()
