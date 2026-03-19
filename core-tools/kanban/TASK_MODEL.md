# Kanban Task Model

## Champs principaux

- **id** (`str`) : identifiant unique `task-xxxxxxxx`.
- **title** (`str`) : titre court de la tâche.
- **project** (`str`) : nom du projet (peut être vide).
- **status** (`\"Backlog\" | \"To Start\" | \"In Progress\" | \"Blocked\" | \"Review\" | \"Done\" | \"Archived\"`).
- **priority** (`\"Critical\" | \"High\" | \"Medium\" | \"Low\"`, défaut `\"Medium\"`).
- **effort_hours** (`float | null`) : estimation d’effort.
- **description** (`str`) : description principale de la tâche.
- **notes** (`str`) : mémo libre, non historisé.
- **timeline** (`str | null`) : date simple (YYYY-MM-DD) utilisée pour le Gantt léger actuel.
- **start_date / end_date** (`str | null`) : dates ISO (optionnelles) pour un futur Gantt plus riche.
- **assignee** (`str`) : personne/agent assigné.
- **dependencies** (`list[str]`) : liste d’IDs de tâches dont celle‑ci dépend.
- **tags** (`list[str]`) : tags libres.
- **comments** (`list[object]`) : commentaires structurés `{id, text, author, created_at}`.
- **progress** (`float`) : 0.0 → 1.0 selon `status`.
- **source_file** (`str`) : éventuelle provenance.
- **created / updated / archived_at** (`str` ISO ou `null`) : timestamps.
- **created_by** (`str`) : créateur logique (`\"user\"`, `\"parser\"`, etc.).

## Rôles description / notes / comments

- **description** : texte officiel de la tâche (affiché en lecture seule dans la modale).
- **notes** : zone de saisie rapide modifiable (brouillon interne).
- **comments** : fil historisé (auteur + date + texte) via les endpoints `/tasks/{id}/comments`.

## Vues consommatrices

- **Board** :
  - utilise `status`, `priority`, `project`, `effort_hours`, `created_by`, `notes`, `description`.
  - groupe par colonnes `status` et filtre par `project`.
- **Gantt** :
  - utilise aujourd’hui `timeline` (date unique) + `project` + `priority` + `effort_hours`.
  - pourra évoluer vers `start_date` / `end_date`.
- **Graph** :
  - consomme `dependencies` + `project` + `title` pour afficher les arêtes de précédence.

## Ordonnancement dans `tasks.json`

Lors de la sauvegarde, les tâches sont normalisées ainsi :

1. **Normalisation** :
   - `dependencies`, `comments`, `tags` sont toujours des listes.
   - `start_date`, `end_date` existent toujours (ou `null`).
   - les dépendances vers des IDs inexistants ou auto‑références sont supprimées.
2. **Tri** :
   - tri par `(project, status, start_date/timeline, created)` :
     - `status` dans l’ordre `Backlog → To Start → In Progress → Blocked → Review → Done → Archived`.
     - puis par `start_date` si définie, sinon `timeline`, puis `created`.

L’API `/tasks` retourne toujours les tâches actives (non `Archived`) avec ce tri appliqué, ainsi que :

- `stats` : agrégats globaux (par status, priorité, effort restant…),
- `projects` : liste des projets actifs.

