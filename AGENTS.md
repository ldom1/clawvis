# AGENTS.md

Project-level agent guidance for Clawvis.

## Working rules

- Prefer direct inspection of code, tests, and docs in this repo over external indexing layers.
- Keep changes local to the requested scope; avoid opportunistic refactors unless they unblock the fix.
- Update documentation when behavior, workflow, setup, or visible UI changes.
- Verify the affected commands/tests before claiming a fix is complete.

## Architecture contract

- Keep architecture docs aligned with the current stack: `hub`, `kanban-api`, `hub-memory-api`, `agent-service`, `telegram`, `scheduler`, `skills`.
- Treat Clawvis default surface as: **hub + brain + agent + skills + telegram + scheduler (cron)**.
- Remove/avoid OpenClaw linkage in default product docs and setup narratives unless explicitly requested for optional integrations.
- Preserve Claude CLI execution support in runtime paths so Clawvis can run user-requested Claude tasks.