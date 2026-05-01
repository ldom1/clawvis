FROM python:3.11-slim

# Pin uv version (distroless binary from GHCR).
COPY --from=ghcr.io/astral-sh/uv:0.10.0 /uv /uvx /usr/local/bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    nodejs \
    npm \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /clawvis
# Workspace root is required for uv to resolve workspace members (hub-core ↔ kanban)
COPY pyproject.toml ./
COPY uv.lock ./
COPY hub-core/ ./hub-core/
COPY services/kanban/ ./services/kanban/
COPY skills/project-init/templates/ ./skills/project-init/templates/
COPY scripts/ ./scripts/

RUN chmod +x scripts/build-quartz.sh

WORKDIR /clawvis
# Workspace venv at /clawvis/.venv; make it world-writable so uid 1000 can run uv in containers
RUN UV_HTTP_TIMEOUT=120 UV_HTTP_RETRIES=8 uv sync --frozen --no-dev --package kanban-api \
    && chmod -R a+rwX .venv /clawvis

EXPOSE 8090

# uv run avoids broken shebangs when host bind-mount overwrites .venv (absolute #! paths).
CMD ["uv", "run", "--directory", "/clawvis/services/kanban", \
     "uvicorn", "kanban_api.server:app", "--host", "0.0.0.0", "--port", "8090"]
