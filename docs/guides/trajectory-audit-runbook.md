# Trajectory Audit Runbook

Centralized message trajectory logs are written to `CENTRAL_LOG_FILE` (default: `logs/message-trajectory.jsonl`).

## Event Schema

Each line is one JSON object:

- `ts`: UTC timestamp (ISO-8601)
- `level`: log level (`INFO`, `WARNING`, `ERROR`, ...)
- `component`: service/component name (`telegram.bot`, `telegram.bridge`, `agent.router`, `agent.orchestrate`, `kanban.api`)
- `event`: canonical event key
- `trace_id`: correlation id for one end-to-end user flow
- `...`: event-specific metadata

## Expected Event Sequence (Telegram task request)

1. `telegram.bot` -> `message.received`
2. `telegram.bridge` -> `agent.request.start`
3. `agent.router` -> `chat.received`
4. `agent.orchestrate` -> `orchestrate.start`
5. `agent.orchestrate` -> `kanban.get_projects.ok` (or `.fail`)
6. `agent.orchestrate` -> `kanban.create_task.ok` (or `.fail`)
7. `agent.router` -> `chat.orchestrated.reply`
8. `telegram.bridge` -> `agent.request.ok` (or `.http_error` / `.network_error`)
9. `telegram.bot` -> `message.replied` (or `message.agent_error`)

## Quick Audit Commands

```bash
rg "\"trace_id\":\"<TRACE_ID>\"" logs/message-trajectory.jsonl
```

```bash
rg "\"event\":\"kanban.create_task" logs/message-trajectory.jsonl
```

```bash
rg "\"level\":\"ERROR\"" logs/message-trajectory.jsonl
```

## Triage Rules

- If no `agent.router chat.received`: Telegram did not reach Agent.
- If no `agent.orchestrate orchestrate.start`: request was routed to non-orchestration chat path.
- If `kanban.get_projects.fail`: check `KANBAN_URL` and `kanban-api` health.
- If `kanban.create_task.fail`: inspect returned error metadata and Kanban API logs.
- If Agent is successful but Telegram returns error: inspect `telegram.bridge agent.request.*` events.
