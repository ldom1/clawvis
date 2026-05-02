from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

_HOME = Path.home()
_CORE_DIR = Path(__file__).resolve().parent.parent
_SKILL_ROOT = _CORE_DIR.parent


def _resolve_clawvis_root() -> Path | None:
    raw = os.getenv("CLAWVIS_ROOT", "").strip()
    if raw:
        p = Path(raw).expanduser().resolve()
        if (p / "hub-core").is_dir():
            return p
    for rel in (_HOME / "lab" / "clawvis", _HOME / "Lab" / "clawvis"):
        rp = rel.resolve()
        if (rp / "hub-core").is_dir():
            return rp
    return None


def _bootstrap_dotenv() -> None:
    load_dotenv(_SKILL_ROOT / ".env", override=True)
    load_dotenv(_CORE_DIR / ".env", override=True)
    root = _resolve_clawvis_root()
    if root is not None and (root / ".env").is_file():
        load_dotenv(root / ".env", override=True)


_bootstrap_dotenv()


def _default_input_folders() -> list[str]:
    raw = os.getenv("DOMBOT_MAIL_IMAP_INPUT_FOLDERS", "INBOX,Promotions,SocialNetworks")
    return [f.strip() for f in raw.split(",") if f.strip()]


class MailSettings(BaseModel):
    imap_host: str = Field(..., description="IMAP hostname")
    imap_port: int = Field(993, description="IMAP port")
    smtp_host: str = Field(..., description="SMTP hostname")
    smtp_port: int = Field(465, description="SMTP port")
    user: str = Field(..., description="Mail account username")
    password: str = Field(..., description="Mail account password")
    sent_folder: str = Field("Sent", description="Folder for sent messages")
    archive_folder: str = Field("Archive", description="Folder for archived/handled messages")
    input_folders: list[str] = Field(
        default_factory=_default_input_folders,
        description="Folders to scan for incoming mail (INBOX, Promotions, SocialNetworks)",
    )

    @classmethod
    def from_env(cls) -> "MailSettings":
        return cls(
            imap_host=env("DOMBOT_MAIL_IMAP_HOST"),
            imap_port=int(os.getenv("DOMBOT_MAIL_IMAP_PORT", "993")),
            smtp_host=env("DOMBOT_MAIL_SMTP_HOST"),
            smtp_port=int(os.getenv("DOMBOT_MAIL_SMTP_PORT", "465")),
            user=env("DOMBOT_MAIL_USER"),
            password=env("DOMBOT_MAIL_PASSWORD"),
            sent_folder=os.getenv("DOMBOT_MAIL_IMAP_SENT_FOLDER", "Sent") or "Sent",
            archive_folder=os.getenv("DOMBOT_MAIL_IMAP_ARCHIVE_FOLDER", "Archive") or "Archive",
            input_folders=_default_input_folders(),
        )


def env(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing env: {name}")
    return value
