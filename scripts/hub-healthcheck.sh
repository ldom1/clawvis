#!/usr/bin/env bash
# Minimal wrapper: run Lab Hub healthcheck (same options as hub/healthcheck.sh).

LAB="${LAB:-$HOME/Lab}"
exec "$LAB/hub/healthcheck.sh" "$@"

