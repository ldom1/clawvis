---
name: skill-tester
description: "Run all Python unit tests for OpenClaw skills and check Slack connectivity. Use when: validating skills after changes, debugging a failing skill, or running a health check. Outputs a pass/fail report."
---

# Skill Tester

Lance les tests unitaires Python de tous les skills OpenClaw et vérifie la connectivité Slack.

## ⚡ Exécution rapide

```bash
# Tester tous les skills
~/.openclaw/skills/skill-tester/scripts/test-all.sh

# Tester un skill spécifique
~/.openclaw/skills/skill-tester/scripts/test-all.sh logger
~/.openclaw/skills/skill-tester/scripts/test-all.sh kanban-implementer

# Lister les skills avec tests
~/.openclaw/skills/skill-tester/scripts/test-all.sh --list
```

---

## Ce qui est testé

| Vérification | Comment |
|---|---|
| Tests unitaires Python | `uv run pytest tests/ -q` dans chaque `core/` |
| Connectivité Slack | `logger/scripts/slack-check.sh` |

### Skills avec tests actifs

| Skill | Fichiers de test |
|-------|-----------------|
| `logger` | test_config, test_logger, test_models, test_slack_router |
| `self-improvement` | test_config, test_protocol_audit |
| `kanban-implementer` | test_selector, test_status |

---

## Ajouter des tests à un skill

Chaque skill Python doit avoir :

```
skills/<nom>/
└── core/
    ├── <package>/        ← code Python
    ├── tests/
    │   ├── __init__.py
    │   └── test_<module>.py
    └── pyproject.toml    ← avec pytest dans [project.optional-dependencies.dev]
```

Format `pyproject.toml` pour activer pytest :

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0"]
```

Lancer :
```bash
uv run --directory ~/.openclaw/skills/<nom>/core pytest tests/ -v
```

---

## Tester manuellement les skills non-Python

Pour les skills sans Python core (git-sync, brain-pulse) :

```bash
# Vérifier la syntaxe bash (si shellcheck installé)
shellcheck ~/.openclaw/skills/git-sync/scripts/sync.sh

# Dry run : lire le SKILL.md et vérifier les chemins référencés
grep -r "~/.openclaw/skills" ~/.openclaw/skills/git-sync/SKILL.md | \
  while read path; do [ -f "$path" ] && echo "✅ $path" || echo "❌ MISSING: $path"; done
```

---

## Est-ce que ça existe déjà ?

**Avant la création de ce skill (2026-03-17)** :
- ✅ Certains skills avaient `core/tests/` (logger, self-improvement)
- ❌ Aucun test runner unifié n'existait
- ❌ Aucun test d'intégration des scripts shell
- ❌ Aucune vérification des chemins dans les SKILL.md

**Ce skill apporte** :
- Un runner unique pour tous les tests existants
- Un point d'entrée pour ajouter des tests futurs
- La vérification Slack comme sanity check infra
