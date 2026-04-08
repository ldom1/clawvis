# Clawvis — Playwright E2E Tests

Persona-driven end-to-end tests covering the critical user journeys of Clawvis.

## Running the tests

```bash
# Against a running hub (auto-starts the stack if no server is detected):
cd tests/playwright && npm ci && npx playwright test --project=chromium

# All browsers:
npx playwright test

# Specific persona:
npx playwright test onboarding.spec.ts

# Via CI script (same as GitHub Actions):
bash tests/ci-playwright.sh
```

Tests automatically **skip** when the Hub is not reachable — they never fail spuriously in offline environments.

## Pre-conditions

| Requirement | Details |
|---|---|
| Hub running | `clawvis start` (Soissons mode) or server at `PLAYWRIGHT_BASE_URL` (default `http://127.0.0.1:8088`) |
| Kanban API | Started by `clawvis start` (port `KANBAN_API_PORT`, default 8090) |
| Memory API | Started by `clawvis start` (port `HUB_MEMORY_API_PORT`, default 8091) |
| Quartz build | Optional — needed only for Brain Quartz tests (`bash scripts/build-quartz.sh`) |

---

## Personas

### Persona 1 — Onboarding & runtime setup
**Files:** `tests/personas/onboarding.spec.ts`, `tests/personas/setup-runtime-stubs.ts`

**User story:** A user lands on the Hub, sees the runtime banner when nothing is configured, opens `/setup/runtime/`, picks **OpenClaw** or **Claude Code**, confirms (POST `/api/hub/setup/provider`), and returns home. Stubs mock `GET /api/hub/agent/config` and `POST /api/hub/setup/provider` so the flow is deterministic.

**Tests (EN):**
- `home, setup runtime wizard — choose Claude and confirm` — Home smoke, opens setup from the banner CTA, selects Claude, asserts POST body and redirect `/`.
- `setup runtime — choose OpenClaw and confirm` — Same for OpenClaw.
- `setup runtime — preselects OpenClaw / Claude from GET /agent/config` — Confirms initial selection from `primary_provider` without clicking a card.
- `setup runtime — user overrides API preselection (OpenClaw → Claude)` — Clicks another provider after the API pre-filled OpenClaw.
- `setup runtime — POST error surfaces in feedback` — 400 from setup/provider shows an error in `#setup-provider-feedback`.
- `setup runtime — Claude stays selected if config arrives late as openclaw` — Regression: user picks Claude before a delayed config response; choice must not be overwritten.

**Tests (FR):**
- `wizard copy and confirm Claude` — `navigator.language` FR, clears `clawvis-locale`, checks headings/copy on `/setup/runtime/`, confirms Claude.
- `AI runtime badge in French` — Home badge shows *Non configuré*.

---

### Persona 2 — Kanban lifecycle
**File:** `tests/personas/kanban.spec.ts`

**User story:** A team member manages tasks on the Kanban board: creates a task, moves it across columns, sets effort, archives it, and verifies the delete confirmation flow.

**Tests:**
- `create task, move columns, effort, archive` — Full CRUD lifecycle: create → move To Start → In Progress → Done → archive → verify in archive overlay.
- `delete task shows confirmation modal` — Verifies the global confirmation modal on delete (cancel keeps task, confirm removes it).

---

### Persona 3 — Project lifecycle
**File:** `tests/personas/projects.spec.ts`

**User story:** A project lead creates a new project from the Hub home page, opens its sheet, saves a description to memory, verifies the Kanban filter, then deletes the project.

**Tests:**
- `create from home, open project, kanban filter, delete` — End-to-end: create project → open project sheet → edit description → save to memory → verify `.md` file via API → filter Kanban by project → delete with confirmation modal. Cleans up via API in `finally` block.

---

### Persona 4 — Brain
**File:** `tests/personas/brain.spec.ts`

**User story:** A knowledge worker navigates to the Brain (memory viewer), selects a memory instance, opens the editor, modifies a project file, and verifies the Kanban graph view.

**Tests:**
- `memory page, edit page list and save` — Opens `/memory/`, checks header and Quartz iframe visibility, navigates to `/memory/edit`, selects a `.md` file, appends a marker line, and saves via the API. Skips if no memory project files exist.
- `kanban filter smoke after brain routes` — Confirms the Kanban board is still accessible after visiting brain routes.
- `dependency graph view on Kanban` — Activates the graph view tab and verifies the canvas element renders.

---

### Brain — Quartz static (technical suite)
**File:** `tests/personas/brain-quartz-static.spec.ts`

**User story:** A developer or operator verifies that the Quartz-built static Brain display is correctly served through the Memory API — with proper `<base>` tag injection, CSS reachability, and iframe stylesheet loading.

> Skips automatically when no Quartz build is present (`quartz/public/`).

**Tests:**
- `quartz-static HTML injects base; index.css is served` — Fetches a Quartz HTML page, checks the injected `<base>` tag points to the correct prefix, and confirms `index.css` is served with valid CSS content including `.page`.
- `quartz-static index.html falls back when Quartz has no root index` — When Quartz only has `README.html` at root, verifies that `/quartz-static/index.html` still resolves (fallback logic in Memory API).
- `nested Quartz page still reaches root index.css` — Fetches a nested page (`projects/example-project.html`) and verifies relative `../index.css` is preserved so it resolves correctly via the base tag.
- `Brain iframe triggers successful Quartz stylesheet load` — Navigates to `/memory/`, waits for the Quartz iframe to load its stylesheet via the API, and verifies the computed font family matches a Quartz theme font.

---

### Persona 5 — Settings
**File:** `tests/personas/settings.spec.ts`

**User story:** An operator opens the Settings page, saves the workspace path, links an instance, confirms the AI runtime configuration link, and returns to the Hub home.

**Tests:**
- `workspace save, instances UI, runtime link, back to hub` — Sets projects root, saves, refreshes instance list, links the first available instance, confirms the `/setup/runtime/` link is visible, and clicks back to home.

---

### Persona 6 — Chat
**File:** `tests/personas/chat.spec.ts`

**User story:** A user opens the Chat page and either interacts with the AI assistant (when backend key is configured) or sees a clear prompt to configure the runtime.

**Tests:**
- `header and status bar when runtime not configured` — Verifies the Chat header, status bar, and the setup link when no server key is set.
- `when agent connected, send message and fail on API error reply` — Sends a probe message and verifies the assistant reply is not an API error string. Skips if no backend key is configured or provider returns an error.
- `send message shows assistant bubble` — Sends "hello" and confirms an assistant bubble appears with non-empty content.
- `Shift+Enter inserts newline in input` — Verifies keyboard UX: Shift+Enter inserts a newline without submitting.

---

### Persona 7 — Health
**File:** `tests/personas/health.spec.ts`

**User story:** An operator verifies that all core APIs are responding and the active-services counter on the home page reflects the real stack state.

**Tests:**
- `active services count and API smoke` — Reads the active-services count widget, verifies it is ≥ 1 with a tooltip, then hits all 7 core API endpoints (`/api/hub/kanban/*`, `/api/hub/chat/status`, `/api/hub/memory/*`, `/api/system.json`) and asserts HTTP 200.

---

### Persona 8 — Project × Memory × Kanban integration
**File:** `tests/personas/project-memory-kanban.spec.ts`

**User story:** A lead creates a project, adds a parent task, splits it into 3 subtasks, triggers a Brain rebuild, verifies the memory `.md` is updated, deletes the subtasks, verifies Kanban cleanup, then deletes the project and confirms both the API and memory file return 404.

**Tests:**
- `create task, split, memory refresh, delete subtasks, delete project` — Full integration: project create → task create → split (3 subtasks) → Brain rebuild via `POST /api/hub/memory/brain/rebuild-static` → poll memory API until subtask names appear in `.md` → delete subtasks with confirmation → delete project → verify 404 on both project and memory endpoints. Timeout: 240s.

---

## Test architecture

```
tests/playwright/
  tests/personas/
    hub-gate.ts                    # registerHubGate() — skips suite when Hub is unreachable
    setup-runtime-stubs.ts         # Mock GET agent/config + POST setup/provider for onboarding tests
    onboarding.spec.ts             # Persona 1
    kanban.spec.ts                 # Persona 2
    projects.spec.ts               # Persona 3
    brain.spec.ts                  # Persona 4
    brain-quartz-static.spec.ts    # Brain Quartz technical suite
    settings.spec.ts               # Persona 5
    chat.spec.ts                   # Persona 6
    health.spec.ts                 # Persona 7
    project-memory-kanban.spec.ts  # Persona 8
  playwright.config.ts             # webServer: auto-starts start-for-e2e.sh in CI
  package.json
```

### Hub gate

Every spec file calls `registerHubGate()` at the top. This registers a `beforeAll` that probes `GET /` and a `beforeEach` that calls `test.skip(true)` when the Hub is unreachable — ensuring tests never fail spuriously in offline or partial-stack environments.

The Quartz technical suite adds a second gate via `skipIfNoQuartz()` inside each test, skipping when `GET /api/hub/memory/quartz` returns no files with `source: "quartz"`.
