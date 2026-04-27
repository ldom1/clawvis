"""Central paths and config for hub_core. Override LAB_DIR via env if needed."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

_CONFIG_DIR = Path(__file__).resolve().parent
load_dotenv(_CONFIG_DIR.parent / ".env")

LAB_DIR = Path(os.getenv("LAB_DIR", "/lab"))
HUB_API_DIR = LAB_DIR / "hub" / "public" / "api"
PROVIDERS_JSON = HUB_API_DIR / "providers.json"
SYSTEM_JSON = HUB_API_DIR / "system.json"
STATUS_JSON = HUB_API_DIR / "status.json"

HUB_CORE_DIR = Path(__file__).resolve().parent
DATA_DIR = HUB_CORE_DIR / "data" / "claude_sessions"
HUB_CORE_PUBLIC_API_DIR = HUB_CORE_DIR / "public" / "api"


def get_anthropic_api_key() -> Optional[str]:
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key
    key_file = Path.home() / ".anthropic" / "api_key"
    if key_file.exists():
        return key_file.read_text().strip()
    return None


MAMMOUTH_API_KEY = os.getenv("MAMMOUTH_API_KEY")
