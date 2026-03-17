import { describe, it, expect, vi, afterEach } from 'vitest';
import { initTypewriter } from './typewriter';

describe('initTypewriter', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    document.body.innerHTML = '';
  });

  it('is an exported function', () => {
    expect(typeof initTypewriter).toBe('function');
  });

  it('does not throw when #typewriter element is absent', () => {
    document.body.innerHTML = '';
    expect(() => initTypewriter()).not.toThrow();
  });

  it('starts typing when #typewriter element is present', () => {
    vi.useFakeTimers();
    document.body.innerHTML = '<span id="typewriter">AI Agent Lab</span>';
    const el = document.getElementById('typewriter')!;

    initTypewriter();
    vi.advanceTimersByTime(80);

    expect(el.textContent).toBe('A');
    vi.useRealTimers();
  });
});
