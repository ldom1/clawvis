# Clawvis — Documentation des tests

> **Dernier audit :** 2026-03-27 — Phase 1.3 complète, `bash tests/ci-docker.sh` vert.

---

## TLDR — Vue d'ensemble

| Couche | Nb de tests | Outil | Commande rapide |
|--------|-------------|-------|-----------------|
| E2E Playwright (UI/personas) | 24 (22 pass, 2 skip) | Playwright / Chromium | `bash tests/ci-playwright.sh` |
| Kanban API (Python) | ~40 | pytest | `bash tests/ci-kanban.sh` |
| Hub-Core (Python) | ~60 | pytest | `bash tests/ci-hub-core.sh` |
| Hub frontend (TS/Vite) | lint + build | Vitest / yarn | `bash tests/ci-hub.sh` |
| Skills (Python multi-package) | ~35 | pytest | `bash tests/ci-skills.sh` |
| CLI (Node) | lint + smoke | node --check | `bash tests/ci-cli.sh` |
| Docker smoke (curl + E2E) | 13 curl + 22 E2E | bash + Playwright | `bash tests/ci-docker.sh` |
| **Total orchestré** | **~170** | | `bash tests/ci-all.sh` |

### Ce que les tests couvrent

- **Parcours utilisateur complets (E2E)** — de la création d'un projet jusqu'à sa suppression, en passant par le Kanban, la mémoire Quartz, le chat, les settings i18n et le health.
- **API Kanban** — CRUD tâches/projets, sync markdown, découpage de tâches, dépendances, stats hebdo, confidence, templates.
- **Orchestration IA (Hub-Core)** — sélection de modèle, adapters Claude/Gemini/Mistral, RBAC, politique réseau, métriques système, transcription.
- **Infrastructure Docker** — 13 checks curl sur tous les endpoints exposés + suite E2E complète sur stack réelle.

### Skips notables

| Test | Raison |
|------|--------|
| `brain-quartz-static.spec.ts` — Brain iframe | Fixme : Brain SPA doit câbler `#quartz-frame` sur les URLs quartz-static |
| `chat.spec.ts` — when agent connected | Skip si aucun runtime IA configuré |
| `test_real_providers.py` | Skip si `MAMMOUTH_API_KEY` absent |
| `test_transcriber_real_audio.py` | Skip en CI (audio réel non disponible) |

---

## Détail par couche

### 1. E2E Playwright — `tests/playwright/tests/personas/`

Lancés contre le Hub en live (docker ou dev). Chaque fichier = un "persona" utilisateur.
Le helper `hub-gate.ts` skippa automatiquement tous les tests si le Hub n'est pas joignable.

---

#### Persona 1 — Onboarding (`onboarding.spec.ts`)

**Suite :** `Persona 1 — onboarding (EN)`

| Test | Ce qu'il vérifie |
|------|-----------------|
| `home, setup runtime wizard through failed connection test` | Page d'accueil visible, badge AI runtime "Not configured", métriques système, wizard 4 étapes, sélection provider, saisie API key (password), résultat test connexion |
| `AI runtime badge in French` *(suite FR)* | Locale `fr-FR` détectée, badge "Non configuré" affiché |

---

#### Persona 2 — Kanban lifecycle (`kanban.spec.ts`)

**Suite :** `Persona 2 — Kanban lifecycle`

| Test | Ce qu'il vérifie |
|------|-----------------|
| `create task, move columns, effort, archive` | Création tâche, déplacement To Start → In Progress → Done, saisie effort, archivage avec confirm dialog, vérification dans archive modal |
| `delete task shows confirmation modal` | Modal "Are you sure", annulation (overlay reste ouvert), confirmation suppression |

---

#### Persona 3 — Project lifecycle (`projects.spec.ts`)

**Suite :** `Persona 3 — project lifecycle`

| Test | Ce qu'il vérifie |
|------|-----------------|
| `create from home, open project, kanban filter, delete` | Création projet (nom, description, tags, template), carte visible en home, page projet (subtitle, avatar), sauvegarde description mémoire, filtre kanban sur projet (3 cartes attendues), suppression avec confirm, carte disparue |

---

#### Persona 4 — Brain (`brain.spec.ts`)

**Suite :** `Persona 4 — Brain`

| Test | Ce qu'il vérifie |
|------|-----------------|
| `memory page, edit page list and save` | `/memory/` charge l'iframe Quartz, `/memory/edit` liste les `.md`, sélection + ajout commentaire + sauvegarde |
| `kanban filter smoke after brain routes` | Board Kanban visible après navigation depuis Brain |
| `dependency graph view on Kanban` | Bouton graph, `#kanban-graph-wrap` visible, canvas présent |

---

#### Persona 5 — Settings (`settings.spec.ts`)

**Suite :** `Persona 5 — Settings`

| Test | Ce qu'il vérifie |
|------|-----------------|
| `workspace save, instances UI, runtime link, back to hub` | Sauvegarde `projects_root=/tmp/...`, refresh liste instances, navigation vers instance, lien setup runtime visible, retour hub (`/`) |

---

#### Persona 6 — Chat (`chat.spec.ts`)

**Suite :** `Persona 6 — Chat`

| Test | Ce qu'il vérifie |
|------|-----------------|
| `header and status bar when runtime not configured` | Header chat visible, status bar présent, lien setup si non configuré |
| `when agent connected, send message and fail on API error reply` *(skip si pas de runtime)* | Envoie "Say OK in one word", attente réponse 45 s, réponse n'est pas une erreur API |
| `send message shows assistant bubble` | Bulle utilisateur "hello", bulle assistant apparaît |
| `Shift+Enter inserts newline in input` | line1 + Shift+Enter + line2 → textarea contient `\n` |

---

#### Persona 7 — Health (`health.spec.ts`)

**Suite :** `Persona 7 — Health`

| Test | Ce qu'il vérifie |
|------|-----------------|
| `active services count and API smoke` | Compteur services chargé (≠ "…"), ≥ 1, tooltip présent ; 7 endpoints API → 200 : kanban/tasks, kanban/hub/projects, kanban/stats, chat/status, memory/projects, memory/settings, system.json |

---

#### Persona 8 — Project × Memory × Kanban (`project-memory-kanban.spec.ts`)

**Suite :** `Persona 8 — Project × Memory × Kanban integration` — timeout 240 s

| Test | Ce qu'il vérifie |
|------|-----------------|
| `create task, split, memory refresh, delete subtasks, delete project` | Création projet + tâche parente → découpage en 3 sous-tâches (via `window.prompt` override) → vérification cartes `SubMem #1/2/3` → check `.md` mémoire si MD sync actif → rebuild Quartz si MD sync actif → suppression des 3 sous-tâches (confirm dialog) → suppression projet → 404 sur kanban + memory API |

> **Note CI Docker :** `_MD_SYNC=False` (kanban_parser absent) → assertions `.md` et Quartz skippées gracieusement.

---

#### Persona 9 — Language switching (`language.spec.ts`)

**Suite :** `Persona 9 — Language switching`

| Test | Ce qu'il vérifie |
|------|-----------------|
| `Settings page renders in French when navigator.language is fr-FR` | Titre "Paramètres", "Retour au hub", radio `#lang-fr` coché |
| `Settings page renders in English when navigator.language is en-US` | Titre "Settings", "Back to hub", radio `#lang-en` coché |
| `Switching to French persists in localStorage and re-renders` | Clic label `fr` → titre devient "Paramètres", `localStorage["clawvis-locale"]="fr"` |
| `Switching to English persists in localStorage and re-renders` | Depuis FR, clic label `en` → titre "Settings", `localStorage["clawvis-locale"]="en"` |
| `localStorage locale overrides navigator.language` | navigator=fr-FR mais localStorage=en → affichage anglais |

---

#### Brain — Quartz static (`brain-quartz-static.spec.ts`)

**Suite :** `Brain — Quartz static (styles + install parity)`

| Test | Statut | Ce qu'il vérifie |
|------|--------|-----------------|
| `quartz-static HTML injects base; index.css is served` | ✓ | `<base>` href dans le HTML, `index.css` joignable > 500 octets, contient `.page` |
| `quartz-static index.html falls back when Quartz has no root index` | ✓ | Retourne 200 avec `<base>` tag |
| `nested Quartz page still reaches root index.css` | ✓ | `projects/example-project.html` contient `../index.css`, CSS accessible |
| `Brain iframe triggers successful Quartz stylesheet load` | **FIXME** | Pending câblage Brain SPA → quartz-static |

---

### 2. Kanban API — `kanban/tests/`

Lancés via `bash tests/ci-kanban.sh` (ruff + pylint + pytest).

---

#### `test_confidence.py`

Tests Pydantic sur la validation du champ `confidence` (0–1) dans `Task`, `TaskCreate`, `TaskUpdate`.
Cas : valeur nulle (défaut None), 0.0, 0.75, 1.0, et rejets de 1.01 / -0.01.
Bonus : statut `Blocked` dans `STATUSES`, `_check_dependencies` skippé pour Blocked.

---

#### `test_md_sync.py`

Tests d'intégration de la synchronisation kanban → fichier markdown.

| Test | Ce qu'il vérifie |
|------|-----------------|
| `test_update_task_syncs_status_to_markdown` | `PUT /tasks/:id` avec source_file → `write_task_to_md` appelé avec bons args |
| `test_update_task_without_source_file_does_not_sync_markdown` | Pas de source_file → pas de sync |
| `test_split_task_creates_markdown_entry_per_child` | Split parent → `create_task_in_md` appelé 2× (une par sous-tâche) |
| `test_split_task_skips_md_when_no_project` | Tâche orpheline (sans projet) → pas d'écriture MD |

---

#### `test_projects_api.py`

Tests d'endpoints FastAPI (archive/delete projet, upload/get logo, delete task).
Mock de la couche core ; vérifie status HTTP et structure de la réponse.

---

#### `test_sse.py`

| Test | Ce qu'il vérifie |
|------|-----------------|
| `test_openapi_stream_get` | Spec OpenAPI contient `/stream` GET |
| `test_build_state_json_tasks_key` | `_build_state()` → JSON avec clé `tasks` |

---

#### `test_weekly_stats.py`

| Test | Ce qu'il vérifie |
|------|-----------------|
| `test_compute_weekly_stats_projects` | Hub project a `active_count=1`, `majority_assignee="DomBot"` |
| `test_compute_weekly_stats_weeks` | `this_week` et `last_week` présents, `done ≥ 1` |
| `test_parse_git_log_valid` | Parse `date|message|author` → 2 commits avec repo, message, author, date |
| `test_parse_git_log_empty` | Entrée vide → `[]` |
| `test_majority_assignee_tie_alphabetical` | Égalité → tri alphabétique |

---

#### `test_project_templates.py`

| Test | Ce qu'il vérifie |
|------|-----------------|
| `test_create_project_uses_cookiecutter_when_available` | `cookiecutter` appelé si disponible, README.md créé |
| `test_create_project_fallback_copy_template` | Fallback copie template, README contient le nom du projet |
| `test_archive_project_moves_repo_memory_and_archives_tasks` | Repo + mémoire déplacés vers `archived/`, tâches marquées Archived |
| `test_delete_project_removes_repo_memory_and_tasks` | Repo + mémoire supprimés, tâche retirée, dépendances nettoyées |

---

#### `test_memory_major.py`

| Test | Ce qu'il vérifie |
|------|-----------------|
| `test_parse_major_reads_description_and_aliases` | Parse MD avec sections Description / Objectifs / Stratégie / Objective → chaque section extraite |
| `test_update_project_memory_major_roundtrip` | Mise à jour puis re-lecture → toutes les sections persistées |

---

#### `test_task_delete.py`

| Test | Ce qu'il vérifie |
|------|-----------------|
| `test_delete_task_removes_and_cleans_deps` | Suppression de task-a → dépendances de task-b nettoyées (task-c conservé) |
| `test_delete_task_missing_raises` | Tâche inexistante → `KeyError` |

---

### 3. Hub-Core — `hub-core/tests/`

Lancés via `bash tests/ci-hub-core.sh` (ruff + pylint + pytest, hors real_providers et real_audio).

---

#### `test_brain_memory.py`

Logique de sélection de la mémoire active (instance liée vs `MEMORY_ROOT`).

| Test | Ce qu'il vérifie |
|------|-----------------|
| `test_falls_back_when_no_linked` | Pas d'instance liée → `memory_root` utilisé |
| `test_prefers_matching_memory_root` | Instance dont le dossier memory = `MEMORY_ROOT` prioritaire |
| `test_first_linked_when_no_runtime_match` | Pas de correspondance → première instance (tri lexicographique) |

---

> **Note (cleanup V1)** : les suites `test_dynamic_models.py`, `test_chat_runtime.py` et `test_integration.py` ont été retirées avec les modules hub-core associés (adaptateurs agents / RBAC réseau / proxy chat inutilisés en prod). Le chat streaming passe par le service `agent/`.

#### `test_transcriber.py`

Transcription audio (Whisper).

Couvre : fichier introuvable → None, `WhisperModel=None` → None, mock model → string, exception → None, paramètres `language` et `model_size`, segments multiples.

---

#### `test_system_metrics.py`

| Test | Ce qu'il vérifie |
|------|-----------------|
| `test_get_system_stats_returns_dict` | `cpu_percent`, `ram_percent` présents |
| `test_cpu_ram_values_in_range` | 0–100 % |
| `test_get_token_stats_returns_dict` | Clés `claude`, `mammouth`, `timestamp` |
| `test_system_metrics_are_fresh` | Deux appels consécutifs : écart < 20 % |

---

#### Autres tests Hub-Core

| Fichier | Focus |
|---------|-------|
| `test_main.py` | `main()` retourne `HubState`, `get_hub_state` agrège providers + metrics |
| `test_models.py` | Sérialisation/round-trip des modèles Pydantic (HubState, ProvidersResponse, StatusResponse) |
| `test_fetch_provider_data.py` | `get_providers_response()` retourne `ProvidersResponse` avec timestamp |
| `test_update_status.py` | `StatusResponse()` sérialise en JSON valide |

---

### 4. Skills — `skills/*/core/tests/`

Lancés via `bash tests/ci-skills.sh` (découverte auto des pyproject.toml).

---

#### `kanban-implementer` — `test_selector.py` et `test_status.py`

| Test | Ce qu'il vérifie |
|------|-----------------|
| `test_eligible_filters_correctly` | Filtre DomBot + To Start/Backlog + effort ≤ 2h |
| `test_select_task_picks_high_priority` | Retourne High priority, 1h |
| `test_task_with_low_confidence_not_eligible` | confidence=0.2 → non éligible |
| `test_human_assignee_confidence_effective_is_one` | Humain → confidence_effective=1.0 |
| `test_is_ambiguous_vague_word` | "Cleanup old routes" → ambigü |
| `test_is_ambiguous_clear_title` | "Add retry to POST /tasks" + description → clair |
| `test_update_status_valid` | Statut "In Progress" mis à jour en JSON |
| `test_update_status_invalid_status` | "InvalidStatus" → False |
| `test_blocked_status_is_valid` | Statut "Blocked" accepté |

---

#### `logger` — `test_models.py`, `test_logger.py`, `test_config.py`, `test_discord_router.py`

| Groupe | Focus |
|--------|-------|
| Models | Format texte des entrées log `[ts][level][process][model]action—msg`, métadonnées |
| Logger | Niveaux INFO/ERROR/WARNING/DEBUG/CRITICAL, JSONL + plaintext `.log`, multi-entrées |
| Config | `load_dotenv(override=False)`, trim whitespace, mapping canal Discord |
| Discord | Bot init, `on_ready`, création canaux text/private, recherche canal par nom |

---

### 5. Scripts CI — `tests/ci-*.sh`

| Script | Étapes |
|--------|--------|
| `ci-all.sh` | Orchestrateur séquentiel : kanban → hub-core → hub → playwright → skills → cli |
| `ci-kanban.sh` | ruff + pylint (E,F) + pytest sur `kanban/` |
| `ci-hub-core.sh` | ruff + pylint + pytest sur `hub-core/` (hors real_providers) |
| `ci-hub.sh` | corepack + yarn install + format:check + test + build |
| `ci-playwright.sh` | npm ci + playwright install chromium + playwright test --project=chromium |
| `ci-skills.sh` | Découverte auto des skills avec pyproject.toml → ruff + pylint + pytest par skill |
| `ci-cli.sh` | npm ci + node --check + smoke `--help` |
| `ci-docker.sh` | docker compose up → wait ready → prime projects_root → 13 curl → 22 E2E Playwright |

---

### 6. Checks additionnels (non-pytest)

| Fichier | Description |
|---------|-------------|
| `hub-core/tests/test_hub_integration.py` | Smoke HTTP réel contre Hub local — dashboard, hub-core imports, config, modèles Pydantic, génération JSON état |

---

## Lancer les tests

```bash
# Tout (qualité + build + E2E)
bash tests/ci-all.sh

# Stack Docker réelle uniquement (smoke + E2E)
bash tests/ci-docker.sh

# Rejouer uniquement les E2E sur la stack déjà lancée
PLAYWRIGHT_BASE_URL=http://localhost:8088 PW_NO_WEBSERVER=1 \
  npx playwright test --project=chromium --reporter=list \
  --prefix tests/playwright

# Un seul persona
PLAYWRIGHT_BASE_URL=http://localhost:8088 PW_NO_WEBSERVER=1 CI=true \
  npx playwright test --project=chromium personas/kanban.spec.ts
```
