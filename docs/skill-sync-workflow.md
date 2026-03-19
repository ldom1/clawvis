# Skill Sync Workflow

## Architecture

```
.openclaw/skills/  ←→  hub/skills/  ←→  github.com/ldom1/hub
(runtime prod)          (canonical)       (collaboration)
```

## Hub repo = source canonique

Le repo `ldom1/hub` est la source de vérité pour les skills.
`.openclaw/skills/` est le runtime de production.

## Flux Push (.openclaw → hub)

Déclenché par `git-sync` (cron ou manuel) :
1. rsync `.openclaw/skills/<skill>/` → `hub/skills/<skill>/` (exclut secrets)
2. `git commit -m "skills: sync from .openclaw"` + `git push hub develop`

## Flux Pull (hub → .openclaw)

Déclenché avant le push par `git-sync` :
1. `git fetch && git merge --ff-only origin/develop`
2. rsync `hub/skills/<skill>/` → `.openclaw/skills/<skill>/`

## Contribuer

1. Fork `ldom1/hub`
2. Créer une branche `feature/<skill>-<change>`
3. Modifier `skills/<skill>/`
4. PR sur `develop`
5. Après merge, DomBot auto-pull via git-sync (cron quotidien)

## Règles de sécurité

- Ne JAMAIS committer : `.env`, `*.key`, `credentials/`, tokens
- OK : `SKILL.md`, `core/` (Python), `scripts/` (shell), `pyproject.toml`, `tests/`
- Le `.gitignore` dans `skills/` applique ces règles automatiquement
