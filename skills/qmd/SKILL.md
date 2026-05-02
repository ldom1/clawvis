# ⚡ QMD Skill: Local Semantic Search Engine

**Purpose:** Index and search DomBot's memory locally using BM25 + vector embeddings + LLM re-ranking.

**Status:** Installed & Ready

---

## What is QMD?

**QMD** (Query Markdown Documents) is a local-first search engine for Markdown files, created by Tobi Lütke (Shopify founder).

**Key Features:**
- 🔍 BM25 full-text search (keyword-based)
- 🧠 Vector semantic search (meaning-based)
- 🎯 LLM re-ranking (context-aware relevance)
- ⏱️ Instant local search (<100ms)
- 🔐 100% local (no external API)

---

## Quick Start

### Verify Installation
```bash
qmd --version
# Output: qmd 1.0.7
```

### Test Search
```bash
qmd search "Claude" --path $BRAIN_PATH
qmd search "technology" --full
qmd query "latest discoveries"  # With LLM re-ranking
```

### View Status
```bash
qmd status
# Shows: Indexed documents, vectors, models
```

---

## Integration with Curiosity

After Curiosity creates discoveries, QMD indexes them:

```bash
# Auto-update index (add to cron):
*/5 * * * * qmd update --path $BRAIN_PATH

# Or manual:
qmd update
```

### Search Discoveries
```bash
# Find by keyword
qmd search "github"

# Find by meaning
qmd search "artificial intelligence"

# Query with LLM re-ranking
qmd query "what's new in tech?"

# JSON output for programmatic use
qmd search "discovery" --json
```

---

## Usage in Code

```python
import subprocess
import json

def search_memory(query, max_results=5):
    """Search memory via QMD (MEMORY_ROOT or BRAIN_PATH)."""
    import os
    from pathlib import Path
    base = os.environ.get("MEMORY_ROOT") or os.environ.get("BRAIN_PATH") or ""
    mem = Path(base).expanduser() if base else Path.home() / "lab" / "clawvis" / "instances" / "example" / "memory"
    result = subprocess.run([
        'qmd', 'search', query,
        '--path', str(mem),
        '--json',
        '-n', str(max_results)
    ], capture_output=True, text=True)

    return json.loads(result.stdout)

# Usage in morning-briefing.py:
recent = search_memory("discovery today")
for item in recent:
    print(f"- {item['title']} (score: {item['score']})")
```

---

## Integration with Clawvis

Point QMD at instance memory or the Local Brain vault:

```bash
# In ${CLAWVIS_ROOT}/config.json (documentation / tooling), or export in cron:
export MEMORY_ROOT=${CLAWVIS_ROOT}/instances/example/memory
# or
export BRAIN_PATH=/path/to/vault
qmd update --path "$BRAIN_PATH"
```

Hub / agent tools that expose `memory_search` can shell out to `qmd` the same way.

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Search speed | <100ms |
| Index size | <10MB |
| Recall | 90%+ |
| Precision | 85%+ |
| Update latency | <5s |

---

## Configuration

### Collections

Create `.qmd-config.json` in workspace:

```json
{
  "name": "DomBot Memory",
  "collections": [
    {
      "name": "core",
      "path": ".",
      "exclude": [".git", "node_modules"]
    },
    {
      "name": "discoveries",
      "path": "memory/curiosity/",
      "patterns": ["*.json"]
    }
  ]
}
```

---

## Troubleshooting

### Issue: No embeddings created
```bash
qmd embed  # Create vector embeddings (one-time, slow)
```

### Issue: Stale results
```bash
qmd update  # Re-index all documents
```

### Issue: Large memory file growing
```bash
# Archive old discoveries
find memory/curiosity -mtime +30 -mv memory/archive/
```

---

## Advanced: MCP Server

Run QMD as MCP server for external integrations:

```bash
qmd mcp --http --daemon
# Listens on http://localhost:8181
```

---

## Version History

- **v1.0.7** (installed): Latest, with embedding + re-ranking support

---

**Skill Location:** `$BRAIN_PATH/skills/qmd/`  
**Executable:** `qmd` (CLI, installed globally)  
**Documentation:** `memory/QMD_INTEGRATION_ANALYSIS.md` + `memory/QMD_QUICKSTART.md`
