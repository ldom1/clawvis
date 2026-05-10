"""Tests for config module."""

from __future__ import annotations

from pathlib import Path

import self_improvment.config as cfg
from self_improvment.config import (
    LAB_ROOT,
    LAB_ROOT_LEGACY,
    LEARNINGS_DIR,
    MEMORY_FILE,
    OPENROUTER_BASE_URL,
    WORKSPACE,
)


def test_learnings_dir_under_skill_root() -> None:
    # tests/ lives under core/ → skill root is parents[2]
    skill_root = Path(__file__).resolve().parents[2]
    assert LEARNINGS_DIR == skill_root / ".learnings"


def test_workspace_and_memory_paths() -> None:
    assert MEMORY_FILE == WORKSPACE / "MEMORY.md"
    assert LAB_ROOT == cfg.HOME / "lab"
    assert LAB_ROOT_LEGACY == cfg.HOME / "Lab"


def test_openrouter_base_url_default() -> None:
    assert OPENROUTER_BASE_URL.startswith("https://")
