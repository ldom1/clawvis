from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .cli_runner import CliRunner


def _dotenv_paths() -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    raw = os.environ.get("CLAWVIS_DOTENV_PATH", "").strip()
    if raw:
        p = Path(raw).expanduser()
        out.append(p)
        try:
            seen.add(str(p.resolve()))
        except OSError:
            seen.add(str(p))
    for p in (Path("/clawvis/.env"), Path(__file__).resolve().parents[3] / ".env"):
        try:
            key = str(p.resolve())
        except OSError:
            key = str(p)
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def _read_dotenv_key(path: Path, key: str) -> str | None:
    prefix = f"{key}="
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("export "):
            s = s[7:].lstrip()
        if not s.startswith(prefix):
            continue
        v = s[len(prefix):].strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        return v
    return None


def primary_ai_provider_raw() -> str:
    for path in _dotenv_paths():
        if path.is_file():
            v = _read_dotenv_key(path, "PRIMARY_AI_PROVIDER")
            if v is not None:
                return v
    return os.environ.get("PRIMARY_AI_PROVIDER", "")


def _normalize_primary_env() -> str | None:
    raw = primary_ai_provider_raw().strip().lower()
    if not raw:
        return None
    if raw in ("anthropic", "claude"):
        return "anthropic"
    if raw in ("mammouth", "mistral", "mammoth", "openrouter"):
        return "mammouth"
    if raw in ("cli", "claude-code", "opencode", "codex"):
        return "cli"
    return None


@dataclass
class ProviderConfig:
    provider: str           # "anthropic" | "mammouth" | "cli"
    primary_from_env: bool
    anthropic_token: str
    mammouth_token: str
    mammouth_base_url: str
    cli_available: bool
    cli_tool: str


def load_provider_config() -> ProviderConfig:
    anthropic_token = os.environ.get("ANTHROPIC_API_KEY", "")
    mammouth_token = (
        os.environ.get("OPENROUTER_API_KEY", "")
        or os.environ.get("MAMMOUTH_API_KEY", "")
        or os.environ.get("OPENAI_API_KEY", "")
    )
    mammouth_base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    primary = _normalize_primary_env()
    primary_from_env = primary is not None
    if primary is not None:
        provider = primary
    else:
        provider = (
            "anthropic" if anthropic_token
            else ("mammouth" if mammouth_token else "anthropic")
        )

    runner = CliRunner()
    return ProviderConfig(
        provider=provider,
        primary_from_env=primary_from_env,
        anthropic_token=anthropic_token,
        mammouth_token=mammouth_token,
        mammouth_base_url=mammouth_base_url,
        cli_available=runner.available(),
        cli_tool=runner.tool,
    )
