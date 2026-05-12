---
name: brain-maintenance
description: "Maintain Clawvis agent docs health: token budgets, drift detection, context recovery. Use when running scheduled maintenance, docs feel bloated or stale, or after long sessions where CLAUDE.md / AGENTS.md may have drifted from recent work. Triggers on: 'trim docs', 'recalibrate', 'check token budgets', 'agent docs drifted', 'recover context'."
---

# Brain Maintenance — L1 docs health

Maintenance scripts for keeping Clawvis **root agent docs** (CLAUDE.md, AGENTS.md, README.md) within token budgets and aligned with recent work from the Local Brain vault.

## Scripts

### trim (weekly)
L1 file audit (token budget). Run via core package:
```bash
uv run --directory ${CLAWVIS_ROOT}/skills/brain-maintenance/core python -m brain_maintenance trim
```

### recalibrate (bi-weekly)
Drift hints: **CLAUDE.md** / **AGENTS.md** expectations vs last daily implementation notes from the Local Brain vault (`BRAIN_PATH` / `inbox/daily/implementation/clawvis/`). Falls back to instance memory (`MEMORY_ROOT`) if brain vault is unavailable.
```bash
uv run --directory ${CLAWVIS_ROOT}/skills/brain-maintenance/core python -m brain_maintenance recalibrate
```

### recover (on-demand)
Context reconstruction from last daily note + L2 breadcrumbs.
```bash
uv run --directory ${CLAWVIS_ROOT}/skills/brain-maintenance/core python -m brain_maintenance recover
```

## Security audit (optional)

If you use **`system_audit.sh`** on a host, it can cover SSH port, firewall, API keys, and exposed ports. Wire it in your own cron — not part of the Clawvis repo by default.

## Schedule

| Trigger | Frequency | Cron (exemple) |
|---------|-----------|------------------|
| trim | Weekly Sunday 22:00 | `0 22 * * 0` (Brain Maintenance — Trim) |
| recalibrate | Weekly Wednesday 22:00 | `0 22 * * 3` (Brain Maintenance — Recalibrate) |
| system-audit | Nightly 04:00 CET | Night Security Audit |
| recover | On-demand | Manual |

## Output

JSON and text under **`${CLAWVIS_ROOT}/.logs/`** (same directory as the repo root used for L1 files).

## Message Telegram (si envoi)

Les crons Trim et Recalibrate n’envoient un message Telegram **que** si nécessaire (L1 dépassé ou drift). **Il est primordial** de suivre le format défini dans **`REPORT_TEMPLATE.md`** (à la racine du skill) pour ce message : 1–2 lignes, résumé clair. Sinon ne rien envoyer.
