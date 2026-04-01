---
name: project-init
description: "Initialise un projet Lab + Kanban : API POST /hub/projects, structure repo (template), fiche mémoire PARA. Use when Ldom demande de créer un projet depuis une idée (vocal/texte)."
---

# Project Init

## Rôle

Créer un projet **clôt côté Hub** : dépôt sous `PROJECTS_ROOT`, mémoire `memory/projects/<slug>.md`, tâches initiales via l’API Kanban.

## Exécution rapide

```bash
# Description (obligatoire), nom affiché optionnel
~/.openclaw/skills/project-init/scripts/init.sh "Description du projet (≥3 caractères)" "Nom lisible"

# Variables optionnelles
export KANBAN_API_URL=http://127.0.0.1:8090
export KANBAN_API_KEY=   # si l’API est protégée
```

Le script appelle `POST /hub/projects` (serveur Kanban Clawvis). Le slug est **dérivé** du nom par l’API.

## Après création

1. Notifier Ldom (Telegram) avec le lien Hub `/hub/project/<slug>`.
2. `dombot-log` niveau INFO si tu ajoutes une action dédiée `project:create` (sinon logs API Kanban suffisent).
3. Optionnel : ouvrir une PR README ou premier PoC selon `PROTOCOL.md`.

## Liens

- Kanban : `GOAL.md` scénario « Initialisation »
- API : `kanban_api` — `ProjectCreate` (`description`, `name`, `stage`, `template`, …)
