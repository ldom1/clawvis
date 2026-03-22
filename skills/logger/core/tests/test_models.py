"""Tests for dombot_logger.models."""
import os

import pytest
from dombot_logger.models import LogEntry


class TestLogEntry:
    def test_defaults(self):
        e = LogEntry()
        assert e.level == "INFO"
        assert e.process == "agent:main"
        assert e.model == ""
        assert e.pid == os.getpid()
        assert e.timestamp.endswith("Z")

    def test_custom_fields(self):
        e = LogEntry(
            level="ERROR",
            process="cron:morning-briefing",
            model="claude-haiku-4-5",
            action="task:fail",
            message="Something broke",
            metadata={"task_id": "task-abc"},
        )
        assert e.level == "ERROR"
        assert e.process == "cron:morning-briefing"
        assert e.metadata["task_id"] == "task-abc"

    def test_invalid_level_rejected(self):
        with pytest.raises(Exception):
            LogEntry(level="TRACE")

    def test_format_text_basic(self):
        e = LogEntry(
            timestamp="2026-03-11T10:00:00+00:00Z",
            level="INFO",
            process="agent:main",
            model="claude-haiku-4-5",
            action="task:start",
            message="Hello",
        )
        txt = e.format_text()
        assert "[2026-03-11 10:00:00]" in txt
        assert "[INFO    ]" in txt
        assert "[agent:main]" in txt
        assert "[claude-haiku-4-5]" in txt
        assert "task:start" in txt
        assert "Hello" in txt

    def test_format_text_no_model(self):
        e = LogEntry(timestamp="2026-01-01T00:00:00Z", model="")
        assert "[-]" in e.format_text()

    def test_format_text_with_metadata(self):
        e = LogEntry(
            timestamp="2026-01-01T00:00:00Z",
            message="test",
            metadata={"k": "v", "n": 42},
        )
        txt = e.format_text()
        assert "(k=v, n=42)" in txt

    def test_format_text_empty_metadata(self):
        e = LogEntry(timestamp="2026-01-01T00:00:00Z", message="test")
        assert "(" not in e.format_text().split("—")[1]
