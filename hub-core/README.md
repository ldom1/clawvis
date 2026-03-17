## dombot-hub-core

Core Python package for the LabOS hub.

- Fetches provider data (e.g. MammouthAI credits)
- Tracks token usage and simple water/system metrics
- Aggregates everything into Pydantic models (`HubState`, `CpuRam`, etc.)
- Writes JSON snapshots for a static/NGINX dashboard (`providers.json`, `system.json`, `tokens.json`, `status.json`).

This package is designed to be:

- **Reused** both in the open‑source `dombot-labos` stack and in private hubs (`Lab/hub`)
- **Stateless** apart from its JSON outputs (no hard‑coded local paths or secrets)

Typical usage:

```bash
uv run python -m hub_core.main
```

Or from Python:

```python
from hub_core.main import get_simple_state

state = get_simple_state(write_json=True)
print(state)
```

