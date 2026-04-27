"""Scheduler — reads YAML skill definitions, fires cron jobs against the agent, posts results to Telegram.

HTTP management API (port 8095):
  GET  /jobs           → list all job definitions + runtime state
  POST /jobs           → create a new job (write YAML + register)
  DELETE /jobs/{name}  → delete a job (remove YAML + unregister)
  PATCH /jobs/{name}   → update fields (enable/disable, reschedule, etc.)
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import httpx
import yaml
from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from hub_core.central_logger import new_trace_id, trace_event
from pydantic import ValidationError

from config import SchedulerSettings, get_settings
from models import AgentChatRequest, RunSkillInput, SkillDefinition, TelegramSendRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("scheduler")

# Module-level state set in main()
_scheduler: AsyncIOScheduler | None = None
_skills_dir: Path | None = None


async def _run_skill(skill_data: dict) -> None:
    trace_id = new_trace_id()
    try:
        skill = RunSkillInput.model_validate(skill_data)
        settings = get_settings()
    except ValidationError as exc:
        log.error("job.invalid_payload payload=%s error=%s", skill_data, exc)
        trace_event(
            "scheduler.job",
            "job.invalid_payload",
            trace_id=trace_id,
            level="ERROR",
            payload=skill_data,
            error=str(exc),
        )
        return

    log.info("job.trigger name=%s", skill.name)
    trace_event("scheduler.job", "job.trigger", trace_id=trace_id, name=skill.name)
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            trace_event("scheduler.job", "agent.request.start", trace_id=trace_id, name=skill.name)
            resp = await client.post(
                f"{settings.agent_url}/chat",
                json=AgentChatRequest(message=skill.prompt).model_dump(),
            )
            resp.raise_for_status()
            result = resp.text
        log.info("job.result name=%s chars=%d", skill.name, len(result))
        trace_event(
            "scheduler.job",
            "agent.request.ok",
            trace_id=trace_id,
            name=skill.name,
            result_chars=len(result),
        )
    except Exception as exc:
        result = f"[agent error: {exc}]"
        log.error("job.agent_error name=%s error=%s", skill.name, exc)
        trace_event(
            "scheduler.job",
            "agent.request.error",
            trace_id=trace_id,
            level="ERROR",
            name=skill.name,
            error=str(exc),
        )

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            trace_event("scheduler.job", "telegram.notify.start", trace_id=trace_id, name=skill.name)
            await client.post(
                f"{settings.telegram_url}/send",
                json=TelegramSendRequest(text=f"[{skill.name}]\n{result}").model_dump(),
            )
        log.info("job.notified name=%s", skill.name)
        trace_event("scheduler.job", "telegram.notify.ok", trace_id=trace_id, name=skill.name)
    except Exception as exc:
        log.error("job.notify_error name=%s error=%s", skill.name, exc)
        trace_event(
            "scheduler.job",
            "telegram.notify.error",
            trace_id=trace_id,
            level="ERROR",
            name=skill.name,
            error=str(exc),
        )


def _load_skills(skills_dir: Path) -> list[SkillDefinition]:
    skills: list[SkillDefinition] = []
    for path in sorted(skills_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            skill = SkillDefinition.model_validate(data)
            if not skill.enabled:
                log.info("skill.disabled name=%s", skill.name)
                continue
            skills.append(skill)
            log.info("skill.loaded name=%s cron=%s", skill.name, skill.cron)
        except (yaml.YAMLError, ValidationError, TypeError) as exc:
            log.error("skill.parse_error path=%s error=%s", path.name, exc)
    return skills


def _register_skill(scheduler: AsyncIOScheduler, skill: SkillDefinition) -> None:
    parts = skill.cron.strip().split()
    if len(parts) != 5:
        log.error("skill.invalid_cron name=%s cron=%r (need 5 fields)", skill.name, skill.cron)
        return

    minute, hour, day, month, day_of_week = parts
    scheduler.add_job(
        _run_skill,
        "cron",
        args=[RunSkillInput(name=skill.name, prompt=skill.prompt).model_dump()],
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
        timezone=skill.timezone,
        id=skill.name,
        name=skill.name,
        replace_existing=True,
    )
    log.info("job.registered name=%s cron=%r tz=%s", skill.name, skill.cron, skill.timezone)


def _skill_to_job_dict(skill: SkillDefinition) -> dict:
    """Build the job response dict, enriched with runtime state if available."""
    apjob = _scheduler.get_job(skill.name) if _scheduler else None
    next_run = None
    if apjob and apjob.next_run_time:
        next_run = apjob.next_run_time.isoformat()
    return {
        "id": skill.name,
        "name": skill.name,
        "schedule": skill.cron,
        "prompt": skill.prompt,
        "enabled": skill.enabled,
        "timezone": skill.timezone,
        "nextRun": next_run,
        "lastRun": None,
        "consecutiveErrors": 0,
    }


# --- HTTP management handlers ---

async def _http_list_jobs(request: web.Request) -> web.Response:
    sd = _skills_dir or get_settings().skills_dir
    jobs = []
    for path in sorted(sd.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            skill = SkillDefinition.model_validate(data)
            jobs.append(_skill_to_job_dict(skill))
        except Exception as exc:
            log.warning("jobs.list_skip path=%s error=%s", path.name, exc)
    return web.json_response({"jobs": jobs, "path": str(sd)})


async def _http_create_job(request: web.Request) -> web.Response:
    sd = _skills_dir or get_settings().skills_dir
    try:
        data = await request.json()
        skill = SkillDefinition.model_validate(data)
    except (ValidationError, ValueError) as exc:
        return web.json_response({"ok": False, "error": str(exc)}, status=400)

    path = sd / f"{skill.name}.yaml"
    if path.exists():
        return web.json_response({"ok": False, "error": "job already exists"}, status=409)

    path.write_text(
        yaml.dump(skill.model_dump(), allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )
    log.info("job.created name=%s", skill.name)

    if skill.enabled and _scheduler:
        _register_skill(_scheduler, skill)

    return web.json_response({"ok": True, "job": _skill_to_job_dict(skill)}, status=201)


async def _http_delete_job(request: web.Request) -> web.Response:
    sd = _skills_dir or get_settings().skills_dir
    name = request.match_info["name"]
    path = sd / f"{name}.yaml"

    if not path.exists():
        return web.json_response({"ok": False, "error": "not found"}, status=404)

    path.unlink()
    log.info("job.deleted name=%s", name)

    if _scheduler and _scheduler.get_job(name):
        _scheduler.remove_job(name)

    return web.json_response({"ok": True})


async def _http_patch_job(request: web.Request) -> web.Response:
    sd = _skills_dir or get_settings().skills_dir
    name = request.match_info["name"]
    path = sd / f"{name}.yaml"

    if not path.exists():
        return web.json_response({"ok": False, "error": "not found"}, status=404)

    try:
        patch = await request.json()
        existing = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        valid_fields = set(SkillDefinition.model_fields)
        existing.update({k: v for k, v in patch.items() if k in valid_fields})
        skill = SkillDefinition.model_validate(existing)
    except (ValidationError, ValueError) as exc:
        return web.json_response({"ok": False, "error": str(exc)}, status=400)

    path.write_text(
        yaml.dump(skill.model_dump(), allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )
    log.info("job.patched name=%s enabled=%s", skill.name, skill.enabled)

    if _scheduler:
        if skill.enabled:
            _register_skill(_scheduler, skill)
        elif _scheduler.get_job(skill.name):
            _scheduler.remove_job(skill.name)
            log.info("job.disabled name=%s", skill.name)

    return web.json_response({"ok": True, "job": _skill_to_job_dict(skill)})


async def _http_trigger_job(request: web.Request) -> web.Response:
    """Fire a job immediately, outside its cron schedule."""
    sd = _skills_dir or get_settings().skills_dir
    name = request.match_info["name"]
    path = sd / f"{name}.yaml"

    if not path.exists():
        return web.json_response({"ok": False, "error": "not found"}, status=404)

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        skill = SkillDefinition.model_validate(data)
    except (yaml.YAMLError, ValidationError, TypeError) as exc:
        return web.json_response({"ok": False, "error": str(exc)}, status=400)

    asyncio.create_task(_run_skill(RunSkillInput(name=skill.name, prompt=skill.prompt).model_dump()))
    log.info("job.manual_trigger name=%s", name)
    return web.json_response({"ok": True, "triggered": name})


async def _start_http_server(port: int) -> None:
    app = web.Application()
    app.router.add_get("/jobs", _http_list_jobs)
    app.router.add_post("/jobs", _http_create_job)
    app.router.add_delete("/jobs/{name}", _http_delete_job)
    app.router.add_patch("/jobs/{name}", _http_patch_job)
    app.router.add_post("/jobs/{name}/run", _http_trigger_job)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info("scheduler.api.listen port=%d", port)
    trace_event("scheduler.api", "scheduler.api.listen", port=port)


async def main() -> None:
    global _scheduler, _skills_dir

    try:
        settings = get_settings()
    except ValidationError as exc:
        log.error("settings.invalid error=%s", exc)
        trace_event("scheduler.main", "settings.invalid", level="ERROR", error=str(exc))
        return

    if not settings.skills_dir.is_dir():
        log.error("skills_dir.missing path=%s", settings.skills_dir)
        trace_event("scheduler.main", "skills_dir.missing", level="ERROR", path=str(settings.skills_dir))
        return

    _skills_dir = settings.skills_dir

    skills = _load_skills(settings.skills_dir)
    log.info("scheduler.start registered=%d skills_dir=%s", len(skills), settings.skills_dir)
    trace_event(
        "scheduler.main",
        "scheduler.start",
        registered=len(skills),
        skills_dir=str(settings.skills_dir),
    )

    _scheduler = AsyncIOScheduler()
    for skill in skills:
        _register_skill(_scheduler, skill)

    _scheduler.start()
    log.info("scheduler.running")
    trace_event("scheduler.main", "scheduler.running")

    await _start_http_server(settings.api_port)

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
