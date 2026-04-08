"""Tests for hub_core.brain_memory.active_brain_memory_root."""

from __future__ import annotations

from pathlib import Path

from hub_core.brain_memory import active_brain_memory_root


def test_falls_back_when_no_linked(tmp_path: Path) -> None:
    mem = tmp_path / "default-mem"
    mem.mkdir()
    assert active_brain_memory_root(
        memory_root=mem, linked_instances=[]
    ) == mem.resolve()


def test_prefers_matching_memory_root(tmp_path: Path) -> None:
    runtime = tmp_path / "a" / "memory"
    runtime.mkdir(parents=True)
    other = tmp_path / "b" / "memory"
    other.mkdir(parents=True)
    assert active_brain_memory_root(
        memory_root=runtime,
        linked_instances=[str(tmp_path / "b"), str(tmp_path / "a")],
    ).resolve() == runtime.resolve()


def test_first_linked_when_no_runtime_match(tmp_path: Path) -> None:
    default = tmp_path / "default" / "memory"
    default.mkdir(parents=True)
    ldom = tmp_path / "ldom" / "memory"
    ldom.mkdir(parents=True)
    assert active_brain_memory_root(
        memory_root=default,
        linked_instances=[str(tmp_path / "ldom")],
    ).resolve() == ldom.resolve()


def test_prefers_runtime_when_runtime_has_projects_md(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime" / "memory"
    (runtime / "projects").mkdir(parents=True)
    (runtime / "projects" / "clawvis.md").write_text("# clawvis\n", encoding="utf-8")
    linked = tmp_path / "linked" / "memory"
    linked.mkdir(parents=True)
    assert active_brain_memory_root(
        memory_root=runtime,
        linked_instances=[str(tmp_path / "linked")],
    ).resolve() == runtime.resolve()
