Scheduler definition examples (reference only).

Live definitions are loaded from:
- `services/scheduler/definitions/jobs/*.yaml`
- `services/scheduler/definitions/workflows/*.yaml`

Use these examples as copy/paste starters:
- `example-job.yaml` — agent job (`prompt` → `POST …/chat`)
- `example-workflow.yaml`
- Shell cron jobs: set `command` (bash snippet, cwd = `CLAWVIS_ROOT`) instead of asking the agent to “run a skill by name”. See live `jobs/hub-refresh.yaml` and `jobs/morning-briefing.yaml`.
