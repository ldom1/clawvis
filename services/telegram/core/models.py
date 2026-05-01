from __future__ import annotations

from pydantic import BaseModel, Field
from telegram import Update


class IncomingMessage(BaseModel):
    text: str
    user_id: int | None = None


class OutcomingMessage(BaseModel):
    text: str


class AgentChatRequest(BaseModel):
    message: str
    history: list = Field(default_factory=list)


def incoming_from_update(update: Update) -> IncomingMessage | None:
    if update.message is None or not update.message.text:
        return None
    return IncomingMessage(
        text=update.message.text,
        user_id=update.effective_user.id if update.effective_user else None,
    )
