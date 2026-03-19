# Design Spec — ClawPilot + Kanban Improvements
**Date:** 2026-03-19
**Status:** Approved (v2 — post-review fixes)
**Scope:** Renommage dombot-labos → ClawPilot + 4 améliorations kanban

---

## 1. Renommage : ClawPilot

### Décision
`dombot-labos` devient **ClawPilot**.

- **Logique :** Claw (grip/outil/Matrix) + Pilot (orchestration, pilotage)
- **Tagline :** *"Your personal AI agent OS — Matrix-grade orchestration, on your machine."*
- **Agent DomBot :** inchangé (c'est l'agent, pas le produit)

### Périmètre du changement
| Fichier | Changement |
|---------|-----------|
| `README.md` | Titre `# ClawPilot` + tagline |
| `landing/src/main.ts` + HTML | Hero title `ClawPilot`, `<title>ClawPilot</title>`, meta description |
| `landing/package.json` | `"name": "clawpilot-landing"` |
| `docker-compose.yml` | `container_name: clawpilot-hub`, `container_name: clawpilot-kanban`, label `app=clawpilot` |
| `TASK_MODEL.md` | Mention du produit |

**Hors scope :** renommage du repo GitHub (action manuelle), nom de domaine, skills internes.

---

## 2. PilotView — Dashboard de pilotage (anciennement PM Meta)

> Note : la section UI s'appelle **PilotView** pour éviter le conflit avec le nom produit ClawPilot.

### Problème
La section PM Meta actuelle n'affiche que des compteurs bas-niveau. L'humain ne peut pas suivre l'activité de la semaine.

### Design

PilotView est structuré en 4 blocs `<details>` repliables (ouverts par défaut).

#### Bloc 1 — Activité hebdomadaire
| | Semaine passée | Cette semaine |
|--|---|---|
| Tasks créées | N | N (↑↓) |
| Tasks Done | N | N (↑↓) |
| Commits | N | N (↑↓) |

Trend : `↑` si cette semaine > semaine passée, `↓` sinon, `=` si égal.

#### Bloc 2 — Projets en cours
Liste des projets avec tâches actives (In Progress + To Start).
Par projet : `active_count`, `remaining_effort_hours`, `majority_assignee`.
`majority_assignee` = valeur `assignee` la plus fréquente parmi les tâches actives du projet ; en cas d'égalité, ordre alphabétique.

#### Bloc 3 — Derniers 5 commits
Tableau : `date | repo | message (50 chars max) | author`
Source : `GET /api/kanban/stats/weekly`.
Label "Actualisé à HH:MM" affiché sous le bloc (timestamp du dernier fetch).

#### Bloc 4 — En attente de validation
Tasks en status "Review" ou "Blocked". Badge rouge si `updated` > 3 jours.
Clic → ouvre la modale détail.

### Nouvel endpoint `GET /api/kanban/stats/weekly`

**Structure de réponse (exemple complet) :**
```json
{
  "weeks": {
    "last_week":  { "created": 5, "done": 3, "commits": 12 },
    "this_week":  { "created": 2, "done": 1, "commits": 4 }
  },
  "projects": [
    {
      "name": "ruflo",
      "active_count": 3,
      "remaining_effort_hours": 6.5,
      "majority_assignee": "DomBot"
    }
  ],
  "recent_commits": [
    {
      "date": "2026-03-19",
      "repo": "hub",
      "message": "feat: ajouter SSE kanban",
      "author": "ldom1"
    }
  ],
  "pending_review": [
    {
      "id": "task-abc123",
      "title": "Implémenter le Gantt",
      "status": "Review",
      "project": "kanban",
      "updated": "2026-03-15T10:00:00Z",
      "days_waiting": 4
    }
  ]
}
```

**Implémentation du git log :**
- Exécution via `asyncio.create_subprocess_exec` (non bloquant)
- Timeout par repo : 3 secondes (`asyncio.wait_for`)
- Si `LAB_REPOS` est vide ou absent → `recent_commits: []`, pas d'erreur
- Si un chemin n'existe pas ou n'est pas un repo git → ignoré silencieusement, log WARNING
- `LAB_REPOS` = chemins séparés par `:` dans `.env` (ex: `/home/lgiron/Lab/hub:/home/lgiron/Lab/dombot-labos`)

**Calcul des semaines :**
- `this_week` = 7 derniers jours glissants (today - 7j à today)
- `last_week` = 14j à 7j avant today
- Basé sur `created` pour les tâches, `commit date` pour les commits

**Refresh frontend :**
- Bouton "⟳ Refresh" sur PilotView → `fetch('/api/kanban/stats/weekly')` manuel
- Le SSE existant ne couvre pas cet endpoint (données git indépendantes de `tasks.json`)

---

## 3. Gantt — Barres proportionnelles

### Problème
Le Gantt actuel place toutes les barres à `left: 210px` fixe. Il ne représente pas la durée des tâches.

### Design

**Calcul start/end — 4 cas :**

| `start_date` | `end_date` | `timeline` | Comportement |
|---|---|---|---|
| défini | défini | — | `start = start_date`, `end = end_date` |
| null | défini | — | `start = created`, `end = end_date` |
| null | null | défini | `start = created`, `end = timeline` |
| null | null | null | **Tâche exclue du Gantt** |

Message affiché si tâches exclues : "X tâche(s) sans date de fin masquée(s)."

**Rendu :**
- Axe temporel : graduations en **semaines**
- Barre min-width : 8px (pour les tâches d'1 jour)
- Tâches Done → vert semi-transparent
- Label tronqué à 160px à gauche
- Durée affichée dans la barre si barre ≥ 60px
- Clic → ouvre modale détail existante

**Calcul de position :**
```js
const barLeft = LABEL_WIDTH + (startMs - rangeStartMs) / totalMs * chartWidth;
const barWidth = Math.max(8, (endMs - startMs) / totalMs * chartWidth);
```

### Changements techniques
Uniquement frontend (`index.html`). Aucun changement modèle ni API.

---

## 4. Graph — DAG topologique par projet

### Problème
Tous les nœuds sont à `cx=120`. Vue illisible.

### Design

Layout D3.js v7 (CDN), groupé par projet, colonnes topologiques.

#### Disposition
- **Un groupe SVG par projet** : rect encadré + label projet
- **Colonnes topologiques** : calculées via l'algorithme de Kahn
  - Niveau 0 : nœuds sans dépendances entrantes
  - Niveau N : nœuds dont tous les prédécesseurs sont au niveau < N
- **Cycles de dépendances** : détectés via Kahn (nœuds résiduels après algo = en cycle). Ces nœuds sont groupés dans un sous-groupe "⚠ Cycles" avec contour rouge.
- **Tâches sans dépendances dans des projets isolés** → groupe "Standalone"
- **Si aucune dépendance dans le filtre actif** → message clair (comportement actuel conservé)

#### Visuel nœuds
- Couleur par status :
  - Backlog → gris (`#52525b`)
  - To Start → cyan (`#06b6d4`)
  - In Progress → bleu (`#3b82f6`)
  - Blocked → violet (`#7c3aed`)
  - Review → amber (`#f59e0b`)
  - Done → vert (`#22c55e`)
- Rayon : `12 + min(effort_hours, 8) * 1.2` (min 12px, max ~22px)
- Clic → ouvre modale détail

#### Arêtes
- Flèches directionnelles (`marker-end`)
- Couleur de l'arête = couleur du nœud source

### Changements techniques
- Ajout CDN dans `index.html` : `<script src="https://d3js.org/d3.v7.min.js"></script>`
- Remplacement complet de `renderGraph()` (~40 lignes → ~150 lignes)
- Aucun changement modèle ni API

---

## 5. Status "Blocked" + Kanban-implementer

### 5a. Nouveau status "Blocked"

**Ordre complet :**
`Backlog → To Start → In Progress → Blocked → Review → Done → Archived`

**Fichiers à modifier :**

| Fichier | Changement |
|---------|-----------|
| `core-tools/kanban/kanban_api/models.py` | Ajouter `"Blocked"` dans le `Literal` du champ `status` + dans la liste `STATUSES` (entre `"In Progress"` et `"Review"`) |
| `core-tools/kanban/kanban_api/core.py` | Ajouter `"Blocked"` dans `STATUSES` (entre `"In Progress"` et `"Review"`) + dans l'ordre de `_normalize_tasks` (idem) + guard au début de `_check_dependencies` : `if target_status in ("Blocked",): return` |
| `core-tools/kanban/TASK_MODEL.md` | Mettre à jour l'ordre de statuts : ajouter `Blocked` entre `In Progress` et `Review` dans la liste de tri (§ Ordonnancement) |
| `hub/public/kanban/index.html` | Ajouter `"Blocked"` dans `STATUSES`, colonne violet `#7c3aed`, icône ⛔, `status-btn` Blocked, badge conf Blocked |

**Interaction avec `_check_dependencies` :**
- Passer une tâche en "Blocked" → pas de vérification de dépendances (DomBot bloque explicitement)
- Passer de "Blocked" → "In Progress" → `_check_dependencies` s'applique normalement

### 5b. Kanban-implementer — Clarification avant implémentation

**Interaction avec `KANBAN_MIN_CONFIDENCE` :**
- Seuil actuel `KANBAN_MIN_CONFIDENCE = 0.4` → tâche non éligible (ignorée silencieusement)
- Nouveau seuil d'ambiguïté : `0.4 ≤ confidence < 0.55` → tâche éligible mais ambiguë → Blocked
- `confidence < 0.4` → toujours non éligible (inchangé)
- `confidence ≥ 0.55` → éligible et claire → implémentation directe

**Nouveau flux (étape 1bis, après sélection) :**

1. **DomBot écrit son interprétation** dans `notes` de la tâche :
   ```
   [DomBot Plan 2026-03-XX]
   Interprétation : <ce que je comprends de la tâche>
   Approche : <ce que je vais faire concrètement>
   ```

2. **Évaluation `is_ambiguous`** — vrai si **au moins une** condition :
   - `0.4 ≤ confidence_effective < 0.55`
   - `description` absente ou < 50 caractères
   - `title` contient uniquement des mots vagues sans complément : "améliorer", "fix", "update", "check", "refactor"

3. **Si ambiguë :**
   - Ajouter dans `notes` : `Question : <ce qui manque pour implémenter>`
   - Status → **"Blocked"**
   - Telegram : `⛔ [TASK_ID] Tâche bloquée — besoin de validation avant impl. Voir kanban.`
   - Arrêt. Pas de code.

4. **Si claire :** implémentation normale.

**Validation humaine :**
1. Ping Telegram reçu
2. Aller sur la tâche dans le kanban
3. Lire le plan + question dans `notes`, corriger/compléter la `description`
4. Repasser le status à **"To Start"**
5. DomBot reprend à la prochaine session

**Changements SKILL.md :**
- Ajouter l'étape 1bis après "Étape 1 — Sélection"
- **Remplacer** (pas compléter) la règle commençant par `- **Tâches ambiguës** :` par le nouveau flux
- La règle "créer une issue" est supprimée — remplacée par "passer en Blocked"

**Changements `selector.py` :**
- Ajouter `is_ambiguous` comme `@computed_field` (Pydantic v2, `@property` avec décorateur) sur le modèle `Task` — propriété transiente, **non sérialisée** dans `tasks.json` (même pattern que `confidence_effective` et `is_eligible` existants)
- L'étape 1bis est implémentée dans `__main__.py` (après `select`, avant implémentation)

---

## Ordre d'implémentation recommandé

1. **Status "Blocked"** (transversal — débloque Graph couleurs + kanban-implementer)
2. **Renommage ClawPilot** (cosmétique, aucune dépendance)
3. **Gantt fix** (frontend only, rapide)
4. **Graph DAG** (frontend only, D3)
5. **PilotView endpoint + frontend** (le plus complexe — nouvel endpoint API async)
6. **Kanban-implementer clarification** (SKILL.md + selector.py)

---

## Hors scope
- Renommage repo GitHub / nom de domaine
- Migration des `timeline` existants vers `start_date`/`end_date` (optionnel, fait manuellement)
- Authentification multi-utilisateur
