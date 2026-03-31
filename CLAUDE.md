# CLAUDE.md

> Règles permanentes pour Claude et Cursor. Ne contient que ce qui est stable et actionnable.
> Pour le contexte produit → `docs/GOAL.md`
> Pour l'architecture technique → `docs/ARCHITECTURE.md`
> Pour les bugs connus et dettes → `docs/PITFALLS.md`
> Pour le modèle de données → `docs/DATA-MODEL.md`

---

## Identité Clawvis — Modes

Clawvis assume une identité inspirée de Clovis et des Mérovingiens pour rendre l'onboarding mémorable et française. Référence : https://fr.wikipedia.org/wiki/Clovis_Ier

| Mode | Usage | Description |
|------|-------|-------------|
| **Franc** (1) | Recommandé | Démarrage rapide Docker — tout est configuré |
| **Mérovingien** (2) | Avancé | Déploiement serveur / VPS, ports et chemins configurables |
| **Soissons** (3) | Contribution | Dev local, open source |

---

## Philosophie — Adoptabilité d'abord

- Install = 1 commande, zéro connaissance technique requise (mode Franc par défaut)
- Labels et prompts en langage clair — pas de jargon Docker/nginx/uv pour l'utilisateur final
- Options techniques (serveur, ports, stack dev) existent mais ne sont pas le chemin par défaut
- Toute friction dans l'onboarding est un bug, pas un "nice to have"

### Règles absolues d'installation

- Point d'entrée unique : `get.sh` (one-liner) ou `./install.sh` — jamais `clawvis install` comme premier contact
- `clawvis install` = raccourci post-install pour re-run le wizard, PAS le bootstrap initial
- `install.sh` gère tout : chmod, symlink `~/.local/bin/clawvis`, injection PATH, wizard
- Un nouvel utilisateur ne tape jamais plus d'une commande pour démarrer
- README : montrer `get.sh` one-liner EN PREMIER, `git clone + ./install.sh` en fallback
- `get.sh` clone dans `~/.clawvis` par défaut, surchargeable via `CLAWVIS_DIR`
- **L'install ne demande pas de clé API.** Provider configuré post-install via Hub UI (`/settings/`)

---

## Contrat Repository — Core vs Instance

Deux couches strictement séparées :

**Core** (partagé, géré upstream) :
- `hub/`, `kanban/`, `hub-core/`, `skills/`, `core-tools/logger/`, `scripts/`
- Fichiers root : compose, installer

**Instance** (géré par l'utilisateur) :
- `instances/<instance_name>/`
- Overrides locaux, secrets, branding, chemins runtime, routes privées
- Mémoire et données opérationnelles instance-spécifiques

### Règles strictes

- DO : implémenter les customisations dans `instances/<instance_name>/` uniquement
- DO : consommer les updates Clawvis depuis des releases versionnées
- DO NOT : patcher les fichiers core root pour des besoins instance-spécifiques
- DO NOT : stocker des secrets dans des fichiers root trackés
- DO NOT : lier une instance à `main` si la stabilité compte

### Layout instance (cible)

```
instances/<instance_name>/
  docker-compose.override.yml
  .env.local                    # gitignored
  memory/
    projects/                   # source de vérité projet (markdown)
    resources/
    daily/
    archive/
    todo/
```

### Source de vérité projet

- `project_slug == memory_page_slug == kanban_project_key`
- La page mémoire `memory/projects/<slug>.md` est canonique
- Le Kanban utilise le même slug comme clé projet

---

## Contrat API — Domaines séparés

Toutes les APIs sous `/api/hub/*`, strictement séparées par domaine :

| Domaine | Préfixe | Contenu |
|---------|---------|---------|
| Kanban | `/api/hub/kanban/*` | projects, tasks, deps, stats |
| Brain | `/api/hub/memory/*` | memory tree, Quartz, brain rebuild |
| Logs | `/api/hub/logs/*` | process logs, filters, SSE |
| Chat | `/api/hub/chat/*` | LLM actions, streaming |

**Règle absolue :** les endpoints Brain/Quartz ne vivent jamais sous la surface Kanban API. Le frontend appelle le préfixe de domaine correspondant.

---

## Contrat UI — Straightforward & Professional

Toutes les surfaces utilisateur (Hub, Settings, Kanban, Logs, prompts install) :

- **Clarté d'abord** : hiérarchie claire, actions évidentes, pas de bruit décoratif
- **Ton professionnel** : labels concis, copy neutre, pas de wording gimmick dans les workflows core
- **Dense mais lisible** : KPIs, statuts, filtres — sans clutter visuel
- **Layout cohérent** : même espacement, mêmes card styles, même comportement boutons partout
- **Statut actionnable** : chaque badge/carte aide à la décision (connecté/non configuré, up/down, done/blocked)
- **Contrôles prédictibles** : filtres et refresh en position stable — pas de UI qui saute
- **Pas d'info critique cachée** : métriques primaires toujours visibles au-dessus du fold
- **Accessibilité baseline** : contraste fort, focus states clairs, labels sémantiques, keyboard-friendly
- **Parité dev/prod** : `hub/src` et `hub/public` visuellement et fonctionnellement alignés

### Checklist PR UI (5 points obligatoires avant merge)

- [ ] **Clarté** : action principale et purpose de la page évidents en < 5 secondes
- [ ] **KPIs critiques visibles** : métriques system/logs/kanban sans scroll
- [ ] **Contrôles stables** : filtres, refresh, toggles alignés et prédictibles
- [ ] **Copy quality** : labels courts, professionnels, sans ambiguïté
- [ ] **Parité dev/prod** : comportement et layout identiques entre `hub/src` et `hub/public`

---

## Règles d'outillage

| Composant | Outil | Commande |
|-----------|-------|---------|
| Hub (frontend) | **Yarn Berry 4** (`yarn@4.12.0`) | `yarn --cwd hub <cmd>` — jamais `npm` |
| CLI (`clawvis-cli/`) | **npm** | `npm ci` / `npm install` |
| Kanban API + hub-core | **uv** | `uv run ...` — jamais `pip` directement |
| CI gate | bash | `bash tests/ci-all.sh` → doit retourner 0 avant tout merge |

---

## Contrat CI / Release

| Workflow | Déclencheur | Rôle |
|----------|-------------|------|
| `ci.yml` | PR / push | Shell syntax, hub format+tests+build, Python compile check |
| `license.yml` | PR | Valide contenu fichier MIT |
| `release-dry-run.yml` | PR | Valide format du tag release futur |
| `release.yml` | Tag `vYYYY-MM-dd` | Publie GitHub Release notes automatiquement |

---

## Commandes CLI (référence)

```bash
# Dev local
clawvis start
clawvis doctor
clawvis shutdown
clawvis restart

# Install / setup
clawvis install        # re-run wizard post-install
clawvis setup provider # configurer provider (future)

# Deploy
clawvis deploy

# Update
clawvis update status
clawvis update status --json
clawvis update wizard
clawvis update --tag <vYYYY-MM-dd>
clawvis update --channel stable|beta|dev

# Backup
clawvis backup create
clawvis backup list
clawvis restore <backup-id>

# Uninstall
clawvis uninstall --dry-run
clawvis uninstall --all --yes
```

---

## Active Brain Memory (hub-core)

La racine mémoire active est résolue par `hub_core.brain_memory.active_brain_memory_root` :

1. Parcourt `linked_instances` — si `<path>/memory` existe, c'est un candidat
2. Si `MEMORY_ROOT` == un des candidats → ce candidat gagne
3. Sinon → premier candidat après tri lexicographique
4. Si aucun linked instance n'a de `memory/` → utilise `MEMORY_ROOT` directement

`GET /hub/settings` expose `active_brain_memory` pour que le Hub UI sache quelle mémoire est active. Tests : `hub-core/tests/test_brain_memory.py`.

---

## Modèle de démarrage par profil

| Profil | Memory API démarrée par |
|--------|------------------------|
| **Franc** (Docker) | `docker compose up hub hub-memory-api` — nginx proxy `/api/hub/memory/` → service |
| **Mérovingien** (VPS) | `docker compose up -d --build` — stack complète |
| **Soissons** (dev local) | `scripts/start.sh` — Kanban API + Memory API (uvicorn) + Vite |

---

## GitNexus — Code Intelligence

Index : **clawvis** (2142 symbols, 4570 relationships, 172 execution flows).

> Si GitNexus signale un index stale : `npx gitnexus analyze`

### Toujours faire

- **MUST** : `gitnexus_impact({target: "symbolName", direction: "upstream"})` avant toute édition de symbol
- **MUST** : `gitnexus_detect_changes()` avant tout commit
- **MUST** : alerter l'utilisateur si impact retourne HIGH ou CRITICAL

### Ne jamais faire

- NEVER éditer une fonction/classe sans `gitnexus_impact` d'abord
- NEVER ignorer les warnings HIGH/CRITICAL
- NEVER renommer avec find-and-replace — utiliser `gitnexus_rename`
- NEVER committer sans `gitnexus_detect_changes()`

### Outils quick reference

| Outil | Usage | Commande |
|-------|-------|---------|
| `query` | Trouver du code par concept | `gitnexus_query({query: "..."})` |
| `context` | Vue 360° d'un symbol | `gitnexus_context({name: "..."})` |
| `impact` | Blast radius avant édition | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Vérification pré-commit | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Renommage multi-fichiers safe | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |

### Self-check avant de finir

1. `gitnexus_impact` run pour tous les symbols modifiés
2. Aucun warning HIGH/CRITICAL ignoré
3. `gitnexus_detect_changes()` confirme le scope attendu
4. Tous les d=1 (WILL BREAK) mis à jour

### Skill files

| Tâche | Fichier |
|-------|---------|
| Explorer l'architecture | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Debug | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Refactoring | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |

---

## RTK — Token-Optimized Commands

**Toujours préfixer les commandes avec `rtk`** pour réduire les tokens de 60-99%.

```bash
# Build & test
rtk cargo build / check / test
rtk tsc / lint / prettier --check
rtk vitest run / playwright test

# Git
rtk git status / log / diff / add / commit / push

# Docker
rtk docker ps / images / logs <container>

# Meta
rtk gain              # stats d'économies
rtk discover          # analyse des sessions Claude Code
```

> Règle : même dans les chaînes `&&`, utiliser `rtk` sur chaque commande.
