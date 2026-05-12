# Self-Improvement Core

Python package for the Self-Improvement Review cron agent.

## Setup

```bash
cd core && uv sync
```

## Run

```bash
# Review mode (default)
uv run python -m self_improvment

# Protocol audit mode
uv run python -m self_improvment protocol_audit
```

## Quality

```bash
uv run pytest tests/
uv run ruff check self_improvment/ tests/
uv run pylint self_improvment/
uv run mypy self_improvment/
```
