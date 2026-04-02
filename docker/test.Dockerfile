# test.Dockerfile — smoke test for get.sh + install.sh bootstrap
# Tests the bootstrap phase only (clone → env setup → instance init → symlink).
# Docker-compose startup is mocked: we verify install logic, not the services.
#
# Build & run (from repo root):
#   docker build -f docker/test.Dockerfile -t clawvis-install-test .
#   docker run --rm clawvis-install-test
#
# Expected: exits 0 if all assertions pass, non-zero + clear message if any fail.

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    git \
    curl \
    python3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Mock docker: a fake binary that always succeeds silently.
# "docker info" → 0, "docker compose up" → 0, everything → 0.
RUN printf '#!/bin/sh\nexit 0\n' > /usr/local/bin/docker \
    && chmod +x /usr/local/bin/docker

# Create a test user (install.sh uses $HOME / $USER)
RUN useradd -m -s /bin/bash tester
USER tester
WORKDIR /home/tester

# Copy repo into the image — simulates post-clone tree (same as get.sh result).
# Automated get.sh/install coverage: bash tests/test-get-sh.sh --workspace (CI) or --clone / --from-github locally.
COPY --chown=tester:tester . /home/tester/.clawvis

ENV CLAWVIS_DIR=/home/tester/.clawvis
ENV HOME=/home/tester
ENV USER=tester
# Skip Node wizard (no node in this image) and Quartz (needs node+npm)
ENV CLAWVIS_NO_NODE_WRAPPER=1
ENV CLAWVIS_SKIP_QUARTZ=1

# Run install: non-interactive, docker mode, skip provider setup
RUN bash /home/tester/.clawvis/install.sh \
    --non-interactive \
    --instance smoketest \
    --mode docker \
    --skip-primary \
    --hub-port 8088 \
    --memory-port 3099 \
    --kanban-api-port 8090

# Assertions
RUN set -e; \
    PASS=0; FAIL=0; \
    check() { \
        if eval "$2"; then \
            printf "  [PASS] %s\n" "$1"; PASS=$((PASS+1)); \
        else \
            printf "  [FAIL] %s\n" "$1"; FAIL=$((FAIL+1)); \
        fi; \
    }; \
    echo ""; \
    echo "=== Clawvis install smoke test ==="; \
    echo ""; \
    check ".env created"                   "[ -f /home/tester/.clawvis/.env ]"; \
    check ".env INSTANCE_NAME=smoketest"   "grep -q 'INSTANCE_NAME=smoketest' /home/tester/.clawvis/.env"; \
    check ".env HUB_PORT=8088"             "grep -q 'HUB_PORT=8088'           /home/tester/.clawvis/.env"; \
    check ".env MEMORY_ROOT set"           "grep -q 'MEMORY_ROOT='            /home/tester/.clawvis/.env"; \
    check ".env MODE=docker"               "grep -q 'MODE=docker'             /home/tester/.clawvis/.env"; \
    check "instance folder created"        "[ -d /home/tester/.clawvis/instances/smoketest ]"; \
    check "memory/projects/ exists"        "[ -d /home/tester/.clawvis/instances/smoketest/memory/projects ]"; \
    check "memory/resources/ exists"       "[ -d /home/tester/.clawvis/instances/smoketest/memory/resources ]"; \
    check "memory/daily/ exists"           "[ -d /home/tester/.clawvis/instances/smoketest/memory/daily ]"; \
    check "example project seeded"         "[ -f /home/tester/.clawvis/instances/smoketest/memory/projects/example-project.md ]"; \
    check "clawvis symlink in ~/.local/bin" "[ -L /home/tester/.local/bin/clawvis ]"; \
    check "clawvis binary is executable"   "[ -x /home/tester/.clawvis/clawvis ]"; \
    echo ""; \
    printf "Results: %d passed, %d failed\n" "${PASS}" "${FAIL}"; \
    echo ""; \
    [ "${FAIL}" -eq 0 ]
