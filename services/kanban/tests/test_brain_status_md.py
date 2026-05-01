"""Tests for YAML frontmatter brain status upsert."""

from __future__ import annotations

import pytest

from kanban_api.core import _upsert_brain_frontmatter_status


def test_upsert_prepends_frontmatter() -> None:
    out = _upsert_brain_frontmatter_status("# Title\n\nx", "active")
    assert out.startswith("---\nstatus: active\n---\n\n")
    assert "# Title" in out


def test_upsert_replaces_status_line() -> None:
    out = _upsert_brain_frontmatter_status("---\nstatus: idle\n---\n\nok", "active")
    assert "status: active" in out
    assert "status: idle" not in out


def test_upsert_appends_status_to_fm() -> None:
    out = _upsert_brain_frontmatter_status("---\ntitle: z\n---\n\n# Hi", "active")
    assert "title: z" in out
    assert "status: active" in out


def test_upsert_rejects_multiline_status() -> None:
    with pytest.raises(ValueError):
        _upsert_brain_frontmatter_status("# x", "a\nb")
