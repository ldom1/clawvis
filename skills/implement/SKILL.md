---
name: implement
description: "Pont entre kanban-implementer et l’agent : charge le contexte tâche (API Kanban), prépare la boucle implémentation → PR → update statut. Use when une carte Todo/To Start doit devenir du code."
---

# Implement (bridge)

## Rôle

Après `kanban-implementer select`, ce skill **matérialise** la tâche pour l’agent OpenClaw :

1. Affiche le JSON tâche (titre, projet, `source_file`, effort).
2. Rappelle l’enchaînement : `In Progress` → code → PR → `Review` (voir `kanban-implementer`).

## Exécution

```bash
~/.openclaw/skills/implement/scripts/run.sh TASK_ID
```

Variables : `KANBAN_API_URL` (défaut `http://127.0.0.1:8090`), `KANBAN_API_KEY` si besoin.

## Feedback loop

1. `kanban-implementer` → `select` → `TASK_ID`
2. **`implement/run.sh TASK_ID`** → contexte affiché sur stdout
3. Agent exécute PROTOCOL.md + implémentation
4. `kanban-implementer update TASK_ID "In Progress" | "Review" | "Done"`
5. `dombot-log` / Telegram selon `kanban-implementer` SKILL

## Séparation

| Skill | Rôle |
|--------|------|
| **kanban-implementer** | Orchestration cron, sélection, statuts, PR |
| **implement** | **Une** tâche → contexte structuré pour l’agent (pas de cron dédié) |
