# SSE Kanban + Confidence Scoring (Kahneman)

## Architecture

Le kanban board reçoit les mises à jour en temps réel via SSE (Server-Sent Events).
L'API expose `GET /stream` (proxié via nginx `/api/kanban/stream`).

## Endpoint SSE

- **Route FastAPI :** `GET /stream` (kanban_api/sse.py, monté sans prefix)
- **Nginx :** `/api/kanban/stream` → rewrite `/$1` → `http://kanban_api/stream`
- **Heartbeat :** `: ping\n\n` toutes les 5s si aucun changement
- **Payload :** même structure que `GET /tasks` (`{tasks, stats, projects, meta}`)
- **Hash-dedup :** `hashlib.md5(json.dumps(..., sort_keys=True).encode()).hexdigest()`
- **Nginx requis :** `proxy_buffering off` + `proxy_read_timeout 3600`
- **Frontend :** `EventSource('/api/kanban/stream')` remplace `setInterval(load, 30000)`
- `load()` initial conservé pour état immédiat (SSE premier tick à +5s)

## Confidence Scoring (Kahneman)

| Score | Niveau | Couleur | Signification |
|-------|--------|---------|---------------|
| 0.0–0.39 | Low | Rouge `#ef4444` | System 1 — intuitif, risqué, validation humaine requise |
| 0.4–0.69 | Mid | Amber `#f59e0b` | Zone boundary — implémentable avec prudence |
| 0.7–1.0 | High | Vert `#22c55e` | System 2 — délibéré, validé, safe to implement |
| `null` (agent) | Mid | Amber | Traité comme 0.5 — badge `0.50` affiché |
| humain | — | (pas de badge) | Confiance effective 1.0, autorité humaine |

## Convention AGENT_ASSIGNEES

```python
AGENT_ASSIGNEES = {"DomBot"}
```

Tout assignee ∉ AGENT_ASSIGNEES est humain → `confidence_effective = 1.0`.
Cette convention est unifiée UI (JS), Python (selector.py), et SKILL.md.

## Variables d'environnement

| Variable | Défaut | Usage | Fichier |
|----------|--------|-------|---------|
| `KANBAN_MIN_CONFIDENCE` | `0.4` | Seuil minimum kanban-implementer | `config.py` |
| `KANBAN_MAX_EFFORT` | `2.0` | Effort max (heures) | `config.py` |

## Grille proactive-innovation

| Type d'amélioration | `confidence` |
|---------------------|-------------|
| Correctif certain (typo, config cassée, sécurité) | `0.75` |
| Amélioration standard (DX, perf mesurable) | `0.55` |
| Idée spéculative (feature, refacto subjective) | `0.3` |

> `0.55` (et non `0.5`) différencie visuellement une amélioration explicitement évaluée du
> défaut `null → 0.50` affiché sur les tâches sans score.

## Fichiers clés

| Composant | Fichier |
|-----------|---------|
| SSE endpoint | `kanban/kanban_api/sse.py` |
| nginx streaming | `Lab/hub/nginx.conf` (bloc `/api/kanban/`) |
| Kanban board UI | `Lab/hub/public/kanban/index.html` |
| Selector filtre | `.openclaw/skills/kanban-implementer/core/kanban_implementer/selector.py` |
| Config seuil | `.openclaw/skills/kanban-implementer/core/kanban_implementer/config.py` |
| Spec | `docs/superpowers/specs/2026-03-17-sse-confidence-scoring-design.md` |
| Plan | `docs/superpowers/plans/2026-03-17-sse-confidence-scoring.md` |
