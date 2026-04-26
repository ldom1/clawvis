FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
ENV HOME=/app
ENV UV_CACHE_DIR=/app/.uv-cache
COPY services/scheduler/pyproject.toml services/scheduler/uv.lock ./
RUN uv venv /app/.venv \
    && uv sync --frozen --no-dev \
    && mkdir -p /app/.uv-cache \
    && chmod -R a+rwX /app/.venv /app/.uv-cache

COPY services/scheduler/core/ ./core/

CMD ["uv", "run", "--python", "/app/.venv/bin/python", "python", "core/scheduler.py"]
