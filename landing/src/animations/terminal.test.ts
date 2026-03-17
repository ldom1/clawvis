import { describe, it, expect, vi } from 'vitest';
import { initTerminal } from './terminal';

describe('initTerminal', () => {
  it('est une fonction exportée', () => {
    expect(typeof initTerminal).toBe('function');
  });

  it('ne throw pas si #hero-terminal est absent du DOM', () => {
    // jsdom démarre sans l'élément — on s'assure qu'il n'existe pas
    document.getElementById('hero-terminal')?.remove();
    expect(() => initTerminal()).not.toThrow();
  });

  it('crée la première ligne de terminal si #hero-terminal existe', () => {
    vi.useFakeTimers();
    const container = document.createElement('div');
    container.id = 'hero-terminal';
    document.body.appendChild(container);

    expect(() => initTerminal()).not.toThrow();

    // Après initialisation, un span terminal-line doit être présent
    expect(container.querySelector('.terminal-line')).not.toBeNull();

    container.remove();
    vi.useRealTimers();
  });
});
