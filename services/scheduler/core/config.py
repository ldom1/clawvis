from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class SchedulerSettings(BaseModel):
    agent_url: str
    telegram_url: str
    skills_dir: Path = Path("/skills")
    api_port: int = 8095


@lru_cache(maxsize=1)
def get_settings() -> SchedulerSettings:
    return SchedulerSettings.model_validate(
        {
            "agent_url": os.environ["AGENT_URL"],
            "telegram_url": os.environ["TELEGRAM_URL"],
            "skills_dir": os.environ.get("SKILLS_DIR", "/skills"),
            "api_port": int(os.environ.get("SCHEDULER_API_PORT", "8095")),
        }
    )
