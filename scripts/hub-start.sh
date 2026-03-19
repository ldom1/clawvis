#!/usr/bin/env bash
# Minimal wrapper: start local Lab Hub using this LabOS checkout.

LAB="${LAB:-$HOME/Lab}"
exec "$LAB/hub/start.sh" "$@"

