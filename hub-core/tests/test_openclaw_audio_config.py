"""Tests for OpenClaw tools.media.audio JSON helpers."""

import json
from pathlib import Path

from hub_core.openclaw_audio_config import audio_block, fragment_document, merge_into


def test_fragment_shape(tmp_path):
    w = str(tmp_path / "transcribe-audio.sh")
    doc = fragment_document(w)
    assert doc["tools"]["media"]["audio"]["enabled"] is True
    assert doc["tools"]["media"]["audio"]["models"][0]["command"] == w


def test_merge_idempotent(tmp_path):
    cfg = tmp_path / "openclaw.json"
    cfg.write_text("{}", encoding="utf-8")
    w = "/opt/clawvis/scripts/transcribe-audio.sh"
    merge_into(cfg, w)
    merge_into(cfg, w)
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert len(data["tools"]["media"]["audio"]["models"]) == 1


def test_merge_preserves_existing_maxbytes(tmp_path):
    cfg = tmp_path / "openclaw.json"
    cfg.write_text(
        '{"tools":{"media":{"audio":{"maxBytes":9999,"models":[]}}}}',
        encoding="utf-8",
    )
    merge_into(cfg, "/bin/sh")
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["tools"]["media"]["audio"]["maxBytes"] == 9999


def test_audio_block_cli_args():
    b = audio_block("/x/script.sh")
    assert b["models"][0]["args"] == ["{{MediaPath}}"]
