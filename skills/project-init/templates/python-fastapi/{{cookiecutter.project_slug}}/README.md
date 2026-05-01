# {{cookiecutter.project_name}}

FastAPI cookie-cutter starter for Clawvis.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
uvicorn app.main:app --reload --port 8000
```

## Quality

```bash
pytest
ruff check .
pylint app tests
```

## Docs

```bash
sphinx-build -b html docs docs/_build
```
