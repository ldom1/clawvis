# CLAUDE.md

> Règles **courtes** pour Claude et Cursor. Détail hors hot path → [`docs/CLAUDE-REFERENCE.md`](docs/CLAUDE-REFERENCE.md)
>
> | Besoin | Fichier |
> |--------|---------|
> | Vision produit | [`docs/GOAL.md`](docs/GOAL.md) |
> | Architecture | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
> | Bugs / dettes | [`docs/PITFALLS.md`](docs/PITFALLS.md) |
> | Modèle de données | [`docs/DATA-MODEL.md`](docs/DATA-MODEL.md) |

---

## Contrat repository

- **Core** (`hub/`, `services/`, `hub-core/`, `skills/`, `scripts/`, compose racine) vs **instance** (`instances/<name>/`). Toute custom instance **uniquement** sous `instances/<name>/` — pas de patch ad hoc au root ; pas de secrets trackés racine ; préférer releases versionnées.
- **Slug projet :** `project_slug == memory_page_slug == kanban_project_key` (détail → `docs/DATA-MODEL.md`).

## Contrat architecture (2026)

- Clawvis expose un stack unique : **hub + brain + agent + skills + telegram + scheduler (cron)**.
- `hub` = UI ; `kanban-api` + `hub-memory-api` = brain/memory ; `agent-service` = exécution agent ; `services/telegram` + `services/scheduler` = notifications + jobs planifiés.
- Le lien produit avec **OpenClaw** est retiré du périmètre par défaut : ne pas réintroduire de dépendance ou wording OpenClaw dans les docs/flows principaux.
- Clawvis doit pouvoir lancer la **CLI Claude** pour exécuter les demandes utilisateur (containers/services doivent conserver ce chemin opérationnel).

## Contrat API

Préfixes `/api/hub/{kanban,memory,logs,chat}/*`. **Jamais** Brain-only sous l’API Kanban seule ; le front appelle le domaine qui va bien.

## Contrat UI

Clarté, ton pro, parité **`hub/src` ↔ `hub/public`**. Checklist PR UI complète → `docs/CLAUDE-REFERENCE.md`.

## Outils (obligatoire)

| Zone | Outil | Commande |
|------|-------|----------|
| Hub | **Yarn Berry 4** | `yarn --cwd hub <cmd>` — pas `npm` |
| CLI `clawvis-cli/` | **npm** | `npm ci` / `npm install` |
| Kanban + hub-core | **uv** | `uv run …` — pas `pip` |
| Merge | bash | `bash tests/ci-all.sh` → exit 0 |

## CI

Gate merge : `bash tests/ci-all.sh`. Noms des workflows → `docs/CLAUDE-REFERENCE.md`.

## RTK

Préfixer les commandes terminal avec **`rtk`** quand disponible (réduction sortie). Ex. `rtk git status`, `rtk yarn --cwd hub test`. Chaînes `&&` : `rtk` sur chaque partie.

## Install (rappel minimal)

Premier contact : **`get.sh`** ou **`./install.sh`** — pas `clawvis install`. Pas de clé API à l’install. Philosophie & modes Franc / Mérovingien / Soissons → **`docs/CLAUDE-REFERENCE.md`**.
