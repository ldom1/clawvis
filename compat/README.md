# clawvis/compat — Agent Compatibility Layer

Clawvis is designed to work with three agent runtimes. This module provides
a unified API that proxies features when available, and raises `FeatureUnavailable`
(with a clear message) when not.

## Runtime Matrix

| Feature | OpenClaw | Claude Code | Mistral Vibe |
|---------|:--------:|:-----------:|:------------:|
| Cron scheduling | ✅ native | ❌ | ❌ |
| Message send (Telegram/Discord) | ✅ native | ❌ | ❌ |
| Skill execution | ✅ native | ✅ via bash | ✅ via bash |
| Memory vault read/write | ✅ native | ✅ file I/O | ✅ file I/O |
| Agent session management | ✅ native | ❌ stateless | ❌ stateless |

## Usage

```python
from clawvis.compat import get_runtime, message_send, cron_schedule, FeatureUnavailable

runtime = get_runtime()  # "openclaw" | "claude" | "mistral" | "unknown"

try:
    message_send("telegram", "5689694685", "Hello from Clawvis!")
except FeatureUnavailable as e:
    print(f"[compat] {e}")  # Feature 'message:send' not available in runtime 'claude'. Available in: openclaw.
```

## Adding a New Feature

1. Add the function to `__init__.py` with the pattern:
   - Check runtime
   - If OpenClaw: proxy via `subprocess.run(["openclaw", ...])`
   - If Claude/Mistral: either fallback (if possible) or raise `FeatureUnavailable`
2. Add a row to the matrix above

## Runtime Detection

Runtime is detected from environment variables:
- `OPENCLAW_AGENT_ID` or `AGENT_ROLE=ORCHESTRATOR` → openclaw
- `CLAUDE_CODE` or `which claude` → claude
- `MISTRAL_VIBE` or `which mistral` → mistral
