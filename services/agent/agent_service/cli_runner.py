"""Generic CLI runner — executes Claude Code, opencode, or Codex CLI as a subprocess."""
from __future__ import annotations

import asyncio
import os
import shutil


_TOOL_FLAGS: dict[str, list[str]] = {
    "claude": ["--print", "--dangerously-skip-permissions"],
    "opencode": ["run"],
    "codex": [],
}


class CliRunner:
    def __init__(self, timeout: int = 120) -> None:
        self.tool = os.environ.get("CLI_TOOL", "claude").strip().lower()
        self.timeout = timeout
        self._bin: str | None = self._resolve_bin()

    def _resolve_bin(self) -> str | None:
        explicit = os.environ.get("CLI_BIN", "").strip()
        if explicit and os.path.isfile(explicit):
            return explicit
        return shutil.which(self.tool)

    def available(self) -> bool:
        return self._bin is not None

    async def run(self, prompt: str, model: str | None = None) -> str:
        if not self._bin:
            raise RuntimeError(f"CLI tool '{self.tool}' not found in PATH")

        flags = list(_TOOL_FLAGS.get(self.tool, []))
        if self.tool == "claude" and model:
            # Claude CLI supports explicit model selection via --model.
            flags += ["--model", model]
        cmd = [self._bin] + flags

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=prompt.encode()),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise TimeoutError(f"CLI tool '{self.tool}' timed out after {self.timeout}s")

        out = stdout.decode(errors="replace").strip()
        err = stderr.decode(errors="replace").strip()
        # claude --print often leaves stdout empty while the reply (or errors) is on stderr
        if not out and err:
            return err
        return out
