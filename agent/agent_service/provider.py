# agent/agent_service/provider.py
from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path


def _normalize_primary_env() -> str | None:
    raw = (os.environ.get("PRIMARY_AI_PROVIDER") or "").strip().lower()
    if not raw:
        return None
    if raw in ("openclaw",):
        return "openclaw"
    if raw in ("anthropic", "claude"):
        return "anthropic"
    if raw in ("mammouth", "mistral", "mammoth"):
        return "mammouth"
    return None


@dataclass
class ProviderConfig:
    provider: str  # "anthropic" | "mammouth" | "openclaw"
    primary_from_env: bool
    anthropic_token: str
    mammouth_token: str
    mammouth_base_url: str
    openclaw_available: bool
    openclaw_bin: str | None
    openclaw_state_dir: str | None


def load_provider_config() -> ProviderConfig:
    state_dir = os.environ.get("OPENCLAW_STATE_DIR")
    anthropic_token = ""
    mammouth_token = ""
    mammouth_base_url = "https://api.mammouth.ai/v1"

    if state_dir:
        profiles_path = (
            Path(state_dir) / "agents" / "main" / "agent" / "auth-profiles.json"
        )
        if profiles_path.exists():
            data = json.loads(profiles_path.read_text(encoding="utf-8"))
            for val in data.get("profiles", {}).values():
                if val.get("provider") == "anthropic" and not anthropic_token:
                    anthropic_token = val.get("token", "")
                elif val.get("provider") == "mistral" and not mammouth_token:
                    mammouth_token = val.get("token", "")

        openclaw_cfg = Path(state_dir) / "openclaw.json"
        if openclaw_cfg.exists():
            cfg = json.loads(openclaw_cfg.read_text(encoding="utf-8"))
            providers = cfg.get("models", {}).get("providers", {})
            if "mistral" in providers:
                mammouth_base_url = providers["mistral"].get(
                    "baseUrl", mammouth_base_url
                )

    anthropic_token = anthropic_token or os.environ.get("ANTHROPIC_API_KEY", "")
    mammouth_token = (
        mammouth_token
        or os.environ.get("MAMMOUTH_API_KEY", "")
        or os.environ.get("OPENAI_API_KEY", "")
    )

    primary = _normalize_primary_env()
    primary_from_env = primary is not None
    if primary is not None:
        provider = primary
    else:
        provider = (
            "anthropic"
            if anthropic_token
            else ("mammouth" if mammouth_token else "anthropic")
        )

    openclaw_bin = os.environ.get("OPENCLAW_BIN") or shutil.which("openclaw")
    from .openclaw_runner import openclaw_available as _openclaw_available

    return ProviderConfig(
        provider=provider,
        primary_from_env=primary_from_env,
        anthropic_token=anthropic_token,
        mammouth_token=mammouth_token,
        mammouth_base_url=mammouth_base_url,
        openclaw_available=_openclaw_available(),
        openclaw_bin=openclaw_bin,
        openclaw_state_dir=state_dir,
    )
