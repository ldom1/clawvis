import { describe, it, expect } from 'vitest';
import { initRouting } from './routing';

describe('initRouting', () => {
  it('est une fonction exportée', () => {
    expect(typeof initRouting).toBe('function');
  });

  it('ne throw pas si les éléments SVG sont absents', () => {
    expect(() => initRouting()).not.toThrow();
  });
});
