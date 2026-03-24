from __future__ import annotations

from enum import Enum
from getpass import getpass
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Provider(str, Enum):
    CLAUDE = "claude"
    MISTRAL = "mistral"
    OPENCLAW = "openclaw"

    def __str__(self) -> str:
        return self.value

    def get_provider(self) -> Provider:
        return self.value

    @staticmethod
    def get_providers() -> tuple[Provider, ...]:
        return tuple[str, ...](p.value for p in Provider)


def _read_env_lines() -> list[str]:
    if not ENV_FILE.exists():
        return []
    return ENV_FILE.read_text(encoding="utf-8").splitlines()


def _set_env_key(lines: list[str], key: str, value: str) -> list[str]:
    prefix = f"{key}="
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith(prefix):
            out.append(f"{key}={value}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{key}={value}")
    return out


def _prompt_provider(default: str = "claude") -> str:
    print("\nSetup AI runtime")
    print("Choisis ton provider principal:")
    print("  1) claude")
    print("  2) mistral")
    print("  3) openclaw")
    raw = input(f"Provider [1-3] (default {default}): ").strip()
    if raw == "2":
        return "mistral"
    if raw == "3":
        return "openclaw"
    if raw in Provider.get_providers():
        return raw
    return default


def run_setup_runtime(
    *,
    provider: str | None = None,
    claude_api_key: str | None = None,
    mistral_api_key: str | None = None,
    openclaw_base_url: str | None = None,
    openclaw_api_key: str | None = None,
    non_interactive: bool = False,
) -> dict:
    selected = (provider or "").strip().lower()
    if selected not in Provider.get_providers():
        if non_interactive:
            raise ValueError("provider must be one of: claude, mistral, openclaw")
        selected = _prompt_provider("claude")

    if selected == "claude" and claude_api_key is None and not non_interactive:
        claude_api_key = getpass("Claude API key (sk-ant-...): ").strip()
    if selected == "mistral" and mistral_api_key is None and not non_interactive:
        mistral_api_key = getpass("Mistral API key: ").strip()
    if selected == "openclaw":
        if openclaw_base_url is None and not non_interactive:
            openclaw_base_url = (
                input("OpenClaw base URL (default http://localhost:3333): ").strip()
                or "http://localhost:3333"
            )
        if openclaw_api_key is None and not non_interactive:
            openclaw_api_key = getpass("OpenClaw API key (optional): ").strip()

    lines = _read_env_lines()
    lines = _set_env_key(lines, "PRIMARY_AI_PROVIDER", selected)
    lines = _set_env_key(lines, "CLAUDE_API_KEY", (claude_api_key or "").strip())
    lines = _set_env_key(lines, "MISTRAL_API_KEY", (mistral_api_key or "").strip())
    lines = _set_env_key(lines, "OPENCLAW_BASE_URL", (openclaw_base_url or "").strip())
    lines = _set_env_key(lines, "OPENCLAW_API_KEY", (openclaw_api_key or "").strip())
    ENV_FILE.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    configured = bool(
        (selected == "claude" and (claude_api_key or "").strip())
        or (selected == "mistral" and (mistral_api_key or "").strip())
        or (selected == "openclaw" and (openclaw_base_url or "").strip())
    )
    return {"provider": selected, "configured": configured, "env_file": str(ENV_FILE)}
