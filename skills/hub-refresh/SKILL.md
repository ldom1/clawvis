---
name: hub-refresh
description: "Rafraîchit l'état du hub (métriques système, crédits MammouthAI, usage Claude) via hub_core. Use when: cron toutes les 5min, ou quand Ldom demande 'état du hub', 'hub status', 'métriques', '/hub-status', 'crédits restants', 'usage Claude'."
---

# Hub Refresh

Exécute `hub_core` pour mettre à jour les JSON publics du dashboard et journaliser via le skill **logger** (`dombot-log`).

## Exécution

```bash
${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/hub-refresh/scripts/run.sh
```

Si le dépôt n’est pas à `~/lab/clawvis`, exporte **`CLAWVIS_ROOT`** (répertoire qui contient `hub-core/` et `skills/`). Le script essaie aussi `~/Lab/clawvis` en secours.

Le script :

- résout **`CLAWVIS_ROOT`** puis `cd` dans **`${CLAWVIS_ROOT}/hub-core`**
- injecte `AGENT_ID=dombot`, `AGENT_ROLE=ORCHESTRATOR`
- lance `timeout 300 uv run python -m hub_core.main` (**pas** de `UV_PYTHON` imposé : uv choisit un Python ≥3.11 selon `hub-core`; surcharge possible avec `UV_PYTHON=/chemin/python` si besoin)
- écrit un log fichier sous **`${CLAWVIS_ROOT}/logs/hub-refresh-<timestamp>.log`**
- appelle **`${CLAWVIS_ROOT}/skills/logger/core`** (`dombot-log`, `cron:hub-refresh`) si présent

Aucun chemin **`~/.openclaw`** n’est utilisé.

## Résultat — mode cron (silencieux)

Aucune réponse utilisateur. Les JSON du hub sont mis à jour dans **`${CLAWVIS_ROOT}/hub/public/api/`** (voir instance / build Vite selon déploiement).

## Résultat — mode on-demand (Telegram)

Après le script, lire les JSON API du hub pour formater une réponse concise (ex. `system.json`, `providers.json` selon ce que publie `hub_core`).

## Identité & RBAC

- `AGENT_ID=dombot`, `AGENT_ROLE=ORCHESTRATOR`
- `NETWORK_MODE=allowlist` — `api.mammouth.ai`, `api.anthropic.com`, `localhost`

Les détails du run sont dans **`logs/hub-refresh-*.log`** sous la racine Clawvis.
