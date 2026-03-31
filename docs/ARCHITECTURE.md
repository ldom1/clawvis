# docs/ARCHITECTURE.md

> Architecture technique de Clawvis. Source de vérité pour les décisions d'implémentation.
> Pour la vision produit → `GOAL.md`
> Pour les règles de dev → `CLAUDE.md`
> Pour le modèle de données → `docs/DATA-MODEL.md`

---

## Vue d'ensemble

```
Utilisateur
    │
    ├── Telegram / Discord  (canaux externes)
    │
    └── Hub UI  (localhost:8088 ou lab.dombot.tech)
            │
            ├── /hub/          → Dashboard projets
            ├── /kanban/       → Task board
            ├── /memory/       → Brain (Quartz iframe)
            ├── /logs/         → Log stream temps réel
            ├── /chat/         → Chat agent
            └── /settings/     → Config runtime AI, workspace

    Hub UI ──► Kanban API      (port 8090)
           ──► Memory API      (port 8091)
           ──► Agent Service   (port 8093)
           ──► OpenClaw        (port 18789)
```

---

## Stack — entry points

| Couche | Technologie | Entry point |
|--------|-------------|-------------|
| Hub SPA | Vite + vanilla JS | `hub/src/main.js` |
| Kanban API | FastAPI (uvicorn) | `kanban/kanban_api/server.py` |
| Memory API | FastAPI (uvicorn) | `hub-core/hub_core/memory_api.py` |
| Agent Service | Python | `agent-service/server.py` |
| Brain display | Quartz static (iframe) | `scripts/build-quartz.sh` |
| Docker proxy | nginx | `hub/nginx.conf` |
| OpenClaw | Node.js | port 18789 |

---

## Services

| Service | Port | Tech | Rôle |
|---------|------|------|------|
| **Hub** | 8088 | Vite SPA + nginx | Interface unique — dashboard, kanban, brain, logs, chat, settings |
| **Kanban API** | 8090 | FastAPI (hub-core) | Gestion projets/tâches, mémoire sync, settings |
| **Memory API** | 8091 | FastAPI (hub-core) | Brain tree, Quartz, instance linking |
| **Agent Service** | 8093 | Python | Streaming LLM, sessions OpenClaw, routing provider |
| **OpenClaw** | 18789 | Node.js | Agent runtime, crons skills, channels Telegram/Discord |

---

## Modes de démarrage

### Franc — Docker (défaut utilisateur)

```bash
docker compose -f docker-compose.yml -f instances/<n>/docker-compose.override.yml up
```

- nginx sert `hub/dist/` (SPA compilée)
- nginx proxy `/api/hub/kanban/*` → kanban-api
- nginx proxy `/api/hub/memory/*` → hub-memory-api
- Brain = Quartz static servi via iframe

**`HUB_HOST`** dans `docker-compose.yml` contrôle le bind :
```yaml
ports:
  - "${HUB_HOST:-127.0.0.1}:${HUB_PORT:-8088}:80"
```
- `HUB_HOST=127.0.0.1` (défaut) → loopback uniquement, safe pour Docker Desktop et setups avec reverse proxy hôte
- `HUB_HOST=0.0.0.0` → container accepte les connexions non-loopback (sans reverse proxy hôte)

### Mérovingien — VPS / serveur

Identique à Franc mais déploiement via `clawvis deploy` (rsync + build remote).
Reverse proxy nginx côté VPS → stack locale via Tailscale ou directement.

### Soissons — Dev local

```bash
clawvis start  # ou scripts/start.sh
```

- Vite dev server sur `HUB_PORT` (8088)
- Proxy Vite `/api/kanban/*` → uvicorn Kanban API (8090)
- Proxy Vite `/api/hub/memory/*` → uvicorn Memory API (8091)
- `system.json` = fichier statique dans `hub/public/api/`, mis à jour par cron via hub-core

---

## Hub routing (SPA)

Toutes les routes sont gérées par `hub/src/main.js` via History API.

Assets statiques dans `hub/public/` copiés verbatim dans `hub/dist/` au build :

| Fichier | Rôle |
|---------|------|
| `hub/public/settings/index.html` | Page settings statique Docker — servie sur `/settings/` par nginx |
| `hub/public/optional-app-placeholder/index.html` | Fallback "App not deployed" |
| `hub/public/api/*.json` | Stubs statiques utilisés en dev et prod |

**Règle nginx critique :** le bloc `location /assets/` doit venir **avant** `/hub/` — Vite génère des paths absolus `/assets/index-HASH.js` qui retournent 404 sinon. Voir pitfall #2 dans `docs/PITFALLS.md`.

---

## Contrat API — domaines séparés

```
/api/hub/kanban/*    → Kanban API (FastAPI, port 8090)
/api/hub/memory/*    → Memory API (FastAPI, port 8091)
/api/hub/logs/*      → Logs (hub-core)
/api/hub/chat/*      → Agent Service (port 8093)
```

**Règle absolue :** les endpoints Brain/Quartz ne vivent jamais sous la surface Kanban API.

### Endpoints principaux

```
GET  /api/kanban/hub/settings
PUT  /api/kanban/hub/settings
GET  /api/kanban/hub/projects?kind=project|poc
POST /api/kanban/hub/projects          # { description, template }
GET  /api/kanban/hub/projects/{slug}
GET  /api/hub/chat/status              # → { openclaw_configured: bool }
```

### Création projet (backend)

`POST /api/kanban/hub/projects` crée en séquence :
1. Dossier repo dans `projects_root` ou `pocs_root`
2. Doc mémoire `memory/projects/<slug>.md`
3. Fichier metadata `.clawvis-project.json`
4. Tâches Kanban depuis le template choisi

---

## Brain — mémoire active et Quartz

### Résolution de la racine mémoire

Résolue par `hub_core.brain_memory.active_brain_memory_root(settings)` :

1. Liste les `linked_instances` — si `<path>/memory` existe → candidat
2. Si `MEMORY_ROOT` == un candidat → ce candidat gagne
3. Sinon → premier candidat après tri lexicographique
4. Si aucun linked instance n'a de `memory/` → `MEMORY_ROOT` direct

`GET /hub/settings` retourne `active_brain_memory` pour la transparence UI.
Tests : `hub-core/tests/test_brain_memory.py`.

### Quartz — service et `<base>` tag

Le build Quartz (`quartz/public/`) est servi via :
```
/api/hub/memory/quartz-static/{path}
```

La Memory API injecte un tag `<base>` dans chaque page HTML pour que les assets relatifs se résolvent correctement quelle que soit la profondeur de l'URL :

```
quartz/public/
  index.html           → <base href="/api/hub/memory/quartz-static/">
  projects/slug.html   → <base href="/api/hub/memory/quartz-static/">
  index.css            → servi directement
```

Si Quartz est absent (submodule non initialisé), le renderer Python léger prend le relais — dégradation gracieuse, pas de page blanche.

### Scope d'édition Brain

- Édition in-Hub : `memory/projects/*.md` uniquement
- Preview Quartz : `memory/projects/*.html`
- Autres dossiers (`resources/`, `daily/`) : lisibles sur disque, non exposés à l'édition in-Hub sauf extension explicite

---

## Pattern Dombot — edge routing multi-vhost

Pour les setups homelab (une IP, plusieurs domaines) :

```
Internet
  → VPS nginx (lab.dombot.tech, terminaison HTTPS)
    → Tailscale / proxy → Dombot :8088
      → nginx hôte (généré depuis instances/<n>/nginx/nginx.conf)
          server_name www.clawvis.fr   → static clawvis-landing/dist/
          server_name lab.dombot.tech  → Hub container (127.0.0.1:8089) + Authelia
```

**Pourquoi pas `HUB_HOST=0.0.0.0` seul :** si le Hub container est publié directement sur `0.0.0.0:8088`, tous les vhosts voient le Hub SPA — impossible de servir la landing sur le même port.

**Pattern correct :**
- `HUB_HOST=127.0.0.1`, Hub bind sur `127.0.0.1:8089` (port interne)
- nginx hôte sur `0.0.0.0:8088`, dispatch par `server_name`

`clawvis start` (Vite dev) n'implémente **pas** ce pattern — production uniquement.
→ Voir `docs/guides/dombot-edge-routing.md` pour le détail opérationnel.

---

## Structure du repo

```
clawvis/
  hub/                    # Vite SPA frontend + nginx Docker image
    src/                  # Source dev (main.js, style.css)
    public/               # Assets statiques, SPA prod compilée
    dist/                 # Build output (gitignored)
  hub-core/               # Python lib partagée — identity, RBAC, AI adapters, Memory API
  kanban/                 # FastAPI Kanban — tasks, projects, deps, stats, memory sync
  skills/                 # Skills Clawvis préconfigurés
  openclaw/               # Wrapper + config OpenClaw
  clawvis-cli/            # CLI unifié (npm) — clawvis start/deploy/update/backup
  core-tools/
    logger/               # Logs UI standalone servie sur /logs/
  scripts/                # Scripts utilitaires (deploy, project-launch, build-quartz…)
  project-templates/      # Templates nouveaux projets (python, vite, empty)
  instances/
    example/              # Template d'instance (copié lors de l'install)
    <instance_name>/      # Données instance réelles (gitignored sauf structure)
  docs/                   # Documentation technique
  tests/                  # CI — ci-all.sh, ci-skills.sh
  .github/workflows/      # CI/CD GitHub Actions
```

---

## OpenClaw — intégration skills

OpenClaw tourne sur le port 18789. Clawvis s'y branche via `OPENCLAW_BASE_URL`.

Les skills Clawvis sont des crons OpenClaw définis dans `skills/` et synchronisés via `clawvis skills sync`.

Configuration channels Discord dans `hub_settings.json` :
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

---

## Cycle de vie update

```
1. Pin release     → tag vYYYY-MM-dd
2. Upgrade prep    → fetch changelog, migration checks compose/env/memory
3. Apply           → update core au tag cible, instances/ inchangées
4. Validate        → smoke tests (Hub, Brain, Logs, Kanban, project creation)
5. Promote         → redeploy uniquement après checks verts
```

---

## CI

```bash
bash tests/ci-all.sh    # gate principal — doit retourner 0
bash tests/ci-skills.sh # inclut skill-tester
```

| Workflow | Déclencheur | Rôle |
|----------|-------------|------|
| `ci.yml` | PR / push | Shell syntax, hub format+tests+build, Python compile |
| `license.yml` | PR | Valide MIT |
| `release-dry-run.yml` | PR | Valide format tag |
| `release.yml` | Tag `vYYYY-MM-dd` | Publie GitHub Release |

---

## ADRs — décisions majeures

| ADR | Titre | Lien |
|-----|-------|------|
| 0001 | Docker comme mode d'install par défaut (Franc) | `docs/adr/0001-docker-as-default-mode.md` |
| 0002 | Mémoire instance-scoped — jamais au root | `docs/adr/0002-instance-scoped-memory.md` |
| 0003 | Migration Dombot (Clawpilot → Clawvis) | `docs/adr/0003-dombot-migration.md` |
| 0004 | Pitfalls prod premier déploiement | `docs/adr/0004-production-deployment-pitfalls.md` |

### Principes clés

- `project_slug == memory_page_slug == kanban_project_key` — identité canonique unique
- La mémoire n'est jamais owned par le core — toujours instance-scoped
- Les symlinks instance → core sont gérés par `clawvis skills sync`
- `docker-compose.override.yml` par instance pour la séparation prod/dev