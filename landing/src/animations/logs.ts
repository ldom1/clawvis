type LogAction = 'EXECUTE' | 'VERIFY' | 'SKIP';

interface LogEntry {
  agent: string;
  action: LogAction;
  confidence: number;
  message: string;
}

const LOG_POOL: LogEntry[] = [
  { agent: 'openclaw',    action: 'EXECUTE', confidence: 0.94, message: 'Running morning briefing...' },
  { agent: 'claude-code', action: 'EXECUTE', confidence: 0.91, message: 'Briefing ready' },
  { agent: 'dombot',      action: 'VERIFY',  confidence: 0.72, message: 'Review suggested' },
  { agent: 'gemini',      action: 'EXECUTE', confidence: 0.88, message: 'Token audit complete' },
  { agent: 'openclaw',    action: 'SKIP',    confidence: 0.31, message: 'Low priority task deferred' },
  { agent: 'claude-code', action: 'VERIFY',  confidence: 0.65, message: 'Checking output format' },
  { agent: 'dombot',      action: 'EXECUTE', confidence: 0.97, message: 'Cron job dispatched' },
  { agent: 'gemini',      action: 'SKIP',    confidence: 0.25, message: 'Context window too small' },
  { agent: 'openclaw',    action: 'EXECUTE', confidence: 0.83, message: 'Memory vault updated' },
  { agent: 'claude-code', action: 'EXECUTE', confidence: 0.90, message: 'PR diff analyzed' },
  { agent: 'dombot',      action: 'VERIFY',  confidence: 0.58, message: 'Anomaly detected, pausing' },
  { agent: 'gemini',      action: 'EXECUTE', confidence: 0.85, message: 'Embeddings refreshed' },
  { agent: 'openclaw',    action: 'SKIP',    confidence: 0.42, message: 'Duplicate task skipped' },
  { agent: 'claude-code', action: 'VERIFY',  confidence: 0.70, message: 'Tool output validated' },
  { agent: 'dombot',      action: 'EXECUTE', confidence: 0.93, message: 'Daily report generated' },
  { agent: 'gemini',      action: 'VERIFY',  confidence: 0.61, message: 'Latency threshold exceeded' },
  { agent: 'openclaw',    action: 'EXECUTE', confidence: 0.87, message: 'Skill index rebuilt' },
];

const MAX_ROWS = 12;
const INTERVAL_MS = 1500;

let poolIndex = 0;
let counts = { high: 0, med: 0, low: 0 };

function getTimestamp(): string {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  return `[${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}]`;
}

function actionClass(action: LogAction): string {
  if (action === 'EXECUTE') return 'log-action-exec';
  if (action === 'VERIFY')  return 'log-action-verify';
  return 'log-action-skip';
}

function confClass(conf: number): string {
  if (conf >= 0.8) return 'conf-high';
  if (conf >= 0.5) return 'conf-med';
  return 'conf-low';
}

function updateCounters(
  elHigh: HTMLElement,
  elMed: HTMLElement,
  elLow: HTMLElement,
): void {
  elHigh.textContent = String(counts.high);
  elMed.textContent  = String(counts.med);
  elLow.textContent  = String(counts.low);
}

function addRow(
  tbody: HTMLElement,
  elHigh: HTMLElement,
  elMed: HTMLElement,
  elLow: HTMLElement,
): void {
  const entry = LOG_POOL[poolIndex % LOG_POOL.length];
  poolIndex++;

  // Update counters
  if (entry.action === 'EXECUTE' && entry.confidence > 0.8) {
    counts.high++;
  } else if (entry.action === 'VERIFY') {
    counts.med++;
  } else {
    counts.low++;
  }

  const tr = document.createElement('tr');
  tr.className = 'log-new';

  const confVal = entry.confidence.toFixed(2);

  tr.innerHTML =
    `<td class="log-ts">${getTimestamp()}</td>` +
    `<td class="log-agent">${entry.agent}</td>` +
    `<td class="${actionClass(entry.action)}">${entry.action}</td>` +
    `<td><span class="log-conf ${confClass(entry.confidence)}">${confVal}</span></td>` +
    `<td class="log-msg">"${entry.message}"</td>`;

  tbody.appendChild(tr);

  // Remove oldest row beyond MAX_ROWS
  const tBody = tbody as HTMLTableSectionElement;
  while (tBody.rows.length > MAX_ROWS) {
    tBody.deleteRow(0);
  }

  // Scroll to bottom
  const table = tbody.closest('table') ?? tbody.parentElement;
  const scrollTarget = table?.parentElement ?? tbody;
  scrollTarget.scrollTop = scrollTarget.scrollHeight;

  updateCounters(elHigh, elMed, elLow);
}

export function initLogs(): void {
  const tbody   = document.getElementById('logs-tbody');
  const elHigh  = document.getElementById('log-count-high');
  const elMed   = document.getElementById('log-count-med');
  const elLow   = document.getElementById('log-count-low');

  if (!tbody || !elHigh || !elMed || !elLow) return;

  setInterval(() => addRow(tbody, elHigh, elMed, elLow), INTERVAL_MS);
}
