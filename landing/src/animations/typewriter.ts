const PHRASES = [
  'AI Agent Lab',
  'Multi-Agent Orchestration',
  'Autonomous Workflows',
  'Open Source Infrastructure',
] as const;

const TIMING = {
  type: 80,
  pause: 2500,
  erase: 40,
  pauseBeforeNext: 500,
} as const;

export function initTypewriter(): void {
  const el = document.getElementById('typewriter');
  if (!el) return;

  let phraseIndex = 0;
  let charIndex = 0;
  let isErasing = false;

  function tick(): void {
    const phrase = PHRASES[phraseIndex];

    if (!isErasing) {
      charIndex++;
      el!.textContent = phrase.slice(0, charIndex);

      if (charIndex === phrase.length) {
        isErasing = true;
        setTimeout(tick, TIMING.pause);
        return;
      }

      setTimeout(tick, TIMING.type);
    } else {
      charIndex--;
      el!.textContent = phrase.slice(0, charIndex);

      if (charIndex === 0) {
        isErasing = false;
        phraseIndex = (phraseIndex + 1) % PHRASES.length;
        setTimeout(tick, TIMING.pauseBeforeNext);
        return;
      }

      setTimeout(tick, TIMING.erase);
    }
  }

  setTimeout(tick, TIMING.type);
}
