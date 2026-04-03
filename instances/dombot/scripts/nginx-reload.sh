#!/usr/bin/env bash
# nginx-reload.sh — Reload nginx from template (delegates to render-nginx.sh --reload).
# Usage: ./nginx-reload.sh
set -euo pipefail
SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPTS}/render-nginx.sh" --reload
