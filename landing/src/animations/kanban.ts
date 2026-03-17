interface KanbanTask {
  id: string;
  title: string;
  confidence: number;
  priority: string;
  column: ColumnId;
}

type ColumnId = 'backlog' | 'progress' | 'review' | 'done';

const COLUMN_ORDER: ColumnId[] = ['backlog', 'progress', 'review', 'done'];

const TASKS: KanbanTask[] = [
  { id: 'task-1', title: 'Analyze morning report', confidence: 87, priority: 'High',     column: 'backlog'   },
  { id: 'task-2', title: 'Generate briefing',      confidence: 72, priority: 'Medium',   column: 'progress'  },
  { id: 'task-3', title: 'Run token audit',        confidence: 55, priority: 'High',     column: 'review'    },
  { id: 'task-4', title: 'Update vault',           confidence: 31, priority: 'Critical', column: 'done'      },
];

function confClass(confidence: number): string {
  if (confidence > 80) return 'conf-high';
  if (confidence >= 50) return 'conf-med';
  return 'conf-low';
}

function buildCard(task: KanbanTask): HTMLDivElement {
  const card = document.createElement('div');
  card.className = 'kanban-card';
  card.dataset['taskId'] = task.id;
  card.style.transition = 'all 0.4s ease';

  const title = document.createElement('div');
  title.className = 'kanban-card-title';
  title.textContent = task.title;

  const meta = document.createElement('div');
  meta.className = 'kanban-card-meta';

  const conf = document.createElement('span');
  conf.className = `confidence-badge ${confClass(task.confidence)}`;
  conf.textContent = `${task.confidence}%`;

  const prio = document.createElement('span');
  prio.className = `priority-badge priority-${task.priority}`;
  prio.textContent = task.priority;

  meta.appendChild(conf);
  meta.appendChild(prio);
  card.appendChild(title);
  card.appendChild(meta);

  return card;
}

function getColumnEl(id: ColumnId): HTMLElement | null {
  return document.getElementById(`col-${id}`);
}

function getCountEl(id: ColumnId): HTMLElement | null {
  return document.getElementById(`col-count-${id}`);
}

function updateCounts(tasks: KanbanTask[]): void {
  for (const colId of COLUMN_ORDER) {
    const el = getCountEl(colId);
    if (el) {
      el.textContent = String(tasks.filter(t => t.column === colId).length);
    }
  }
}

function renderAll(tasks: KanbanTask[]): void {
  for (const colId of COLUMN_ORDER) {
    const col = getColumnEl(colId);
    if (!col) continue;
    col.querySelectorAll<HTMLElement>('.kanban-card').forEach(c => c.remove());
    tasks
      .filter(t => t.column === colId)
      .forEach(t => col.appendChild(buildCard(t)));
  }
  updateCounts(tasks);
}

function nextColumn(colId: ColumnId): ColumnId {
  const idx = COLUMN_ORDER.indexOf(colId);
  return COLUMN_ORDER[(idx + 1) % COLUMN_ORDER.length];
}

export function initKanban(): void {
  const board = document.getElementById('kanban-board');
  if (!board) return;

  const tasks: KanbanTask[] = TASKS.map(t => ({ ...t }));
  renderAll(tasks);

  setInterval(() => {
    // Find the first task in the leftmost non-empty column
    for (const colId of COLUMN_ORDER) {
      const first = tasks.find(t => t.column === colId);
      if (first) {
        const col = getColumnEl(colId);
        const cardEl = col?.querySelector<HTMLElement>(`[data-task-id="${first.id}"]`);
        if (cardEl) {
          cardEl.style.opacity = '0';
          cardEl.style.transform = 'translateX(20px)';
        }
        setTimeout(() => {
          first.column = nextColumn(colId);
          renderAll(tasks);
        }, 400);
        break;
      }
    }
  }, 4000);
}
