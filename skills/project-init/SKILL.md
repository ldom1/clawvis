---
name: project-init
description: "Initialise un projet Lab + Kanban : API POST /hub/projects, structure repo (template), fiche mémoire PARA. Use when Ldom demande de créer un projet depuis une idée (vocal/texte)."
---

# Project Init

<<<<<<< HEAD
## Rôle

Créer un projet **clôt côté Hub** : dépôt sous `PROJECTS_ROOT`, mémoire `memory/projects/<slug>.md`, tâches initiales via l’API Kanban.

## Exécution rapide

```bash
# Description (obligatoire), nom affiché optionnel
~/.openclaw/skills/project-init/scripts/init.sh "Description du projet (≥3 caractères)" "Nom lisible"

# Variables optionnelles
export KANBAN_API_URL=http://127.0.0.1:8090
export KANBAN_API_KEY=   # si l’API est protégée
```

Le script appelle `POST /hub/projects` (serveur Kanban Clawvis). Le slug est **dérivé** du nom par l’API.

## Après création

1. Notifier Ldom (Telegram) avec le lien Hub `/hub/project/<slug>`.
2. `dombot-log` niveau INFO si tu ajoutes une action dédiée `project:create` (sinon logs API Kanban suffisent).
3. Optionnel : ouvrir une PR README ou premier PoC selon `PROTOCOL.md`.

## Liens

- Kanban : `GOAL.md` scénario « Initialisation »
- API : `kanban_api` — `ProjectCreate` (`description`, `name`, `stage`, `template`, …)
=======
Creates a complete project from a single voice note or text idea.

## Quick run

```bash
# From text
uv run --directory ~/.openclaw/skills/project-init/core python -m project_init \
  --slug "my-project" \
  --name "My Project" \
  --description "A SaaS to automate freelance quotes with AI"

# Check what would be created (dry-run)
uv run --directory ~/.openclaw/skills/project-init/core python -m project_init \
  --slug "my-project" --name "My Project" --description "..." --dry-run
```

---

## Workflow (execute in order)

### Step 1 — Parse input

If the input is a **voice note**: transcribe it first with `hub_core transcribe <file>`.

Extract from the text:
- **slug**: short kebab-case identifier (e.g. `devis-ai`) — no spaces, no accents
- **name**: display name
- **description**: one sentence, the problem being solved
- **tech_stack** (optional): preferred technology if mentioned, otherwise `auto`

### Step 2 — Create project + tasks

```bash
uv run --directory ~/.openclaw/skills/project-init/core python -m project_init \
  --slug "<slug>" --name "<name>" --description "<description>"
```

This script:
1. POSTs the project to the Kanban API (`POST /api/hub/kanban/projects`)
2. Writes the Brain note to `$MEMORY_ROOT/projects/<slug>.md` (PARA format)
3. Prints `PROJECT_SLUG=<slug>` and `PROJECT_URL=<hub_url>/project/<slug>`

### Step 3 — Generate initial kanban tasks

With the project context loaded, generate 5–10 initial tasks covering:
- Discovery / specs (1–2 tasks)
- Core implementation (3–5 tasks)
- Testing + delivery (1–2 tasks)

For each task, POST to Kanban API:
```
POST /api/hub/kanban/tasks
{
  "title": "...",
  "project": "<slug>",
  "status": "To Start",
  "priority": "High|Medium|Low",
  "effort_hours": <float>,
  "assignee": "DomBot",
  "description": "..."
}
```

### Step 4 — (Optional) Create GitHub repo

If `GITHUB_TOKEN` is set and `GITHUB_USER` is configured:
- Create a private repo named `<slug>` via GitHub API
- Add link to Brain note

### Step 5 — PoC scaffold (optional, if requested)

Generate a minimal working scaffold in `$LAB/<slug>/` using the chosen tech stack.
Keep it under 100 lines — goal is a runnable skeleton, not a full implementation.

### Step 6 — Notify

**Telegram:**
```
"Projet '<name>' créé ✅ — PoC disponible sur <HUB_URL>/project/<slug>"
```

**Discord `#projects`** (via logger skill):
```
[project-init] <name> — <N> tâches créées — PoC généré — <HUB_URL>/project/<slug>
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `KANBAN_API_URL` | `http://localhost:8088/api/hub/kanban` | Kanban API base URL |
| `HUB_URL` | `http://localhost:8088` | Hub public URL (used in messages) |
| `MEMORY_ROOT` | `~/.openclaw/workspace/memory` | Path to instance memory root |
| `GITHUB_TOKEN` | _(empty)_ | GitHub PAT — repo creation skipped if absent |
| `GITHUB_USER` | _(empty)_ | GitHub username or org |
| `TELEGRAM_TARGET` | _(empty)_ | Telegram user ID for confirmation message |

---

## Invariants

- **Slug is the single key** — project slug == Brain note filename == kanban project key
- **Brain note is created even without GitHub** — memory is always set up
- **Tasks start as `To Start`** — ready for `kanban-implementer` on first run
- **One Telegram message max** — no per-task messages
- **PoC is optional** — skip if not explicitly requested or if unclear
>>>>>>> 6d193cb (feat(core): audit and rationalization of the code)
