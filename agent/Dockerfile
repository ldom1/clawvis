FROM python:3.11-slim

# Node.js 20 — needed to run openclaw CLI (Node.js binary) when mounted
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /clawvis
COPY agent/ ./agent/

WORKDIR /clawvis/agent
RUN uv sync --no-dev

EXPOSE 8092

CMD ["/clawvis/agent/.venv/bin/uvicorn", "agent_service.main:app", \
     "--host", "0.0.0.0", "--port", "8092"]
