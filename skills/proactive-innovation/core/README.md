# Proactive Innovation (core)

Scan projets Second Brain + idées entrepreneur. **Un seul rapport par run, pas d’envoi de messages** dans le code (le script envoie une fois).

## Setup

```bash
cd core && uv sync
```

## Run

```bash
uv run python -m proactive_innovation
```

Sortie : une ligne de rapport sur stdout (≤280 car). Le script `../scripts/run-proactive-innovation.sh` capture cette sortie et envoie **un** message Telegram.

## Limites (anti-boucle)

- `MAX_PROJECTS_PER_RUN = 10`
- `MAX_IMPROVEMENTS_PER_PROJECT = 5`
- `MAX_IDEAS_PER_RUN = 3`
- Au plus 2 appels LLM par run (Phase 1 + Phase 3)
