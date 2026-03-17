# Design — SSE Kanban + Confidence Scoring (Kahneman)

**Date:** 2026-03-17
**Status:** Approved
**Repos:** `dombot-labos/core-tools/kanban/`, `Lab/hub/`, `.openclaw/skills/`

---

## Contexte

Le kanban board utilise actuellement `setInterval(load, 30000)` (polling 30s). Le champ `confidence: float | None` existe déjà dans les modèles Pydantic mais n'est pas affiché dans l'UI ni utilisé comme critère de sélection dans les skills.

---

## Objectifs

1. Remplacer le polling kanban par SSE (Server-Sent Events)
2. Afficher un badge de confiance Kahneman sur chaque carte kanban
3. Filtrer les tâches par confiance dans `kanban-implementer`
4. Poser un score de confiance sur les tâches créées par `proactive-innovation`

---

## Convention : agent vs humain

Un assignee est considéré **agent** si `assignee in {"DomBot"}` (constante `AGENT_ASSIGNEES`).
Tout autre assignee (`"user"`, `"lgiron"`, etc.) est **humain**.

Cette convention est utilisée de façon cohérente dans l'UI, les skills, et la logique de sélection.

---

## Architecture — 7 fichiers touchés

### 1. `core-tools/kanban/kanban_api/sse.py` (nouveau)

Endpoint SSE pour les mises à jour kanban en temps réel.

- **Route :** `GET /stream` (sans prefix — nginx rewrite `/api/kanban/stream` → `/stream`)
- **Pas de conflit** : aucune route existante dans `api.py` ne s'appelle `/stream`
- **Media type :** `text/event-stream`
- **Headers obligatoires sur la réponse :**
  ```python
  headers = {
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",  # désactive le buffering pour les proxies intermédiaires éventuels
  }
  ```
  > Note : avec `proxy_buffering off` dans nginx.conf, ce header est redondant mais inoffensif.

**Implémentation complète du générateur :**

```python
import asyncio
import hashlib
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from .core import list_active_tasks, TASKS_FILE

router = APIRouter()


def _build_state() -> str:
    """Retourne le state kanban sérialisé (sort_keys=True pour stabilité du hash)."""
    try:
        data = list_active_tasks()
    except FileNotFoundError:
        data = {"tasks": [], "stats": {}, "projects": [], "meta": {}}
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


@router.get("/stream")
async def stream_kanban():
    async def event_generator():
        last_hash = ""
        try:
            while True:
                await asyncio.sleep(5)
                current = _build_state()
                h = hashlib.md5(current.encode()).hexdigest()
                if h != last_hash:
                    last_hash = h
                    yield f"data: {current}\n\n"
                else:
                    yield ": ping\n\n"
        finally:
            pass  # futur cleanup (file handles, DB connections)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

- **`sort_keys=True`** : crucial pour la stabilité du hash MD5 — sans ça, l'ordre des clés dict peut varier entre deux appels et déclencher des faux événements.
- **`try/finally`** : garantit la cancellation-safety (`GeneratorExit` via `finally`) pour Starlette.
- **`FileNotFoundError`** : géré si `TASKS_FILE` n'existe pas au démarrage.

**Enregistrement dans `server.py` :**
```python
from .sse import router as sse_router
app.include_router(sse_router)  # pas de prefix — route /stream
```

### 2. `hub/nginx.conf` (modifié)

Ajout de `proxy_buffering off` et `proxy_read_timeout 3600` sur le bloc `/api/kanban/` :

```nginx
location /api/kanban/ {
    auth_request /_authelia_auth;
    rewrite ^/api/kanban/(.*)$ /$1 break;
    proxy_pass http://kanban_api;
    proxy_http_version 1.1;
    proxy_set_header Host "localhost";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Content-Type $content_type;
    proxy_buffering off;        # ← AJOUT : requis pour SSE (streaming sans bufferisation)
    proxy_read_timeout 3600;   # ← AJOUT : évite la coupure à 60s (défaut nginx)
}
```

> Sans `proxy_read_timeout 3600`, nginx ferme la connexion SSE après 60s (défaut) même avec heartbeats.

### 3. `hub/public/kanban/index.html` (modifié)

Remplacement du polling par EventSource + badge confiance.

**SSE :**
- Supprimer `setInterval(load, 30000)`
- Ajouter après `load()` initial :
  ```js
  const sse = new EventSource('/api/kanban/stream');
  sse.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      tasks = data.tasks; stats = data.stats;
      projects = data.projects || []; meta = data.meta || {};
      render(); renderStats(); renderMeta(); populateProjectFilter();
    } catch(err) { /* ignore heartbeat comments */ }
  };
  sse.onerror = () => console.warn('SSE kanban reconnecting...');
  ```
- Garder `load()` au démarrage (état initial immédiat sans attendre le 1er tick SSE à +5s)
- Garder les `await load()` dans les mutations (archiveTask, restoreTask, etc.) : ils restent utiles pour forcer le rafraîchissement post-action, la duplication avec SSE est inoffensive.

**Badge confiance — CSS à ajouter :**
```css
.badge-conf-high { background: rgba(34,197,94,0.2);  color: #22c55e; }
.badge-conf-mid  { background: rgba(245,158,11,0.2); color: #f59e0b; }
.badge-conf-low  { background: rgba(239,68,68,0.2);  color: #ef4444; }
```

**Badge confiance — logique dans `renderCard(task)` :**
```js
const AGENT_ASSIGNEES = new Set(['DomBot']);
const isAgent = AGENT_ASSIGNEES.has(task.assignee);
let confBadge = '';
if (isAgent) {
  const score = task.confidence ?? 0.5;  // null → 0.5 (neutre, affiché Mid/amber)
  const level = score >= 0.7 ? 'high' : score >= 0.4 ? 'mid' : 'low';
  confBadge = `<span class="badge badge-conf-${level}"
    title="Confiance DomBot (Kahneman) — Low<0.4 System1 | Mid 0.4–0.7 | High≥0.7 System2">
    ${score.toFixed(2)}</span>`;
}
// Insérer confBadge dans .card-meta, après le badge priorité
```
- **Humain** (`assignee ∉ AGENT_ASSIGNEES`) : aucun badge — décision humaine = autorité
- **DomBot avec `confidence = null`** : badge affiché avec `0.50` (Mid/amber)
- **DomBot avec `confidence` explicite** : badge affiché avec la valeur réelle

### 4. `core-tools/kanban/tests/test_sse.py` (nouveau)

```python
import json
from unittest.mock import patch
from fastapi.testclient import TestClient
from kanban_api.server import app

client = TestClient(app)


def test_sse_content_type():
    """GET /stream retourne 200 + text/event-stream."""
    with client.stream("GET", "/stream") as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]


def test_sse_first_chunk_valid_json():
    """Le premier chunk data: contient un JSON valide avec clé 'tasks'."""
    # Mock asyncio.sleep pour éviter le délai de 5s et l'attente infinie
    with patch("kanban_api.sse.asyncio.sleep", return_value=None):
        with client.stream("GET", "/stream") as r:
            for i, line in enumerate(r.iter_lines()):
                if i > 50:
                    break  # garde-fou anti-boucle infinie
                if line.startswith("data:"):
                    payload = json.loads(line[5:].strip())
                    assert "tasks" in payload
                    break
```

> Tests heartbeat et hash-deduplication déférés (phase 2).

### 5. `skills/kanban-implementer/SKILL.md` (modifié)

Ajout du critère de confiance dans la sélection de tâches.

**Constante :**
```
AGENT_ASSIGNEES = {"DomBot"}
```

**Calcul de confiance effective :**
```
si assignee ∉ AGENT_ASSIGNEES (humain) → confidence_effective = 1.0
sinon → confidence_effective = task.confidence if task.confidence is not None else 0.5
```

**Critère d'éligibilité (ajouté aux critères existants) :**
```
confidence_effective >= KANBAN_MIN_CONFIDENCE
```

**Variable d'environnement** (lue via `float(os.environ.get("KANBAN_MIN_CONFIDENCE", "0.4"))`) :
```bash
KANBAN_MIN_CONFIDENCE=0.4   # seuil minimum (0.0–1.0), configurable dans .env du skill
```

**Règle humain = 1.0** : toute tâche avec `assignee ∉ AGENT_ASSIGNEES` est considérée comme
ayant une confiance effective de 1.0. Les décisions humaines ne sont jamais bloquées par le
filtre de confiance. Cette règle est documentée dans le SKILL.md.

### 6. `skills/proactive-innovation/SKILL.md` (modifié)

Ajout du score de confiance sur les tâches créées.

**Grille d'estimation** (à inclure dans le payload `POST /kanban/tasks`) :

| Type d'amélioration | `confidence` |
|---------------------|-------------|
| Correctif certain (typo, config cassée, sécurité) | `0.75` |
| Amélioration standard (DX, perf mesurable) | `0.55` |
| Idée spéculative (feature, refacto subjective) | `0.3` |

> Note : `0.55` (et non `0.5`) différencie visuellement une amélioration explicitement évaluée du défaut `null → 0.5` affiché sur les tâches sans score.

---

## Règles de confiance (Kahneman)

| Score | Niveau | Couleur | Signification |
|-------|--------|---------|---------------|
| 0.0 – 0.39 | Low | Rouge `#ef4444` | System 1 — intuitif, risqué, validation humaine requise |
| 0.4 – 0.69 | Mid | Amber `#f59e0b` | Zone boundary — implémentable avec prudence |
| 0.7 – 1.0 | High | Vert `#22c55e` | System 2 — délibéré, validé, safe to implement |
| `null` + agent | Mid | Amber | Traité comme `0.5` — badge affiché `0.50` |
| humain | — | (pas de badge) | Confiance effective `1.0`, autorité humaine |

---

## Routing nginx (clarification)

Le proxy nginx rewrite : `rewrite ^/api/kanban/(.*)$ /$1 break;`

| URL client | Route FastAPI reçue |
|-----------|---------------------|
| `/api/kanban/tasks` | `/tasks` |
| `/api/kanban/logs/stream` | `/logs/stream` |
| `/api/kanban/stream` | `/stream` ← nouveau endpoint SSE |

Donc `sse.py` utilise `@router.get("/stream")` sans prefix, monté dans `server.py` sans prefix.

---

## Fichiers touchés

| Fichier | Action |
|---------|--------|
| `core-tools/kanban/kanban_api/sse.py` | Créer |
| `core-tools/kanban/kanban_api/server.py` | Modifier (monter router SSE) |
| `core-tools/kanban/tests/test_sse.py` | Créer |
| `hub/nginx.conf` | Modifier (`proxy_buffering off` + `proxy_read_timeout 3600`) |
| `hub/public/kanban/index.html` | Modifier (SSE + badge) |
| `.openclaw/skills/kanban-implementer/SKILL.md` | Modifier (filtre confidence) |
| `.openclaw/skills/proactive-innovation/SKILL.md` | Modifier (grille scoring) |

---

## Hors scope

- Refacto de `logs_api.py` (SSE logs déjà fonctionnel)
- Modification du modèle Pydantic `Task` (confidence déjà présent)
- Interface d'édition du score de confiance dans l'UI (phase ultérieure)
- Tests heartbeat et hash-deduplication (déférés phase 2)

## Documentation

Ajoute ca à la documentation de dombot-labos ainsi que dans ta mémoire .openclaw/workspace/memory