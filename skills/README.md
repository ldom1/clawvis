# skills

Pre-configured OpenClaw skills for Clawvis. Register them via `clawvis skills sync` — adds this directory to `skills.load.extraDirs` in your OpenClaw config (no symlinks required).

| Skill | Trigger | Role |
|-------|---------|------|
| `project-init` | Event (voice/text) | Create project: slug, Brain note (PARA), kanban tasks, optional GitHub repo |
| `implement` | Called by `kanban-implementer` | Execute one kanban task: read Brain, implement, update status |
| `kanban-implementer` | Cron (4h) | Select next task, orchestrate session → delegate to `implement` |
| `morning-briefing` | Cron (08:00) | Daily brief → Telegram: projects status, tech news, system health |
| `proactive-innovation` | Cron (weekly) | Scan projects for opportunities → Discord `#innovation` + draft project |
| `knowledge-consolidator` | Cron (weekly) | Synthesize completed tasks and decisions into `MEMORY.md` |
| `brain-maintenance` | Background | Keep the Brain (L1/L2/L3 memory hierarchy) healthy on disk |
| `git-sync` | Post-validation | Push workspace + skills to the backup repo without committing secrets |
| `logger` | Post-action | Structure and route logs to Discord by channel (`#projects`, `#logs`, `#ops`) |
| `qmd` | Memory writes | Local semantic search (BM25 + embeddings) for Brain read/write |
| `skill-tester` | CI / manual | Run all skill unit tests, report pass/fail |
| `reverse-prompt` | Manual | Derive prompts from observed agent behaviour |
