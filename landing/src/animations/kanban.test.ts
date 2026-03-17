import { describe, it, expect, beforeEach, vi } from 'vitest';
import { initKanban } from './kanban';

function setupDOM(): void {
  document.body.innerHTML = `
    <div id="kanban-board">
      <div id="col-backlog">
        <span id="col-count-backlog">0</span>
      </div>
      <div id="col-progress">
        <span id="col-count-progress">0</span>
      </div>
      <div id="col-review">
        <span id="col-count-review">0</span>
      </div>
      <div id="col-done">
        <span id="col-count-done">0</span>
      </div>
    </div>
  `;
}

describe('initKanban', () => {
  beforeEach(() => {
    setupDOM();
    vi.useFakeTimers();
  });

  it('is an exported function', () => {
    expect(typeof initKanban).toBe('function');
  });

  it('does not throw when all columns exist', () => {
    expect(() => initKanban()).not.toThrow();
  });

  it('renders 4 cards across the board', () => {
    initKanban();
    const cards = document.querySelectorAll('.kanban-card');
    expect(cards.length).toBe(4);
  });

  it('places initial tasks in the correct columns', () => {
    initKanban();
    expect(document.querySelector('#col-backlog .kanban-card-title')?.textContent).toBe('Analyze morning report');
    expect(document.querySelector('#col-progress .kanban-card-title')?.textContent).toBe('Generate briefing');
    expect(document.querySelector('#col-review .kanban-card-title')?.textContent).toBe('Run token audit');
    expect(document.querySelector('#col-done .kanban-card-title')?.textContent).toBe('Update vault');
  });

  it('updates column counts correctly at init', () => {
    initKanban();
    expect(document.getElementById('col-count-backlog')?.textContent).toBe('1');
    expect(document.getElementById('col-count-progress')?.textContent).toBe('1');
    expect(document.getElementById('col-count-review')?.textContent).toBe('1');
    expect(document.getElementById('col-count-done')?.textContent).toBe('1');
  });

  it('moves task after 4s + animation delay', () => {
    initKanban();
    vi.advanceTimersByTime(4000 + 400);
    // After one cycle: task-1 moves from backlog → progress
    const progressCards = document.querySelectorAll('#col-progress .kanban-card');
    expect(progressCards.length).toBe(2);
    expect(document.getElementById('col-count-backlog')?.textContent).toBe('0');
    expect(document.getElementById('col-count-progress')?.textContent).toBe('2');
  });

  it('does not throw if kanban-board is absent', () => {
    document.body.innerHTML = '';
    expect(() => initKanban()).not.toThrow();
  });
});
