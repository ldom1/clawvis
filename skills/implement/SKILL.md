---
name: implement
description: "Execute a single kanban task. Auto-selects the best eligible task (DomBot-assigned, highest priority, effort ≤ KANBAN_MAX_EFFORT) or loads a specific task via --task-id. Use when: running the daily implementation cron, or when Ldom asks 'implémente la prochaine tâche du kanban'. Always one task per run."
---

# Implement

Executes one kanban task end-to-end.

**Invariant : une seule tâche par run, sans exception.**

---

## Deux logiques d'entrée

### Logique A — Auto-select (sans `--task-id`)

Lit `tasks.json` directement depuis le système de fichiers pour sélectionner la meilleure tâche éligible.

**Critères d'éligibilité :**
- `status ∈ {Backlog, To Start}`
- `assignee = DomBot`
- `effort_hours ≤ KANBAN_MAX_EFFORT` (défaut : 2h)
- `confidence ≥ KANBAN_MIN_CONFIDENCE` (défaut : 0.4 ; `null` traité comme 0.5 ; assignee humain = 1.0)

**Tri de sélection :**
1. Projet prioritaire en premier (`KANBAN_PRIORITY_PROJECT` ou `--project`)
2. Puis par priorité : High < Medium < Low
3. Puis par effort croissant

**Sortie :** contexte markdown de la tâche + `TASK_ID` + `IS_AMBIGUOUS`

```bash
# Sélection automatique
uv run --directory ${CLAWVIS_ROOT}/skills/implement/core python -m implement

# Avec projet prioritaire
uv run --directory ${CLAWVIS_ROOT}/skills/implement/core python -m implement --project hub

# Lister les tâches éligibles sans en choisir une
uv run --directory ${CLAWVIS_ROOT}/skills/implement/core python -m implement --list
uv run --directory ${CLAWVIS_ROOT}/skills/implement/core python -m implement --list --project hub
```

**Source de données :** `MEMORY_ROOT/kanban/tasks.json` (lecture directe JSON)

---

### Logique B — Tâche explicite (avec `--task-id`)

Interroge l'API Kanban REST pour charger une tâche précise, et enrichit avec la note Brain.

**Sortie :** variables shell `TASK_ID`, `TASK_TITLE`, `TASK_PROJECT`, etc. + `BRAIN_NOTE` (path) + `BRAIN_CONTENT` (contenu complet de la note Brain du projet)

```bash
# Charger une tâche spécifique
uv run --directory ${CLAWVIS_ROOT}/skills/implement/core python -m implement \
  --task-id task-XXXXXXXX
```

**Source de données :** `GET {KANBAN_API_URL}/tasks/{task_id}` + lecture fichier Brain

---

### Mutations de statut (requièrent `--task-id`)

Toujours via l'API REST (`PATCH /tasks/{task_id}`).

```bash
# Marquer "In Progress" au début
uv run --directory ${CLAWVIS_ROOT}/skills/implement/core python -m implement \
  --task-id <TASK_ID> --set-status "In Progress"

# Marquer "Done" à la fin
uv run --directory ${CLAWVIS_ROOT}/skills/implement/core python -m implement \
  --task-id <TASK_ID> --mark-done
```

Statuts valides : `Backlog | To Start | In Progress | Blocked | Review | Done`

---

## Workflow complet

```
1. Sélection
   ├─ sans --task-id → auto-select (tasks.json)  [Logique A]
   └─ avec --task-id → chargement API            [Logique B]

2. Lire la note Brain (BRAIN_NOTE / BRAIN_CONTENT)
   └─ Contexte, décisions passées, archive

3. Implémenter
   └─ uv (Python) | yarn (JS) | tests | commit sémantique

4. Mettre à jour le statut
   ├─ --set-status "In Progress" au départ (optionnel)
   └─ --mark-done à la fin (obligatoire)

5. Logger
   └─ Discord via logger skill : [implement] <projet> — <titre> done
```

---

## Configuration

| Variable | Défaut | Description |
|----------|--------|-------------|
| `KANBAN_API_URL` | `http://localhost:8088/api/hub/kanban` | API Kanban (Logique B + mutations) |
| `MEMORY_ROOT` | dérivé de `CLAWVIS_ROOT` | Racine mémoire instance |
| `KANBAN_PRIORITY_PROJECT` | `(aucun)` | Projet prioritaire en auto-select |
| `KANBAN_MAX_EFFORT` | `2.0` | Effort max (heures) pour auto-select |
| `KANBAN_MIN_CONFIDENCE` | `0.4` | Score confiance minimum (Kahneman) |

---

## Invariants

- **Une tâche par session.** Ne jamais implémenter plus d'une tâche par run.
- **Brain d'abord.** Toujours lire la note Brain avant d'écrire du code.
- **Statut à jour.** La tâche doit être `Done` avant de logger la complétion.
- **Pas de Telegram.** Le log de complétion va sur Discord uniquement (`logger` skill).
