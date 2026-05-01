from __future__ import annotations

from pydantic import BaseModel, Field


class SkillDefinition(BaseModel):
    name: str
    cron: str | None = None  # None = manual only
    prompt: str
    enabled: bool = True
    timezone: str = "UTC"


class WorkflowDefinition(BaseModel):
    name: str
    jobs: list[str]       # ordered list of existing job names
    cron: str | None = None
    enabled: bool = True
    timezone: str = "UTC"


class RunSkillInput(BaseModel):
    name: str
    prompt: str


class AgentChatRequest(BaseModel):
    message: str
    history: list = Field(default_factory=list)
    mode: str = "skill"


class TelegramSendRequest(BaseModel):
    text: str
