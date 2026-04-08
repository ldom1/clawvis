# Clawvis — Test documentation

> **Last audit:** 2026-03-27 — Phase 1.3 complete, `bash tests/ci-docker.sh` green.

---

## TLDR — Overview

| Layer | Test count | Tool | Quick command |
|--------|------------|------|---------------|
| E2E Playwright (UI/personas) | 24 (22 pass, 2 skip) | Playwright / Chromium | `bash tests/ci-playwright.sh` |
| Kanban API (Python) | ~40 | pytest | `bash tests/ci-kanban.sh` |
| Hub-Core (Python) | ~60 | pytest | `bash tests/ci-hub-core.sh` |
| Hub frontend (TS/Vite) | lint + build | Vitest / yarn | `bash tests/ci-hub.sh` |
| Skills (Python multi-package) | ~35 | pytest | `bash tests/ci-skills.sh` |
| CLI (Node) | lint + smoke | node --check | `bash tests/ci-cli.sh` |
| Docker smoke (curl + E2E) | 13 curl + 22 E2E | bash + Playwright | `bash tests/ci-docker.sh` |
| **Total orchestrated** | **~170** | | `bash tests/ci-all.sh` |

### What the tests cover

- **Full user journeys (E2E)** — project creation through deletion, Kanban, Quartz memory, chat, i18n settings, health.
- **Kanban API** — CRUD tasks/projects, markdown sync, task split, dependencies, weekly stats, confidence, templates.
- **AI orchestration (Hub-Core)** — model selection, Claude/Gemini/Mistral adapters, RBAC, network policy, system metrics, transcription.
- **Docker infrastructure** — 13 curl checks on all exposed endpoints + full E2E suite on real stack.

### Notable skips

| Test | Reason |
|------|--------|
| `brain-quartz-static.spec.ts` — Brain iframe | Fixme: Brain SPA must wire `#quartz-frame` to quartz-static URLs |
| `chat.spec.ts` — when agent connected | Skip if no AI runtime configured |
| `test_real_providers.py` | Skip if `MAMMOUTH_API_KEY` missing |
| `test_transcriber_real_audio.py` | Skip in CI (real audio unavailable) |

---

## Detail by layer

### 1. E2E Playwright — `tests/playwright/tests/personas/`

Run against live Hub (docker or dev). Each file = one user "persona".
Helper `hub-gate.ts` skips all tests if Hub is unreachable.

---

#### Persona 1 — Onboarding (`onboarding.spec.ts`)

**Suite:** `Persona 1 — onboarding (EN)`

| Test | What it checks |
|------|----------------|
| `home, setup runtime wizard through failed connection test` | Home visible, AI runtime badge "Not configured", system metrics, 4-step wizard, provider selection, API key entry (password), connection test result |
| `AI runtime badge in French` *(FR suite)* | Locale `fr-FR` detected, badge "Non configuré" shown |

---

#### Persona 2 — Kanban lifecycle (`kanban.spec.ts`)

**Suite:** `Persona 2 — Kanban lifecycle`

| Test | What it checks |
|------|----------------|
| `create task, move columns, effort, archive` | Create task, move To Start → In Progress → Done, effort entry, archive with confirm dialog, verification in archive modal |
| `delete task shows confirmation modal` | Modal "Are you sure", cancel (overlay stays open), confirm delete |

---

#### Persona 3 — Project lifecycle (`projects.spec.ts`)

**Suite:** `Persona 3 — project lifecycle`

| Test | What it checks |
|------|----------------|
| `create from home, open project, kanban filter, delete` | Create project (name, description, tags, template), card visible on home, project page (subtitle, avatar), save memory description, kanban filter on project (3 cards expected), delete with confirm, card gone |

---

#### Persona 4 — Brain (`brain.spec.ts`)

**Suite:** `Persona 4 — Brain`

| Test | What it checks |
|------|----------------|
| `memory page, edit page list and save` | `/memory/` loads Quartz iframe, `/memory/edit` lists `.md`, select + comment + save |
| `kanban filter smoke after brain routes` | Kanban board visible after navigation from Brain |
| `dependency graph view on Kanban` | Graph button, `#kanban-graph-wrap` visible, canvas present |

---

#### Persona 5 — Settings (`settings.spec.ts`)

**Suite:** `Persona 5 — Settings`

| Test | What it checks |
|------|----------------|
| `workspace save, instances UI, runtime link, back to hub` | Save `projects_root=/tmp/...`, refresh instance list, navigate to instance, setup runtime link visible, back to hub (`/`) |

---

#### Persona 6 — Chat (`chat.spec.ts`)

**Suite:** `Persona 6 — Chat`

| Test | What it checks |
|------|----------------|
| `header and status bar when runtime not configured` | Chat header visible, status bar present, setup link if not configured |
| `when agent connected, send message and fail on API error reply` *(skip if no runtime)* | Sends "Say OK in one word", waits 45s, response is not an API error |
| `send message shows assistant bubble` | User bubble "hello", assistant bubble appears |
| `Shift+Enter inserts newline in input` | line1 + Shift+Enter + line2 → textarea contains `\n` |

---

#### Persona 7 — Health (`health.spec.ts`)

**Suite:** `Persona 7 — Health`

| Test | What it checks |
|------|----------------|
| `active services count and API smoke` | Service count loaded (≠ "…"), ≥ 1, tooltip present; 7 API endpoints → 200: kanban/tasks, kanban/hub/projects, kanban/stats, chat/status, memory/projects, memory/settings, system.json |

---

#### Persona 8 — Project × Memory × Kanban (`project-memory-kanban.spec.ts`)

**Suite:** `Persona 8 — Project × Memory × Kanban integration` — timeout 240s

| Test | What it checks |
|------|----------------|
| `create task, split, memory refresh, delete subtasks, delete project` | Create project + parent task → split into 3 subtasks (via `window.prompt` override) → verify `SubMem #1/2/3` cards → check `.md` memory if MD sync active → rebuild Quartz if MD sync active → delete 3 subtasks (confirm) → delete project → 404 on kanban + memory API |

> **Note CI Docker:** `_MD_SYNC=False` (kanban_parser absent) → `.md` and Quartz assertions skipped gracefully.

---

#### Persona 9 — Language switching (`language.spec.ts`)

**Suite:** `Persona 9 — Language switching`

| Test | What it checks |
|------|----------------|
| `Settings page renders in French when navigator.language is fr-FR` | Title "Paramètres", "Retour au hub", radio `#lang-fr` checked |
| `Settings page renders in English when navigator.language is en-US` | Title "Settings", "Back to hub", radio `#lang-en` checked |
| `Switching to French persists in localStorage and re-renders` | Click label `fr` → title becomes "Paramètres", `localStorage["clawvis-locale"]="fr"` |
| `Switching to English persists in localStorage and re-renders` | From FR, click `en` → title "Settings", `localStorage["clawvis-locale"]="en"` |
| `localStorage locale overrides navigator.language` | navigator=fr-FR but localStorage=en → English UI |

---

#### Brain — Quartz static (`brain-quartz-static.spec.ts`)

**Suite:** `Brain — Quartz static (styles + install parity)`

| Test | Status | What it checks |
|------|--------|----------------|
| `quartz-static HTML injects base; index.css is served` | ✓ | `<base>` href in HTML, `index.css` reachable > 500 bytes, contains `.page` |
| `quartz-static index.html falls back when Quartz has no root index` | ✓ | Returns 200 with `<base>` tag |
| `nested Quartz page still reaches root index.css` | ✓ | `projects/example-project.html` contains `../index.css`, CSS accessible |
| `Brain iframe triggers successful Quartz stylesheet load` | **FIXME** | Pending Brain SPA wiring to quartz-static |

---

### 2. Kanban API — `kanban/tests/`

Run via `bash tests/ci-kanban.sh` (ruff + pylint + pytest).

---

#### `test_confidence.py`

Pydantic tests for `confidence` field (0–1) on `Task`, `TaskCreate`, `TaskUpdate`.
Cases: null (default None), 0.0, 0.75, 1.0, reject 1.01 / -0.01.
Bonus: `Blocked` status in `STATUSES`, `_check_dependencies` skipped for Blocked.

---

#### `test_md_sync.py`

Integration tests for kanban → markdown file sync.

| Test | What it checks |
|------|----------------|
| `test_update_task_syncs_status_to_markdown` | `PUT /tasks/:id` with source_file → `write_task_to_md` called with correct args |
| `test_update_task_without_source_file_does_not_sync_markdown` | No source_file → no sync |
| `test_split_task_creates_markdown_entry_per_child` | Split parent → `create_task_in_md` called 2× (per child) |
| `test_split_task_skips_md_when_no_project` | Orphan task (no project) → no MD write |

---

#### `test_projects_api.py`

FastAPI endpoint tests (archive/delete project, logo upload/get, delete task).
Mocks core layer; checks HTTP status and response shape.

---

#### `test_sse.py`

| Test | What it checks |
|------|----------------|
| `test_openapi_stream_get` | OpenAPI spec contains GET `/stream` |
| `test_build_state_json_tasks_key` | `_build_state()` → JSON with `tasks` key |

---

#### `test_weekly_stats.py`

| Test | What it checks |
|------|----------------|
| `test_compute_weekly_stats_projects` | Hub project has `active_count=1`, `majority_assignee="DomBot"` |
| `test_compute_weekly_stats_weeks` | `this_week` and `last_week` present, `done ≥ 1` |
| `test_parse_git_log_valid` | Parse `date|message|author` → 2 commits with repo, message, author, date |
| `test_parse_git_log_empty` | Empty input → `[]` |
| `test_majority_assignee_tie_alphabetical` | Tie → alphabetical sort |

---

#### `test_project_templates.py`

| Test | What it checks |
|------|----------------|
| `test_create_project_uses_cookiecutter_when_available` | `cookiecutter` called if available, README.md created |
| `test_create_project_fallback_copy_template` | Fallback copy template, README contains project name |
| `test_archive_project_moves_repo_memory_and_archives_tasks` | Repo + memory moved to `archived/`, tasks marked Archived |
| `test_delete_project_removes_repo_memory_and_tasks` | Repo + memory removed, task removed, deps cleaned |

---

#### `test_memory_major.py`

| Test | What it checks |
|------|----------------|
| `test_parse_major_reads_description_and_aliases` | Parse MD with Description / Objectifs / Stratégie / Objective sections → each extracted |
| `test_update_project_memory_major_roundtrip` | Update then re-read → all sections persisted |

---

#### `test_task_delete.py`

| Test | What it checks |
|------|----------------|
| `test_delete_task_removes_and_cleans_deps` | Delete task-a → task-b deps cleaned (task-c kept) |
| `test_delete_task_missing_raises` | Missing task → `KeyError` |

---

### 3. Hub-Core — `hub-core/tests/`

Run via `bash tests/ci-hub-core.sh` (ruff + pylint + pytest, excluding real_providers and real_audio).

---

#### `test_brain_memory.py`

Active memory selection logic (linked instance vs `MEMORY_ROOT`).

| Test | What it checks |
|------|----------------|
| `test_falls_back_when_no_linked` | No linked instance → `memory_root` used |
| `test_prefers_matching_memory_root` | Instance whose memory folder = `MEMORY_ROOT` wins |
| `test_first_linked_when_no_runtime_match` | No match → first instance (lexicographic sort) |

---

> **Note (V1 cleanup):** suites `test_dynamic_models.py`, `test_chat_runtime.py`, and `test_integration.py` were removed with unused hub-core modules (agent adapters / RBAC network / unused chat proxy). Streaming chat goes through `agent/` service.

#### `test_transcriber.py`

Audio transcription (Whisper).

Covers: missing file → None, `WhisperModel=None` → None, mock model → string, exception → None, `language` and `model_size` params, multiple segments.

---

#### `test_system_metrics.py`

| Test | What it checks |
|------|----------------|
| `test_get_system_stats_returns_dict` | `cpu_percent`, `ram_percent` present |
| `test_cpu_ram_values_in_range` | 0–100 % |
| `test_get_token_stats_returns_dict` | Keys `claude`, `mammouth`, `timestamp` |
| `test_system_metrics_are_fresh` | Two consecutive calls: drift < 20 % |

---

#### Other Hub-Core tests

| File | Focus |
|------|-------|
| `test_main.py` | `main()` returns `HubState`, `get_hub_state` aggregates providers + metrics |
| `test_models.py` | Pydantic serialization round-trip (HubState, ProvidersResponse, StatusResponse) |
| `test_fetch_provider_data.py` | `get_providers_response()` returns `ProvidersResponse` with timestamp |
| `test_update_status.py` | `StatusResponse()` serializes to valid JSON |

---

### 4. Skills — `skills/*/core/tests/`

Run via `bash tests/ci-skills.sh` (auto-discover pyproject.toml).

---

#### `kanban-implementer` — `test_selector.py` and `test_status.py`

| Test | What it checks |
|------|----------------|
| `test_eligible_filters_correctly` | Filter DomBot + To Start/Backlog + effort ≤ 2h |
| `test_select_task_picks_high_priority` | Returns High priority, 1h |
| `test_task_with_low_confidence_not_eligible` | confidence=0.2 → not eligible |
| `test_human_assignee_confidence_effective_is_one` | Human → confidence_effective=1.0 |
| `test_is_ambiguous_vague_word` | "Cleanup old routes" → ambiguous |
| `test_is_ambiguous_clear_title` | "Add retry to POST /tasks" + description → clear |
| `test_update_status_valid` | Status "In Progress" updated in JSON |
| `test_update_status_invalid_status` | "InvalidStatus" → False |
| `test_blocked_status_is_valid` | Status "Blocked" accepted |

---

#### `logger` — `test_models.py`, `test_logger.py`, `test_config.py`, `test_discord_router.py`

| Group | Focus |
|-------|-------|
| Models | Log text format `[ts][level][process][model]action—msg`, metadata |
| Logger | INFO/ERROR/WARNING/DEBUG/CRITICAL levels, JSONL + plaintext `.log`, multi-entries |
| Config | `load_dotenv(override=False)`, trim whitespace, Discord channel mapping |
| Discord | Bot init, `on_ready`, text/private channel creation, channel lookup by name |

---

### 5. CI scripts — `tests/ci-*.sh`

| Script | Steps |
|--------|-------|
| `ci-all.sh` | Sequential orchestrator: kanban → hub-core → hub → playwright → skills → cli |
| `ci-kanban.sh` | ruff + pylint (E,F) + pytest on `kanban/` |
| `ci-hub-core.sh` | ruff + pylint + pytest on `hub-core/` (excluding real_providers) |
| `ci-hub.sh` | corepack + yarn install + format:check + test + build |
| `ci-playwright.sh` | npm ci + playwright install chromium + playwright test --project=chromium |
| `ci-skills.sh` | Auto-discover skills with pyproject.toml → ruff + pylint + pytest per skill |
| `ci-cli.sh` | npm ci + node --check + smoke `--help` |
| `ci-docker.sh` | docker compose up → wait ready → prime projects_root → 13 curl → 22 E2E Playwright |

---

### 6. Additional checks (non-pytest)

| File | Description |
|------|-------------|
| `hub-core/tests/test_hub_integration.py` | Real HTTP smoke against local Hub — dashboard, hub-core imports, config, Pydantic models, JSON state generation |

---

## Running tests

```bash
# Everything (quality + build + E2E)
bash tests/ci-all.sh

# Real Docker stack only (smoke + E2E)
bash tests/ci-docker.sh

# Replay E2E only on already running stack
PLAYWRIGHT_BASE_URL=http://localhost:8088 PW_NO_WEBSERVER=1 \
  npx playwright test --project=chromium --reporter=list \
  --prefix tests/playwright

# Single persona
PLAYWRIGHT_BASE_URL=http://localhost:8088 PW_NO_WEBSERVER=1 CI=true \
  npx playwright test --project=chromium personas/kanban.spec.ts
```
