# 0002 — Instance-scoped memory separation

## Status
Accepted

## Context
Multiple users or deployments of Clawvis must be able to coexist in the same repository without overwriting each other's data. Early versions stored memory at the repo root (`memory/`), which created conflicts on updates and made it impossible to safely pull upstream changes.

## Decision
All runtime data (memory, secrets, overrides) lives under `instances/<instance_name>/`. The core repo (`hub/`, `kanban/`, `hub-core/`, `scripts/`) is never modified by user data.

- `instances/example/` is the template, tracked in git and whitelisted in `.gitignore`
- User instances (`instances/<name>/`) are gitignored
- `MEMORY_ROOT` always resolves to `instances/<name>/memory`
- Kanban project slugs are bound to memory page slugs (`projects/<slug>.md`)

## Alternatives considered

- **Shared root memory:** Rejected — breaks on `git pull`, leaks user data into git history if accidentally committed.
- **Separate git repository per instance:** Rejected — too much operational overhead for a self-hosted tool.
- **Database-backed memory:** Rejected for V1 — markdown files are human-readable, portable, and work with Logseq/Quartz out of the box.

## Consequences
- `install.sh` renames `instances/example/` to `instances/<name>/` on first install.
- Core updates (`clawvis update --tag`) never touch `instances/`.
- Multiple linked instances can be browsed from the Hub Brain via `linked_instances` in `hub_settings.json`.
- The active brain memory root is resolved dynamically — see `hub_core.brain_memory.active_brain_memory_root`.
