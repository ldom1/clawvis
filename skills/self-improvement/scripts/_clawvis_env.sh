#!/usr/bin/env bash
# Re-export shared Clawvis env (canonical: skills/_clawvis_env.sh).
_skill_scripts="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${_skill_scripts}/../../_clawvis_env.sh"
