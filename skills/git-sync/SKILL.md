---
name: git-sync
description: "Sync OpenClaw workspace + skills into ONE repo (openclaw-dombot). Never commits API keys, tokens, or openclaw.json."
metadata:
---

# Git Sync

## ⚡ Exécution rapide

```bash
~/.openclaw/skills/git-sync/scripts/sync.sh
```

Synchronise la configuration essentielle OpenClaw dans **un seul dépôt** : **openclaw-dombot**. Contenu : `workspace/` (AGENTS, SOUL, memory, etc.) et `skills/`. Aucune clé API ni fichier sensible.

## Repo unique

- **Nom :** `openclaw-dombot` (ou `GIT_SYNC_REPO` si défini).
- **Structure :** à la racine du repo : `workspace/`, `skills/`, et `cron/jobs.json` (pas de `runs/`).
- **Emplacement local :** `~/openclaw-dombot/` (dans le home, miroir pour git, pas les répertoires de travail réels).

## Règle de sécurité

- **Jamais** commiter : `openclaw.json`, `auth*.json`, `*.key`, `.env`, tokens. Les `.git` imbriqués dans skills sont supprimés pour éviter les sous-modules.

## Invocation

1. Exécuter : `~/.openclaw/skills/git-sync/scripts/sync.sh`
2. Rapporter : succès/échec, push OK ou erreur.

## GitHub CLI (gh)

Si `gh` est connecté (`gh auth login`), le script peut créer le repo (privé) s’il n’existe pas et pousser. Variable optionnelle : `GIT_SYNC_REPO=mon-repo` pour un autre nom de dépôt.
