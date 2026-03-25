# Clawvis — Playwright Persona Test Guide

This guide defines the full user journeys that Playwright should exercise to verify Clawvis is functional end-to-end. Each persona section maps to a concrete test file.

---

## Setup

```bash
# Install Playwright
npm install -D @playwright/test
npx playwright install chromium

# Run all persona tests
npx playwright test --project=chromium

# Run a single persona
npx playwright test tests/personas/onboarding.spec.ts
```

Base URL: `http://localhost:8088` (or `HUB_PORT` value).

---

## Persona 1 — First-time user: onboarding & AI Runtime setup

**File:** `tests/personas/onboarding.spec.ts`

### Journey

1. **Land on Hub home** (`/`)
   - Assert topbar is visible with Clawvis logo and title
   - Assert AI runtime banner is visible with "Not configured" / "Non configuré" status badge
   - Assert System Status card is visible (CPU, RAM, Disk)
   - Assert Business KPIs row is visible (Projects, Active tasks, Done, Brain notes)
   - Assert "Core tools" section with Kanban, Brain, Chat tiles is visible

2. **Navigate to Setup Runtime** via AI runtime banner CTA
   - Assert URL is `/setup/runtime/`
   - Assert page header contains "Setup · Clawvis" or "Setup · Clawvis"
   - Assert stepper is visible with 4 step circles

3. **Step 1 — Choose provider**
   - Assert 3 provider cards visible: Claude, Mistral, OpenClaw
   - Assert "Next →" button is disabled
   - Click "Claude" card
   - Assert "Next →" button is now enabled

4. **Step 2 — Credentials**
   - Click "Next →"
   - Assert stepper advances to step 2 (circle 2 is active)
   - Assert API key input is visible (`type=password`, placeholder `sk-ant-...`)
   - Assert "Next →" is disabled
   - Type `sk-ant-test-key-00000000`
   - Assert "Next →" is now enabled
   - Click "Next →"

5. **Step 3 — Test gate**
   - Assert stepper is on step 3
   - Assert "Next →" is disabled (no test run yet)
   - Click "Run test" / "Lancer le test"
   - Assert test result is shown (error expected — key is fake)
   - Assert "Next →" remains **disabled** (failed test must not unlock step 4)
   - *(Journey ends here — step 4 mini-chat not tested with fake key)*

---

## Persona 2 — Kanban: full task lifecycle

**File:** `tests/personas/kanban.spec.ts`

### Journey

1. **Open Kanban** (`/kanban/`)
   - Assert page header "Kanban · Clawvis"
   - Assert stats bar visible (total, by status, effort, % done)
   - Assert board columns visible: To Start, In Progress, Done

2. **Create a task**
   - Click "New task" or press `n`
   - Assert create overlay opens
   - Fill: Title = "Test E2E task", Project = first available, Priority = High
   - Click "Create"
   - Assert task card appears in "To Start" column
   - Assert stats bar updates (+1 total)

3. **Move task to In Progress**
   - Find the task card
   - Click the card to open detail modal
   - Assert detail modal shows title, priority, effort fields
   - Change status to "In Progress"
   - Close modal
   - Assert task card is in "In Progress" column

4. **Set confidence/effort on task**
   - Open the task detail again
   - Set effort = 2h
   - Assert effort displayed on card
   - Close modal

5. **Move task to Done**
   - Open task detail
   - Set status = "Done"
   - Close modal
   - Assert task card appears in "Done" column
   - Assert stats bar shows +1 Done, effort remaining decreases

6. **Archive task**
   - Open task detail
   - Click "Archive"
   - Confirm dialog / assert task removed from board
   - Open archive panel
   - Assert task visible in archive with "Done" status

---

## Persona 3 — Projects: full project lifecycle

**File:** `tests/personas/projects.spec.ts`

### Journey

1. **Home page — create a project**
   - Navigate to `/`
   - Assert Projects section visible
   - Click "+" (new project button)
   - Assert modal opens with: Name, Summary, Tags, Template, Stage fields
   - Fill: Name = "E2E Project", Summary = "Testing via Playwright", Tags = ["e2e"]
   - Select Template = "Python FastAPI"
   - Click "Create project"
   - Assert modal closes
   - Assert new project card appears in the projects grid

2. **Open project page**
   - Click the project card
   - Assert project hero shows name "E2E Project"
   - Assert Kanban tasks section visible for this project
   - Assert Brain/Memory notes section visible

3. **Verify project in Kanban**
   - Navigate to `/kanban/`
   - Assert project appears in the CoDir (project list) section
   - Filter board by "E2E Project"
   - Assert board shows only tasks for this project

4. **Delete project**
   - Navigate back to `/project/e2e-project` (or similar slug)
   - Find delete action (kebab menu or settings section)
   - Confirm deletion
   - Assert redirect to home `/`
   - Assert project card no longer visible in the grid

---

## Persona 4 — Brain / Quartz: search and navigation

**File:** `tests/personas/brain.spec.ts`

### Journey

1. **Open Brain** (`/memory/`)
   - Assert Brain page header
   - Assert either:
     - Quartz iframe/embed visible (when `quartz/public/` exists), OR
     - Python-rendered project list visible (fallback)

2. **Navigate to a project note**
   - If Quartz: interact with the Quartz UI to open a page
   - If fallback: click on a project note link
   - Assert note content visible

3. **Edit a project note**
   - Navigate to `/memory/edit`
   - Assert edit page header "Edit Brain · Clawvis"
   - Assert project file list visible (`.md` files)
   - Click on a project file
   - Assert markdown editor loads with content
   - Make a small edit: append a line
   - Click "Save"
   - Assert success feedback visible

4. **Compare with Kanban tasks**
   - Open the Brain note for a project (e.g. via graph or list)
   - Note the task list mentioned in the `.md`
   - Navigate to `/kanban/` and filter by same project
   - Assert task titles overlap (smoke check — no hard assertions on content)

5. **Memory graph**
   - Navigate to `/memory/?view=graph` or the graph subpage
   - Assert graph nodes visible
   - Type a project name in search
   - Assert matching node highlighted or focused

---

## Persona 5 — Settings: workspace, instances, appearance

**File:** `tests/personas/settings.spec.ts`

### Journey

1. **Workspace config**
   - Navigate to `/settings/`
   - Fill "Projects root" with a path (e.g. `/home/user/lab`)
   - Click "Save workspace"
   - Assert "Workspace saved" / "Workspace sauvegardé" feedback

2. **Instance explorer**
   - Assert instances multiselect is visible
   - Click "Refresh"
   - Assert at least one instance option appears (the `example` instance)
   - Select an instance
   - Click "Link selection"
   - Assert success or info feedback

3. **AI Runtime section (no modal)**
   - Assert a link with text matching "Configurer le runtime" / "Configure runtime" is visible
   - Assert the link's `href` attribute is `/setup/runtime/`
   - Assert **no modal overlay is present** (`#ai-wizard-overlay` must not exist in the DOM)

4. **Back to hub**
   - Click "← Back to hub" / "Retour au hub"
   - Assert URL returns to `/`

---

## Persona 6 — Chat: AI runtime validation

**File:** `tests/personas/chat.spec.ts`

### Journey

1. **Open Chat** (`/chat/`)
   - Assert page header "Chat · Clawvis"
   - Assert status bar visible
   - If runtime not configured: assert warn status bar contains a link with `href="/setup/runtime/"` and visible text matching "Configurer le runtime" / "Setup runtime"
   - If configured: assert "Connected" / "Connecté" status

2. **Send a message (unconfigured)**
   - If no provider configured: type "hello" and send
   - Assert response contains a hint about configuring a provider

3. **Send a message (with test key)**
   - Configure Claude with a test key first (reuse Persona 1 setup)
   - Navigate to `/chat/`
   - Type: "What is Clawvis?"
   - Press Enter
   - Assert user bubble appears with "What is Clawvis?"
   - Assert assistant response bubble appears (streaming tokens visible)
   - Assert response is non-empty

4. **Multi-turn conversation**
   - Send a follow-up: "How do I create a project?"
   - Assert history preserved — second user bubble visible
   - Assert second assistant response appears

5. **Keyboard shortcuts**
   - Clear input
   - Type multiline text using Shift+Enter
   - Assert textarea grows
   - Press Enter (without Shift) — assert message sent

---

## Persona 7 — Services health check

**File:** `tests/personas/health.spec.ts`

### Journey

1. **Check active services count** on home page
   - Assert `#active-services-count` is not "0" (at least 1 service up)
   - Hover the count — assert tooltip shows service status

2. **API endpoints smoke test**
   - `GET /api/kanban/tasks` — assert 200
   - `GET /api/kanban/hub/projects` — assert 200
   - `GET /api/kanban/hub/settings` — assert 200
   - `GET /api/kanban/memory/projects` — assert 200
   - `GET /api/kanban/chat/status` — assert 200
   - `GET /api/kanban/stats` — assert 200
   - `GET /api/system.json` — assert 200

---

## Notes for test authors

- **Locale**: Test in both FR (navigator.language = "fr") and EN. Use `page.addInitScript` to mock locale.
- **Fixtures**: Seed a project + a few tasks before running project/kanban tests. Use the Kanban API directly.
- **Cleanup**: Each test should clean up its created data (delete project, archive tasks).
- **CI**: Run with `--reporter=html` to capture screenshots on failure.
- **Timeouts**: Chat streaming can take 5–15s — use `expect(locator).toBeVisible({ timeout: 20000 })`.
