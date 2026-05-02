---
name: git-sync
description: "Mirror Clawvis .claude + templates into one git repo (GIT_SYNC_REPO). Never commits .env or secrets."
metadata:
---

# Git Sync

## Exécution rapide

```bash
${CLAWVIS_ROOT}/skills/git-sync/scripts/sync.sh
```

Copie un **sous-ensemble** du dépôt Clawvis (fichiers `.claude/`, `.env.example`, etc.) vers **`~/clawvis-config-mirror/`** (ou `GIT_SYNC_REPO`). Puis enchaîne sur **`~/Lab/git-sync.sh`** si présent.

## Paramètres

- **`GIT_SYNC_REPO`** — nom du dossier sous `$HOME` (défaut : `clawvis-config-mirror`).
- **`CLAWVIS_ROOT`** — racine du dépôt Clawvis (détection `~/lab/clawvis`, `~/Lab/clawvis` si absent).

## Sécurité

Ne committe pas : `.env`, tokens, clés. Le script exclut les motifs usuels en rsync.

## Invocation

1. `${CLAWVIS_ROOT}/skills/git-sync/scripts/sync.sh`
2. Rapporter : succès push ou erreur git.
