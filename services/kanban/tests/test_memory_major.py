"""Tests for project memory major sections (markdown round-trip)."""

from __future__ import annotations

import json

from kanban_api.core import (
    _parse_markdown_major_info,
    _parse_memory_md_structure,
    update_project_memory_major,
)


def test_parse_major_reads_description_and_aliases():
    md = """# My app

## Description
Hello

## Objectifs macro
Reach users

## Stratégie
Ship fast

## Objective
One goal

## Hub
- x: 1
"""
    m = _parse_markdown_major_info(md)
    assert m["title"] == "My app"
    assert m["description"] == "Hello"
    assert m["macro_objectives"] == "Reach users"
    assert m["strategy"] == "Ship fast"
    assert m["objective"] == "One goal"


def test_update_project_memory_major_roundtrip(monkeypatch, tmp_path):
    from kanban_api import core

    projects_root = tmp_path / "projects"
    projects_root.mkdir()
    slug = "demo-proj"
    repo = projects_root / slug
    repo.mkdir()
    mem_root = tmp_path / "memory"
    mem_file = mem_root / "projects" / f"{slug}.md"
    (repo / ".clawvis-project.json").write_text(
        json.dumps(
            {
                "name": "Demo",
                "slug": slug,
                "stage": "PoC",
                "tags": [],
                "template": "python",
                "description": "x",
                "repo_path": str(repo),
                "memory_path": str(mem_file),
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(core, "_memory_root_path", mem_root)
    monkeypatch.setattr(
        core,
        "get_hub_settings",
        lambda: {
            "projects_root": str(projects_root),
            "instances_external_root": "",
            "linked_instances": [],
        },
    )

    mem_file.parent.mkdir(parents=True, exist_ok=True)
    mem_file.write_text(
        "# Demo\n\n## Description\nOld\n\n## Hub\n- keep: me\n",
        encoding="utf-8",
    )

    update_project_memory_major(
        slug,
        {
            "title": "Demo 2",
            "description": "New body",
            "macro_objectives": "Macro",
            "strategy": "Strat",
        },
    )
    title, preamble, blocks = _parse_memory_md_structure(mem_file.read_text())
    assert title == "Demo 2"
    canon = {core._section_key_from_heading(h): b for h, b in blocks}
    assert canon["description"] == "New body"
    assert canon["macro_objectives"] == "Macro"
    assert canon["strategy"] == "Strat"
    assert canon["hub"] == "- keep: me"
