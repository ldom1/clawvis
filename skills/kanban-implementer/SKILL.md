---
name: kanban-implementer
description: "DEPRECATED — merged into `implement`. Use implement instead."
---

# ⚠️ Deprecated — use `implement`

This skill has been merged into `implement`.

```bash
# Auto-select next task
uv run --directory ${CLAWVIS_ROOT}/skills/implement/core python -m implement

# Select from specific project
uv run --directory ${CLAWVIS_ROOT}/skills/implement/core python -m implement --project hub

# List eligible tasks
uv run --directory ${CLAWVIS_ROOT}/skills/implement/core python -m implement --list
```

Delete this directory: `rm -rf ${CLAWVIS_ROOT}/skills/kanban-implementer`
