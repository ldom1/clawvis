---
name: proactive-innovation
description: "Scan Second Brain projects every 4h: propose improvements in project .md (section Améliorations proposées (auto) only, never Timeline), create MR when fix is certain, propose business/OSS ideas to CAPS entrepreneur. Use when: cron Self-Improvement Review (run after self-improvement) or when Ldom asks for proactive project/innovation scan."
---
# Proactive Innovation

Scan périodique du Second Brain : améliorations projets, MR si certain, idées entreprise/OSS. Conçu pour être invoqué **après** le skill self-improvement dans le cron 4h, avec un rapport combiné concis.

**Référence :** [[memory/resources/knowledge/operational/proactive-innovation-approach]]

---

## Script (évite les boucles de messages)

⚠️ **IMPORTANT** : Il n’existe PAS de `scripts/scan_projects.py` ni de `scripts/innovate.py`.
L’exécution se fait UNIQUEMENT via le module Python ou le script shell :

```bash
# Option 1 — Script shell (recommandé, gère les logs + Telegram)
${CLAWVIS_ROOT}/skills/proactive-innovation/scripts/run-proactive-innovation.sh

# Option 2 — Module Python direct
uv run --directory ${CLAWVIS_ROOT}/skills/proactive-innovation/core python -m proactive_innovation
```

Le package `core/` et le script `scripts/run-proactive-innovation.sh` exécutent le scan **sans** que l’agent envoie de messages en boucle : un seul rapport est produit, puis **un seul** message Telegram à la fin.

Le module Python ne fait **jamais** d’appel Telegram/OpenClaw ; le script shell envoie **une fois** le rapport combiné. Limites par run : 10 projets, 5 améliorations/projet, 3 idées.

---

## Entrées

- `$BRAIN_PATH/resources/projects/*.md` (projets actifs, hors `_template`)
- Champ `path` dans le frontmatter (repo à scanner)
- `$BRAIN_PATH/resources/knowledge/`, `$BRAIN_PATH/resources/knowledge/curiosity/` (pour idées)
- `$BRAIN_PATH/caps/entrepreneur.md` (destination idées)

`BRAIN_PATH` est défini dans `~/ai-dotfiles/config/brain.env` → `/mnt/c/Users/louis/Documents/Local Brain`
- **Kanban API** :
  - `http://localhost:8088/api/kanban/tasks` (GET pour contexte, POST pour créer des tâches),
  - `http://localhost:8088/api/kanban/meta` (PUT) pour mettre à jour la zone **PM Meta** (vision/description synthétique, liens de PR ; les compteurs restent gérés automatiquement par l'API).

---

## Phase 1 — Scan projets

**Règle :** les propositions vont **uniquement** dans la section **## Améliorations proposées (auto)**. Ne jamais ajouter de lignes dans la table Timeline (réservée aux tâches validées par Ldom).

1. Pour chaque fichier dans `memory/projects/*.md` (exclure `_template.md`) :
   - Lire objectif, Timeline, Ressources liées.
   - Si `path` existe et est lisible : explorer le repo (structure, config, tests).
   - Proposer **améliorations** (fix, perf, DX, sécurité) dans la section **## Améliorations proposées (auto)**.
2. **Format de la section** (à créer ou compléter) :
   - Placer la section après **## Timeline** et avant **## Ressources liées** (ou **## Notes**).
   - Chaque item : `- **YYYY-MM-DD** — Description courte (contexte si besoin).`
   - Ne pas dupliquer une tâche déjà dans la Timeline ni une proposition déjà listée.
3. Si la section n'existe pas, la créer ; sinon append les nouveaux items (sans supprimer les anciens).
4. **Kanban integration :** pour chaque amélioration proposée, créer aussi une tâche via l'API Kanban
   avec un score de confiance estimé selon la grille ci-dessous :

   | Type d'amélioration | `confidence` |
   |---------------------|-------------|
   | Correctif certain (typo, config cassée, sécurité) | `0.75` |
   | Amélioration standard (DX, perf mesurable) | `0.55` |
   | Idée spéculative (feature, refacto subjective) | `0.3` |

   > `0.55` (et non `0.5`) différencie visuellement une amélioration explicitement évaluée du
   > défaut `null → 0.50` affiché sur les tâches sans score.

   ```bash
   curl -X POST http://localhost:8088/api/kanban/tasks \
     -H 'Content-Type: application/json' \
     -d '{"title":"...","project":"<nom-projet>","priority":"Medium","assignee":"DomBot","confidence":0.55}'
   ```
   La tâche arrive dans **To Start** — Ldom valide ou déplace. Vérifier via GET /api/kanban/tasks avant de créer pour éviter les doublons.

---

## Phase 2 — MR si « certain »

- **Certain =** correctif sans ambiguïté : typo critique, config cassée, dépendance de sécurité, régression connue. Pas de refacto subjective ni feature non validée.
- **Actions :** branche → fix minimal → ouvrir MR (ou commit si pas de workflow MR). Rédiger 1–2 lignes par MR pour le report.
- **Pas certain :** rester en proposition dans le .md, pas de MR.

---

## Phase 3 — Idées entrepreneur / OSS

- Lire `$BRAIN_PATH/resources/knowledge/` et `$BRAIN_PATH/resources/knowledge/curiosity/` (ou synthèses récentes).
- Proposer des idées courtes (entreprise, OSS, side-project) et les écrire dans `$BRAIN_PATH/resources/innovation/YYYY-MM-DD-<sujet>.md` (une idée = un fichier) et dans `$BRAIN_PATH/caps/entrepreneur.md` (section **Idées (propositions auto)**).
- Une idée = un paragraphe court, ton propositionnel. Ldom trie et valide avant promotion en projet.
- Pour les idées structurées, créer aussi une tâche Kanban avec `confidence: 0.3` (idée spéculative) :
  ```bash
  curl -X POST http://localhost:8088/api/kanban/tasks \
    -H 'Content-Type: application/json' \
    -d '{"title":"...","project":"entrepreneur","priority":"Low","assignee":"DomBot","confidence":0.3}'
  ```

---

## Rapport (cron 4h)

**Il est primordial** de suivre le format défini dans **`REPORT_TEMPLATE.md`** (à la racine du skill) pour le message envoyé à Ldom (Telegram).

Si invoqué avec self-improvement dans le même cron, produire **un seul message** :

- **Learnings** (résumé self-improvement) : 1 ligne.
- **Innovation** : projets scannés, N todos/améliorations ajoutés (+ tâches kanban créées), M MR créées (avec **lien URL** et 1 ligne par MR si M > 0), P idées → entrepreneur ; lien Kanban si pertinent.
- Longueur totale : 2–4 lignes max.

Exemple : *« 4h — Learnings: tout vert. Innovation: 3 projets scannés, 2 améliorations (hub, debate-arena), 1 MR (hub: nginx try_files) [lien]. 1 idée → entrepreneur. Kanban: [url]. »*

---

## Séparation avec les autres skills

| Skill | Rôle |
|-------|------|
| **self-improvement** | .learnings, promotion → AGENTS/SOUL/TOOLS, réactif |
| **knowledge_consolidator** | `$BRAIN_PATH/inbox/daily/`, curiosity notes, consolidation |
| **proactive-innovation** | Scan projets Second Brain, MR si certain, idées CAPS entrepreneur |
