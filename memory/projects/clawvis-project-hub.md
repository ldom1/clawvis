# Clawvis Project Hub

## Goal

Créer un vrai hub de projet dans la home Clawvis:
- création rapide avec `+`
- mémoire projet centralisée
- tâches Kanban filtrées automatiquement

## MVP Scope

1. Grid projet sur la main page.
2. Flow de création basé sur description.
3. Auto bootstrap repo + mémoire.
4. Vue projet intégrée (lien + mémoire + tâches filtrées).
5. Settings pour définir chemins `projects` et `poc`.

## API

- `GET /api/kanban/hub/settings`
- `PUT /api/kanban/hub/settings`
- `GET /api/kanban/hub/projects?kind=project|poc`
- `POST /api/kanban/hub/projects`
- `GET /api/kanban/hub/projects/{slug}`

## Template bootstrap

- `python`: `pyproject.toml`, `main.py`, `README.md`
- `vite`: `package.json`, `src/main.js`, `README.md`
- `empty`: `README.md`

## Notes

- Le slug projet est dérivé du nom/description.
- La mémoire est stockée dans `memory/projects/<slug>.md`.
- Les tâches Kanban sont récupérées via `GET /api/kanban/tasks?project=<slug>`.
