type AgentKey = 'openclaw' | 'claude' | 'gemini';

const AGENTS: AgentKey[] = ['openclaw', 'claude', 'gemini'];

const LABELS: Record<AgentKey, string> = {
  openclaw: '→ Selected: OpenClaw  ·  cost: free  ·  quality: 85%  ·  local model',
  claude:   '→ Selected: Claude Code  ·  cost: $0.01  ·  quality: 95%  ·  best accuracy',
  gemini:   '→ Selected: Gemini  ·  cost: cheap  ·  quality: 80%  ·  fast response',
};

function getEl<T extends Element>(id: string): T | null {
  return document.getElementById(id) as T | null;
}

function animateArrow(path: SVGPathElement): void {
  path.style.strokeDasharray = '200';
  path.style.strokeDashoffset = '200';
  path.classList.add('active');

  let start: number | null = null;
  const duration = 500;

  function step(ts: number): void {
    if (start === null) start = ts;
    const elapsed = ts - start;
    const progress = Math.min(elapsed / duration, 1);
    path.style.strokeDashoffset = String(200 * (1 - progress));
    if (progress < 1) requestAnimationFrame(step);
  }

  requestAnimationFrame(step);
}

function activate(agent: AgentKey): void {
  for (const key of AGENTS) {
    const node = getEl<SVGGElement>(`node-${key}`);
    const arrow = getEl<SVGPathElement>(`arrow-${key}`);
    if (node)  node.classList.toggle('active', key === agent);
    if (arrow) arrow.classList.remove('active');
  }

  const arrow = getEl<SVGPathElement>(`arrow-${agent}`);
  if (arrow) animateArrow(arrow);

  const label = getEl<SVGTextElement>('routing-label');
  if (label) label.textContent = LABELS[agent];
}

export function initRouting(): void {
  let index = 0;
  activate(AGENTS[index]);

  setInterval(() => {
    index = (index + 1) % AGENTS.length;
    activate(AGENTS[index]);
  }, 3000);
}
