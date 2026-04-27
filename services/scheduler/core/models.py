from __future__ import annotations

from pydantic import BaseModel, Field


class SkillDefinition(BaseModel):
    name: str
    cron: str
    prompt: str
    enabled: bool = True
    timezone: str = "UTC"


class RunSkillInput(BaseModel):
    name: str
    prompt: str


class AgentChatRequest(BaseModel):
    message: str
    history: list = Field(default_factory=list)


class TelegramSendRequest(BaseModel):
    text: str
