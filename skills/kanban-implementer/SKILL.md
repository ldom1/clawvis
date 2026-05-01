---
name: kanban-implementer
description: "Sélectionne chaque jour une tâche Kanban assignée à DomBot et l'implémente en suivant PROTOCOL.md (uv, pydantic, pytest, commits sémantiques), puis ouvre une PR GitHub. Supporte la priorisation par projet via KANBAN_PRIORITY_PROJECT. Use when: cron daily-implementation ou quand Ldom demande 'implémente la prochaine tâche du kanban'."
---

# Kanban Implementer

Implémentation automatique de tâches Kanban par DomBot, une par session. Suit scrupuleusement `~/Lab/PROTOCOL.md`.

## ⚡ Exécution rapide

```bash
# Sélectionner la prochaine tâche (affiche contexte + TASK_ID)
uv run --directory ${CLAWVIS_ROOT}/skills/kanban-implementer/core python -m kanban_implementer select

# Prioriser un projet spécifique
uv run --directory ${CLAWVIS_ROOT}/skills/kanban-implementer/core python -m kanban_implementer select --project hub

# Lister les tâches éligibles
uv run --directory ${CLAWVIS_ROOT}/skills/kanban-implementer/core python -m kanban_implementer list

# Mettre à jour le statut d'une tâche
uv run --directory ${CLAWVIS_ROOT}/skills/kanban-implementer/core python -m kanban_implementer update task-XXXXXXXX "In Progress"
uv run --directory ${CLAWVIS_ROOT}/skills/kanban-implementer/core python -m kanban_implementer update task-XXXXXXXX "Review"
uv run --directory ${CLAWVIS_ROOT}/skills/kanban-implementer/core python -m kanban_implementer update task-XXXXXXXX "Done"

# Via script shell (avec logs)
${CLAWVIS_ROOT}/skills/kanban-implementer/scripts/run.sh [--project PROJECT_NAME]
```

---

## Priorisation par projet

Définir `KANBAN_PRIORITY_PROJECT` dans le `.env` du skill ou en variable d'environnement :

```bash
# Priorité au projet "hub"
KANBAN_PRIORITY_PROJECT=hub

# Priorité max effort (défaut: 2h)
KANBAN_MAX_EFFORT=1.5
```

Le sélecteur choisit en priorité les tâches du projet spécifié (toutes priorités confondues), puis les tâches globales par High > Medium > Low, effort croissant.

---

## Critères de sélection

Une tâche est **éligible** si :
- `assignee = "DomBot"`
- `status ∈ {"To Start", "Backlog"}`
- `effort_hours ≤ KANBAN_MAX_EFFORT` (défaut 2h)
- `confidence_effective ≥ KANBAN_MIN_CONFIDENCE` (défaut 0.4)

**Calcul de `confidence_effective` :**
- assignee ∉ `{"DomBot"}` (humain) → 1.0
- sinon → `task.confidence ?? 0.5` (null → 0.5)

Si aucune tâche éligible → arrêt propre (pas d'erreur).

---

## Workflow DomBot (étapes obligatoires)

### Étape 1 — Sélection

```bash
uv run --directory ${CLAWVIS_ROOT}/skills/kanban-implementer/core python -m kanban_implementer select [--project PROJECT]
```

Note le `TASK_ID` retourné. Si "Aucune tâche éligible" → session terminée, rapporter à Ldom.

### Étape 1bis — Ambiguïté (`IS_AMBIGUOUS`)

La sortie de `select` inclut `IS_AMBIGUOUS=true|false` (heuristique sur titre + description).

- Si **`IS_AMBIGUOUS=true`** : **ne pas implémenter**. Ouvrir une issue GitHub pour clarifier, puis :
  ```bash
  uv run --directory ${CLAWVIS_ROOT}/skills/kanban-implementer/core python -m kanban_implementer update TASK_ID "Blocked"
  ```
  Rapporter à Ldom (Telegram / log) et **arrêter la session** (pas de branche, pas de PR).

### Étape 2 — Lecture du contexte

Avant de coder :
1. Exécuter **`${CLAWVIS_ROOT}/skills/implement/scripts/run.sh TASK_ID`** — affiche le JSON tâche et le rappel des étapes (pont agent).
2. Lire `~/Lab/PROTOCOL.md` (règles obligatoires du Lab).
3. Lire le fichier projet (`source_file` affiché par `select`).
4. Si le repo concerné existe : explorer la structure, lire les tests existants.

### Étape 3 — Marquer "In Progress"

```bash
uv run --directory ${CLAWVIS_ROOT}/skills/kanban-implementer/core python -m kanban_implementer update TASK_ID "In Progress"
```

### Étape 4 — Implémentation (règles PROTOCOL.md obligatoires)

**Emplacement :**
- Feature sur un projet existant → modifier `Lab/project/<slug>/` ou `Lab/poc/<slug>/`
- Nouveau POC → créer `Lab/poc/<slug>/`

**Stack (selon PROTOCOL.md) :**
- Python → `uv` + `pyproject.toml` + `pydantic` + `python-dotenv`
- Frontend → Vite (React/Vue) ou HTML+CSS minimal
- Backend API → FastAPI

**Qualité minimale :**
- [ ] Au moins 1 test (`uv run pytest tests/ -v`)
- [ ] `uv run ruff check .` sans erreur bloquante
- [ ] `.env.example` cohérent avec les variables utilisées
- [ ] Logs via `dombot-logger` si le code touche DomBot/OpenClaw
- [ ] Hub mis à jour si app exposée (tuile + nginx.conf)

**Git :**
```bash
# Branche dédiée
git checkout -b feat/TASK_ID-slug-descriptif

# Commits sémantiques
git commit -m "feat: description courte"
git commit -m "test: ajouter tests pour X"
git commit -m "docs: mettre à jour hub tile"
```

### Étape 5 — Ouvrir une Pull Request

```bash
git push -u origin feat/TASK_ID-slug-descriptif

gh pr create \
  --title "feat: [TASK_ID] Titre de la tâche" \
  --body "## Tâche Kanban

**ID:** TASK_ID
**Projet:** PROJECT_NAME

## Changements
- ...

## Tests
- [ ] uv run pytest OK
- [ ] ruff check OK

🤖 Implémenté par DomBot · kanban-implementer"
```

Si `gh` non disponible ou pas de remote : committer sur `develop` et noter la branche dans le rapport.

### Étape 6 — Marquer "Review" (après PR ouverte)

La tâche passe en **Review** (pas Done) — c'est Ldom qui valide et merge.

```bash
uv run --directory ${CLAWVIS_ROOT}/skills/kanban-implementer/core python -m kanban_implementer update TASK_ID "Review"
```

### Étape 7 — Rapport Telegram + log

```bash
msg=$'🔧 Kanban — PR prête pour review\n\n📋 [TASK_ID] Titre de la tâche\n📁 Projet : project-name\n⏱️ Effort réel : Xh\n\n🔗 PR : https://github.com/ldom1/<repo>/pull/<N>\n🧪 Tests : OK\n📎 Branch : feat/TASK_ID-slug\n\nKanban mis à jour → Review ⏳'

openclaw message send --channel telegram --target 5689694685 --message "$msg"

uv run --directory ${CLAWVIS_ROOT}/skills/logger/core \
  dombot-log "INFO" "cron:kanban-implementer" "system" "impl:complete" "Task TASK_ID implemented + PR opened"
```

---

## Règles de prudence

- **Une seule tâche par session** : ne pas chaîner plusieurs implémentations.
- **Ne pas fermer une PR sans tests** : si les tests échouent, noter le problème dans la PR et la laisser en Draft.
- **Ne pas modifier `main` directement** : toujours passer par une branche + PR.
- **Tâches ambiguës** : si `IS_AMBIGUOUS=true` ou la tâche nécessite une décision de design, créer une issue (pas de PR), passer le statut à **Blocked**, et laisser Ldom arbitrer.
- **Effort > MAX_EFFORT** : si l'implémentation dépasse l'estimation, ouvrir la PR avec ce qui est fait + commentaire sur la complexité.

---

## Vérification du skill (appels exacts)

Commandes exactes utilisées pour valider que le skill fonctionne — à réutiliser après toute modification.

### 1. Vérifier le sélecteur (Python)

```bash
cd ${CLAWVIS_ROOT}/skills/kanban-implementer/core
uv run python -c "
from kanban_implementer.selector import load_tasks, select_task

tasks = load_tasks()
eligible = [t for t in tasks if t.is_eligible]
print(f'Total tasks: {len(tasks)}')
print(f'Eligible: {len(eligible)}')
for t in eligible[:5]:
    print(f'  [{t.confidence_effective:.2f}] {t.id} — {t.title[:50]}')

selected = select_task()
if selected:
    print(f'Selected: {selected.id} — {selected.title}')
    print(f'  confidence_effective={selected.confidence_effective:.2f}')
else:
    print('No task selected')
"
```

Résultat attendu : une tâche sélectionnée avec `confidence_effective ≥ 0.40`.

### 2. Vérifier le filtre confidence (tests unitaires)

```bash
cd ${CLAWVIS_ROOT}/skills/kanban-implementer/core
uv run python -m pytest tests/test_selector.py -v
```

Résultat attendu : **15 passed**.
Couvre : filtre confidence, `is_ambiguous` (mots-vagues / titre clair), statut **Blocked**.

### 3. Vérifier le passage de statut via CLI

```bash
cd ${CLAWVIS_ROOT}/skills/kanban-implementer/core

# Récupérer un TASK_ID éligible
TASK_ID=$(uv run python -c "
from kanban_implementer.selector import select_task
t = select_task()
print(t.id if t else '')
")

echo "Task: $TASK_ID"

# Cycle complet
uv run python -m kanban_implementer update "$TASK_ID" "In Progress"
uv run python -m kanban_implementer update "$TASK_ID" "Review"
uv run python -m kanban_implementer update "$TASK_ID" "Backlog"
```

Résultat attendu :
```
✅ Task task-XXXXXXXX: Backlog → In Progress
✅ Task task-XXXXXXXX: In Progress → Review
✅ Task task-XXXXXXXX: Review → Backlog
```

### 4. Vérifier via l'API Kanban (HTTP)

```bash
# Lire l'état d'une tâche
curl -s http://localhost:8090/tasks/TASK_ID | python3 -c "
import json, sys
t = json.load(sys.stdin)
print(f'status={t[\"status\"]} confidence={t.get(\"confidence\")}')
"

# Passer In Progress via HTTP
curl -s -X PUT http://localhost:8090/tasks/TASK_ID \
  -H 'Content-Type: application/json' \
  -d '{"status":"In Progress"}' | python3 -c "
import json, sys
t = json.load(sys.stdin)
print(f'status={t[\"status\"]} progress={t.get(\"progress\")}')
"

# Passer Review via HTTP
curl -s -X PUT http://localhost:8090/tasks/TASK_ID \
  -H 'Content-Type: application/json' \
  -d '{"status":"Review"}' | python3 -c "
import json, sys; t = json.load(sys.stdin); print(f'status={t[\"status\"]}')
"
```

### 5. Vérifier les tâches en Review

```bash
curl -s http://localhost:8090/tasks | python3 -c "
import json, sys
data = json.load(sys.stdin)
review = [t for t in data['tasks'] if t['status'] == 'Review']
print(f'In Review: {len(review)}')
for t in review:
    print(f'  {t[\"id\"]} — {t[\"title\"][:55]}')
"
```

---

## Séparation avec les autres skills

| Skill | Rôle |
|-------|------|
| **proactive-innovation** | Propose des améliorations et idées (pas d'implémentation directe) |
| **kanban-implementer** | Implémente une tâche concrète existante dans le Kanban |
| **self-improvement** | Capture erreurs et learnings (pas de code produit) |
