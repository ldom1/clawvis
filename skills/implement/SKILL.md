---
name: implement
description: "Execute a single kanban task selected by kanban-implementer. Reads the task context + Brain note, implements the change, updates task status. Called by kanban-implementer, never standalone. Use when: kanban-implementer has selected a task and passes TASK_ID + context."
---

# Implement

Executes one kanban task end-to-end. Called by `kanban-implementer` after task selection.

## Quick run

```bash
# Implement a specific task
uv run --directory ~/.openclaw/skills/implement/core python -m implement \
  --task-id task-XXXXXXXX

# Mark task done after implementation
uv run --directory ~/.openclaw/skills/implement/core python -m implement \
  --task-id task-XXXXXXXX --mark-done
```

---

## Workflow

### Step 1 — Load context

```bash
uv run --directory ~/.openclaw/skills/implement/core python -m implement \
  --task-id <TASK_ID>
```

This prints:
- `TASK_TITLE`, `TASK_DESCRIPTION`, `TASK_PROJECT`, `TASK_EFFORT`
- `BRAIN_NOTE` — path to the project Brain note
- `BRAIN_CONTENT` — full content of the Brain note (context for implementation)

### Step 2 — Read the Brain

The Brain note at `BRAIN_NOTE` contains project context, decisions, and previous work. **Always read it before implementing.**

Key sections to use:
- **Contexte / Objectif** — what the project is solving
- **Archive** — past decisions, avoid re-doing what's already done
- **Ressources** — existing components to reuse

### Step 3 — Implement

Implement the task following `PROTOCOL.md` rules:
- Use `uv` for Python, `npm`/`yarn` for JS
- Write tests alongside the code
- Keep changes minimal and focused on the task
- Commit with semantic message: `feat(<scope>): <what>` / `fix(<scope>): <what>`

### Step 4 — Update Brain note

If implementation introduces a new decision or component, append to the **Archive** section of the Brain note.

### Step 5 — Update task status

```bash
# Mark In Progress at start (optional, for long tasks)
uv run --directory ~/.openclaw/skills/implement/core python -m implement \
  --task-id <TASK_ID> --set-status "In Progress"

# Mark Done when complete
uv run --directory ~/.openclaw/skills/implement/core python -m implement \
  --task-id <TASK_ID> --mark-done
```

### Step 6 — Log to Discord

Via logger skill:
```
[implement] <project> — <task title> done — <N> lines changed
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `KANBAN_API_URL` | `http://localhost:8088/api/hub/kanban` | Kanban API base URL |
| `MEMORY_ROOT` | `~/.openclaw/workspace/memory` | Path to instance memory root |

---

## Invariants

- **One task per session.** Never implement more than one task per `implement` call.
- **Brain first.** Always read the Brain note before writing code.
- **Status discipline.** Task must be `Done` before logging completion.
- **No Telegram.** `kanban-implementer` sends the session summary — `implement` only logs to Discord.
