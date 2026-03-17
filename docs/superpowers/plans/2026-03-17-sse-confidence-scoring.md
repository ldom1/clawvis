# SSE Kanban + Confidence Scoring Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer le polling kanban par SSE et afficher des badges de confiance Kahneman (0–1) sur les cartes, puis intégrer le filtre de confiance dans les skills DomBot.

**Architecture:** Nouveau module `sse.py` dans la kanban API (endpoint `GET /stream` via FastAPI StreamingResponse), patch nginx pour activer le streaming, puis modification de l'UI kanban et des deux skills. Chaque composant est indépendant et testable séparément.

**Tech Stack:** Python 3.12, FastAPI, Starlette StreamingResponse, nginx, vanilla JS (EventSource), pytest + unittest.mock

---

## File Map

> **Deux repos distincts :**
> - `dombot-labos/` → `core-tools/kanban/`, skills (via `.openclaw/`)
> - `Lab/hub/` → nginx.conf, kanban board HTML

| Fichier | Repo | Action | Responsabilité |
|---------|------|--------|----------------|
| `core-tools/kanban/kanban_api/sse.py` | dombot-labos | Créer | Endpoint SSE `/stream`, hash-dedup, heartbeat |
| `core-tools/kanban/kanban_api/server.py` | dombot-labos | Modifier | Monter le router SSE |
| `core-tools/kanban/tests/test_sse.py` | dombot-labos | Créer | Tests content-type + payload |
| `/home/lgiron/Lab/hub/nginx.conf` | Lab/hub | Modifier | `proxy_buffering off` + `proxy_read_timeout 3600` |
| `/home/lgiron/Lab/hub/public/kanban/index.html` | Lab/hub | Modifier | EventSource + badge confiance |
| `.openclaw/skills/kanban-implementer/SKILL.md` | openclaw | Modifier | Critère confidence_effective ≥ seuil |
| `.openclaw/skills/kanban-implementer/core/kanban_implementer/config.py` | openclaw | Modifier | Ajouter MIN_CONFIDENCE |
| `.openclaw/skills/kanban-implementer/core/kanban_implementer/selector.py` | openclaw | Modifier | Champ confidence + is_eligible |
| `.openclaw/skills/proactive-innovation/SKILL.md` | openclaw | Modifier | Grille scoring sur POST tasks |

---

## Task 1: SSE endpoint (sse.py)

**Files:**
- Create: `core-tools/kanban/kanban_api/sse.py`
- Test: `core-tools/kanban/tests/test_sse.py`

- [ ] **Step 1.1: Écrire le test de content-type (TDD)**

Créer `core-tools/kanban/tests/test_sse.py` :

```python
import json
from unittest.mock import AsyncMock, patch
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
    # AsyncMock requis : asyncio.sleep est une coroutine, patch avec return_value=None lèverait TypeError
    with patch("kanban_api.sse.asyncio.sleep", new=AsyncMock(return_value=None)):
        with client.stream("GET", "/stream") as r:
            for i, line in enumerate(r.iter_lines()):
                if i > 50:
                    break  # garde-fou anti-boucle infinie
                if line.startswith("data:"):
                    payload = json.loads(line[5:].strip())
                    assert "tasks" in payload
                    break
```

- [ ] **Step 1.2: Vérifier que les tests échouent (endpoint inexistant)**

```bash
cd /home/lgiron/Lab/dombot-labos/core-tools/kanban
uv run pytest tests/test_sse.py -v
```
Expected: `FAILED` — `404 Not Found` ou `AttributeError`.

- [ ] **Step 1.3: Créer `sse.py`**

Créer `core-tools/kanban/kanban_api/sse.py` :

```python
"""SSE endpoint — live kanban stream with hash-based deduplication."""
import asyncio
import hashlib
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from .core import list_active_tasks

router = APIRouter()


def _build_state() -> str:
    """Serialize kanban state. sort_keys=True ensures hash stability."""
    try:
        data = list_active_tasks()
    except FileNotFoundError:
        data = {"tasks": [], "stats": {}, "projects": [], "meta": {}}
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


@router.get("/stream")
async def stream_kanban():
    """SSE endpoint: push full state on change, heartbeat otherwise."""
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
            pass  # future cleanup hook

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

- [ ] **Step 1.4: Monter le router dans `server.py`**

Modifier `core-tools/kanban/kanban_api/server.py` — ajouter après les imports existants :

```python
from .sse import router as sse_router
```

Et après `app.include_router(logs_router)` :

```python
app.include_router(sse_router)
```

Le fichier complet doit ressembler à :
```python
"""FastAPI app: Kanban + Logs API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router
from .logs_api import router as logs_router
from .sse import router as sse_router

app = FastAPI(title="Kanban & Logs API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
app.include_router(logs_router)
app.include_router(sse_router)
```

- [ ] **Step 1.5: Vérifier que les tests passent**

```bash
cd /home/lgiron/Lab/dombot-labos/core-tools/kanban
uv run pytest tests/test_sse.py -v
```
Expected: `2 passed`.

- [ ] **Step 1.6: Commit**

```bash
git add core-tools/kanban/kanban_api/sse.py \
        core-tools/kanban/kanban_api/server.py \
        core-tools/kanban/tests/test_sse.py
git commit -m "feat(kanban): add SSE endpoint /stream with hash-dedup heartbeat"
```

---

## Task 2: nginx — activer le streaming SSE

**Files:**
- Modify: `/home/lgiron/Lab/hub/nginx.conf` (lignes 282–291)

- [ ] **Step 2.1: Modifier le bloc `/api/kanban/` dans `hub/nginx.conf`**

Remplacer le bloc existant (lignes 283–291) :

```nginx
        location /api/kanban/ {
            auth_request /_authelia_auth;
            rewrite ^/api/kanban/(.*)$ /$1 break;
            proxy_pass http://kanban_api;
            proxy_http_version 1.1;
            proxy_set_header Host "localhost";
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header Content-Type $content_type;
        }
```

Par :

```nginx
        location /api/kanban/ {
            auth_request /_authelia_auth;
            rewrite ^/api/kanban/(.*)$ /$1 break;
            proxy_pass http://kanban_api;
            proxy_http_version 1.1;
            proxy_set_header Host "localhost";
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header Content-Type $content_type;
            proxy_buffering off;        # required for SSE streaming
            proxy_read_timeout 3600;   # prevent 60s default timeout on long-lived connections
        }
```

- [ ] **Step 2.2: Valider la syntaxe nginx**

```bash
nginx -t -c /home/lgiron/Lab/hub/nginx.conf 2>&1 || echo "check variables — envsubst needed"
```
Si la commande échoue à cause des variables `${HUB_ROOT}` / `${LAB}`, c'est normal (fichier template). Vérifier visuellement que la syntaxe du bloc modifié est cohérente avec les autres blocs.

- [ ] **Step 2.3: Commit dans le repo Lab/hub**

```bash
cd /home/lgiron/Lab/hub
git add nginx.conf
git commit -m "fix(nginx): enable SSE streaming on /api/kanban/ (proxy_buffering off + read_timeout 3600)"
```

---

## Task 3: UI kanban — SSE + badge confiance

**Files:**
- Modify: `/home/lgiron/Lab/hub/public/kanban/index.html`
  - CSS badge: autour de la ligne 116 (après `.card-archive-btn:hover`)
  - Logique card: lignes 366–373 (`renderBoard` → construction HTML carte)
  - SSE init: lignes 793–795 (fin du script, remplace `setInterval`)

- [ ] **Step 3.1: Ajouter le CSS des badges confiance**

Dans le bloc `<style>`, après la règle `.card-archive-btn:hover { ... }` (ligne ~116), insérer :

```css
    .badge-conf-high { background: rgba(34,197,94,0.2);  color: #22c55e; }
    .badge-conf-mid  { background: rgba(245,158,11,0.2); color: #f59e0b; }
    .badge-conf-low  { background: rgba(239,68,68,0.2);  color: #ef4444; }
```

- [ ] **Step 3.2: Ajouter la constante AGENT_ASSIGNEES et le badge dans `renderBoard`**

Dans la fonction `renderBoard`, trouver le bloc qui construit le HTML de la carte (lignes 366–373) :

```js
      let html = `<div class="card-title">${esc(task.title)}</div><div class="card-meta">`;
      if (task.project) html += `<span class="badge badge-project">${esc(task.project)}</span>`;
      html += `<span class="badge badge-${task.priority}">${task.priority}</span>`;
      if (task.created_by === 'user') html += `<span class="badge" style="background:rgba(99,102,241,0.1);color:var(--accent)">you</span>`;
      if (task.effort_hours) html += `<span class="card-effort">${task.effort_hours}h</span>`;
      html += `</div>`;
```

Remplacer par :

```js
      const AGENT_ASSIGNEES = new Set(['DomBot']);
      const isAgent = AGENT_ASSIGNEES.has(task.assignee);
      let confBadge = '';
      if (isAgent) {
        const score = task.confidence ?? 0.5;
        const level = score >= 0.7 ? 'high' : score >= 0.4 ? 'mid' : 'low';
        confBadge = `<span class="badge badge-conf-${level}" title="Confiance DomBot (Kahneman) — Low<0.4 System1 | Mid 0.4–0.7 | High≥0.7 System2">${score.toFixed(2)}</span>`;
      }
      let html = `<div class="card-title">${esc(task.title)}</div><div class="card-meta">`;
      if (task.project) html += `<span class="badge badge-project">${esc(task.project)}</span>`;
      html += `<span class="badge badge-${task.priority}">${task.priority}</span>`;
      html += confBadge;
      if (task.created_by === 'user') html += `<span class="badge" style="background:rgba(99,102,241,0.1);color:var(--accent)">you</span>`;
      if (task.effort_hours) html += `<span class="card-effort">${task.effort_hours}h</span>`;
      html += `</div>`;
```

- [ ] **Step 3.3: Remplacer le polling par EventSource**

À la fin du script (lignes 793–795), remplacer :

```js
// Init
load();
setInterval(load, 30000);
```

Par :

```js
// Init
load();

// SSE — live kanban updates (replaces setInterval polling)
(function() {
  const sse = new EventSource('/api/kanban/stream');
  sse.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      tasks = data.tasks; stats = data.stats;
      projects = data.projects || []; meta = data.meta || {};
      render(); renderStats(); renderMeta(); populateProjectFilter();
      document.getElementById('api-error')?.remove();
    } catch(err) { /* ignore heartbeat comments (": ping") */ }
  };
  sse.onerror = () => console.warn('SSE kanban reconnecting...');
})();
```

- [ ] **Step 3.4: Vérifier visuellement (optionnel si kanban API tourne)**

Si la kanban API est accessible, ouvrir `/kanban/` et vérifier :
- Les cartes DomBot affichent un badge coloré (rouge/amber/vert)
- Les cartes humaines (`assignee = "user"`) n'ont pas de badge confiance
- La console ne montre plus de requêtes toutes les 30s, mais une connexion SSE persistante

- [ ] **Step 3.5: Commit dans le repo Lab/hub**

```bash
cd /home/lgiron/Lab/hub
git add public/kanban/index.html
git commit -m "feat(kanban-ui): SSE EventSource + Kahneman confidence badge on cards"
```

---

## Task 4: Skill kanban-implementer — filtre confiance

**Files:**
- Modify: `.openclaw/skills/kanban-implementer/SKILL.md`
- Modify: `.openclaw/skills/kanban-implementer/core/kanban_implementer/config.py`
- Modify: `.openclaw/skills/kanban-implementer/core/kanban_implementer/selector.py`
- Test: `.openclaw/skills/kanban-implementer/core/tests/test_selector.py`

- [ ] **Step 4.1: Ajouter la section confiance dans les critères d'éligibilité du SKILL.md**

Dans `.openclaw/skills/kanban-implementer/SKILL.md`, trouver la section **Critères de sélection** :

```markdown
Une tâche est **éligible** si :
- `assignee = "DomBot"`
- `status ∈ {"To Start", "Backlog"}`
- `effort_hours ≤ KANBAN_MAX_EFFORT` (défaut 2h)
```

Remplacer par :

```markdown
Une tâche est **éligible** si :
- `assignee = "DomBot"`
- `status ∈ {"To Start", "Backlog"}`
- `effort_hours ≤ KANBAN_MAX_EFFORT` (défaut 2h)
- `confidence_effective ≥ KANBAN_MIN_CONFIDENCE` (défaut 0.4)

**Calcul de `confidence_effective` :**

```
AGENT_ASSIGNEES = {"DomBot"}
si assignee ∉ AGENT_ASSIGNEES (humain) → confidence_effective = 1.0
sinon → confidence_effective = task.confidence ?? 0.5  (null → 0.5)
```

**Règle humain = 1.0** : toute tâche assignée à un humain (assignee ∉ AGENT_ASSIGNEES)
a une confiance effective de 1.0. Les décisions humaines ne sont jamais bloquées par ce filtre.
```

Ajouter dans le bloc variables d'environnement :

```bash
# Seuil minimum de confiance (Kahneman) — tâches en-dessous ignorées
# null (DomBot) → traité comme 0.5 ; humain → toujours 1.0
KANBAN_MIN_CONFIDENCE=0.4
```

- [ ] **Step 4.2: Ajouter MIN_CONFIDENCE dans config.py**

Dans `.openclaw/skills/kanban-implementer/core/kanban_implementer/config.py`, après la ligne `MAX_EFFORT`:

```python
# Minimum confidence score (Kahneman) — tasks below are skipped
# null treated as 0.5; human assignee always gets 1.0
MIN_CONFIDENCE: float = float(os.environ.get("KANBAN_MIN_CONFIDENCE", "0.4"))
```

- [ ] **Step 4.3: Écrire le test TDD pour le filtre confidence**

Dans `.openclaw/skills/kanban-implementer/core/tests/test_selector.py`, ajouter :

```python
def test_task_with_low_confidence_not_eligible():
    """Task with confidence below threshold is not eligible."""
    from kanban_implementer.selector import Task
    t = Task(
        id="t1", title="Test", project="hub", status="To Start",
        priority="Medium", effort_hours=1.0, assignee="DomBot",
        source_file="", confidence=0.2,
    )
    assert not t.is_eligible


def test_task_with_null_confidence_uses_default():
    """Null confidence treated as 0.5 → eligible if threshold ≤ 0.5."""
    from kanban_implementer.selector import Task
    t = Task(
        id="t2", title="Test", project="hub", status="To Start",
        priority="Medium", effort_hours=1.0, assignee="DomBot",
        source_file="", confidence=None,
    )
    assert t.is_eligible  # 0.5 >= 0.4 (default threshold)


def test_human_assignee_always_eligible():
    """Human assignee → confidence_effective = 1.0, always passes filter."""
    from kanban_implementer.selector import Task
    t = Task(
        id="t3", title="Test", project="hub", status="To Start",
        priority="Medium", effort_hours=1.0, assignee="lgiron",
        source_file="", confidence=0.0,
    )
    assert t.is_eligible
```

- [ ] **Step 4.4: Vérifier que les tests échouent**

```bash
cd /home/lgiron/.openclaw/skills/kanban-implementer/core
uv run pytest tests/test_selector.py -v -k "confidence or human"
```
Expected: `FAILED` — `Task` n'a pas de champ `confidence`, `is_eligible` ne filtre pas encore.

- [ ] **Step 4.5: Modifier selector.py — ajouter le champ confidence et mettre à jour is_eligible**

Dans `.openclaw/skills/kanban-implementer/core/kanban_implementer/selector.py` :

**1. Modifier la ligne d'import existante (ligne 8 de selector.py) — ne pas dupliquer :**
```python
from kanban_implementer.config import TASKS_JSON, PRIORITY_PROJECT, MAX_EFFORT, WORKSPACE, MIN_CONFIDENCE
```

**2. Ajouter la constante AGENT_ASSIGNEES après ELIGIBLE_STATUSES :**
```python
AGENT_ASSIGNEES = {"DomBot"}
```

**3. Ajouter le champ `confidence` dans le dataclass `Task` (après `notes`) :**
```python
    confidence: float | None = None
```

**4. Remplacer la propriété `is_eligible` :**
```python
    @property
    def confidence_effective(self) -> float:
        """1.0 for humans, task.confidence ?? 0.5 for agents."""
        if self.assignee not in AGENT_ASSIGNEES:
            return 1.0
        return self.confidence if self.confidence is not None else 0.5

    @property
    def is_eligible(self) -> bool:
        return (
            self.status in ELIGIBLE_STATUSES
            and self.assignee == "DomBot"
            and self.effort_hours <= MAX_EFFORT
            and self.confidence_effective >= MIN_CONFIDENCE
        )
```

**5. Ajouter `confidence` dans `load_tasks()` lors de la création de Task :**
```python
            confidence=t.get("confidence"),  # float | None
```

- [ ] **Step 4.6: Vérifier que les tests passent**

```bash
cd /home/lgiron/.openclaw/skills/kanban-implementer/core
uv run pytest tests/test_selector.py -v
```
Expected: tous les tests passent (y compris les 3 nouveaux).

- [ ] **Step 4.7: Commit**

```bash
cd /home/lgiron/.openclaw/skills/kanban-implementer
git add SKILL.md core/kanban_implementer/config.py core/kanban_implementer/selector.py core/tests/test_selector.py
git commit -m "feat(skill/kanban-implementer): add confidence_effective filter (Kahneman, null=0.5, human=1.0)"
```

---

## Task 5: Skill proactive-innovation — grille de scoring

**Files:**
- Modify: `.openclaw/skills/proactive-innovation/SKILL.md`

- [ ] **Step 5.1: Ajouter la grille de scoring dans Phase 1 (Scan projets)**

Dans la section **Phase 1 — Scan projets**, trouver le bloc `curl -X POST /kanban/tasks` et modifier pour inclure `confidence` :

```markdown
4. **Kanban integration :** pour chaque amélioration proposée, créer aussi une tâche via l'API Kanban
   avec un score de confiance estimé selon la grille ci-dessous :

   | Type d'amélioration | `confidence` |
   |---------------------|-------------|
   | Correctif certain (typo, config cassée, sécurité) | `0.75` |
   | Amélioration standard (DX, perf mesurable) | `0.55` |
   | Idée spéculative (feature, refacto subjective) | `0.3` |

   > `0.55` (et non `0.5`) différencie visuellement une amélioration explicitement évaluée du
   > défaut `null → 0.50` affiché sur les tâches sans score.

   ```bash
   curl -X POST http://localhost:8088/api/kanban/tasks \
     -H 'Content-Type: application/json' \
     -d '{"title":"...","project":"<nom-projet>","priority":"Medium","assignee":"DomBot","confidence":0.55}'
   ```
```

- [ ] **Step 5.2: Ajouter la grille dans Phase 3 (Idées entrepreneur/OSS)**

Dans la section **Phase 3**, modifier la création de tâche kanban pour inclure `confidence: 0.3` (idées spéculatives par défaut) :

```markdown
Pour les idées structurées, créer aussi une tâche Kanban avec `confidence: 0.3` (idée spéculative) :
```bash
curl -X POST http://localhost:8088/api/kanban/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"...","project":"entrepreneur","priority":"Low","assignee":"DomBot","confidence":0.3}'
```
```

- [ ] **Step 5.3: Commit**

```bash
git add .openclaw/skills/proactive-innovation/SKILL.md
git commit -m "feat(skill/proactive-innovation): add Kahneman confidence grid on task creation"
```

---

## Task 6: Documentation + mémoire

**Files:**
- Create or update: `docs/architecture/sse-confidence.md` (dombot-labos)
- Update: `.openclaw/workspace/memory/resources/knowledge/agents/claude-memory.md`
- Update: `.openclaw/workspace/memory/projects/hub.md` (si existant)

- [ ] **Step 6.1: Créer la doc dans dombot-labos**

Créer `docs/architecture/sse-confidence.md` :

```markdown
# SSE Kanban + Confidence Scoring (Kahneman)

## Architecture

Le kanban board reçoit les mises à jour en temps réel via SSE (Server-Sent Events).
L'API expose `GET /stream` (proxié via nginx `/api/kanban/stream`).

## Endpoint SSE

- **Route FastAPI :** `GET /stream` (kanban_api/sse.py)
- **Nginx :** `/api/kanban/stream` → `http://kanban_api/stream`
- **Heartbeat :** `: ping\n\n` toutes les 5s si aucun changement
- **Payload :** même structure que `GET /tasks` ({tasks, stats, projects, meta})
- **Nginx requis :** `proxy_buffering off` + `proxy_read_timeout 3600`

## Confidence Scoring (Kahneman)

| Score | Niveau | Couleur | Signification |
|-------|--------|---------|---------------|
| 0.0–0.39 | Low | Rouge | System 1 — intuitif, risqué |
| 0.4–0.69 | Mid | Amber | Zone boundary |
| 0.7–1.0 | High | Vert | System 2 — délibéré, validé |
| `null` (agent) | Mid | Amber | Traité comme 0.5 |
| humain | — | (pas de badge) | Confiance effective 1.0 |

## Convention AGENT_ASSIGNEES

```python
AGENT_ASSIGNEES = {"DomBot"}
```

Tout assignee ∉ AGENT_ASSIGNEES est humain → confidence_effective = 1.0.

## Variables d'environnement

| Variable | Défaut | Usage |
|----------|--------|-------|
| `KANBAN_MIN_CONFIDENCE` | `0.4` | Seuil minimum pour kanban-implementer |

## Grille proactive-innovation

| Type | confidence |
|------|-----------|
| Correctif certain | 0.75 |
| Amélioration standard | 0.55 |
| Idée spéculative | 0.3 |
```

- [ ] **Step 6.2: Mettre à jour la mémoire Claude**

Dans `.openclaw/workspace/memory/resources/knowledge/agents/claude-memory.md`, ajouter dans la section **Patterns & Décisions techniques** :

```markdown
### SSE Kanban (2026-03-17)
- `GET /stream` dans `kanban_api/sse.py` — hash MD5 (sort_keys=True) pour détecter les changements
- nginx requis : `proxy_buffering off` + `proxy_read_timeout 3600` sur `/api/kanban/`
- Frontend : `EventSource('/api/kanban/stream')` remplace `setInterval(load, 30000)`
- `load()` initial conservé pour état immédiat au démarrage (SSE premier tick à +5s)

### Confidence scoring Kahneman final (2026-03-17)
- Grille proactive-innovation : correctif=0.75, standard=0.55, spéculatif=0.3
- `null` (agent) → affiché 0.50 Mid/amber ; humain → pas de badge, effective=1.0
- `KANBAN_MIN_CONFIDENCE=0.4` (env var, float cast) dans kanban-implementer
- `AGENT_ASSIGNEES = {"DomBot"}` — convention unifiée UI + Python + SKILL.md
```

- [ ] **Step 6.3: Commit docs**

```bash
git add docs/architecture/sse-confidence.md
git commit -m "docs: add SSE + Kahneman confidence scoring architecture doc"
```

---

## Task 7: MR — squash et merge dans main

- [ ] **Step 7.1: Vérifier l'état de la branche**

```bash
git log --oneline main..HEAD
git diff main --stat
```

- [ ] **Step 7.2: Lancer tous les tests kanban**

```bash
cd /home/lgiron/Lab/dombot-labos/core-tools/kanban
uv run pytest tests/ -v
```
Expected: tous les tests existants + 2 nouveaux tests SSE passent.

- [ ] **Step 7.3: Créer la MR (PR GitHub)**

> Note : Les modifications Tasks 2 et 3 (`Lab/hub/`) sont committées directement dans ce repo séparé (pas de PR). Seules les modifications `dombot-labos/` font l'objet d'une PR.

```bash
cd /home/lgiron/Lab/dombot-labos
git push -u origin HEAD
gh pr create \
  --title "feat: SSE kanban + Kahneman confidence scoring" \
  --body "$(cat <<'EOF'
## Résumé

- **SSE** : remplace le polling 30s du kanban board par `EventSource('/api/kanban/stream')` (heartbeat 5s, hash-dedup)
- **nginx** : `proxy_buffering off` + `proxy_read_timeout 3600` sur `/api/kanban/`
- **Badge confiance** : affichage Kahneman (rouge/amber/vert) sur les cartes DomBot uniquement
- **kanban-implementer** : filtre `confidence_effective ≥ KANBAN_MIN_CONFIDENCE (0.4)`
- **proactive-innovation** : grille de scoring (0.75 / 0.55 / 0.3) sur les tâches créées

## Règle humain = 1.0
Toute tâche assignée à un humain (`assignee ∉ {"DomBot"}`) a une confiance effective de 1.0 — jamais bloquée par le filtre.

## Tests
- [ ] `uv run pytest core-tools/kanban/tests/ -v` — 2 nouveaux tests SSE + tests existants OK
- [ ] nginx syntaxe validée

🤖 Implémenté via superpowers:brainstorming + writing-plans
EOF
)"
```

- [ ] **Step 7.4: Squash et merge dans main**

```bash
gh pr merge --squash --delete-branch
```

Ou via l'interface GitHub : **Squash and merge**.

- [ ] **Step 7.5: Vérifier**

```bash
git checkout main && git pull
git log --oneline -5
```
Expected: un seul commit de squash avec le titre de la PR.
