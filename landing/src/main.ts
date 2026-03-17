import './style.css';
import { initTerminal } from './animations/terminal';
import { initKanban } from './animations/kanban';
import { initLogs } from './animations/logs';
import { initRouting } from './animations/routing';
import { initTypewriter } from './animations/typewriter';

// ── Tab switching (Demo section) ──────────────────────────────
function initDemoTabs(): void {
  const btns = document.querySelectorAll<HTMLButtonElement>('.tab-btn');
  const panels = document.querySelectorAll<HTMLElement>('.tab-panel');
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      btns.forEach(b => b.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const target = document.getElementById(`tab-${btn.dataset.tab}`);
      if (target) target.classList.add('active');
    });
  });
}

// ── Tab switching (How It Works section) ─────────────────────
function initHowTabs(): void {
  const btns = document.querySelectorAll<HTMLButtonElement>('.how-tab-btn');
  const panels = document.querySelectorAll<HTMLElement>('.how-panel');
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      btns.forEach(b => b.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const target = document.getElementById(`how-${btn.dataset.how}`);
      if (target) target.classList.add('active');
    });
  });
}

// ── Copy buttons (Get Started section) ───────────────────────
function initCopyBtns(): void {
  document.querySelectorAll<HTMLButtonElement>('.copy-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const text = btn.dataset.copy ?? '';
      navigator.clipboard.writeText(text).then(() => {
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
      }).catch(() => {/* silent fail */});
    });
  });
}

// ── Init ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initDemoTabs();
  initHowTabs();
  initCopyBtns();
  initTypewriter();
  initTerminal();
  initKanban();
  initLogs();
  initRouting();
});
