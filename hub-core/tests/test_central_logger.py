from __future__ import annotations

import json
import time

from hub_core import central_logger


def test_trace_event_writes_canonical_jsonl(tmp_path, monkeypatch):
    log_file = tmp_path / "trajectory.jsonl"
    monkeypatch.setenv("CENTRAL_LOG_FILE", str(log_file))
    monkeypatch.setattr(central_logger, "_INITIALIZED", False)
    monkeypatch.setattr(central_logger, "_LOG_PATH", None)

    payload = central_logger.trace_event(
        "test.component",
        "event.test",
        trace_id="trace-123",
        level="INFO",
        foo="bar",
    )
    assert payload["component"] == "test.component"
    assert payload["event"] == "event.test"
    assert payload["trace_id"] == "trace-123"

    for _ in range(20):
        if log_file.exists() and log_file.stat().st_size > 0:
            break
        time.sleep(0.05)
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    saved = json.loads(lines[0])
    assert saved["component"] == "test.component"
    assert saved["event"] == "event.test"
    assert saved["trace_id"] == "trace-123"
    assert saved["foo"] == "bar"
