"""LINKED_INSTANCES env must be able to clear linked_instances from hub_settings.json."""

from __future__ import annotations

import json
from pathlib import Path

import kanban_api.core as core


def test_empty_linked_instances_env_overrides_file(tmp_path, monkeypatch):
    settings_path = tmp_path / "kanban" / "hub_settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps({"linked_instances": ["/nope/instance"], "projects_root": "/tmp/x"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(core, "HUB_SETTINGS_FILE", settings_path)
    monkeypatch.setenv("LINKED_INSTANCES", "")
    monkeypatch.delenv("PROJECTS_ROOT", raising=False)
    out = core.get_hub_settings()
    assert out["linked_instances"] == []
