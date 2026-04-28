FROM python:3.11-slim

# Node.js 22 — openclaw CLI requires v22+ (v20 not supported)
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.10.0 /uv /uvx /usr/local/bin/

# Pre-create the runtime home dir so the entrypoint can write .claude.json.
# The container runs as HOST_UID (default 1000); chmod 1777 lets any uid write.
RUN mkdir -p /home/lgiron && chmod 1777 /home/lgiron

WORKDIR /clawvis
# Workspace root files are required for uv workspace source resolution.
COPY pyproject.toml ./
COPY uv.lock ./
COPY hub-core/ ./hub-core/
COPY services/kanban/ ./services/kanban/
COPY services/agent/ ./services/agent/

RUN uv sync --frozen --no-dev --package agent-service \
    && chmod -R a+rwX .venv /clawvis

EXPOSE 8092

# Restore .claude.json from the newest backup found inside the mounted ~/.claude/backups/
# when the file is absent (avoids fragile WSL Docker Desktop file bind-mounts).
COPY services/agent/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uv", "run", "--frozen", "--directory", "/clawvis/services/agent", \
     "uvicorn", "agent_service.main:app", "--host", "0.0.0.0", "--port", "8092"]
