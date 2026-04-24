"""list_projects() discovers brain Markdown via BRAIN_PATH when memory symlink is unreadable."""

from __future__ import annotations

from pathlib import Path

from kanban_api import core


def test_list_projects_scans_brain_path_when_active_projects_missing(
    monkeypatch, tmp_path: Path
) -> None:
    empty_mem = tmp_path / "instance_mem"
    (empty_mem / "kanban").mkdir(parents=True)
    (empty_mem / "kanban" / "tasks.json").write_text(
        '{"tasks":[],"meta":{}}', encoding="utf-8"
    )
    ext = tmp_path / "external_brain"
    (ext / "projects").mkdir(parents=True)
    (ext / "projects" / "via-brain-path.md").write_text(
        "# Via Path\n", encoding="utf-8"
    )
    proj_root = tmp_path / "proj_root"
    proj_root.mkdir()

    monkeypatch.setattr(core, "_memory_root_path", empty_mem)
    monkeypatch.setenv("BRAIN_PATH", str(ext))
    monkeypatch.setattr(
        core,
        "get_hub_settings",
        lambda: {
            "projects_root": str(proj_root),
            "instances_external_root": "",
            "linked_instances": [],
        },
    )

    out = core.list_projects()
    slugs = {p["slug"] for p in out["projects"]}
    assert "via-brain-path" in slugs


def test_brain_path_not_duplicated_when_same_as_active(
    monkeypatch, tmp_path: Path
) -> None:
    mem = tmp_path / "mem"
    (mem / "projects").mkdir(parents=True)
    (mem / "projects" / "once.md").write_text("# One\n", encoding="utf-8")
    (mem / "kanban").mkdir(parents=True)
    (mem / "kanban" / "tasks.json").write_text(
        '{"tasks":[],"meta":{}}', encoding="utf-8"
    )
    proj_root = tmp_path / "proj_root"
    proj_root.mkdir()
    resolved = mem.resolve()
    monkeypatch.setattr(core, "_memory_root_path", mem)
    monkeypatch.setenv("BRAIN_PATH", str(resolved))
    monkeypatch.setattr(
        core,
        "get_hub_settings",
        lambda: {
            "projects_root": str(proj_root),
            "instances_external_root": "",
            "linked_instances": [],
        },
    )

    out = core.list_projects()
    assert len([p for p in out["projects"] if p["slug"] == "once"]) == 1
