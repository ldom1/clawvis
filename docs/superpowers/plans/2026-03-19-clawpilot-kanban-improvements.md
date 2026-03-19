# ClawPilot + Kanban Improvements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Renommer dombot-labos en ClawPilot, ajouter le status "Blocked", corriger Gantt et Graph, créer le dashboard PilotView, et améliorer kanban-implementer pour clarifier les tâches ambiguës avant implémentation.

**Architecture:** 6 tâches indépendantes dans l'ordre de dépendance : (1) "Blocked" est un prérequis pour (4) Graph couleurs et (6) kanban-implementer ; les autres sont parallélisables. L'API kanban (FastAPI) et le frontend (index.html vanilla JS) sont dans des répertoires séparés. Le skill kanban-implementer est dans `~/.openclaw/`.

**Tech Stack:** Python 3.12 + Pydantic v2 + FastAPI + pytest + uv ; vanilla JS + D3.js v7 (CDN) ; Vite + TypeScript (landing)

---

## File Map

### Task 1 — Status "Blocked"
| Action | Fichier |
|--------|---------|
| Modify | `core-tools/kanban/kanban_api/models.py` |
| Modify | `core-tools/kanban/kanban_api/core.py` |
| Modify | `core-tools/kanban/TASK_MODEL.md` |
| Modify | `hub/public/kanban/index.html` |
| Modify | `core-tools/kanban/tests/test_confidence.py` (nouveaux tests Blocked) |

### Task 2 — Renommage ClawPilot
| Action | Fichier |
|--------|---------|
| Modify | `README.md` |
| Modify | `landing/index.html` |
| Modify | `landing/package.json` |
| Modify | `docker-compose.yml` |

### Task 3 — Gantt fix
| Action | Fichier |
|--------|---------|
| Modify | `hub/public/kanban/index.html` — fonction `renderGantt()` |

### Task 4 — Graph DAG
| Action | Fichier |
|--------|---------|
| Modify | `hub/public/kanban/index.html` — ajout D3 CDN + `renderGraph()` |

### Task 5 — PilotView
| Action | Fichier |
|--------|---------|
| Create | `core-tools/kanban/kanban_api/weekly_stats.py` |
| Modify | `core-tools/kanban/kanban_api/api.py` — ajout `GET /stats/weekly` |
| Modify | `hub/public/kanban/index.html` — `renderMeta()` → `renderPilotView()` |
| Create | `core-tools/kanban/tests/test_weekly_stats.py` |

### Task 6 — Kanban-implementer clarification
| Action | Fichier |
|--------|---------|
| Modify | `~/.openclaw/skills/kanban-implementer/core/kanban_implementer/selector.py` |
| Modify | `~/.openclaw/skills/kanban-implementer/core/kanban_implementer/__main__.py` |
| Modify | `~/.openclaw/skills/kanban-implementer/SKILL.md` |
| Modify | `~/.openclaw/skills/kanban-implementer/core/tests/test_selector.py` |

---

## Task 1 : Status "Blocked"

**Prérequis :** aucun. **Débloque :** Tasks 4 et 6.

**Files:**
- Modify: `core-tools/kanban/kanban_api/models.py:8-10`
- Modify: `core-tools/kanban/kanban_api/core.py:22,111,224-230`
- Modify: `core-tools/kanban/TASK_MODEL.md`
- Modify: `hub/public/kanban/index.html`

- [ ] **Step 1 : Écrire les tests qui échouent**

Dans `core-tools/kanban/tests/test_confidence.py`, ajouter à la fin :

```python
def test_blocked_status_is_valid():
    from kanban_api.models import Task
    t = Task(id="x", title="T", status="Blocked")
    assert t.status == "Blocked"


def test_blocked_status_in_statuses_list():
    from kanban_api.models import STATUSES
    assert "Blocked" in STATUSES
    # Blocked doit être entre In Progress et Review
    idx_blocked = STATUSES.index("Blocked")
    idx_ip = STATUSES.index("In Progress")
    idx_review = STATUSES.index("Review")
    assert idx_ip < idx_blocked < idx_review


def test_blocked_skips_dependency_check():
    """Passer en Blocked ne déclenche pas _check_dependencies."""
    from kanban_api.core import _check_dependencies, DependencyBlockedError
    data = {
        "tasks": [
            {"id": "dep-1", "title": "Dep", "status": "To Start"},
        ]
    }
    task = {"id": "t-1", "title": "T", "dependencies": ["dep-1"]}
    # Ne doit pas lever DependencyBlockedError
    _check_dependencies(data, task, "Blocked")  # no exception expected
```

- [ ] **Step 2 : Lancer les tests — vérifier qu'ils échouent**

```bash
cd /home/lgiron/Lab/dombot-labos/core-tools/kanban
uv run pytest tests/test_confidence.py::test_blocked_status_is_valid tests/test_confidence.py::test_blocked_status_in_statuses_list tests/test_confidence.py::test_blocked_skips_dependency_check -v
```
Attendu : FAIL (`'Blocked' is not a valid Status`)

- [ ] **Step 3 : Modifier `models.py`**

Remplacer lignes 8–10 :

```python
Status = Literal["Backlog", "To Start", "In Progress", "Blocked", "Review", "Done", "Archived"]
Priority = Literal["Critical", "High", "Medium", "Low"]
STATUSES: list[str] = ["Backlog", "To Start", "In Progress", "Blocked", "Review", "Done", "Archived"]
```

- [ ] **Step 4 : Modifier `core.py`**

**Ligne 22** — remplacer `STATUSES` :
```python
STATUSES: list[str] = ["Backlog", "To Start", "In Progress", "Blocked", "Review", "Done"]
```

**Fonction `_check_dependencies`** (ligne 224) — ajouter le guard :
```python
def _check_dependencies(data: dict, task: dict, target_status: str) -> None:
    if target_status in ("Blocked", "Review", "Done"):
        return
    if target_status != "In Progress":
        return
    for dep_id in task.get("dependencies") or []:
        dep = next((t for t in data["tasks"] if t["id"] == dep_id), None)
        if dep and dep.get("status") != "Done":
            raise DependencyBlockedError(dep.get("title", dep_id))
```

Note : le guard `target_status in ("Blocked", "Review", "Done")` couvre Blocked + conserve le comportement Review/Done existant.

- [ ] **Step 5 : Modifier `TASK_MODEL.md`**

Dans la section "Ordonnancement dans `tasks.json`", item 2, mettre à jour l'ordre :
- Remplacer `Backlog → To Start → In Progress → Review → Done → Archived`
- Par `Backlog → To Start → In Progress → Blocked → Review → Done → Archived`

- [ ] **Step 6 : Modifier `index.html`** (kanban frontend)

Dans `hub/public/kanban/index.html` :

**a) Constante STATUSES** (ligne ~266) :
```js
const STATUSES = ['Backlog', 'To Start', 'In Progress', 'Blocked', 'Review', 'Done'];
```

**b) COL_ICONS** :
```js
const COL_ICONS = {'To Start': '🤖', 'Backlog': '📥', 'In Progress': '🔨', 'Blocked': '⛔', 'Review': '👀', 'Done': '✅'};
```

**c) CSS — ajouter après `.badge-conf-low` (ligne ~119)** :
```css
.column[data-status="Blocked"] { border-color: rgba(124,58,237,0.4); }
.column[data-status="Blocked"] .col-header { color: #7c3aed; }
.badge-Blocked { background: rgba(124,58,237,0.15); color: #7c3aed; }
```

**d) status-btn Blocked** — dans `openDetail()`, dans le `STATUSES.map(...)` des status-buttons, aucun changement de code nécessaire (STATUSES est itéré dynamiquement). Ajouter le style CSS :
```css
.status-btn[data-s="Blocked"] { --sc: #7c3aed; }
.status-btn.active[data-s="Blocked"] { background: #7c3aed; border-color: #7c3aed; }
```

**e) Grille CSS board** — passer de `repeat(5, 1fr)` à `repeat(6, 1fr)` :
```css
.board { display: grid; grid-template-columns: repeat(6, 1fr); gap: 0.75rem; ... }
@media (max-width: 1300px) { .board { grid-template-columns: repeat(3, 1fr); } }
```

- [ ] **Step 7 : Lancer les tests**

```bash
cd /home/lgiron/Lab/dombot-labos/core-tools/kanban
uv run pytest tests/ -v
```
Attendu : tous les tests passent, y compris les 3 nouveaux.

- [ ] **Step 8 : Commit**

```bash
cd /home/lgiron/Lab/dombot-labos
git add core-tools/kanban/kanban_api/models.py core-tools/kanban/kanban_api/core.py core-tools/kanban/TASK_MODEL.md hub/public/kanban/index.html core-tools/kanban/tests/test_confidence.py
git commit -m "feat: add Blocked status to kanban (model, core, UI)"
```

---

## Task 2 : Renommage ClawPilot

**Prérequis :** aucun. **Débloque :** rien.

**Files:**
- Modify: `README.md`
- Modify: `landing/index.html`
- Modify: `landing/package.json`
- Modify: `docker-compose.yml`

- [ ] **Step 1 : Modifier `README.md`**

Remplacer le titre et tagline :
```markdown
# ClawPilot

> Your personal AI agent OS — Matrix-grade orchestration, on your machine.
> Open Source · Self-Hosted · AI-Native
```

- [ ] **Step 2 : Modifier `landing/index.html`**

Remplacer :
- `<title>DomBot LabOS</title>` → `<title>ClawPilot</title>`
- `<meta name="description" content="...">` → `<meta name="description" content="ClawPilot — Your personal AI agent OS. Matrix-grade orchestration, self-hosted, open source.">`
- Tout texte "DomBot LabOS" dans le HTML → "ClawPilot"
- Hero h1/tagline → "ClawPilot" + "Your personal AI agent OS — Matrix-grade orchestration, on your machine."

- [ ] **Step 3 : Modifier `landing/package.json`**

```json
{
  "name": "clawpilot-landing",
  ...
}
```

- [ ] **Step 4 : Modifier `docker-compose.yml`**

Pour chaque service, remplacer les labels et container_name :
```yaml
container_name: clawpilot-hub   # était: dombot-hub ou labos-hub
labels:
  - "app=clawpilot"
```

- [ ] **Step 5 : Build landing pour vérifier aucune erreur**

```bash
cd /home/lgiron/Lab/dombot-labos/landing
yarn build
```
Attendu : build sans erreur, output dans `hub/public/`.

- [ ] **Step 6 : Commit**

```bash
cd /home/lgiron/Lab/dombot-labos
git add README.md landing/index.html landing/package.json docker-compose.yml
git commit -m "feat: rename dombot-labos → ClawPilot (README, landing, docker)"
```

---

## Task 3 : Gantt fix — barres proportionnelles

**Prérequis :** aucun. **Débloque :** rien.

**Files:**
- Modify: `hub/public/kanban/index.html` — fonction `renderGantt()`

- [ ] **Step 1 : Remplacer `renderGantt()` dans `index.html`**

Localiser la fonction `renderGantt(filtered)` (ligne ~497) et la remplacer intégralement :

```js
function renderGantt(filtered) {
  const board = document.getElementById('board');
  board.innerHTML = '';

  const LABEL_W = 200;  // px réservés pour le label gauche

  // Calcul start/end selon les 4 cas du spec
  function getRange(t) {
    const end = t.end_date || t.timeline;
    if (!end) return null;
    const start = t.start_date || t.created || end;
    return { start: new Date(start), end: new Date(end) };
  }

  const tasksWithRange = filtered.map(t => ({ t, range: getRange(t) })).filter(x => x.range);
  const excluded = filtered.length - tasksWithRange.length;

  if (!tasksWithRange.length) {
    board.innerHTML = '<div class="column" style="grid-column:1/-1;align-items:center;justify-content:center;"><div class="empty-col">Aucune tâche avec date de fin pour ce filtre.</div></div>';
    return;
  }

  const allStarts = tasksWithRange.map(x => x.range.start.getTime());
  const allEnds   = tasksWithRange.map(x => x.range.end.getTime());
  const padMs = 3 * 24 * 60 * 60 * 1000;
  const rangeStart = new Date(Math.min(...allStarts) - padMs);
  const rangeEnd   = new Date(Math.max(...allEnds)   + padMs);
  const totalMs    = Math.max(rangeEnd - rangeStart, 24 * 60 * 60 * 1000);

  // Axe en semaines
  const weekMs = 7 * 24 * 60 * 60 * 1000;
  const totalWeeks = totalMs / weekMs;
  const tickStep = Math.max(1, Math.ceil(totalWeeks / 10));

  const container = document.createElement('div');
  container.className = 'column';
  container.style.gridColumn = '1 / -1';
  container.innerHTML =
    `<div class="col-header"><h2>📆 Vue Gantt</h2><span class="col-count">${tasksWithRange.length}</span></div>` +
    (excluded ? `<div style="font-size:0.72rem;color:var(--muted);margin-bottom:0.4rem">${excluded} tâche(s) sans date de fin masquée(s)</div>` : '');

  const gantt = document.createElement('div');
  gantt.className = 'gantt-container';
  const inner = document.createElement('div');
  inner.className = 'gantt-inner';

  // Axe temporel
  const axis = document.createElement('div');
  axis.className = 'gantt-axis';
  for (let w = 0; w <= totalWeeks; w += tickStep) {
    const d = new Date(rangeStart.getTime() + w * weekMs);
    const pct = Math.min(100, (d - rangeStart) / totalMs * 100);
    const tick = document.createElement('div');
    tick.className = 'gantt-axis-tick';
    tick.style.left = `calc(${LABEL_W}px + ${pct}% * (100% - ${LABEL_W}px) / 100)`;
    tick.innerHTML = `<div class="gantt-axis-tick-line"></div><div>${d.toISOString().slice(5,10)}</div>`;
    axis.appendChild(tick);
  }

  // Lignes de tâches
  const rows = document.createElement('div');
  rows.className = 'gantt-rows';
  tasksWithRange.sort((a,b) => a.range.start - b.range.start);

  tasksWithRange.forEach(({ t, range }) => {
    const row = document.createElement('div');
    row.className = 'gantt-row';

    const label = document.createElement('div');
    label.className = 'gantt-label';
    label.style.maxWidth = LABEL_W + 'px';
    label.textContent = t.title;
    row.appendChild(label);

    const startPct = (range.start - rangeStart) / totalMs * 100;
    const durationPct = Math.max(0, (range.end - range.start) / totalMs * 100);

    const bar = document.createElement('div');
    bar.className = 'gantt-bar';
    bar.dataset.status = t.status;
    // Position relative à la zone de chart (après le label)
    bar.style.position = 'absolute';
    bar.style.left = `calc(${LABEL_W}px + ${startPct}% * (100% - ${LABEL_W}px) / 100)`;
    bar.style.width = `calc(max(8px, ${durationPct}% * (100% - ${LABEL_W}px) / 100))`;
    bar.style.top = '50%';
    bar.style.transform = 'translateY(-50%)';
    bar.onclick = () => openDetail(t);

    const durationDays = Math.round((range.end - range.start) / (24*60*60*1000));
    bar.innerHTML = durationDays >= 3
      ? `<span>${durationDays}j</span>`
      : '';

    row.appendChild(bar);
    rows.appendChild(row);
  });

  inner.appendChild(axis);
  inner.appendChild(rows);
  gantt.appendChild(inner);
  container.appendChild(gantt);
  board.appendChild(container);
}
```

- [ ] **Step 2 : Tester manuellement dans le navigateur**

Ouvrir `https://lab.dombot.tech/kanban/`, cliquer "Gantt".
Vérifier : barres proportionnelles visibles, axe en semaines, tâches Done en vert.

Si pas de tâche avec date → voir le message "Aucune tâche avec date de fin".

- [ ] **Step 3 : Commit**

```bash
cd /home/lgiron/Lab/dombot-labos
git add hub/public/kanban/index.html
git commit -m "fix: gantt proportional bars using start_date/end_date with created/timeline fallback"
```

---

## Task 4 : Graph DAG par projet (D3.js)

**Prérequis :** Task 1 (pour les couleurs Blocked). **Débloque :** rien.

**Files:**
- Modify: `hub/public/kanban/index.html` — ajout D3 CDN + `renderGraph()`

- [ ] **Step 1 : Ajouter D3 CDN dans `<head>`**

Dans `hub/public/kanban/index.html`, avant `</head>` :
```html
<script src="https://d3js.org/d3.v7.min.js"></script>
```

- [ ] **Step 2 : Remplacer `renderGraph()` intégralement**

Localiser la fonction `renderGraph(filtered)` (ligne ~573) et la remplacer :

```js
function renderGraph(filtered) {
  const board = document.getElementById('board');
  board.innerHTML = '';

  // Couleurs par status
  const STATUS_COLOR = {
    'Backlog':     '#52525b',
    'To Start':    '#06b6d4',
    'In Progress': '#3b82f6',
    'Blocked':     '#7c3aed',
    'Review':      '#f59e0b',
    'Done':        '#22c55e',
  };

  // Algorithme de Kahn pour tri topologique + détection cycles
  function kahnLevels(nodes, edges) {
    // edges: [{source: id, target: id}]
    const inDeg = {};
    nodes.forEach(n => inDeg[n.id] = 0);
    edges.forEach(e => { if (inDeg[e.target] !== undefined) inDeg[e.target]++; });

    const queue = nodes.filter(n => inDeg[n.id] === 0).map(n => n.id);
    const level = {};
    let processed = 0;

    while (queue.length) {
      const id = queue.shift();
      processed++;
      edges.filter(e => e.source === id).forEach(e => {
        if (inDeg[e.target] !== undefined) {
          inDeg[e.target]--;
          level[e.target] = Math.max(level[e.target] || 0, (level[id] || 0) + 1);
          if (inDeg[e.target] === 0) queue.push(e.target);
        }
      });
    }

    const cycleNodes = nodes.filter(n => level[n.id] === undefined);
    nodes.forEach(n => { if (level[n.id] === undefined) level[n.id] = -1; }); // cycle marker
    return { level, cycleNodes };
  }

  // Grouper par projet
  const byProject = {};
  filtered.forEach(t => {
    const p = t.project || '(aucun projet)';
    (byProject[p] = byProject[p] || []).push(t);
  });

  const allDepsEdges = [];
  filtered.forEach(t => {
    (t.dependencies || []).forEach(depId => {
      if (filtered.find(x => x.id === depId)) {
        allDepsEdges.push({ source: depId, target: t.id });
      }
    });
  });

  const hasDeps = allDepsEdges.length > 0;
  if (!hasDeps) {
    board.innerHTML = '<div class="column" style="grid-column:1/-1;align-items:center;justify-content:center;"><div class="empty-col">Aucune dépendance définie</div></div>';
    return;
  }

  const col = document.createElement('div');
  col.className = 'column';
  col.style.gridColumn = '1 / -1';
  col.innerHTML = '<div class="col-header"><h2>🕸️ Dependency graph</h2><span class="col-count">' + allDepsEdges.length + '</span></div>';

  const graphDiv = document.createElement('div');
  graphDiv.className = 'graph-container';
  col.appendChild(graphDiv);
  board.appendChild(col);

  // Layout par projet
  const NODE_R = 14;
  const COL_W  = 120;
  const ROW_H  = 70;
  const PAD    = 30;
  const PROJ_GAP = 50;

  const projectGroups = [];
  let globalX = PAD;

  Object.entries(byProject).forEach(([proj, nodes]) => {
    const projEdges = allDepsEdges.filter(e =>
      nodes.find(n => n.id === e.source) && nodes.find(n => n.id === e.target)
    );
    const { level, cycleNodes } = kahnLevels(nodes, projEdges);
    const maxLevel = Math.max(0, ...nodes.filter(n => level[n.id] >= 0).map(n => level[n.id]));

    // Répartir par niveau
    const byLevel = {};
    nodes.forEach(n => {
      const lv = level[n.id] >= 0 ? level[n.id] : maxLevel + 1;
      (byLevel[lv] = byLevel[lv] || []).push(n);
    });

    // Calculer positions
    const posById = {};
    let projW = 0;
    Object.entries(byLevel).forEach(([lv, lvNodes]) => {
      const x = globalX + parseInt(lv) * COL_W;
      lvNodes.forEach((n, i) => {
        posById[n.id] = { x, y: PAD + i * ROW_H + ROW_H / 2 };
      });
      projW = Math.max(projW, (parseInt(lv) + 1) * COL_W);
    });

    projectGroups.push({ proj, nodes, projEdges, posById, cycleNodes, x: globalX, w: projW });
    globalX += projW + PROJ_GAP;
  });

  const totalH = Math.max(200, PAD * 2 + Math.max(...projectGroups.map(g =>
    Math.max(...Object.values(g.posById).map(p => p.y)) + ROW_H
  )));
  const totalW = globalX;

  const svg = d3.select(graphDiv)
    .append('svg')
    .attr('width', '100%')
    .attr('viewBox', `0 0 ${totalW} ${totalH}`)
    .attr('class', 'graph-svg');

  svg.append('defs').append('marker')
    .attr('id', 'arrow')
    .attr('viewBox', '0 0 10 10').attr('refX', 10).attr('refY', 5)
    .attr('markerWidth', 6).attr('markerHeight', 6)
    .attr('orient', 'auto-start-reverse')
    .append('path').attr('d', 'M0 0 L10 5 L0 10 z')
    .attr('fill', 'rgba(148,163,184,0.8)');

  projectGroups.forEach(({ proj, nodes, projEdges, posById, cycleNodes, x, w }) => {
    const maxY = Math.max(...Object.values(posById).map(p => p.y)) + ROW_H;
    // Boîte projet
    svg.append('rect')
      .attr('x', x - 10).attr('y', 10)
      .attr('width', w + 10).attr('height', maxY - 10)
      .attr('rx', 8).attr('fill', 'none')
      .attr('stroke', 'rgba(148,163,184,0.3)').attr('stroke-dasharray', '4 3');
    svg.append('text')
      .attr('x', x).attr('y', 24)
      .attr('fill', 'var(--muted)').attr('font-size', '0.65rem')
      .text(proj);

    // Arêtes
    projEdges.forEach(e => {
      const s = posById[e.source], t2 = posById[e.target];
      if (!s || !t2) return;
      const color = STATUS_COLOR[nodes.find(n => n.id === e.source)?.status] || '#52525b';
      svg.append('line')
        .attr('x1', s.x + NODE_R).attr('y1', s.y)
        .attr('x2', t2.x - NODE_R).attr('y2', t2.y)
        .attr('stroke', color).attr('stroke-width', 1.2)
        .attr('marker-end', 'url(#arrow)');
    });

    // Nœuds
    nodes.forEach(n => {
      const pos = posById[n.id];
      if (!pos) return;
      const isCycle = cycleNodes.find(c => c.id === n.id);
      const color = STATUS_COLOR[n.status] || '#52525b';
      const r = 12 + Math.min(n.effort_hours || 0, 8) * 1.2;

      svg.append('circle')
        .attr('cx', pos.x).attr('cy', pos.y).attr('r', r)
        .attr('fill', '#020617')
        .attr('stroke', isCycle ? '#ef4444' : color)
        .attr('stroke-width', isCycle ? 2 : 1.2)
        .style('cursor', 'pointer')
        .on('click', () => openDetailById(n.id));

      const label = (n.title || '').length > 18 ? (n.title || '').slice(0, 15) + '…' : (n.title || '');
      svg.append('text')
        .attr('x', pos.x + r + 4).attr('y', pos.y + 4)
        .attr('fill', '#e5e7eb').attr('font-size', '0.68rem')
        .style('cursor', 'pointer')
        .on('click', () => openDetailById(n.id))
        .text(label);
    });

    // Groupe cycle si présent
    if (cycleNodes.length) {
      svg.append('text')
        .attr('x', x).attr('y', maxY - 5)
        .attr('fill', '#ef4444').attr('font-size', '0.6rem')
        .text(`⚠ Cycle détecté : ${cycleNodes.map(n => n.title.slice(0,12)).join(', ')}`);
    }
  });
}
```

- [ ] **Step 3 : Tester manuellement**

Ouvrir `https://lab.dombot.tech/kanban/`, cliquer "Graph".
Vérifier : groupes projet séparés, arêtes avec flèches, couleurs par status, clic ouvre modale.
Si aucune dépendance → message "Aucune dépendance définie".

- [ ] **Step 4 : Commit**

```bash
cd /home/lgiron/Lab/dombot-labos
git add hub/public/kanban/index.html
git commit -m "feat: graph DAG layout per project with D3.js (topological columns, cycle detection)"
```

---

## Task 5 : PilotView — Dashboard de pilotage

**Prérequis :** aucun. **Débloque :** rien.

**Files:**
- Create: `core-tools/kanban/kanban_api/weekly_stats.py`
- Modify: `core-tools/kanban/kanban_api/api.py`
- Modify: `hub/public/kanban/index.html`
- Create: `core-tools/kanban/tests/test_weekly_stats.py`

- [ ] **Step 1 : Écrire les tests qui échouent**

Créer `core-tools/kanban/tests/test_weekly_stats.py` :

```python
"""Tests for PilotView weekly stats endpoint."""
from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, AsyncMock
import pytest
from kanban_api.weekly_stats import compute_weekly_stats, parse_git_log


def _iso(days_ago: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat() + "Z"


SAMPLE_TASKS = [
    {"id": "t1", "title": "A", "project": "hub", "status": "Done",        "assignee": "DomBot", "effort_hours": 1.0, "created": _iso(3),  "updated": _iso(3)},
    {"id": "t2", "title": "B", "project": "hub", "status": "In Progress", "assignee": "DomBot", "effort_hours": 2.0, "created": _iso(2),  "updated": _iso(2)},
    {"id": "t3", "title": "C", "project": "ruflo", "status": "To Start",  "assignee": "ldom1",  "effort_hours": 0.5, "created": _iso(10), "updated": _iso(10)},
]


def test_compute_weekly_stats_projects():
    result = compute_weekly_stats(SAMPLE_TASKS, recent_commits=[], pending_review=[])
    projects = {p["name"]: p for p in result["projects"]}
    assert "hub" in projects
    assert projects["hub"]["active_count"] == 1  # only In Progress (Done excluded from active)
    assert projects["hub"]["majority_assignee"] == "DomBot"


def test_compute_weekly_stats_weeks():
    result = compute_weekly_stats(SAMPLE_TASKS, recent_commits=[], pending_review=[])
    assert "this_week" in result["weeks"]
    assert "last_week" in result["weeks"]
    # t1 created 3 days ago → this_week done=1
    assert result["weeks"]["this_week"]["done"] >= 1


def test_parse_git_log_valid():
    raw = "2026-03-19|hub|feat: add blocked status|ldom1\n2026-03-18|kanban|fix: gantt bars|ldom1\n"
    commits = parse_git_log(raw, repo="hub")
    assert len(commits) == 2
    assert commits[0]["repo"] == "hub"
    assert commits[0]["message"] == "feat: add blocked status"


def test_parse_git_log_empty():
    assert parse_git_log("", repo="hub") == []


def test_majority_assignee_tie_alphabetical():
    tasks = [
        {"project": "p", "status": "In Progress", "assignee": "zara", "effort_hours": 1},
        {"project": "p", "status": "To Start",    "assignee": "alice", "effort_hours": 1},
    ]
    result = compute_weekly_stats(tasks, recent_commits=[], pending_review=[])
    p = next(x for x in result["projects"] if x["name"] == "p")
    assert p["majority_assignee"] == "alice"  # alphabetical tiebreak
```

- [ ] **Step 2 : Lancer les tests — vérifier qu'ils échouent**

```bash
cd /home/lgiron/Lab/dombot-labos/core-tools/kanban
uv run pytest tests/test_weekly_stats.py -v
```
Attendu : FAIL (module `weekly_stats` inexistant)

- [ ] **Step 3 : Créer `kanban_api/weekly_stats.py`**

```python
"""Compute weekly stats for PilotView dashboard."""
from __future__ import annotations

import asyncio
import logging
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

LAB_REPOS_ENV_VAR = "LAB_REPOS"


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _in_window(iso: str | None, days_start: int, days_end: int) -> bool:
    """True if the ISO date is between days_start and days_end days ago."""
    dt = _parse_iso(iso)
    if not dt:
        return False
    now = datetime.now(timezone.utc)
    return (now - timedelta(days=days_start)) >= dt >= (now - timedelta(days=days_end))


def compute_weekly_stats(
    tasks: list[dict],
    recent_commits: list[dict],
    pending_review: list[dict],
) -> dict:
    """Pure computation — no I/O."""
    active_statuses = {"Backlog", "To Start", "In Progress", "Blocked", "Review"}
    done_status = "Done"

    # Semaines glissantes
    def week_stats(days_start: int, days_end: int) -> dict:
        created = sum(1 for t in tasks if _in_window(t.get("created"), days_start, days_end))
        done    = sum(1 for t in tasks if t.get("status") == done_status and _in_window(t.get("updated"), days_start, days_end))
        commits = sum(1 for c in recent_commits if _in_window(c.get("date") + "T00:00:00+00:00", days_start, days_end))
        return {"created": created, "done": done, "commits": commits}

    # Projets actifs
    active_tasks = [t for t in tasks if t.get("status") in active_statuses]
    proj_names = sorted(set(t.get("project", "") for t in active_tasks if t.get("project")))

    projects = []
    for name in proj_names:
        proj_tasks = [t for t in active_tasks if t.get("project") == name]
        assignees = [t.get("assignee", "") for t in proj_tasks if t.get("assignee")]
        if assignees:
            count = Counter(assignees)
            max_count = max(count.values())
            majority = sorted(k for k, v in count.items() if v == max_count)[0]  # alphabetical tiebreak
        else:
            majority = ""
        projects.append({
            "name": name,
            "active_count": len(proj_tasks),
            "remaining_effort_hours": sum(t.get("effort_hours") or 0 for t in proj_tasks),
            "majority_assignee": majority,
        })

    return {
        "weeks": {
            "this_week": week_stats(0, 7),
            "last_week": week_stats(7, 14),
        },
        "projects": projects,
        "recent_commits": recent_commits[:5],
        "pending_review": pending_review,
    }


def parse_git_log(raw: str, repo: str) -> list[dict]:
    """Parse `git log --format='%as|%s|%an'` output."""
    commits = []
    for line in raw.strip().splitlines():
        parts = line.split("|", 3)
        if len(parts) >= 3:
            date, message, author = parts[0], parts[1], parts[2]
            commits.append({
                "date": date,
                "repo": repo,
                "message": message[:50],
                "author": author,
            })
    return commits


async def _git_log_async(repo_path: Path) -> list[dict]:
    """Run git log in subprocess with 3s timeout. Returns [] on error."""
    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                "git", "-C", str(repo_path), "log",
                "--since=14 days ago", "--format=%as|%s|%an",
                "--no-merges", "-20",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            ),
            timeout=3.0,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3.0)
        return parse_git_log(stdout.decode("utf-8", errors="replace"), repo=repo_path.name)
    except (asyncio.TimeoutError, FileNotFoundError, OSError) as e:
        logger.warning("git log failed for %s: %s", repo_path, e)
        return []


async def get_weekly_stats_data(tasks: list[dict], lab_repos_env: str) -> dict:
    """Async entry point: fetch git logs + compute stats."""
    # Parse LAB_REPOS
    repo_paths = []
    for p in (lab_repos_env or "").split(":"):
        p = p.strip()
        if p:
            path = Path(p)
            if path.exists() and (path / ".git").exists():
                repo_paths.append(path)
            else:
                logger.warning("LAB_REPOS path invalid or not a git repo: %s", p)

    # Fetch all git logs concurrently
    all_commits: list[dict] = []
    if repo_paths:
        results = await asyncio.gather(*(_git_log_async(p) for p in repo_paths))
        for commits in results:
            all_commits.extend(commits)
    all_commits.sort(key=lambda c: c.get("date", ""), reverse=True)

    # Pending review tasks
    now = datetime.now(timezone.utc)
    pending_review = []
    for t in tasks:
        if t.get("status") in ("Review", "Blocked"):
            updated = _parse_iso(t.get("updated"))
            days_waiting = (now - updated).days if updated else 0
            pending_review.append({
                "id": t["id"],
                "title": t.get("title", ""),
                "status": t.get("status"),
                "project": t.get("project", ""),
                "updated": t.get("updated", ""),
                "days_waiting": days_waiting,
            })
    pending_review.sort(key=lambda x: x["days_waiting"], reverse=True)

    return compute_weekly_stats(tasks, all_commits, pending_review)
```

- [ ] **Step 4 : Lancer les tests — vérifier qu'ils passent**

```bash
cd /home/lgiron/Lab/dombot-labos/core-tools/kanban
uv run pytest tests/test_weekly_stats.py -v
```
Attendu : 5 tests PASS

- [ ] **Step 5 : Ajouter l'endpoint dans `api.py`**

Dans `core-tools/kanban/kanban_api/api.py`, ajouter l'import et l'endpoint :

```python
import os
from .weekly_stats import get_weekly_stats_data

@router.get("/stats/weekly")
async def get_weekly_stats():
    data = list_active_tasks()
    tasks = data["tasks"]
    lab_repos = os.environ.get("LAB_REPOS", "")
    return await get_weekly_stats_data(tasks, lab_repos)
```

- [ ] **Step 6 : Remplacer `renderMeta()` + `renderPilotView()` dans `index.html`**

Dans `hub/public/kanban/index.html` :

**a) CSS — remplacer le bloc `.pm-meta-card` et ajouter les styles PilotView :**
```css
.pilotview-card {
  margin-bottom: 1rem;
  padding: 0.9rem 1.1rem;
  border-radius: 12px;
  background:
    radial-gradient(circle at top left, rgba(99,102,241,0.32), transparent 60%),
    radial-gradient(circle at bottom right, rgba(6,182,212,0.24), transparent 60%),
    var(--surface);
  border: 1px solid rgba(148,163,184,0.45);
  box-shadow: 0 18px 45px rgba(15,23,42,0.65);
}
.pilotview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; }
.pilotview-title { font-size: 0.92rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: #e5e7eb; }
.pilotview-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
@media (max-width: 900px) { .pilotview-grid { grid-template-columns: 1fr; } }
.pilotview-block { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 0.6rem 0.8rem; }
.pilotview-block summary { font-size: 0.78rem; font-weight: 600; cursor: pointer; color: var(--muted); letter-spacing: 0.04em; text-transform: uppercase; }
.pilotview-block summary:hover { color: var(--text); }
.pilotview-week-table { width: 100%; font-size: 0.75rem; border-collapse: collapse; margin-top: 0.4rem; }
.pilotview-week-table th { color: var(--muted); font-weight: 500; text-align: left; padding: 0.15rem 0.4rem; }
.pilotview-week-table td { padding: 0.15rem 0.4rem; font-weight: 600; }
.trend-up { color: var(--green); }
.trend-down { color: var(--red); }
.trend-eq { color: var(--muted); }
.pilotview-project-row { display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; padding: 0.2rem 0; border-bottom: 1px solid var(--border); }
.pilotview-project-row:last-child { border-bottom: none; }
.commit-table { width: 100%; font-size: 0.72rem; border-collapse: collapse; margin-top: 0.4rem; }
.commit-table td { padding: 0.15rem 0.4rem; vertical-align: top; }
.commit-table tr:hover { background: rgba(255,255,255,0.02); }
.badge-waiting { background: rgba(239,68,68,0.2); color: var(--red); font-size: 0.6rem; padding: 0.1rem 0.35rem; border-radius: 3px; }
.pilotview-footer { font-size: 0.65rem; color: var(--muted); margin-top: 0.4rem; text-align: right; }
```

**b) HTML — remplacer `<div class="project-summary pm-meta-card" id="pm-meta" ...>` par :**
```html
<div class="pilotview-card" id="pilot-view" style="display:none"></div>
```

**c) JS — remplacer la fonction `renderMeta()` par `renderPilotView()` et mettre à jour les appels :**

```js
let pilotData = null;
let pilotFetchedAt = null;

async function fetchPilotView() {
  try {
    pilotData = await api('/stats/weekly');
    pilotFetchedAt = new Date();
    renderPilotView();
  } catch(e) { console.warn('PilotView fetch failed:', e); }
}

function renderPilotView() {
  const box = document.getElementById('pilot-view');
  if (!box || !pilotData) return;
  const d = pilotData;
  const tw = d.weeks.this_week, lw = d.weeks.last_week;

  function trend(a, b) {
    if (a > b) return `<span class="trend-up">↑</span>`;
    if (a < b) return `<span class="trend-down">↓</span>`;
    return `<span class="trend-eq">=</span>`;
  }

  const weekTable = `
    <table class="pilotview-week-table">
      <tr><th></th><th>S. passée</th><th>Cette semaine</th><th></th></tr>
      <tr><td>Tasks créées</td><td>${lw.created}</td><td>${tw.created}</td><td>${trend(tw.created, lw.created)}</td></tr>
      <tr><td>Tasks Done</td><td>${lw.done}</td><td>${tw.done}</td><td>${trend(tw.done, lw.done)}</td></tr>
      <tr><td>Commits</td><td>${lw.commits}</td><td>${tw.commits}</td><td>${trend(tw.commits, lw.commits)}</td></tr>
    </table>`;

  const projectsHtml = d.projects.length
    ? d.projects.map(p => `
        <div class="pilotview-project-row">
          <span><strong>${esc(p.name)}</strong></span>
          <span>${p.active_count} tâche(s) · ${p.remaining_effort_hours.toFixed(1)}h · <span class="dombot-badge">${esc(p.majority_assignee)}</span></span>
        </div>`).join('')
    : '<div style="color:var(--muted);font-size:0.75rem">Aucun projet actif</div>';

  const commitsHtml = d.recent_commits.length
    ? `<table class="commit-table">${d.recent_commits.map(c =>
        `<tr><td style="color:var(--muted)">${c.date}</td><td><span class="badge badge-project">${esc(c.repo)}</span></td><td>${esc(c.message)}</td><td style="color:var(--muted)">${esc(c.author)}</td></tr>`
      ).join('')}</table>`
    : '<div style="color:var(--muted);font-size:0.75rem">Aucun commit (configurer LAB_REPOS)</div>';

  const pendingHtml = d.pending_review.length
    ? d.pending_review.map(t => `
        <div class="pilotview-project-row" style="cursor:pointer" onclick="openDetailById('${t.id}')">
          <span>${esc(t.title)}</span>
          <span>${t.days_waiting > 3 ? `<span class="badge-waiting">${t.days_waiting}j</span>` : `${t.days_waiting}j`} · <span class="badge badge-project">${esc(t.project)}</span></span>
        </div>`).join('')
    : '<div style="color:var(--muted);font-size:0.75rem">Rien en attente ✓</div>';

  const fetchedAt = pilotFetchedAt ? pilotFetchedAt.toLocaleTimeString('fr-FR', {hour:'2-digit',minute:'2-digit'}) : '—';

  box.innerHTML = `
    <div class="pilotview-header">
      <div class="pilotview-title">🎛 ClawPilot</div>
      <button onclick="fetchPilotView()" style="font-size:0.7rem;padding:0.2rem 0.65rem">⟳ Refresh</button>
    </div>
    <div class="pilotview-grid">
      <details class="pilotview-block" open>
        <summary>Activité hebdomadaire</summary>${weekTable}
      </details>
      <details class="pilotview-block" open>
        <summary>Projets en cours (${d.projects.length})</summary>
        <div style="margin-top:0.4rem">${projectsHtml}</div>
      </details>
      <details class="pilotview-block" open>
        <summary>Derniers commits</summary>${commitsHtml}
      </details>
      <details class="pilotview-block" open>
        <summary>En attente de validation (${d.pending_review.length})</summary>
        <div style="margin-top:0.4rem">${pendingHtml}</div>
      </details>
    </div>
    <div class="pilotview-footer">Actualisé à ${fetchedAt}</div>`;
  box.style.display = 'block';
}
```

**d) Dans la fonction `load()`, remplacer l'appel `renderMeta()` :**
```js
// Remplacer: renderMeta();
// Par: (rien — PilotView se charge séparément)
```

**e) Dans l'initialisation (bas du script), ajouter :**
```js
// Init PilotView
fetchPilotView();
```

**f) Dans le SSE `onmessage`, remplacer `renderMeta()` par rien** (PilotView ne suit pas le SSE).

- [ ] **Step 7 : Lancer tous les tests**

```bash
cd /home/lgiron/Lab/dombot-labos/core-tools/kanban
uv run pytest tests/ -v
```
Attendu : tous les tests passent.

- [ ] **Step 8 : Tester manuellement**

Ouvrir `https://lab.dombot.tech/kanban/`. Vérifier le bloc ClawPilot avec les 4 sections.
Configurer `LAB_REPOS=/home/lgiron/Lab/hub:/home/lgiron/Lab/dombot-labos` dans `.env` pour voir les commits.

- [ ] **Step 9 : Commit**

```bash
cd /home/lgiron/Lab/dombot-labos
git add core-tools/kanban/kanban_api/weekly_stats.py core-tools/kanban/kanban_api/api.py hub/public/kanban/index.html core-tools/kanban/tests/test_weekly_stats.py
git commit -m "feat: add PilotView dashboard (weekly stats API + frontend)"
```

---

## Task 6 : Kanban-implementer — clarification avant implémentation

**Prérequis :** Task 1 (status Blocked doit exister dans l'API). **Débloque :** rien.

**Files:**
- Modify: `~/.openclaw/skills/kanban-implementer/core/kanban_implementer/selector.py`
- Modify: `~/.openclaw/skills/kanban-implementer/core/kanban_implementer/__main__.py`
- Modify: `~/.openclaw/skills/kanban-implementer/SKILL.md`
- Modify: `~/.openclaw/skills/kanban-implementer/core/tests/test_selector.py`

- [ ] **Step 1 : Écrire les tests qui échouent**

Dans `~/.openclaw/skills/kanban-implementer/core/tests/test_selector.py`, ajouter à la fin :

```python
def make_task_ambig(**kw) -> Task:
    defaults = dict(
        id="task-x", title="Améliorer le kanban", project="hub",
        status="To Start", priority="Medium", effort_hours=1.0,
        assignee="DomBot", source_file="", description="", notes="", confidence=None,
    )
    return Task(**{**defaults, **kw})


class TestIsAmbiguous:
    def test_low_confidence_is_ambiguous(self):
        t = make_task_ambig(confidence=0.42)
        assert t.is_ambiguous is True

    def test_high_confidence_is_not_ambiguous(self):
        t = make_task_ambig(confidence=0.7, description="Implement X by doing Y and Z with tests")
        assert t.is_ambiguous is False

    def test_short_description_is_ambiguous(self):
        t = make_task_ambig(confidence=0.8, description="fix bug")
        assert t.is_ambiguous is True

    def test_vague_title_no_description_is_ambiguous(self):
        t = make_task_ambig(title="fix", confidence=0.8, description="")
        assert t.is_ambiguous is True

    def test_clear_title_long_description_not_ambiguous(self):
        t = make_task_ambig(
            title="Add SSE endpoint for kanban stream",
            confidence=0.8,
            description="Create GET /stream endpoint in sse.py using asyncio. Must send JSON diffs every 5s.",
        )
        assert t.is_ambiguous is False

    def test_null_confidence_default_05_not_ambiguous_if_clear(self):
        # confidence=None → 0.5, between 0.4 and 0.55 → ambiguous
        t = make_task_ambig(confidence=None, description="A clear long enough description for the task")
        assert t.is_ambiguous is True  # 0.5 < 0.55

    def test_human_assignee_never_ambiguous(self):
        t = make_task_ambig(assignee="ldom1", confidence=None, description="fix")
        assert t.is_ambiguous is False  # humain → confiance 1.0, pas de filtre ambiguïté
```

- [ ] **Step 2 : Lancer les tests — vérifier qu'ils échouent**

```bash
cd /home/lgiron/.openclaw/skills/kanban-implementer/core
uv run pytest tests/test_selector.py::TestIsAmbiguous -v
```
Attendu : FAIL (`Task has no attribute 'is_ambiguous'`)

- [ ] **Step 3 : Ajouter `is_ambiguous` dans `selector.py`**

Dans la classe `Task`, après la propriété `is_eligible` :

```python
_VAGUE_WORDS = frozenset(["améliorer", "fix", "update", "check", "refactor"])

@property
def is_ambiguous(self) -> bool:
    """True si la tâche nécessite une clarification avant implémentation."""
    # Les humains ne sont jamais bloqués
    if self.assignee not in AGENT_ASSIGNEES:
        return False
    # Confidence dans la zone grise 0.4–0.55
    if 0.4 <= self.confidence_effective < 0.55:
        return True
    # Description absente ou trop courte
    if len((self.description or "").strip()) < 50:
        return True
    # Titre uniquement des mots vagues (sans complément)
    title_words = set(self.title.lower().split())
    if title_words and title_words.issubset(_VAGUE_WORDS):
        return True
    return False
```

- [ ] **Step 4 : Lancer les tests — vérifier qu'ils passent**

```bash
cd /home/lgiron/.openclaw/skills/kanban-implementer/core
uv run pytest tests/test_selector.py -v
```
Attendu : tous les tests passent (8 anciens + 7 nouveaux = 15 PASS)

- [ ] **Step 5 : Modifier `__main__.py`**

Dans `main_select()`, après `print(format_task_context(task))`, ajouter l'étape 1bis :

```python
def main_select() -> None:
    # ... code existant jusqu'à task = select_task(...)
    if task is None:
        # ... code existant
        return

    print(format_task_context(task))
    print(f"\n---\nPROJET_PRIORITAIRE={project or PRIORITY_PROJECT or '(none)'}")
    print(f"TASK_ID={task.id}")

    # ── Étape 1bis : Évaluation d'ambiguïté ──────────────────────────
    if task.is_ambiguous:
        print("\n⚠️  TÂCHE AMBIGUË — clarification requise avant implémentation.")
        print("   Actions à effectuer AVANT de coder :")
        print("   1. Écrire dans notes de la tâche :")
        print("      [DomBot Plan <date>]")
        print("      Interprétation : <ce que tu comprends>")
        print("      Approche : <ce que tu vas faire>")
        print("      Question : <ce qui manque pour implémenter>")
        print(f"   2. Passer la tâche en 'Blocked' : kanban-implementer update {task.id} Blocked")
        print("   3. Envoyer notification Telegram.")
        print("   4. Ne pas implémenter. Attendre que Ldom repasse en 'To Start'.")
        print("\nIS_AMBIGUOUS=true")
    else:
        print("\nIS_AMBIGUOUS=false")
        print("✅ Tâche claire — tu peux implémenter.")
```

Note : les appels Telegram et mise à jour des notes sont faits par DomBot manuellement après avoir lu ce output. Le script indique clairement la procédure.

- [ ] **Step 6 : Mettre à jour `SKILL.md`**

Dans `~/.openclaw/skills/kanban-implementer/SKILL.md` :

**a) Après "### Étape 1 — Sélection", ajouter "### Étape 1bis — Évaluation d'ambiguïté" :**

```markdown
### Étape 1bis — Évaluation d'ambiguïté (NOUVELLE)

Immédiatement après `select`, lire le output :

- Si `IS_AMBIGUOUS=false` → continuer à l'Étape 2 normalement.
- Si `IS_AMBIGUOUS=true` → **STOP** avant toute implémentation :

  1. Mettre à jour les `notes` de la tâche via l'API :
     ```bash
     curl -s -X PUT http://localhost:8090/tasks/TASK_ID \
       -H 'Content-Type: application/json' \
       -d '{"notes": "[DomBot Plan $(date +%Y-%m-%d)]\nInterprétation : <ton interprétation>\nApproche : <ce que tu vas faire>\nQuestion : <ce qui manque>"}'
     ```
  2. Passer en "Blocked" :
     ```bash
     uv run --directory ~/.openclaw/skills/kanban-implementer/core python -m kanban_implementer update TASK_ID "Blocked"
     ```
  3. Envoyer notification Telegram :
     ```bash
     openclaw message send --channel telegram --target 5689694685 \
       --message "⛔ [TASK_ID] Tâche bloquée — besoin validation avant impl. Voir kanban."
     ```
  4. **Arrêter la session.** Ldom reviews dans le kanban, corrige la description, repasse en "To Start".
```

**b) Remplacer** la règle commençant par `- **Tâches ambiguës** :` (dans la section "Règles de prudence") par :

```markdown
- **Tâches ambiguës** : géré automatiquement par l'étape 1bis — voir ci-dessus. Ne pas créer d'issue GitHub.
```

- [ ] **Step 7 : Lancer la suite complète de tests**

```bash
cd /home/lgiron/.openclaw/skills/kanban-implementer/core
uv run pytest tests/ -v
```
Attendu : tous les tests passent.

- [ ] **Step 8 : Commit**

```bash
cd /home/lgiron/.openclaw/skills/kanban-implementer
git add core/kanban_implementer/selector.py core/kanban_implementer/__main__.py SKILL.md core/tests/test_selector.py
git commit -m "feat: kanban-implementer evaluates task ambiguity before implementing (is_ambiguous, Blocked flow)"
```

Note : si le skill est dans un repo séparé, adapter le chemin git. Sinon, committer dans dombot-labos :
```bash
cd /home/lgiron/Lab/dombot-labos
git add -p  # sélectionner les fichiers du skill si inclus dans ce repo
```

---

## Vérification finale

- [ ] **Lancer tous les tests kanban API**

```bash
cd /home/lgiron/Lab/dombot-labos/core-tools/kanban
uv run pytest tests/ -v
```
Attendu : tous les tests passent.

- [ ] **Lancer tous les tests kanban-implementer**

```bash
cd /home/lgiron/.openclaw/skills/kanban-implementer/core
uv run pytest tests/ -v
```
Attendu : tous les tests passent.

- [ ] **Vérification UI manuelle**

Ouvrir `https://lab.dombot.tech/kanban/` et vérifier :
- Colonne "Blocked" visible (violet, ⛔)
- Titre page = "LabOS — Kanban" (ou ClawPilot si renommé)
- Vue Gantt : barres proportionnelles
- Vue Graph : DAG par projet avec D3
- Section ClawPilot : 4 blocs visibles

- [ ] **Commit final si nécessaire**

```bash
cd /home/lgiron/Lab/dombot-labos
git add .
git commit -m "chore: final cleanup ClawPilot kanban improvements"
```
