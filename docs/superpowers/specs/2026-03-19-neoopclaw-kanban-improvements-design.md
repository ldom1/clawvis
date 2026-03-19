# Design Spec — NeoOpClaw + Kanban Improvements
**Date:** 2026-03-19
**Status:** Approved
**Scope:** Renommage dombot-labos → NeoOpClaw + 4 améliorations kanban

---

## 1. Renommage : NeoOpClaw

### Décision
`dombot-labos` devient **NeoOpClaw**.

- **Logique :** Neo (Matrix) + Op (Ops/orchestration) + Claw (grip/outil)
- **Tagline :** *"Your personal AI agent OS — Matrix-grade orchestration, on your machine."*
- **Agent DomBot :** inchangé (c'est l'agent, pas le produit)

### Périmètre du changement
| Fichier | Changement |
|---------|-----------|
| `README.md` | Titre + tagline |
| `landing/src/` | Hero title, meta tags, `<title>` |
| `landing/package.json` | `name: "neoopclaw-landing"` |
| `docker-compose.yml` | Labels/container names |
| `TASK_MODEL.md` | Mention du produit |

**Hors scope :** renommage du repo GitHub (action manuelle), nom de domaine, skills internes.

---

## 2. ClawPilot — Dashboard de pilotage (PM Meta)

### Problème
La section PM Meta actuelle n'affiche que des compteurs bas-niveau (tâches créées, transitions). L'humain ne peut pas suivre l'activité de la semaine.

### Design

La section PM Meta est rebaptisée **ClawPilot** et restructurée en 4 blocs repliables :

#### Bloc 1 — Activité hebdomadaire
- Colonnes : Semaine passée / Cette semaine
- Métriques : tasks créées, tasks Done, commits (depuis git log)
- Trend : indicateur ↑↓ entre les deux semaines

#### Bloc 2 — Projets en cours
- Liste des projets avec tâches actives (In Progress + To Start)
- Par projet : N tâches actives, effort restant (h), assignee majoritaire

#### Bloc 3 — Derniers 5 commits
Tableau : `date | repo | message court | auteur`
Source : `GET /stats/weekly` → appel `git log` sur les repos configurés via env `LAB_REPOS`.

#### Bloc 4 — En attente de validation
- Tasks en status "Review" ou "Blocked" sans assignee humain
- Badge rouge si > 3 jours sans action
- Clic → ouvre la modale détail

### Changements techniques
- **Nouvel endpoint** `GET /api/kanban/stats/weekly` dans kanban FastAPI
  - Calcule vélocité sur 7j glissants (comparé aux 7j précédents)
  - Parse `git log --oneline --since="14 days ago"` sur `LAB_REPOS`
  - Retourne : `{ weeks: [{created, done, commits}×2], projects: [...], recent_commits: [...], pending_review: [...] }`
- **Frontend** : PM Meta card remplacée par ClawPilot card, sections `<details>` repliables, refresh via SSE existant
- **Config** : `LAB_REPOS` = liste de chemins git séparés par `:` (env var dans `.env`)

---

## 3. Gantt — Barres proportionnelles

### Problème
Le Gantt actuel place toutes les barres à `left: 210px` fixe avec une largeur calculée incorrectement. Il ne représente pas la durée des tâches.

### Design
Barres proportionnelles à la durée réelle :

- `start = start_date ?? created` (champs déjà présents dans le modèle)
- `end = end_date ?? timeline`
- Tâches sans date de fin → exclues, compteur affiché ("X tâches sans date")
- Tâches Done → affichées en vert semi-transparent
- Axe temporel : graduations en **semaines** (lisible même sur 3 mois)
- Clic sur barre → ouvre modale détail existante
- Label à gauche tronqué à 160px, label de durée dans la barre si ≥ 3 jours

### Calcul de position
```
barLeft = LABEL_WIDTH + (start - rangeStart) / totalMs * chartWidth
barWidth = max(8px, (end - start) / totalMs * chartWidth)
```

### Changements techniques
Uniquement frontend (`index.html` kanban). Aucun changement modèle ni API.

---

## 4. Graph — DAG topologique par projet

### Problème
Tous les nœuds sont à `cx=120` (même position X). La vue est illisible : pile verticale avec flèches sur la même ligne.

### Design
Layout D3.js force-directed avec contrainte topologique, groupé par projet.

#### Disposition
- **Un groupe par projet** : boîte encadrée avec label projet en haut
- **Colonnes topologiques** : niveau 0 = pas de dépendances entrantes, niveau 1 = dépend d'un niveau 0, etc.
- **Tâches sans dépendances dans des projets isolés** → groupe "Standalone"
- **Si aucune dépendance dans le filtre actif** → message clair (comportement actuel conservé)

#### Visuel des nœuds
- Couleur par status (même palette que le board : cyan=To Start, blue=In Progress, amber=Review, green=Done, purple=Blocked, gray=Backlog)
- Rayon proportionnel à `effort_hours` (min 12px, max 22px)
- Clic → ouvre modale détail

#### Arêtes
- Flèches directionnelles (marker-end)
- Couleur selon status de la tâche source

### Changements techniques
- Ajout D3.js v7 via CDN dans `index.html` : `<script src="https://d3js.org/d3.v7.min.js"></script>`
- Remplacement complet de `renderGraph()` (~40 lignes → ~120 lignes)
- Aucun changement modèle ni API

---

## 5. Kanban-implementer — Clarification avant implémentation

### Problème
DomBot implémente des tâches avec des descriptions ambiguës, produisant des PRs incorrectes (ex: PR ruflo).

### Nouveau status : "Blocked"
Ajout du status **Blocked** dans le système :

- **Ordre :** `Backlog → To Start → In Progress → Blocked → Review → Done → Archived`
- **Couleur UI :** violet (`#7c3aed`)
- **Icône :** ⛔
- **Colonne kanban :** 6ème colonne visible (entre In Progress et Review)

### Nouveau flux kanban-implementer (étape 1bis)

Après sélection de la tâche et avant toute implémentation :

1. **DomBot écrit son interprétation** dans le champ `notes` de la tâche :
   ```
   [DomBot Plan 2026-03-XX]
   Interprétation : <ce que je comprends de la tâche>
   Approche : <ce que je vais faire concrètement>
   ```

2. **Évaluation de clarté** — la tâche est "ambiguë" si **l'une** de ces conditions est vraie :
   - `confidence < 0.55`
   - `description` absente ou < 50 caractères
   - `title` contient des mots vagues : "améliorer", "fix", "update", "check" sans complément

3. **Si ambiguë :**
   - Status → **"Blocked"**
   - Notes mises à jour avec la question spécifique : `Question : <ce qui manque pour implémenter>`
   - Telegram : `⛔ [TASK_ID] Tâche bloquée — besoin de validation avant impl. Voir kanban.`
   - Arrêt. Pas de code.

4. **Si claire :** implémentation normale selon le workflow existant.

### Validation humaine
1. Tu reçois le ping Telegram
2. Tu vas sur la tâche dans le kanban
3. Tu lis le plan DomBot dans `notes`, tu complètes/corriges la `description`
4. Tu repasses le status à **"To Start"**
5. DomBot reprend à la prochaine session

### Changements techniques
- **TASK_MODEL.md** : ajouter "Blocked" dans la liste des statuts
- **`kanban_api/core.py`** : ajouter "Blocked" dans `VALID_STATUSES`
- **`index.html`** : ajouter colonne Blocked, couleur violet, icône ⛔, status-btn Blocked
- **`kanban-implementer/SKILL.md`** : ajouter étape 1bis (clarification)
- **`kanban-implementer/core/kanban_implementer/selector.py`** : ajouter logique `is_ambiguous`

---

## Ordre d'implémentation recommandé

1. Status "Blocked" (transversal — débloque Graph couleurs + kanban-implementer)
2. Renommage NeoOpClaw (cosmétique, aucune dépendance)
3. Gantt fix (frontend only, rapide)
4. Graph DAG (frontend only, D3)
5. ClawPilot endpoint + frontend (le plus complexe — nouvel endpoint API)
6. Kanban-implementer clarification (SKILL.md + selector.py)

---

## Hors scope
- Renommage repo GitHub / nom de domaine
- Migration des `timeline` existants vers `start_date`/`end_date` (optionnel, fait manuellement)
- Authentification multi-utilisateur
