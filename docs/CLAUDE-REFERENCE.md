# Référence agent — complément de CLAUDE.md

> Détail et politiques **hors hot path** : ouvrir quand la tâche le exige (install, UI review, CI, Authelia/Dombot, résolution mémoire active, etc.).
> Le **résumé** toujours chargé → [`CLAUDE.md`](../CLAUDE.md).

**Sources canoniques :** `GOAL.md` · `docs/ARCHITECTURE.md` · `docs/PITFALLS.md` · `docs/DATA-MODEL.md`

---

## Identité Clawvis — modes

Clawvis assume une identité inspirée de Clovis et des Mérovingiens (onboarding mémorable, FR). Référence : https://fr.wikipedia.org/wiki/Clovis_Ier

| Mode | Usage | Description |
|------|-------|-------------|
| **Franc** (1) | Recommandé | Démarrage rapide Docker — tout est configuré |
| **Mérovingien** (2) | Avancé | Déploiement serveur / VPS, ports et chemins configurables |
| **Soissons** (3) | Contribution | Dev local, open source |

---

## Philosophie — adoptabilité

- Install = 1 commande, zéro jargon pour l’utilisateur final (Franc par défaut)
- Options techniques existent mais ne sont pas le chemin par défaut
- Toute friction d’onboarding = bug

### Règles absolues d’installation

- Entrée : `get.sh` (one-liner) ou `./install.sh` — pas `clawvis install` comme premier contact
- `clawvis install` = re-run wizard **après** install
- `install.sh` : chmod, symlink `~/.local/bin/clawvis`, PATH, wizard ; utilisateur : **une commande** pour démarrer
- README : `get.sh` en premier, `git clone + ./install.sh` en secours
- `get.sh` → `~/.clawvis` par défaut (`CLAWVIS_DIR` surchargeable)
- **Pas de clé API à l’install** — provider via Hub `/settings/`

---

## Contrat repository — Core vs Instance

**Core** : `hub/`, `kanban/`, `hub-core/`, `skills/`, `scripts/`, compose + installer à la racine.

**Instance** : `instances/<instance_name>/` — overrides, secrets, branding, mémoire, données opérationnelles.

### Règles strictes

- DO : customisations **uniquement** sous `instances/<instance_name>/`
- DO : updates via **releases** versionnées
- DO NOT : patcher le core root pour un besoin instance ; pas de secrets trackés à la racine ; pas `main` si stabilité requise ; pas de multiplication de scripts shell sous l’instance (objectif : pas besoin de cloner pour l’utilisateur final)

### Layout instance (cible)

```
instances/<instance_name>/
  docker-compose.override.yml
  .env.local
  memory/
    projects/
    resources/
    daily/
    archive/
    todo/
```

### Source de vérité projet

- `project_slug == memory_page_slug == kanban_project_key`
- `memory/projects/<slug>.md` canonique ; Kanban utilise le même slug

---

## Contrat API — domaines

| Domaine | Préfixe | Contenu |
|---------|---------|---------|
| Kanban | `/api/hub/kanban/*` | projects, tasks, deps, stats |
| Brain | `/api/hub/memory/*` | memory tree, Quartz, brain rebuild |
| Logs | `/api/hub/logs/*` | process logs, filters, SSE |
| Chat | `/api/hub/chat/*` | LLM actions, streaming |

**Règle absolue :** Brain/Quartz **jamais** sous la surface Kanban uniquement ; le frontend utilise le bon préfixe.

---

## Contrat UI — straightforward & professional

Hub, Settings, Kanban, Logs, prompts install : clarté, ton pro, dense mais lisible, layout cohérent, statuts actionnables, contrôles stables, métriques critiques visibles, a11y baseline, **parité** `hub/src` et `hub/public`.

### Checklist PR UI (avant merge)

- [ ] Action principale évidente en moins de 5 s
- [ ] KPIs system/logs/kanban visibles sans scroll
- [ ] Filtres / refresh / toggles stables
- [ ] Copy courte et professionnelle
- [ ] Parité dev/prod

---

## CI / Release (workflows)

| Workflow | Déclencheur | Rôle |
|----------|-------------|------|
| `ci.yml` | PR / push | Shell, hub format+tests+build, Python compile |
| `license.yml` | PR | Fichier MIT |
| `release-dry-run.yml` | PR | Format tag release |
| `release.yml` | Tag `vYYYY-MM-dd` | GitHub Release |

---

## Commandes CLI

```bash
clawvis start | doctor | shutdown | restart
clawvis install
clawvis deploy
clawvis update status [--json] | wizard | --tag <vYYYY-MM-dd> | --channel stable|beta|dev
clawvis backup create | list
clawvis restore <backup-id>
clawvis uninstall --dry-run | --all --yes
```

---

## Active Brain Memory (hub-core)

Résolution via `hub_core.brain_memory.active_brain_memory_root` :

1. Parcourt `linked_instances` — candidat si `<path>/memory` existe
2. Si `MEMORY_ROOT` == un candidat → ce candidat gagne
3. Sinon premier candidat (tri lexicographique)
4. Sinon `MEMORY_ROOT` direct

`GET /hub/settings` expose `active_brain_memory`. Tests : `hub-core/tests/test_brain_memory.py`.

**Démarrage par profil (détail)** → `docs/ARCHITECTURE.md` § *Modes de démarrage*.

---
