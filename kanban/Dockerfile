FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /clawvis
# Workspace root is required for uv to resolve workspace members (hub-core ↔ kanban)
COPY pyproject.toml ./
COPY uv.lock ./
COPY hub-core/ ./hub-core/
COPY kanban/ ./kanban/
COPY project-templates/ ./project-templates/

WORKDIR /clawvis/kanban
# Install production deps from lockfile
RUN uv sync --no-dev

EXPOSE 8090

# Call uvicorn directly from the pre-built venv — avoids uv re-sync at startup
CMD ["/clawvis/.venv/bin/uvicorn", "kanban_api.server:app", \
     "--host", "0.0.0.0", "--port", "8090"]
