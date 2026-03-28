from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class OpenClawResult:
    success: bool
    output: dict | str
    error: str | None = None


def _openclaw_bin() -> str | None:
    custom = os.environ.get("OPENCLAW_BIN")
    if custom and os.path.isfile(custom):
        return custom
    return shutil.which("openclaw")


def openclaw_available() -> bool:
    return (
        os.environ.get("OPENCLAW_AVAILABLE", "").lower() == "true"
        and bool(_openclaw_bin())
    )


def _run(args: list[str], timeout: int = 30) -> OpenClawResult:
    bin_path = _openclaw_bin()
    if not bin_path:
        return OpenClawResult(success=False, output={}, error="openclaw not found")

    env = os.environ.copy()
    state_dir = os.environ.get("OPENCLAW_STATE_DIR")
    if state_dir:
        env["OPENCLAW_STATE_DIR"] = state_dir

    try:
        result = subprocess.run(
            [bin_path, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        if result.returncode != 0:
            return OpenClawResult(success=False, output={}, error=result.stderr.strip())
        try:
            return OpenClawResult(success=True, output=json.loads(result.stdout))
        except json.JSONDecodeError:
            return OpenClawResult(success=True, output=result.stdout.strip())
    except subprocess.TimeoutExpired:
        return OpenClawResult(success=False, output={}, error="timeout")
    except Exception as exc:
        return OpenClawResult(success=False, output={}, error=str(exc))


def run_agent_session(message: str, session_id: str | None = None) -> OpenClawResult:
    args = ["agent", "--message", message, "--json"]
    if session_id:
        args += ["--session-id", session_id]
    return _run(args, timeout=120)


def list_sessions() -> OpenClawResult:
    return _run(["sessions", "--json"])


def restart_gateway() -> OpenClawResult:
    return _run(["gateway", "--kill", "--start"], timeout=30)
