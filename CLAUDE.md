# CLAUDE.md

> Règles **courtes** pour Claude et Cursor. Détail hors hot path → [`docs/CLAUDE-REFERENCE.md`](docs/CLAUDE-REFERENCE.md)
>
> | Besoin | Fichier |
> |--------|---------|
> | Vision produit | [`docs/GOAL.md`](docs/GOAL.md) |
> | Architecture | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
> | Bugs / dettes | [`docs/PITFALLS.md`](docs/PITFALLS.md) |
> | Modèle de données | [`docs/DATA-MODEL.md`](docs/DATA-MODEL.md) |
> | GitNexus (obligations, outils) | [`AGENTS.md`](AGENTS.md) |

---

## Contrat repository

- **Core** (`hub/`, `kanban/`, `hub-core/`, `skills/`, `scripts/`, compose racine) vs **instance** (`instances/<name>/`). Toute custom instance **uniquement** sous `instances/<name>/` — pas de patch ad hoc au root ; pas de secrets trackés racine ; préférer releases versionnées.
- **Slug projet :** `project_slug == memory_page_slug == kanban_project_key` (détail → `docs/DATA-MODEL.md`).

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

## GitNexus

Avant **édition** d’un symbole : `gitnexus_impact`. Avant **commit** : `gitnexus_detect_changes`. HIGH/CRITICAL = alerter l’utilisateur. Pas de rename grep — `gitnexus_rename`. Détail et skills → **`AGENTS.md`**.

## RTK

Préfixer les commandes terminal avec **`rtk`** quand disponible (réduction sortie). Ex. `rtk git status`, `rtk yarn --cwd hub test`. Chaînes `&&` : `rtk` sur chaque partie.

## Install (rappel minimal)

Premier contact : **`get.sh`** ou **`./install.sh`** — pas `clawvis install`. Pas de clé API à l’install. Philosophie & modes Franc / Mérovingien / Soissons → **`docs/CLAUDE-REFERENCE.md`**.
