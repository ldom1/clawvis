#!/usr/bin/env bash
# Minimal wrapper: restart local Lab Hub (stop + start).

LAB="${LAB:-$HOME/Lab}"
exec "$LAB/hub/restart.sh" "$@"

