---
name: knowledge_consolidator
description: "Two-phase skill: (collect) fetch external knowledge via curiosity.py; (consolidate) synthesize daily memory into MEMORY.md and persist with QMD."
---

# 🧠 Knowledge Consolidator

Deux modes distincts, invoqués par deux crons séparés.

## Sources de vérité

- `$BRAIN_PATH/inbox/daily/` — notes journalières
- `$BRAIN_PATH/resources/knowledge/curiosity/<type>/` — notes de curiosité par domaine

`BRAIN_PATH` est défini dans `~/ai-dotfiles/config/brain.env` → `/mnt/c/Users/louis/Documents/Local Brain`

---

## ⚡ Exécution rapide

```bash
# Phase collect (lancer toutes les sessions curiosity)
${CLAWVIS_ROOT}/skills/knowledge-consolidator/scripts/collect.sh

# Phase consolidate (synthèse + QMD update)
${CLAWVIS_ROOT}/skills/knowledge-consolidator/scripts/consolidate.sh

# Session unique
uv run --directory ${CLAWVIS_ROOT}/skills/knowledge-consolidator/core python -m knowledge_consolidator tech
```

## Phase 1 — collect (1× par jour, avant consolidate)

Invoqué par le job **Knowledge Acquisition** (23h00).

```bash
${CLAWVIS_ROOT}/skills/knowledge-consolidator/scripts/collect.sh
# ou une session : uv run --directory ${CLAWVIS_ROOT}/skills/knowledge-consolidator/core python -m knowledge_consolidator tech
```

Lance toutes les sessions (tech, geopolitics, culture, community, latest, tech_news). Écrit dans `$BRAIN_PATH/resources/knowledge/curiosity/<type>/YYYY-MM-DD-knowledge_<type>.md`. Ne pas modifier `MEMORY.md` (mémoire pérenne uniquement). Travail silencieux.

**Cette phase est silencieuse — ne pas envoyer de message Telegram.** Le rapport est réservé à la Phase 2 uniquement.

---

## Phase 2 — consolidate (23h30 chaque soir)

Invoqué par le job **Memory Consolidation**.

### Étapes

1. **Scan** : lire les fichiers de `$BRAIN_PATH/inbox/daily/` et `$BRAIN_PATH/resources/knowledge/curiosity/` modifiés dans les dernières 24h ; inclure les interactions Ldom–DomBot du jour (sessions `*.jsonl` modifiées, hors crons isolés) — extraire faits, décisions, apprentissages.
2. **Synthèse** : extraire les faits durables, décisions, patterns ; regrouper par thème, dédupliquer.
3. **Écriture** : ne pas ajouter de sections datées ni de digests daily/Curiosity dans `MEMORY.md`. MEMORY.md = index pérenne uniquement (~2000 caractères max). Écrire la synthèse du jour dans `$BRAIN_PATH/inbox/daily/YYYY-MM-DD.md` (section dédiée « Consolidation »). Mettre à jour `MEMORY.md` seulement si un fait vraiment pérenne émerge (nouveau pattern, nouvelle ref) — sans dépasser la limite de taille.
4. **Nettoyage** : si MEMORY.md dépasse la cible ou contient du daté, le ramener à un index stable (référer daily/curiosity au lieu d’y coller le contenu).
5. **Persistance QMD** : exécuter le script :
   ```bash
   ${CLAWVIS_ROOT}/skills/knowledge-consolidator/scripts/consolidate.sh
   ```
6. **Rapport Telegram** : envoyer à Ldom (ID: 5689694685) un résumé en suivant **`REPORT_TEMPLATE.md`** (à la racine du skill). **Il est primordial d’utiliser ce template** : N souvenirs consolidés, thèmes principaux, statut QMD, plus l’insight du jour en une phrase.

---

## Séparation avec self-improvement

| Domaine | knowledge_consolidator | self-improvement |
|---------|------------------------|------------------|
| Sources | `$BRAIN_PATH/inbox/daily/`, `$BRAIN_PATH/resources/knowledge/curiosity/`, sessions | `.learnings/`, etc. |
| Cible | Synthèse → `$BRAIN_PATH/inbox/daily/` ; QMD index. `MEMORY.md` = index pérenne uniquement (pas de daily/curiosity) | `TODO.md`, `SOUL.md`, `AGENTS.md`, `TOOLS.md` |
| Nature | Connaissances & mémoire durable | Erreurs & auto-amélioration |
