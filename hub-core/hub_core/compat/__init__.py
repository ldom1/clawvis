"""
clawvis.compat — Agent compatibility layer.

Clawvis targets three agent runtimes:
  - openclaw  : Full-featured (cron, message, tools, skills, memory)
  - claude    : Claude Code CLI (no cron, no message send, no native skills)
  - mistral   : Mistral Vibe CLI (subset of claude capabilities)

Each function in this module either:
  - Proxies to the available runtime feature, or
  - Raises FeatureUnavailable with a clear explanation.

Usage:
    from clawvis.compat import get_runtime, cron, message_send

    runtime = get_runtime()  # "openclaw" | "claude" | "mistral" | "unknown"
"""

import os
import shutil
import subprocess
from typing import Any

RUNTIME_OPENCLAW = "openclaw"
RUNTIME_CLAUDE = "claude"
RUNTIME_MISTRAL = "mistral"
RUNTIME_UNKNOWN = "unknown"


class FeatureUnavailable(NotImplementedError):
    """Raised when a feature is not available in the current agent runtime."""

    def __init__(self, feature: str, available_in: list[str], current_runtime: str):
        runtimes = ", ".join(available_in)
        super().__init__(
            f"Feature '{feature}' is not available in runtime '{current_runtime}'. "
            f"Available in: {runtimes}."
        )
        self.feature = feature
        self.available_in = available_in
        self.current_runtime = current_runtime


def get_runtime() -> str:
    """Detect the current agent runtime from environment variables."""
    # OpenClaw sets OPENCLAW_AGENT_ID or AGENT_ID=dombot
    if (
        os.environ.get("OPENCLAW_AGENT_ID")
        or os.environ.get("AGENT_ROLE") == "ORCHESTRATOR"
    ):
        return RUNTIME_OPENCLAW
    # Claude Code sets CLAUDE_CODE or is detected via binary
    if os.environ.get("CLAUDE_CODE") or shutil.which("claude"):
        return RUNTIME_CLAUDE
    # Mistral Vibe CLI
    if os.environ.get("MISTRAL_VIBE") or shutil.which("mistral"):
        return RUNTIME_MISTRAL
    return RUNTIME_UNKNOWN


# ─────────────────────────────────────────────────────────────────────────────
# Feature: Cron scheduling
# Available in: openclaw
# Not available in: claude, mistral (no native scheduler)
# ─────────────────────────────────────────────────────────────────────────────


def cron_schedule(
    name: str, expr: str, command: str, runtime: str | None = None
) -> dict[str, Any]:
    """
    Schedule a recurring cron job.

    OpenClaw: creates a job via cron/jobs.json.
    Claude / Mistral: NOT AVAILABLE — use system cron (crontab) or an external scheduler.
    """
    rt = runtime or get_runtime()
    if rt == RUNTIME_OPENCLAW:
        # Proxy: OpenClaw CLI
        result = subprocess.run(
            [
                "openclaw",
                "cron",
                "add",
                "--name",
                name,
                "--schedule",
                expr,
                "--command",
                command,
            ],
            capture_output=True,
            text=True,
        )
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "output": result.stdout,
        }

    raise FeatureUnavailable(
        feature="cron:schedule",
        available_in=[RUNTIME_OPENCLAW],
        current_runtime=rt,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Feature: Message send (Telegram / Discord)
# Available in: openclaw
# Not available in: claude, mistral
# ─────────────────────────────────────────────────────────────────────────────


def message_send(
    channel: str, target: str, message: str, runtime: str | None = None
) -> dict[str, Any]:
    """
    Send a message to a channel (telegram, discord, etc.).

    OpenClaw: proxies to `openclaw message send`.
    Claude / Mistral: NOT AVAILABLE — no native outbound messaging.
    """
    rt = runtime or get_runtime()
    if rt == RUNTIME_OPENCLAW:
        result = subprocess.run(
            [
                "openclaw",
                "message",
                "send",
                "--channel",
                channel,
                "--target",
                target,
                "--message",
                message,
            ],
            capture_output=True,
            text=True,
        )
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "output": result.stdout,
        }

    raise FeatureUnavailable(
        feature="message:send",
        available_in=[RUNTIME_OPENCLAW],
        current_runtime=rt,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Feature: Skill execution
# Available in: openclaw (native), claude (via bash), mistral (via bash, limited)
# ─────────────────────────────────────────────────────────────────────────────


def skill_run(
    skill_name: str, *args: str, runtime: str | None = None
) -> dict[str, Any]:
    """
    Execute a Clawvis skill script.

    OpenClaw: native skill runner.
    Claude / Mistral: fallback to direct bash execution of the skill script.
    """
    rt = runtime or get_runtime()
    skill_script = os.path.expanduser(f"~/.openclaw/skills/{skill_name}/scripts/run.sh")

    if rt == RUNTIME_OPENCLAW:
        result = subprocess.run(
            ["openclaw", "skill", "run", skill_name, *args],
            capture_output=True,
            text=True,
        )
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "output": result.stdout,
        }

    if os.path.exists(skill_script):
        result = subprocess.run(
            ["bash", skill_script, *args], capture_output=True, text=True
        )
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "output": result.stdout,
        }

    raise FeatureUnavailable(
        feature=f"skill:{skill_name}",
        available_in=[RUNTIME_OPENCLAW, RUNTIME_CLAUDE],
        current_runtime=rt,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Feature: Memory vault access
# Available in: openclaw (native), claude (file read), mistral (file read, limited)
# ─────────────────────────────────────────────────────────────────────────────


def memory_read(path: str, runtime: str | None = None) -> str:
    """
    Read a file from the memory vault.

    All runtimes: direct file read (memory is at hub-ldom/instances/ldom/memory/,
    symlinked from ~/.openclaw/workspace/memory/).
    """
    vault = os.path.expanduser("~/.openclaw/workspace/memory")
    full_path = os.path.join(vault, path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Memory file not found: {path}")
    with open(full_path, encoding="utf-8") as f:
        return f.read()


def memory_write(path: str, content: str, runtime: str | None = None) -> None:
    """
    Write a file to the memory vault.

    All runtimes: direct file write.
    """
    vault = os.path.expanduser("~/.openclaw/workspace/memory")
    full_path = os.path.join(vault, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)


# ─────────────────────────────────────────────────────────────────────────────
# Feature: Agent session management
# Available in: openclaw
# Not available in: claude (stateless CLI), mistral (stateless CLI)
# ─────────────────────────────────────────────────────────────────────────────


def session_list(runtime: str | None = None) -> list[dict[str, Any]]:
    """
    List active agent sessions.

    OpenClaw: `openclaw session list`.
    Claude / Mistral: NOT AVAILABLE — stateless CLIs have no persistent sessions.
    """
    rt = runtime or get_runtime()
    if rt == RUNTIME_OPENCLAW:
        result = subprocess.run(
            ["openclaw", "session", "list", "--json"], capture_output=True, text=True
        )
        if result.returncode == 0:
            import json

            return json.loads(result.stdout)
        return []

    raise FeatureUnavailable(
        feature="session:list",
        available_in=[RUNTIME_OPENCLAW],
        current_runtime=rt,
    )
