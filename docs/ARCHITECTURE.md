# docs/ARCHITECTURE.md

> Architecture technique de Clawvis. Source de vérité pour les décisions d'implémentation.
> Pour la vision produit → `docs/GOAL.md`
> Pour les règles de dev → `CLAUDE.md`

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
            ├── /memory/       → Brain (iframe Logseq ou renderer Python)
            ├── /logs/         → Log stream temps réel
            ├── /chat/         → Chat agent
            └── /settings/     → Config runtime AI, workspace

    Hub UI ──► Kanban API (port 8090)
           ──► Memory API (port 8091)
           ──► Agent Service (port 8093)
           ──► OpenClaw (port 18789)
```

---

## Services

| Service | Port | Tech | Rôle |
|---------|------|------|------|
| **Hub** | 8088 | Vite SPA + nginx | Interface unique — dashboard, kanban, brain, logs, chat, settings |
| **Kanban API** | 8090 | FastAPI (hub-core) | Gestion projets/tâches, mémoire sync, settings |
| **Memory API** | 8091 | FastAPI (hub-core) | Brain tree, Quartz, instance linking |
| **Agent Service** | 8093 | Python | Streaming LLM, sessions OpenClaw, routing provider |
| **OpenClaw** | 18789 | Node.js | Agent runtime, crons skills, channels Telegram/Discord |
| **Brain (Logseq)** | MEMORY_PORT | Docker image | Web app Logseq servie en iframe sous `/memory/` |

---

## Modes de démarrage

### Franc — Docker (défaut utilisateur)

```bash
docker compose -f docker-compose.yml -f instances/<name>/docker-compose.override.yml up
```

- nginx sert `hub/dist/` (SPA compilée)
- nginx proxy `/api/hub/kanban/*` → kanban-api
- nginx proxy `/api/hub/memory/*` → hub-memory-api
- Brain = Logseq web app en iframe

### Mérovingien — VPS / serveur

Identique à Franc mais avec déploiement via `clawvis deploy` (rsync + build remote).
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

## Structure du repo

```
clawvis/
  hub/                    # Vite SPA frontend + nginx Docker image
    src/                  # Source dev (main.js, style.css)
    public/               # Assets statiques, SPA prod compilée
    dist/                 # Build output (gitignored)
  hub-core/               # Python lib partagée — identity, RBAC, AI adapters, Memory API
  kanban/                 # FastAPI Kanban — tasks, projects, deps, stats, memory sync
  skills/                 # Skills Clawvis préconfigurés (kanban-implementer, logger, brain…)
  openclaw/               # Wrapper + config OpenClaw
  clawvis-cli/            # CLI unifié (npm) — clawvis start/deploy/update/backup
  core-tools/
    logger/               # Logs UI standalone servie sur /logs/
  scripts/                # Scripts utilitaires (deploy, project-launch, build-quartz…)
  project-templates/      # Templates pour nouveaux projets (python, vite, empty)
  instances/
    example/              # Template d'instance (copié lors de l'install)
    <instance_name>/      # Données instance réelles (gitignored sauf structure)
  docs/                   # Documentation technique
  tests/                  # CI — ci-all.sh, ci-skills.sh
  .github/workflows/      # CI/CD GitHub Actions
```

---

## Contrat API détaillé

### Domaines

```
/api/hub/kanban/*    → Kanban API (FastAPI, port 8090)
/api/hub/memory/*    → Memory API (FastAPI, port 8091)
/api/hub/logs/*      → Logs (hub-core)
/api/hub/chat/*      → Agent Service (port 8093)
```

### Endpoints principaux Kanban

```
GET  /api/kanban/hub/settings
PUT  /api/kanban/hub/settings
GET  /api/kanban/hub/projects?kind=project|poc
POST /api/kanban/hub/projects          # { description, template }
GET  /api/kanban/hub/projects/{slug}
GET  /api/hub/chat/status              # → { openclaw_configured: bool }
```

### Création projet (backend)

`POST /api/kanban/hub/projects` crée :
1. Dossier repo dans `projects_root` ou `pocs_root`
2. Doc mémoire dans `memory/projects/<slug>.md`
3. Fichier metadata `.clawvis-project.json`

---

## Brain — résolution de la mémoire active

Résolue par `hub_core.brain_memory.active_brain_memory_root(settings)` :

1. Liste les `linked_instances` — si `<path>/memory` existe → candidat
2. Si `MEMORY_ROOT` == un candidat → ce candidat gagne
3. Sinon → premier candidat après tri lexicographique
4. Si aucun linked instance n'a de `memory/` → `MEMORY_ROOT` direct

`GET /hub/settings` retourne `active_brain_memory` pour la transparence UI.

### Scope d'édition Brain

- Édition in-Hub : `memory/projects/*.md` uniquement
- Preview Quartz : `memory/projects/*.html`
- Autres dossiers (`resources/`, `daily/`) : lisibles sur disque, non exposés à l'édition in-Hub sauf extension explicite

---

## OpenClaw — intégration skills

OpenClaw tourne sur le port 18789. Clawvis s'y branche comme provider principal via `OPENCLAW_BASE_URL`.

Les skills Clawvis sont des crons OpenClaw définis dans `skills/` et synchronisés via `clawvis skills sync`.

### Configuration channels

```json
// instances/<name>/.env.local ou hub_settings.json
{
  "discord_channels": {
    "innovation": "#innovation",
    "projects":   "#projects",
    "logs":       "#logs",
    "ops":        "#ops"
  }
}
```

Les crons livrent sur `"channel": "telegram"` ou `"channel": "discord"` selon la nature du message.

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

Workflows GitHub Actions :
- `ci.yml` → shell syntax, hub format+tests+build, Python compile
- `license.yml` → valide MIT
- `release-dry-run.yml` → valide format tag
- `release.yml` → publie Release sur tag `vYYYY-MM-dd`

---

## Décisions d'architecture majeures (ADRs)

| ADR | Décision |
|-----|----------|
| `0003-dombot-migration` | Migration vers pattern `instances/ldom/` — séparation core/instance |
| `0004-production-deployment-pitfalls` | Pitfalls prod documentés — voir `docs/PITFALLS.md` |

### Principes clés

- `project_slug == memory_page_slug == kanban_project_key` — identité unique
- La mémoire n'est jamais owned par le core — toujours instance-scoped
- Les symlinks instance → core sont gérés par `clawvis skills sync`
- `docker-compose.override.yml` par instance pour la séparation prod/dev
