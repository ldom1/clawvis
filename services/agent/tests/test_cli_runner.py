# services/agent/tests/test_cli_runner.py
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


def test_available_false_when_no_bin(monkeypatch):
    monkeypatch.delenv("CLI_BIN", raising=False)
    monkeypatch.setenv("CLI_TOOL", "claude")
    with patch("shutil.which", return_value=None):
        from agent_service.cli_runner import CliRunner
        runner = CliRunner()
        assert runner.available() is False


def test_available_true_when_bin_found(monkeypatch, tmp_path):
    fake_bin = tmp_path / "claude"
    fake_bin.write_text("#!/bin/sh\necho hello")
    fake_bin.chmod(0o755)
    monkeypatch.setenv("CLI_BIN", str(fake_bin))
    monkeypatch.setenv("CLI_TOOL", "claude")
    from agent_service.cli_runner import CliRunner
    runner = CliRunner()
    assert runner.available() is True


@pytest.mark.asyncio
async def test_run_returns_stdout(monkeypatch, tmp_path):
    monkeypatch.setenv("CLI_TOOL", "claude")
    fake_bin = tmp_path / "claude"
    fake_bin.write_text("#!/bin/sh\ncat")
    fake_bin.chmod(0o755)
    monkeypatch.setenv("CLI_BIN", str(fake_bin))

    from agent_service.cli_runner import CliRunner
    runner = CliRunner()
    result = await runner.run("hello world")
    assert "hello world" in result


@pytest.mark.asyncio
async def test_run_uses_stderr_when_stdout_empty(monkeypatch, tmp_path):
    """claude --print often leaves stdout empty; surface stderr for JSON / errors."""
    monkeypatch.setenv("CLI_TOOL", "claude")
    fake_bin = tmp_path / "claude"
    fake_bin.write_text("#!/bin/sh\necho only-stderr >&2")
    fake_bin.chmod(0o755)
    monkeypatch.setenv("CLI_BIN", str(fake_bin))

    from agent_service.cli_runner import CliRunner

    runner = CliRunner()
    result = await runner.run("x")
    assert "only-stderr" in result


@pytest.mark.asyncio
async def test_run_raises_on_timeout(monkeypatch, tmp_path):
    monkeypatch.setenv("CLI_TOOL", "claude")
    fake_bin = tmp_path / "claude"
    fake_bin.write_text("#!/bin/sh\necho ok")
    fake_bin.chmod(0o755)
    monkeypatch.setenv("CLI_BIN", str(fake_bin))

    from agent_service.cli_runner import CliRunner

    async def fail_wait(aw, timeout=None):
        if asyncio.iscoroutine(aw):
            aw.close()
        raise asyncio.TimeoutError()

    with patch("asyncio.wait_for", side_effect=fail_wait):
        runner = CliRunner(timeout=1)
        with pytest.raises(TimeoutError, match="timed out"):
            await runner.run("hello")
