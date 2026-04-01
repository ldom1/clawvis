# GOAL.md — Clawvis

> Ce document décrit la vision produit et les workflows de référence de Clawvis.
> Il sert de contexte pour orienter les développements : chaque fonctionnalité implémentée doit contribuer à rendre ces workflows possibles.
>
> Pour les règles de dev → `CLAUDE.md`
> Pour l'architecture technique → `docs/ARCHITECTURE.md`
> Pour le modèle de données → `docs/DATA-MODEL.md`

---

## TL;DR

**Clawvis est un control center self-hosted pour agents IA.**

Il résout un problème précis : après quelques prompts, les agents dérivent, le contexte se perd, rien n'est traçable. Clawvis impose un cadre — projet, kanban, mémoire, logs — pour que les agents restent autonomes *et* auditables.

**Ce qui le rend unique :**
- Le kanban est le miroir exact de la mémoire (format PARA) — pas deux outils séparés
- Les skills (crons OpenClaw) exécutent des tâches de manière autonome : innovation, implémentation, morning briefing
- Tout est self-hosted, souverain, traçable

**Cible prioritaire :** solopreneur / dev solo qui utilise déjà des LLM mais perd le contrôle sans structure.

**Le moment aha :** en 10 minutes, tu envoies un message → Clawvis structure, planifie et exécute un PoC complet. Pas de chaos. Du concret.

---

## Acteurs du workflow

| Acteur | Rôle |
|--------|------|
| **@Ldom** | L'utilisateur — entrepreneur solo, pilote les projets via Telegram et le Hub Clawvis |
| **@Dombot** | L'agent IA — instance OpenClaw configurée par @Ldom, exécute les tâches via les skills Clawvis |
| **Clawvis** | Le framework — fournit la structure (projets, kanban, mémoire, logs) et les skills que @Dombot utilise |

**Canaux de communication :**
- **Telegram** → discussion directe @Ldom ↔ @Dombot (questions, confirmations, liens)
- **Discord** → logging structuré par channels thématiques (`#innovation`, `#projects`, `#logs`, `#ops`)

**Règle fondamentale :** Telegram = conversation. Discord = observabilité. Si @Ldom n'a pas besoin d'agir, il ne reçoit pas de message Telegram.

---

## Scénario principal : de l'idée au PoC itératif

### 1. Déclenchement — @Ldom a une idée

@Ldom envoie un **message vocal** à @Dombot sur Telegram :

> *"J'ai une idée de SaaS pour automatiser les devis freelance avec l'IA. Lance un projet."*

---

### 2. Initialisation — @Dombot s'exécute

@Dombot transcrit le vocal et déclenche le **skill `project-init`** :

1. Crée le projet dans Clawvis (slug, nom, description extraits du vocal)
2. Crée le repository GitHub (repo privé lié au projet)
3. Crée la fiche projet dans le Brain (format PARA : contexte, objectif, ressources, archive)
4. Génère le kanban initial (tâches estimées, statuts `To Start` / `In Progress` / `Done`)
5. Produit un premier PoC (technologie choisie par l'agent selon le contexte)

**Telegram** → `"Projet 'devis-ai' créé ✅ — PoC disponible sur lab.dombot.tech/apps/devis-ai/"`
**Discord `#projects`** → `Nouveau projet : devis-ai — 8 tâches créées — PoC généré — [lien Hub]`

---

### 3. Exploration — @Ldom découvre le projet

@Ldom ouvre le **Hub Clawvis** :

- **Vue projet** → kanban, estimations, statut global
- **Brain** → fiche mémoire : contexte, objectif, décisions prises par l'agent
- **PoC** → prototype généré par @Dombot
- **Chat** → questions directes :
  > *"Pourquoi tu as choisi React et pas Vue ?"*
  > @Dombot explique en s'appuyant sur la fiche mémoire

@Ldom passe certaines tâches en **`To Start`** → rend les tâches éligibles au prochain cycle `kanban-implementer`.

---

### 4. Itération autonome — @Dombot tourne en fond

Toutes les **4 heures**, le **skill `kanban-implementer`** se déclenche (cron OpenClaw).

`kanban-implementer` orchestre la session complète (sélection, update statuts, PR, logs) puis délègue l'exécution unitaire au **skill `implement`** :

1. Lit les tâches en `To Start`
2. Choisit la première tâche prioritaire
3. L'implémente en s'appuyant sur le Brain
4. Met à jour le PoC
5. Passe la tâche en `Done`

**Telegram** → 1 message par session (pas par tâche) : `"Session complète ✅ — 2 tâches done — PoC mis à jour"`
**Discord `#logs`** → `[implement] devis-ai — tâche #3 done — 47 lignes ajoutées — [diff GitHub]`

---

### 5. Validation — @Ldom valide et @Dombot livre

@Ldom visualise les évolutions dans le Hub, valide (ou demande une correction via le chat).

Une fois validé, @Dombot :
- Push sur GitHub (**skill `git-sync`**)
- Met à jour le Brain (**skill `knowledge-consolidator`**)
- Logge sur **Discord `#projects`** (**skill `logger`**) : `devis-ai — PoC v0.2 mergé — 3/8 tâches complétées`

En tâche de fond : **`brain-maintenance`** maintient la structure du Brain, **`qmd`** gère les écritures mémoire structurées.

---

## Scénarios complémentaires

### 6. Morning Briefing — décision stratégique

**Déclenchement :** cron quotidien → **skill `morning-briefing`**

`morning-briefing` consolide l'état de tous les projets actifs (tâches `In Progress`, `Blocked`, `Done`), métriques système, veille tech si activée.

**Telegram** → 1 message unique :
> *"☀️ Brief du 31/03 — devis-ai: 2 tâches complétées, 1 bloquée; clawvis: 0 activité; système: OK. Répondre pour réorienter."*

@Ldom répond : *"Mets devis-ai en pause, focus sur clawvis."*

@Dombot : passe les tâches `To Start` de `devis-ai` en `Backlog`, remonte les priorités de `clawvis` en `To Start`, met à jour le Brain, confirme sur Telegram, logge sur **Discord `#ops`**.

**Ce que ce scénario révèle :** `morning-briefing` est le seul point de contact quotidien obligatoire. @Ldom pilote la stratégie depuis Telegram sans ouvrir le Hub.

---

### 7. Innovation proactive — projet draft

**Déclenchement :** cron hebdomadaire → **skill `proactive-innovation`**

Le skill détecte un pattern dupliqué entre plusieurs projets et identifie une opportunité.

1. Publie une fiche structurée sur **Discord `#innovation`** (contexte, proposition, effort estimé, lien Brain)
2. Crée un projet **`draft`** dans Clawvis (fiche Brain générée, kanban vide, invisible dans la vue principale)
3. **Telegram** → 1 message de décision : `"💡 Opportunité : 'invoice-parser' — projet draft créé. [lien Hub]"`

Si @Ldom **valide** → statut `active`, kanban généré, éligible `kanban-implementer`
Si @Ldom **rejette** → archivage du draft, décision tracée dans le Brain

**Ce que ce scénario révèle :** l'agent crée de la valeur sans sollicitation. Le mode `draft` protège la lisibilité du Hub.

---

### 8. Revue hebdomadaire — consolidation

**Déclenchement :** cron hebdomadaire → **skill `knowledge-consolidator`**

Consolide tâches terminées, vélocité, décisions Brain, blocages récurrents. Écrit dans `WEEKLY.md` ou `MEMORY.md` global.

**Discord `#projects`** → résumé par projet
**Telegram** → 1 message minimal : `"📋 Revue hebdo disponible → [lien Brain]"`

**Ce que ce scénario révèle :** Telegram porte le signal court. Le Brain est la source long terme. Les décisions de roadmap se prennent dans le Hub.

---

### 9. Nouveau projet depuis l'existant — réutilisation

**Déclenchement :** vocal Telegram → **skill `project-init`**

Avant de créer, `project-init` lit le Brain global pour détecter composants et décisions réutilisables :
- Crée le projet avec liens explicites vers les projets parents
- Kanban initial excluant les briques déjà couvertes
- Note dans le Brain : *"Réutilise invoice-parser v0.3 — pas besoin de réimplémenter"*

**Telegram** → `"Projet 'client-tracker' créé ✅ — 2 composants réutilisés depuis devis-ai. [lien]"`
**Discord `#projects`** → traçabilité de la réutilisation

**Ce que ce scénario révèle :** plus il y a de projets, plus le Brain rend `project-init` pertinent. La réutilisation est explicite et tracée.

---

## Composants et leur rôle dans les workflows

| Composant | Rôle |
|-----------|------|
| **Kanban** | Centre de pilotage — source de vérité sur ce qui reste à faire |
| **Brain (Memory)** | Mémoire long terme — l'agent s'en nourrit à chaque itération, évite la dérive |
| **Skills (crons)** | Workflows autonomes déclenchés par événement ou planification |
| **Chat** | Interaction directe @Ldom ↔ @Dombot dans le contexte du projet |
| **Logs** | Traçabilité complète — chaque action visible dans le Hub et sur Discord |
| **Hub UI** | Point d'entrée visuel — projets, kanban, Brain, PoC en un seul endroit |
| **Mode `draft`** | Bac à opportunités — visible pour décision, sans bruit dans le flux principal |

---

## Panorama des skills Clawvis

| Skill | Déclencheur | Rôle |
|-------|-------------|------|
| `project-init` | Événement (vocal/message) | Crée projet complet (slug, repo, Brain, kanban, PoC) |
| `kanban-implementer` | Cron 4h | Orchestre la session (sélection, statuts, PR, logs) → délègue à `implement` |
| `implement` | Appelé par `kanban-implementer` | Exécution unitaire d'une tâche sélectionnée |
| `morning-briefing` | Cron quotidien | Brief consolidé → Telegram + décision stratégique |
| `proactive-innovation` | Cron hebdomadaire | Détecte opportunités → draft projet + Discord `#innovation` |
| `knowledge-consolidator` | Cron hebdomadaire + post-validation | Agrège la connaissance dans `MEMORY.md` |
| `brain-maintenance` | Tâche de fond | Maintient structure et santé du Brain sur disque |
| `git-sync` | Post-validation | Synchronise workspace et repo sans committer de secrets |
| `logger` | Post-action | Centralise et structure les logs vers Discord |
| `qmd` | Écritures mémoire | Lit/écrit fichiers mémoire format QMD pour le Brain |
| `skill-tester` | CI / manuel | Teste les skills et renvoie un rapport de santé |
| `reverse-prompt` | Manuel | Dérive les bons prompts depuis le comportement observé |

---

## Invariants — à respecter dans toute implémentation

- **Tout est tracé.** Chaque action de @Dombot produit un log visible (Hub + Discord).
- **Le Brain est la mémoire de l'agent.** @Dombot lit le Brain avant d'agir — jamais de zéro.
- **Le kanban est la source de vérité.** État du projet = état du kanban. Pas d'actions hors kanban.
- **@Ldom garde le contrôle.** L'agent propose et exécute, @Ldom valide avant tout push définitif.
- **Telegram = conversation, Discord = observabilité.**

---

## Contraintes transverses — Signal vs Bruit

### Telegram : 1 message max par événement significatif

| Situation | Comportement attendu |
|-----------|----------------------|
| Cron interne (implémentation, maintenance Brain) | Pas de message Telegram — Discord uniquement |
| Session `kanban-implementer` complète | 1 message résumé (pas 1 par tâche) |
| Projet créé | 1 message de confirmation avec lien |
| Revue hebdo | 1 message minimal avec lien Brain |
| Blocage ou erreur critique | 1 message d'alerte avec question précise |

**Règle d'or :** si @Ldom n'a pas besoin d'agir, il ne reçoit pas de message Telegram.

### Hub : lisibilité multi-projets

| Mécanisme | Description |
|-----------|-------------|
| Statut `draft` | Projets non validés, masqués de la vue principale |
| Statut `backlog` | Projets en pause, visibles mais réduits (sans tâches) |
| Vue projet unique | Navigation par projet — pas de kanban global agrégé |
| Limite `In Progress` | `kanban-implementer` ne monte jamais plus de N tâches (défaut : 2, configurable) |
| Archivage suggéré | `morning-briefing` propose l'archivage après X jours d'inactivité |

---

## Roadmap exécution (suivi ops / produit)

### [DONE] 2026-04-01 — Stabilisation Dombot & Core skills

- **Cron git-sync** : l’échec venait de `~/Lab/git-sync.sh` (fetch impossible sur certains repos Lab) qui terminait en exit 1 après un push `openclaw-dombot` réussi — le script `git-sync` ne propage plus cet exit (backup OpenClaw prioritaire).
- **Backup** : `README.md` dans le dépôt `openclaw-dombot` (architecture + DRP + snippet compaction), copié par le skill `git-sync`.
- **Skills** : `project-init` (init projet via API Kanban), `implement` (pont contexte tâche → agent), documenté dans `kanban-implementer`.
- **Hub** : `marked` avec `gfm` + `breaks` ; KPI logs (INFO / WARN / ERROR / DEBUG / Total) cliquables ; cartes Kanban moins denses (méta essentielle).
- **Logger Discord** : filtre anti-spam — erreurs, échecs, init/milestone projet ; pas les `:complete` routiniers.
- **OpenClaw 2026.4.1** : voir snippet `agents.defaults.compaction.model` dans le README backup (ex. `gpt-4o-mini` / Haiku selon routeur).

### [TODO] Phase 2.5 — laptop-first, wizard

- Parcours d’installation guidé (wizard) sur machine locale.
- Réduction de friction « premier run » sans SSH devbox.
