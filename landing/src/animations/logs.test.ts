import { describe, it, expect } from 'vitest';
import { initLogs } from './logs';

describe('initLogs', () => {
  it('est une fonction exportée', () => {
    expect(typeof initLogs).toBe('function');
  });

  it('ne throw pas si les éléments DOM sont absents', () => {
    expect(() => initLogs()).not.toThrow();
  });

  it('ne throw pas si certains éléments sont présents mais pas tous', () => {
    document.body.innerHTML = '<table><tbody id="logs-tbody"></tbody></table>';
    expect(() => initLogs()).not.toThrow();
    document.body.innerHTML = '';
  });
});
