type LineClass = 'ts' | 'agent' | 'action-exec' | 'action-verify' | 'action-skip' | 'msg';
interface TerminalLine { text: string; cls: LineClass }

const LINES: TerminalLine[] = [
  { text: '[08:00:01] DomBot morning briefing started',                       cls: 'ts' },
  { text: '[08:00:03] claude-code EXECUTE confidence=0.94 "Briefing ready"', cls: 'action-exec' },
  { text: '[08:00:05] kanban 3 tasks moved to In Progress',                   cls: 'msg' },
  { text: '[08:00:08] openclaw EXECUTE confidence=0.85 "Token audit running..."', cls: 'action-exec' },
  { text: '[08:00:11] dombot VERIFY confidence=0.72 "Review suggested"',      cls: 'action-verify' },
  { text: '[08:00:14] claude-code EXECUTE confidence=0.91 "Optimization applied"', cls: 'action-exec' },
  { text: '[08:00:17] kanban 1 task moved to Done',                           cls: 'msg' },
  { text: '[08:00:20] dombot SKIP confidence=0.28 "Manual review required"',  cls: 'action-skip' },
  { text: '[08:00:23] gemini EXECUTE confidence=0.88 "Report generated"',     cls: 'action-exec' },
  { text: '[08:00:26] DomBot cycle complete. Next run in 30s',                cls: 'agent' },
];

const CHAR_DELAY  = 80;
const LINE_PAUSE  = 1500;
const CYCLE_PAUSE = 2000;
const MAX_VISIBLE = 8;

export function initTerminal(): void {
  const container = document.getElementById('hero-terminal');
  if (!container) return;

  let lineIndex = 0;
  let charIndex = 0;
  let currentSpan: HTMLSpanElement | null = null;
  let cursor: HTMLSpanElement | null = null;
  let rafId = 0;
  let lastCharTime = 0;
  let pauseUntil = 0;

  function getCursor(): HTMLSpanElement {
    if (!cursor) { cursor = document.createElement('span'); cursor.className = 'terminal-cursor'; cursor.textContent = '▋'; }
    return cursor;
  }

  function startLine(): void {
    const def = LINES[lineIndex];
    currentSpan = document.createElement('span');
    currentSpan.className = `terminal-line ${def.cls}`;
    container!.appendChild(currentSpan);
    currentSpan.appendChild(getCursor());
    charIndex = 0;
    const all = container!.querySelectorAll('.terminal-line');
    if (all.length > MAX_VISIBLE) all[0].remove();
  }

  function reset(): void {
    container!.innerHTML = '';
    currentSpan = null;
    cursor = null;
    lastCharTime = 0;
    lineIndex = 0;
    startLine();
    rafId = requestAnimationFrame(tick);
  }

  function tick(now: number): void {
    if (now < pauseUntil) { rafId = requestAnimationFrame(tick); return; }
    if (now - lastCharTime < CHAR_DELAY) { rafId = requestAnimationFrame(tick); return; }
    lastCharTime = now;

    const text = LINES[lineIndex].text;
    if (charIndex < text.length) {
      currentSpan!.insertBefore(document.createTextNode(text[charIndex++]), getCursor());
      rafId = requestAnimationFrame(tick);
    } else {
      getCursor().remove();
      lineIndex++;
      if (lineIndex < LINES.length) {
        pauseUntil = now + LINE_PAUSE;
        startLine();
        rafId = requestAnimationFrame(tick);
      } else {
        setTimeout(reset, CYCLE_PAUSE);
      }
    }
  }

  startLine();
  rafId = requestAnimationFrame(tick);
  (container as HTMLElement & { _termCleanup?: () => void })._termCleanup = () => cancelAnimationFrame(rafId);
}
