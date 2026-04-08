# DATA MODEL

> Clawvis reference data model. Formalizes states, lifecycles, and configurable parameters.
> All implementations must conform.
> For workflows that use these states → `docs/GOAL.md`

---

## Kanban states

Exhaustive ordered list of task statuses:

| Status | Meaning | Allowed transitions |
|--------|---------|---------------------|
| `Backlog` | Task identified, not prioritized | → `To Start` |
| `To Start` | Ready for @Dombot to work | → `In Progress`, → `Backlog` |
| `In Progress` | Task being implemented | → `Done`, → `Blocked` |
| `Blocked` | Blocked — human escalation required | → `To Start`, → `Backlog` |
| `Done` | Completed and validated | → (terminal) |

**Transition rules:**
- Only `kanban-implementer` may move a task from `To Start` to `In Progress`
- Only @Ldom (or Clawvis chat) may move a task from `Backlog` to `To Start`
- A `Blocked` task always generates a Telegram message to @Ldom
- `Done` is terminal — no rollback (create a new task if needed)

---

## Project lifecycle

```
draft ──────────────────────────────────────────► archived
  │                                                   ▲
  │ (@Ldom validation)                                │
  ▼                                           (morning-briefing suggest)
active ◄──► backlog                                   │
  │                                                   │
  └──────────────────────────────────────────────────►┘
       (@Ldom decision)
```

| Status | Meaning | Visible in Hub | Eligible for `kanban-implementer` |
|--------|---------|----------------|-------------------------------------|
| `draft` | Unvalidated opportunity — from `proactive-innovation` | ❌ dedicated view | ❌ |
| `active` | Project in progress | ✅ | ✅ |
| `backlog` | Project paused | ✅ reduced, no tasks | ❌ |
| `archived` | Finished or abandoned project | ❌ | ❌ |

**Transition rules:**
- `draft` → `active`: explicit @Ldom validation only
- `active` → `backlog`: @Ldom decision (via chat or morning-briefing)
- `backlog` → `active`: @Ldom decision only
- `* → archived`: always suggested by `morning-briefing`, never applied automatically

---

## Configurable parameters

Live in `hub_settings.json` unless stated otherwise.

| Parameter | Default | Scope | Location | Description |
|-----------|---------|-------|----------|-------------|
| `max_in_progress` | `2` | global | `hub_settings.json` | Max simultaneous `In Progress` tasks per project |
| `kanban_cron_interval` | `4h` | global | `.env` (OpenClaw) | `kanban-implementer` cron frequency |
| `briefing_time` | `08:00` | global | `.env` (OpenClaw) | `morning-briefing` trigger time |
| `innovation_cron_interval` | `7d` | global | `.env` (OpenClaw) | `proactive-innovation` cron frequency |
| `weekly_review_day` | `friday` | global | `.env` (OpenClaw) | Weekly `knowledge-consolidator` day |
| `inactivity_threshold_days` | `14` | global | `hub_settings.json` | Days without activity before archive suggestion |
| `telegram_notifications` | `true` | global | `hub_settings.json` | Enable/disable Telegram (useful in dev) |
| `discord_channels` | see below | global | `hub_settings.json` | Discord channel mapping by log type |
| `github_repo_visibility` | `private` | per project | `hub_settings.json` | Repo visibility created by `project-init` |
| `poc_auto_generate` | `true` | per project | `hub_settings.json` | Auto PoC generation on `project-init` |

### Default Discord mapping

```json
{
  "discord_channels": {
    "innovation": "#innovation",
    "projects":   "#projects",
    "logs":       "#logs",
    "ops":        "#ops"
  }
}
```

| Channel | Content |
|---------|---------|
| `#innovation` | `proactive-innovation` briefs, detected opportunities |
| `#projects` | Project creation, PoC merge, weekly review |
| `#logs` | Per-task implementation logs, GitHub diffs |
| `#ops` | System metrics, `morning-briefing` reorientations, cron errors |

---

## Brain page structure (PARA format)

Every project page in the Brain follows this schema. File: `memory/projects/<slug>.md`.

```markdown
# [project-name]

## Context
Why this project exists. Problem addressed. Origin (voice, proactive innovation, reuse...).

## Objective
What the project must deliver (PoC, MVP, OSS lib...).

## Decisions
- [DATE] Tech choice: React + FastAPI — reason: consistency with devis-ai
- [DATE] Reuse: invoice-parser v0.3 — no need to reimplement parsing

## Resources
- GitHub repo: [link]
- PoC: [link]
- Related projects: [parent-slug-1], [parent-slug-2]

## Archive
History of dropped decisions, resolved blockages, archived tasks.
```

**Rules:**
- The `Decisions` section is **append-only** — never rewritten retroactively, always dated
- `knowledge-consolidator` enriches `Resources` and `Archive`
- `brain-maintenance` checks file structure without changing content
- `project-init` and `proactive-innovation` create the page with this full schema

---

## Project identity — canonical key

```
project_slug == memory_page_slug == kanban_project_key
```

A project that violates this (divergent slug between kanban and memory) is invalid. `brain-maintenance` can detect and report these inconsistencies.
