FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.0 /uv /uvx /usr/local/bin/

WORKDIR /app
ENV HOME=/app
ENV UV_CACHE_DIR=/app/.uv-cache

# Workspace root required for uv workspace source resolution (hub-core editable dep).
COPY pyproject.toml uv.lock ./
COPY hub-core/ ./hub-core/
COPY services/kanban/ ./services/kanban/
COPY services/scheduler/ ./services/scheduler/

RUN uv sync --frozen --no-dev --package clawvis-scheduler \
    && mkdir -p /app/.uv-cache \
    && chmod -R a+rwX /app/.venv /app/.uv-cache /app/uv.lock /app/pyproject.toml

COPY services/scheduler/core/ ./core/

CMD ["uv", "run", "--python", "/app/.venv/bin/python", "python", "core/scheduler.py"]
