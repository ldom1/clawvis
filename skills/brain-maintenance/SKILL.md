# Brain Maintenance — L1/L2/L3 Health

Maintenance scripts for keeping DomBot's memory hierarchy healthy.

## Scripts

### trim (weekly)
L1 Brain file audit (token budget). Run via core package:
```bash
uv run --directory ${CLAWVIS_ROOT}/skills/brain-maintenance/core python -m brain_maintenance trim
```

### recalibrate (bi-weekly)
Drift detection: SOUL.md / AGENTS.md vs recent behavior.
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
|---------|-----------|----------------|
| trim | Weekly Sunday 22:00 | `0 22 * * 0` (Brain Maintenance — Trim) |
| recalibrate | Weekly Wednesday 22:00 | `0 22 * * 3` (Brain Maintenance — Recalibrate) |
| system-audit | Nightly 04:00 CET | Night Security Audit |
| recover | On-demand | Manual |

## Output

All logs written to `$BRAIN_PATH/.logs/`.

## Message Telegram (si envoi)

Les crons Trim et Recalibrate n’envoient un message à Ldom (Telegram, 5689694685) **que** si nécessaire (L1 dépassé ou drift). **Il est primordial** de suivre le format défini dans **`REPORT_TEMPLATE.md`** (à la racine du skill) pour ce message : 1–2 lignes, résumé clair. Sinon ne rien envoyer.
