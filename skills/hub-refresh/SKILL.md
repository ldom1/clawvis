---
name: hub-refresh
description: "Rafraîchit l'état du hub (métriques système, crédits MammouthAI, usage Claude) via hub_core. Use when: cron toutes les 5min, ou quand Ldom demande 'état du hub', 'hub status', 'métriques', '/hub-status', 'crédits restants', 'usage Claude'."
---

# Hub Refresh

Exécute hub_core pour mettre à jour les JSON publics du dashboard et logger l'état système dans dombot.log.

## Exécution

```bash
~/.openclaw/skills/hub-refresh/scripts/run.sh
```

Ce script :
- Se positionne dans `~/Lab/dombot-labos/hub-core`
- Injecte l'identité DomBot (`AGENT_ID=dombot`, `AGENT_ROLE=ORCHESTRATOR`)
- Lance `uv run python -m hub_core.main` (écrit les JSON + logs dombot.log)

## Résultat — mode cron (silencieux)

Aucune réponse. Les fichiers JSON sont mis à jour dans `~/Lab/hub/public/api/`.

## Résultat — mode on-demand (Telegram)

Quand Ldom demande l'état du hub, exécuter le script puis formatter une réponse concise :

```
🖥️ Hub — <timestamp>
CPU: <cpu>%  RAM: <ram>%  Disk: <disk>%
MammouthAI: €<available> / €<limit>
Claude: <usage>% utilisé
```

Lire `~/Lab/hub/public/api/system.json` et `providers.json` après le script pour obtenir les valeurs.

## Identité & RBAC

Le script injecte :
- `AGENT_ID=dombot` → identity: `dombot@labos.local`
- `AGENT_ROLE=ORCHESTRATOR` → capabilities: workflows.execute, kanban.*, files.*, …
- `NETWORK_MODE=allowlist` → seuls `api.mammouth.ai`, `api.anthropic.com`, `localhost` autorisés

Ces valeurs sont loggées dans `~/.openclaw/logs/dombot.log` à chaque run.
