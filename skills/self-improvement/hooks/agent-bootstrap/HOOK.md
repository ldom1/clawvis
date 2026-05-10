---
name: self-improvement
description: "Injects self-improvement reminder during agent bootstrap"
metadata: {"clawvis":{"events":["agent:bootstrap"]}}
---

# Self-improvement hook (bootstrap)

Injects a short reminder to capture learnings. Your agent runtime must support `agent:bootstrap` (or equivalent) and pass `context.bootstrapFiles` as an array.

## Behaviour

- On bootstrap, append a virtual `SELF_IMPROVEMENT_REMINDER.md` with logging guidance.
- Skip sub-agent sessions when `sessionKey` contains `:subagent:`.

## Install

Copy `hooks/agent-bootstrap/` into the hooks directory your toolchain documents, or follow `references/clawvis-skills.md`.
