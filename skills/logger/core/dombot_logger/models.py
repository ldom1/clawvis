"""Log entry model for OpenClaw unified logging."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from dombot_logger.config import list_available_discord_channels

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class LogEntry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat() + "Z")
    level: LogLevel = "INFO"
    process: str = "agent:main"
    model: str = ""
    action: str = ""
    message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    pid: int = Field(default_factory=lambda: __import__("os").getpid())

    def format_text(self) -> str:
        ts = self.timestamp[:19].replace("T", " ")
        meta = ""
        if self.metadata:
            parts = [f"{k}={v}" for k, v in self.metadata.items()]
            meta = f" ({', '.join(parts)})"
        return (
            f"[{ts}] [{self.level:<8}] [{self.process}] [{self.model or '-'}] "
            f"{self.action} — {self.message}{meta}"
        )

    def format_human(self) -> str:
        """Format lisible pour humains (Discord). Emojis, texte naturel, sans technique."""
        level = (self.level or "INFO").upper()
        action = (self.action or "").lower()
        process = (self.process or "")
        message = self.message or ""

        # Emoji principal par niveau/action
        if level in ("ERROR", "CRITICAL") or "fail" in action:
            emoji = "\u274c"
        elif level == "WARNING":
            emoji = "\u26a0\ufe0f"
        elif "start" in action:
            emoji = "\u25b6\ufe0f"
        elif "complete" in action or "done" in action or "success" in action:
            emoji = "\u2705"
        elif "innov" in action or "idea" in action:
            emoji = "\U0001f4a1"
        elif "hub" in action:
            emoji = "\U0001f4ca"
        else:
            emoji = "\u2139\ufe0f"

        # Nom lisible du process
        name = process
        for prefix in ("cron:", "skill:", "subagent:", "channel:", "agent:"):
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        name = name.replace("-", " ").replace("_", " ").title()

        # Message court : strip les parties trop techniques
        short = message
        # Retirer les parenthèses avec métriques internes (ex: "(exit_code=0, log_file=...)")
        import re as _re
        short = _re.sub(r"\s*\(log_file=[^)]+\)", "", short)

        text = f"{emoji} **{name}** — {short}"

        # Métadonnées utiles seulement (pas les paths internes)
        if self.metadata:
            useful_keys = {"cpu", "ram", "exit_code", "status", "mammouth_credits", "claude_usage"}
            parts = [f"{k}={v}" for k, v in self.metadata.items() if k in useful_keys]
            if parts:
                text += f"\n`{', '.join(parts)}`"

        return text


class DiscordCliRunConfig(BaseModel):
    token: str
    channel_id: int
    once: bool = False
    message: str = "Test integration OK"


class DiscordCliCreateChannelsConfig(BaseModel):
    token: str
    guild_id: int
    channel_id: int
    channels: list[str]
    store_path: str = ".local/discord_channels.json"

    @field_validator("channels")
    @classmethod
    def _validate_channels(cls, value: list[str]) -> list[str]:
        cleaned = [v.strip() for v in value if v.strip()]
        if not cleaned:
            raise ValueError("No channels provided. Use --channels 'name1,name2'")
        available = list_available_discord_channels()
        invalid = [name for name in cleaned if name.lower().replace("-", "_") not in available]
        if invalid:
            allowed = ", ".join(sorted(available))
            bad = ", ".join(invalid)
            raise ValueError(f"Unknown channels: {bad}. Allowed: {allowed}")
        return cleaned


class DiscordCliDeleteChannelsConfig(BaseModel):
    token: str
    guild_id: int
    channel_id: int
    channels: list[str]
    store_path: str = ".local/discord_channels.json"

    @field_validator("channels")
    @classmethod
    def _validate_delete_names(cls, value: list[str]) -> list[str]:
        cleaned = [v.strip() for v in value if v.strip()]
        if not cleaned:
            raise ValueError("No channels provided. Use --channels 'name1,name2'")
        return cleaned
