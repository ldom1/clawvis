"""Tests for dombot_logger.logger — writes to temp files."""
import json

import pytest
from dombot_logger.logger import DomBotLogger, get_logger, log


@pytest.fixture(autouse=True)
def _isolate_logs(tmp_path, monkeypatch):
    """Redirect all log output to tmp_path so tests don't pollute real logs."""
    import dombot_logger.logger as mod
    monkeypatch.setattr(mod, "LOG_DIR", tmp_path)
    monkeypatch.setattr(mod, "LOG_TEXT", tmp_path / "dombot.log")
    monkeypatch.setattr(mod, "LOG_JSONL", tmp_path / "dombot.jsonl")
    monkeypatch.setattr(mod, "_configured", False)
    yield tmp_path


class TestDomBotLogger:
    def test_info(self, _isolate_logs):
        logger = DomBotLogger(process="test:proc", model="test-model")
        logger.info("test:action", "hello world")
        jsonl = (_isolate_logs / "dombot.jsonl").read_text()
        entry = json.loads(jsonl.strip())
        assert entry["level"] == "INFO"
        assert entry["process"] == "test:proc"
        assert entry["model"] == "test-model"
        assert entry["action"] == "test:action"
        assert entry["message"] == "hello world"

    def test_error(self, _isolate_logs):
        logger = DomBotLogger(process="agent:main")
        logger.error("task:fail", "broken", task_id="task-123")
        entry = json.loads((_isolate_logs / "dombot.jsonl").read_text().strip())
        assert entry["level"] == "ERROR"
        assert entry["metadata"]["task_id"] == "task-123"

    def test_warning(self, _isolate_logs):
        logger = DomBotLogger()
        logger.warning("api:retry", "retrying")
        entry = json.loads((_isolate_logs / "dombot.jsonl").read_text().strip())
        assert entry["level"] == "WARNING"

    def test_debug(self, _isolate_logs):
        logger = DomBotLogger()
        logger.debug("parse:step", "parsing line 42")
        entry = json.loads((_isolate_logs / "dombot.jsonl").read_text().strip())
        assert entry["level"] == "DEBUG"

    def test_critical(self, _isolate_logs):
        logger = DomBotLogger()
        logger.critical("system:down", "disk full")
        entry = json.loads((_isolate_logs / "dombot.jsonl").read_text().strip())
        assert entry["level"] == "CRITICAL"

    def test_multiple_writes(self, _isolate_logs):
        logger = DomBotLogger()
        logger.info("a", "first")
        logger.info("b", "second")
        lines = (_isolate_logs / "dombot.jsonl").read_text().strip().split("\n")
        assert len(lines) == 2

    def test_text_log_written(self, _isolate_logs):
        logger = DomBotLogger(process="cron:test", model="m")
        logger.info("act", "msg")
        text = (_isolate_logs / "dombot.log").read_text()
        assert "[cron:test]" in text
        assert "msg" in text


class TestGetLogger:
    def test_returns_instance(self):
        l = get_logger("cron:job", "model-x")
        assert isinstance(l, DomBotLogger)
        assert l.process == "cron:job"
        assert l.model == "model-x"

    def test_defaults(self):
        l = get_logger()
        assert l.process == "agent:main"
        assert l.model == ""


class TestLogFunction:
    def test_writes_entry(self, _isolate_logs):
        log(level="WARNING", process="api:kanban", model="haiku", action="req:slow", message="slow query")
        entry = json.loads((_isolate_logs / "dombot.jsonl").read_text().strip())
        assert entry["level"] == "WARNING"
        assert entry["process"] == "api:kanban"

    def test_defaults(self, _isolate_logs):
        log(message="default test")
        entry = json.loads((_isolate_logs / "dombot.jsonl").read_text().strip())
        assert entry["level"] == "INFO"
        assert entry["process"] == "agent:main"
