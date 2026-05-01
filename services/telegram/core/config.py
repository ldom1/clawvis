from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel


class TelegramSettings(BaseModel):
    agent_url: str
    bot_token: str = ""
    chat_id: int = 0
    send_port: int = 8094

    @property
    def stub_mode(self) -> bool:
        return not self.bot_token

    @property
    def has_chat_id(self) -> bool:
        return self.chat_id != 0


@lru_cache(maxsize=1)
def get_settings() -> TelegramSettings:
    return TelegramSettings.model_validate(
        {
            "agent_url": os.environ["AGENT_URL"],
            "bot_token": os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(),
            "chat_id": int(os.environ.get("TELEGRAM_CHAT_ID", "0") or "0"),
            "send_port": int(os.environ.get("TELEGRAM_SEND_PORT", "8094")),
        }
    )
