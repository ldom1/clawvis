# DATA MODEL

> Modèle de données de référence Clawvis. Formalise les états, cycles de vie et paramètres configurables.
> Toute implémentation doit s'y conformer.
> Pour les workflows qui utilisent ces états → `docs/GOAL.md`

---

## États du kanban

Liste exhaustive et ordonnée des statuts de tâche :

| Statut | Signification | Transitions autorisées |
|--------|--------------|----------------------|
| `Backlog` | Tâche identifiée, non prioritaire | → `To Start` |
| `To Start` | Tâche prête à être traitée par @Dombot | → `In Progress`, → `Backlog` |
| `In Progress` | Tâche en cours d'implémentation | → `Done`, → `Blocked` |
| `Blocked` | Tâche bloquée — escalade humaine requise | → `To Start`, → `Backlog` |
| `Done` | Tâche complétée et validée | → (terminal) |

**Règles de transition :**
- Seul `kanban-implementer` peut passer une tâche de `To Start` à `In Progress`
- Seul @Ldom (ou le chat Clawvis) peut passer une tâche de `Backlog` à `To Start`
- Une tâche `Blocked` génère toujours un message Telegram à @Ldom
- `Done` est terminal — pas de retour arrière (créer une nouvelle tâche si besoin)

---

## Cycle de vie d'un projet

```
draft ──────────────────────────────────────────► archived
  │                                                   ▲
  │ (validation @Ldom)                                │
  ▼                                           (morning-briefing suggest)
active ◄──► backlog                                   │
  │                                                   │
  └──────────────────────────────────────────────────►┘
       (décision @Ldom)
```

| Statut | Signification | Visible dans Hub | Éligible `kanban-implementer` |
|--------|--------------|-----------------|------------------------------|
| `draft` | Opportunité non validée — générée par `proactive-innovation` | ❌ vue dédiée | ❌ |
| `active` | Projet en cours | ✅ | ✅ |
| `backlog` | Projet mis en pause | ✅ réduit, sans tâches | ❌ |
| `archived` | Projet terminé ou abandonné | ❌ | ❌ |

**Règles de transition :**
- `draft` → `active` : validation explicite de @Ldom uniquement
- `active` → `backlog` : décision @Ldom (via chat ou morning-briefing)
- `backlog` → `active` : décision @Ldom uniquement
- `* → archived` : toujours proposé par `morning-briefing`, jamais appliqué automatiquement

---

## Paramètres configurables

Vivent dans `hub_settings.json` sauf mention contraire.

| Paramètre | Défaut | Portée | Emplacement | Description |
|-----------|--------|--------|-------------|-------------|
| `max_in_progress` | `2` | global | `hub_settings.json` | Max tâches `In Progress` simultanées par projet |
| `kanban_cron_interval` | `4h` | global | `.env` (OpenClaw) | Fréquence cron `kanban-implementer` |
| `briefing_time` | `08:00` | global | `.env` (OpenClaw) | Heure déclenchement `morning-briefing` |
| `innovation_cron_interval` | `7d` | global | `.env` (OpenClaw) | Fréquence cron `proactive-innovation` |
| `weekly_review_day` | `friday` | global | `.env` (OpenClaw) | Jour déclenchement `knowledge-consolidator` hebdo |
| `inactivity_threshold_days` | `14` | global | `hub_settings.json` | Jours sans activité avant suggestion archivage |
| `telegram_notifications` | `true` | global | `hub_settings.json` | Active/désactive Telegram (utile en mode dev) |
| `discord_channels` | voir ci-dessous | global | `hub_settings.json` | Mapping channels Discord par type de log |
| `github_repo_visibility` | `private` | par projet | `hub_settings.json` | Visibilité repo créé par `project-init` |
| `poc_auto_generate` | `true` | par projet | `hub_settings.json` | Génération automatique PoC lors de `project-init` |

### Mapping Discord par défaut

```json
{
  "discord_channels": {
    "innovation": "#innovation",
    "projects":   "#projects",
    "logs":       "#logs",
    "ops":        "#ops"
  }
}
```

| Channel | Contenu |
|---------|---------|
| `#innovation` | Fiches `proactive-innovation`, opportunités détectées |
| `#projects` | Création projet, merge PoC, revue hebdo |
| `#logs` | Logs d'implémentation tâche par tâche, diffs GitHub |
| `#ops` | Métriques système, réorientations `morning-briefing`, erreurs crons |

---

## Structure de la fiche Brain (format PARA)

Toute fiche projet créée dans le Brain suit ce schéma. Fichier : `memory/projects/<slug>.md`.

```markdown
# [nom-projet]

## Contexte
Pourquoi ce projet existe. Problème adressé. Origine (vocal, innovation proactive, réutilisation...).

## Objectif
Ce que le projet doit produire concrètement (PoC, MVP, lib OSS...).

## Décisions
- [DATE] Choix technologique : React + FastAPI — raison : cohérence avec devis-ai
- [DATE] Réutilisation : invoice-parser v0.3 — pas besoin de réimplémenter le parsing

## Ressources
- Repo GitHub : [lien]
- PoC : [lien]
- Projets liés : [slug-parent-1], [slug-parent-2]

## Archive
Historique des décisions abandonnées, blocages résolus, tâches archivées.
```

**Règles :**
- La section `Décisions` est **append-only** — jamais modifiée rétroactivement, toujours datée
- `knowledge-consolidator` enrichit `Ressources` et `Archive`
- `brain-maintenance` vérifie la structure du fichier sans modifier le contenu
- `project-init` et `proactive-innovation` créent la fiche avec ce schéma complet

---

## Identité projet — clé canonique

```
project_slug == memory_page_slug == kanban_project_key
```

Un projet qui viole cette contrainte (slug divergent entre kanban et mémoire) est dans un état invalide. `brain-maintenance` peut détecter et signaler ces incohérences.
