---
name: knowledge_consolidator
description: "Two-phase skill: (collect) fetch external knowledge via curiosity.py; (consolidate) synthesize daily memory into MEMORY.md and persist with QMD."
---

# 🧠 Knowledge Consolidator

Deux modes distincts, invoqués par deux crons séparés.

## Sources de vérité

- `~/.openclaw/workspace/MEMORY.md` — index pérenne uniquement (~2000 car.), pas de daily ni Curiosity
- `~/.openclaw/workspace/memory/` — notes journalières, Curiosity, synthèses de consolidation

---

## ⚡ Exécution rapide

```bash
# Phase collect (lancer toutes les sessions curiosity)
~/.openclaw/skills/knowledge-consolidator/scripts/collect.sh

# Phase consolidate (synthèse + QMD update)
~/.openclaw/skills/knowledge-consolidator/scripts/consolidate.sh

# Session unique
uv run --directory ~/.openclaw/skills/knowledge-consolidator/core python -m knowledge_consolidator tech
```

## Phase 1 — collect (1× par jour, avant consolidate)

Invoqué par le job **Knowledge Acquisition** (23h00).

```bash
~/.openclaw/skills/knowledge-consolidator/scripts/collect.sh
# ou une session : uv run --directory ~/.openclaw/skills/knowledge-consolidator/core python -m knowledge_consolidator tech
```

Lance toutes les sessions (tech, geopolitics, culture, community, latest, tech_news). Écrit uniquement dans `memory/resources/curiosity/YYYY-MM-DD-<session>.md`. Ne pas modifier `MEMORY.md` (mémoire pérenne uniquement). Travail silencieux.

**Cette phase est silencieuse — ne pas envoyer de message Telegram.** Le rapport est réservé à la Phase 2 uniquement.

---

## Phase 2 — consolidate (23h30 chaque soir)

Invoqué par le job **Memory Consolidation**.

### Étapes

1. **Scan** : lire les fichiers de `memory/daily/` et `memory/resources/curiosity/` modifiés dans les dernières 24h ; inclure les interactions Ldom–DomBot du jour (sessions `*.jsonl` modifiées, hors crons isolés) — extraire faits, décisions, apprentissages.
2. **Synthèse** : extraire les faits durables, décisions, patterns ; regrouper par thème, dédupliquer.
3. **Écriture** : ne pas ajouter de sections datées ni de digests daily/Curiosity dans `MEMORY.md`. MEMORY.md = index pérenne uniquement (~2000 caractères max). Écrire la synthèse du jour dans `memory/daily/YYYY-MM-DD.md` (section dédiée « Consolidation ») ou dans un fichier sous `memory/` (ex. `memory/consolidation/YYYY-MM-DD.md`). Mettre à jour `MEMORY.md` seulement si un fait vraiment pérenne émerge (nouveau pattern, nouvelle ref) — sans dépasser la limite de taille.
4. **Nettoyage** : si MEMORY.md dépasse la cible ou contient du daté, le ramener à un index stable (référer daily/curiosity au lieu d’y coller le contenu).
5. **Persistance QMD** : exécuter le script :
   ```bash
   ~/.openclaw/skills/knowledge-consolidator/scripts/consolidate.sh
   ```
6. **Rapport Telegram** : envoyer à Ldom (ID: 5689694685) un résumé en suivant **`REPORT_TEMPLATE.md`** (à la racine du skill). **Il est primordial d’utiliser ce template** : N souvenirs consolidés, thèmes principaux, statut QMD, plus l’insight du jour en une phrase.

---

## Séparation avec self-improvement

| Domaine | knowledge_consolidator | self-improvement |
|---------|------------------------|------------------|
| Sources | `memory/daily/`, `memory/resources/curiosity/`, sessions | `.learnings/`, etc. |
| Cible | Synthèse → `memory/daily/` ou `memory/consolidation/` ; QMD index. `MEMORY.md` = index pérenne uniquement (pas de daily/curiosity) | `TODO.md`, `SOUL.md`, `AGENTS.md`, `TOOLS.md` |
| Nature | Connaissances & mémoire durable | Erreurs & auto-amélioration |
