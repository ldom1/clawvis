"""Scheduler — reads YAML skill definitions, fires cron jobs against the agent, posts results to Telegram."""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

import httpx
import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler

AGENT_URL = os.environ["AGENT_URL"]        # e.g. http://agent-service:8092
TELEGRAM_URL = os.environ["TELEGRAM_URL"]  # e.g. http://telegram:8094
SKILLS_DIR = Path(os.environ.get("SKILLS_DIR", "/skills"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("scheduler")


async def _run_skill(name: str, prompt: str) -> None:
    log.info("job.trigger name=%s", name)
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{AGENT_URL}/chat",
                json={"message": prompt, "history": []},
            )
            resp.raise_for_status()
            result = resp.text
        log.info("job.result name=%s chars=%d", name, len(result))
    except Exception as exc:
        result = f"[agent error: {exc}]"
        log.error("job.agent_error name=%s error=%s", name, exc)

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(
                f"{TELEGRAM_URL}/send",
                json={"text": f"[{name}]\n{result}"},
            )
        log.info("job.notified name=%s", name)
    except Exception as exc:
        log.error("job.notify_error name=%s error=%s", name, exc)


def _load_skills() -> list[dict]:
    skills: list[dict] = []
    for path in sorted(SKILLS_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                log.warning("skill.skip path=%s reason=not_a_mapping", path.name)
                continue
            missing = [k for k in ("name", "cron", "prompt") if k not in data]
            if missing:
                log.warning("skill.skip path=%s reason=missing_fields fields=%s", path.name, missing)
                continue
            if not data.get("enabled", True):
                log.info("skill.disabled name=%s", data["name"])
                continue
            skills.append(data)
            log.info("skill.loaded name=%s cron=%s", data["name"], data["cron"])
        except Exception as exc:
            log.error("skill.parse_error path=%s error=%s", path.name, exc)
    return skills


def _register_skill(scheduler: AsyncIOScheduler, skill: dict) -> None:
    name: str = skill["name"]
    cron: str = skill["cron"]
    prompt: str = skill["prompt"]
    timezone: str = skill.get("timezone", "UTC")

    parts = cron.strip().split()
    if len(parts) != 5:
        log.error("skill.invalid_cron name=%s cron=%r (need 5 fields)", name, cron)
        return

    minute, hour, day, month, day_of_week = parts
    scheduler.add_job(
        _run_skill,
        "cron",
        args=[name, prompt],
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
        timezone=timezone,
        id=name,
        name=name,
        replace_existing=True,
    )
    log.info("job.registered name=%s cron=%r tz=%s", name, cron, timezone)


async def main() -> None:
    if not SKILLS_DIR.is_dir():
        log.error("skills_dir.missing path=%s", SKILLS_DIR)
        return

    skills = _load_skills()
    log.info("scheduler.start registered=%d skills_dir=%s", len(skills), SKILLS_DIR)

    scheduler = AsyncIOScheduler()
    for skill in skills:
        _register_skill(scheduler, skill)

    scheduler.start()
    log.info("scheduler.running")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
