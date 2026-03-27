FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /clawvis
# hub-core is a local path dependency of kanban — copy first
COPY hub-core/ ./hub-core/
COPY kanban/ ./kanban/
COPY project-templates/ ./project-templates/

WORKDIR /clawvis/kanban
# Install production deps from lockfile
RUN uv sync --no-dev

EXPOSE 8090

# Call uvicorn directly from the pre-built venv — avoids uv re-sync at startup
CMD ["/clawvis/kanban/.venv/bin/uvicorn", "kanban_api.server:app", \
     "--host", "0.0.0.0", "--port", "8090"]
