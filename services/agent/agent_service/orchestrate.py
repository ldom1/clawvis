"""Two-phase: LLM JSON plan, then agent POSTs to Kanban (works with CLI or API models)."""
from __future__ import annotations

import json
import re
from typing import Any

import httpx
from hub_core.central_logger import trace_event

from agent_service import llm_sync
from agent_service.kanban_client import create_task, fetch_projects
from agent_service.provider import ProviderConfig


def _normalize_provider_str(v: str) -> str:
    s = (v or "").strip().lower()
    if not s:
        return "anthropic"
    if s in ("anthropic", "claude"):
        return "anthropic"
    if s in ("mammouth", "mistral", "mammoth", "openrouter"):
        return "openrouter"
    if s in ("cli", "claude-code", "opencode", "codex"):
        return "cli"
    return s


def _effective_provider(conf: dict, cfg: ProviderConfig) -> str:
    if cfg.primary_from_env:
        return cfg.provider
    pp = conf.get("preferred_provider")
    if pp:
        return _normalize_provider_str(str(pp))
    return cfg.provider


def _lane_provider(conf: dict, cfg: ProviderConfig, key: str) -> str:
    lane = conf.get(key)
    if not lane:
        return _effective_provider(conf, cfg)
    c = dict(conf)
    c["preferred_provider"] = lane
    return _effective_provider(c, cfg)


def _provider_available(name: str, cfg: ProviderConfig) -> bool:
    if name == "cli":
        return cfg.cli_available
    if name == "anthropic":
        return bool(cfg.anthropic_token)
    if name == "mammouth":
        return bool(cfg.mammouth_token)
    return False


def _resolve_provider_for_task(preferred: str, cfg: ProviderConfig) -> str:
    order = [preferred, "cli", "mammouth", "anthropic"]
    seen: set[str] = set()
    for p in order:
        if p in seen:
            continue
        seen.add(p)
        if _provider_available(p, cfg):
            return p
    return preferred

_TASK_INTENT = re.compile(
    r"(?is).*\b(create|add|new|créer|creer|ajouter|nouvelle?|nouveau)\b.{0,160}\b(task|tâche|tache)\b|"
    r".*\b(task|tâche|tache)\b.{0,100}\b(for|dans|pour|in)\b.{0,40}\b(project|projet)\b|"
    r".*\b(nouveau|new)\b.{0,40}\b(projet|project)\b.{0,80}\b(task|tâche|tache)\b",
)

_PLAN_SYSTEM = (
    "You are the Clawvis task planner. The user may write in English or French. "
    "You must respond with a single JSON object only (no markdown fences). Schema:\n"
    '{"should_create": boolean, "project_slug": string, "title": string, '
    '"description": string, "reason": string}\n'
    "Rules:\n"
    "- If the user wants to add/create a task in a project, set should_create true and fill title (short), "
    "description (optional), project_slug (must be one of the listed slugs).\n"
    "- If the user message is not clearly a task to create, or the project cannot be matched, set should_create false "
    "and explain in reason (one sentence).\n"
    "- project_slug must be exactly one of the slugs listed under Projects; never invent slugs.\n"
)


def _looks_like_task_intent(message: str) -> bool:
    t = (message or "").strip()
    if len(t) < 8:
        return False
    return bool(_TASK_INTENT.search(t))


def _extract_json_obj(raw: str) -> dict[str, Any] | None:
    s = (raw or "").strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", s)
    if m:
        s = m.group(1).strip()
    a = s.find("{")
    b = s.rfind("}")
    if a < 0 or b <= a:
        return None
    try:
        out = json.loads(s[a : b + 1])
        return out if isinstance(out, dict) else None
    except json.JSONDecodeError:
        return None


def _format_projects(data: dict[str, Any]) -> tuple[str, set[str]]:
    projects = data.get("projects") or []
    lines: list[str] = []
    slugs: set[str] = set()
    for p in projects:
        if not isinstance(p, dict):
            continue
        slug = str(p.get("slug") or "").strip()
        name = str(p.get("name") or slug).strip()
        if slug:
            slugs.add(slug)
            lines.append(f"- {slug} — {name}")
    if not lines:
        return "(no projects — ask the user to create a project in the Hub first.)", set()
    return "\n".join(lines), slugs


async def maybe_orchestrate_task_creation(
    message: str,
    *,
    trace_id: str | None,
    cfg: ProviderConfig,
    conf: dict,
    system: str,
    preferred_model: str,
    use_cli: bool,
    use_anthropic: bool,
    use_mammouth: bool,
) -> str | None:
    if not _looks_like_task_intent(message):
        return None

    trace_event("agent.orchestrate", "orchestrate.start", trace_id=trace_id, message_len=len(message))

    try:
        pdata = await fetch_projects()
    except (httpx.HTTPError, OSError) as e:
        trace_event("agent.orchestrate", "kanban.get_projects.fail", trace_id=trace_id, level="WARNING", error=str(e))
        return (
            "Kanban is unreachable from the agent right now, so the task was not created. "
            f"Error: {e!s}. Check KANBAN_URL and that kanban-api is running."
        )

    list_text, slugs = _format_projects(pdata)
    trace_event("agent.orchestrate", "kanban.get_projects.ok", trace_id=trace_id, project_count=len(slugs))

    user_block = f"User message:\n{message}\n\nProjects (slug — name):\n{list_text}"

    plan_sys = f"{(system or '').strip()}\n\n{_PLAN_SYSTEM}"

    if use_cli and cfg.cli_available:
        raw = await llm_sync.complete_cli(user_block, plan_sys, model=preferred_model)
    elif use_anthropic and cfg.anthropic_token:
        raw = await llm_sync.complete_anthropic(
            plan_sys, user_block, cfg.anthropic_token, model=preferred_model
        )
    elif use_mammouth and cfg.mammouth_token:
        raw = await llm_sync.complete_openai_compat(
            plan_sys,
            user_block,
            cfg.mammouth_token,
            cfg.mammouth_base_url,
            model=preferred_model,
        )
    else:
        trace_event("agent.orchestrate", "orchestrate.skip.no_llm", trace_id=trace_id)
        return (
            "No LLM is configured for the planning step, so the task was not created. "
            "Set ANTHROPIC_API_KEY or OPENROUTER_API_KEY, or use provider=cli with a working CLI."
        )

    if not (raw or "").strip():
        trace_event("agent.orchestrate", "orchestrate.empty_llm_response", trace_id=trace_id, level="WARNING")
        return (
            "The planner returned an empty response; task was not created. "
            "If you use provider=cli: run `claude` in a terminal and ensure login works; "
            "check agent logs. For API providers, verify the model returned text (not only tool calls)."
        )

    if raw.strip().startswith("[CLAWVIS:HTTP:") or raw.strip().startswith("[CLAWVIS:empty-content:"):
        return raw.strip()

    plan = _extract_json_obj(raw)
    if not plan:
        trace_event("agent.orchestrate", "orchestrate.bad_json", trace_id=trace_id, level="WARNING", raw_head=(raw or "")[:200])
        return "Could not parse a JSON plan from the model; task was not created."

    should = bool(plan.get("should_create"))
    reason = str(plan.get("reason") or "").strip()
    title = str(plan.get("title") or "").strip()
    descrip = str(plan.get("description") or "").strip()
    slug = str(plan.get("project_slug") or "").strip()

    if not should:
        trace_event("agent.orchestrate", "orchestrate.declined", trace_id=trace_id, reason=reason[:120])
        return reason or "No task was created (the planner could not match this to a new task)."

    if not title:
        return "The plan was missing a title; task was not created."

    if not slug or slug not in slugs:
        trace_event("agent.orchestrate", "orchestrate.bad_slug", trace_id=trace_id, slug=slug)
        return (
            f"Project slug {slug!r} is not in the current Hub project list. "
            "Check the name or add the project in the Hub. Task was not created."
        )

    try:
        task = await create_task(title=title, project=slug, description=descrip)
    except (httpx.HTTPError, OSError) as e:
        trace_event("agent.orchestrate", "kanban.create_task.fail", trace_id=trace_id, level="ERROR", error=str(e))
        return f"Could not create the task in Kanban: {e!s}"

    tid = str(task.get("id") or "")
    trace_event("agent.orchestrate", "kanban.create_task.ok", trace_id=trace_id, task_id=tid, project=slug)
    return f"Created task {tid or '(no id)'}: {title} (project: {slug})"


async def run_orchestrate_or_none(
    message: str,
    cfg: ProviderConfig,
    conf: dict,
    system: str,
    anthropic_model: str,
    mammouth_model: str,
    trace_id: str | None = None,
) -> str | None:
    eff = _resolve_provider_for_task(
        _lane_provider(conf, cfg, "task_preferred_provider"), cfg
    )
    use_cli = eff == "cli" and cfg.cli_available
    use_anthropic = eff == "anthropic" and bool(cfg.anthropic_token)
    use_mammouth = eff == "mammouth" and bool(cfg.mammouth_token)
    preferred_model = str(
        conf.get("task_preferred_model") or anthropic_model or mammouth_model
    )
    return await maybe_orchestrate_task_creation(
        message,
        trace_id=trace_id,
        cfg=cfg,
        conf=conf,
        system=system,
        preferred_model=preferred_model,
        use_cli=use_cli,
        use_anthropic=use_anthropic,
        use_mammouth=use_mammouth,
    )
