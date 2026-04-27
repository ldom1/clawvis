FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
ENV HOME=/app
ENV UV_CACHE_DIR=/app/.uv-cache

# Workspace root required for uv workspace source resolution (hub-core editable dep).
COPY pyproject.toml uv.lock ./
COPY hub-core/ ./hub-core/
COPY services/kanban/ ./services/kanban/
COPY services/telegram/ ./services/telegram/

RUN uv sync --frozen --no-dev --package clawvis-telegram \
    && mkdir -p /app/.uv-cache \
    && chmod -R a+rwX /app/.venv /app/.uv-cache /app/uv.lock /app/pyproject.toml

COPY services/telegram/core/ ./core/

EXPOSE 8094

CMD ["uv", "run", "--python", "/app/.venv/bin/python", "python", "-m", "core.bot"]
