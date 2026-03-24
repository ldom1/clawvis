# Clawvis CI Test Scripts

This folder contains CI-oriented test runners used by GitHub Actions.

## Scripts

- `ci-kanban.sh`: runs `ruff`, `pylint`, `pytest` for `kanban`
- `ci-hub-core.sh`: runs `ruff`, `pylint`, `pytest` for `hub-core`
- `ci-hub.sh`: runs `yarn format:check`, `yarn test`, `yarn build` for `hub`
- `ci-skills.sh`: discovers each `skills/*/core` package and runs lint/tests
- `ci-cli.sh`: installs CLI deps and runs syntax/help smoke tests
- `ci-all.sh`: global orchestrator that runs all scripts in order

## Local usage

```bash
bash tests/ci-all.sh
```
