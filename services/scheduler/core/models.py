from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class SkillDefinition(BaseModel):
    name: str
    cron: str | None = None  # None = manual only
    prompt: str = ""
    """Sent to agent-service /chat when ``command`` is empty."""
    command: str | None = None
    """When set, scheduler runs this shell snippet on the Clawvis repo (``CLAWVIS_ROOT``) instead of calling the agent."""
    enabled: bool = True
    timezone: str = "UTC"

    @model_validator(mode="after")
    def _prompt_or_command(self) -> SkillDefinition:
        if (self.command or "").strip():
            return self
        if not (self.prompt or "").strip():
            raise ValueError("prompt is required when command is empty")
        return self


class WorkflowDefinition(BaseModel):
    name: str
    jobs: list[str]       # ordered list of existing job names
    cron: str | None = None
    enabled: bool = True
    timezone: str = "UTC"


class RunSkillInput(BaseModel):
    name: str
    prompt: str = ""
    command: str | None = None

    @model_validator(mode="after")
    def _prompt_or_command(self) -> RunSkillInput:
        if (self.command or "").strip():
            return self
        if not (self.prompt or "").strip():
            raise ValueError("prompt is required when command is empty")
        return self


class AgentChatRequest(BaseModel):
    message: str
    history: list = Field(default_factory=list)
    mode: str = "skill"


class TelegramSendRequest(BaseModel):
    text: str
