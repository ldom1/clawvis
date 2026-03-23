# Clawvis Architecture Addendum

## Project Hub (MVP)

- Main page (`hub/public/index.html`) now includes a project grid with `+ Nouveau projet`.
- Create flow calls `POST /api/kanban/hub/projects` with description + template.
- Backend creates:
  - repo folder in configured path (`projects_root` or `pocs_root`)
  - memory doc in `memory/projects/<slug>.md`
  - metadata file `.clawvis-project.json`
- Project click opens hub panel with:
  - project link (repo path)
  - memory content
  - Kanban tasks filtered by project slug

## ECC Integration Points

- Hub settings endpoints:
  - `GET /api/kanban/hub/settings`
  - `PUT /api/kanban/hub/settings`
- Project endpoints:
  - `GET /api/kanban/hub/projects?kind=project|poc`
  - `POST /api/kanban/hub/projects`
  - `GET /api/kanban/hub/projects/{slug}`
- Cookie-cutter style template generation:
  - `python` (minimal `pyproject.toml` + `main.py`)
  - `vite` (minimal `package.json` + `src/main.js`)
  - `empty`
