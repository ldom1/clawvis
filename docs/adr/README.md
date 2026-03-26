# Architecture Decision Records

ADRs document significant architectural decisions: why they were made, what alternatives were considered, and what consequences follow.

## Format

```markdown
# NNNN — Title

## Status
Accepted | Superseded by [NNNN](./NNNN-title.md)

## Context
Why this decision was needed.

## Decision
What was decided.

## Alternatives considered
What else was evaluated and why it was rejected.

## Consequences
What changes as a result.
```

## Adding an ADR

1. Pick the next number (`ls docs/adr/ | tail -1`)
2. Copy the format above into `docs/adr/NNNN-short-title.md`
3. Commit as `update(docs): add ADR NNNN — <title>`

## Index

| # | Title | Status |
|---|-------|--------|
| [0001](./0001-docker-as-default-mode.md) | Docker as default install mode (Franc) | Accepted |
| [0002](./0002-instance-scoped-memory.md) | Instance-scoped memory separation | Accepted |
