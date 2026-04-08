FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

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
COPY kanban/ ./kanban/
COPY project-templates/ ./project-templates/
COPY scripts/ ./scripts/

RUN chmod +x scripts/build-quartz.sh

WORKDIR /clawvis
# Workspace venv at /clawvis/.venv; make it world-writable so uid 1000 can run uv in containers
RUN uv sync --no-dev --all-packages && chmod -R a+rwX .venv

EXPOSE 8090

# uv run avoids broken shebangs when host bind-mount overwrites .venv (absolute #! paths).
CMD ["/usr/local/bin/uv", "run", "--directory", "/clawvis/kanban", \
     "uvicorn", "kanban_api.server:app", "--host", "0.0.0.0", "--port", "8090"]
