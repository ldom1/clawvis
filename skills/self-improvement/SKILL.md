---
name: self-improvement
description: "Captures learnings, errors, and corrections to enable continuous improvement. Use when: (1) A command or operation fails unexpectedly, (2) User corrects Claude ('No, that's wrong...', 'Actually...'), (3) User requests a capability that doesn't exist, (4) An external API or tool fails, (5) Claude realizes its knowledge is outdated or incorrect, (6) A better approach is discovered for a recurring task. Also review learnings before major tasks."
metadata:
---

# Self-Improvement Skill

## ⚠️ IMPORTANT

**CRITICAL:** This skill **DOES NOT** write to `MEMORY.md`.

- ❌ Report is NOT appended to MEMORY.md
- ✅ Report sent via Clawvis Telegram service (`POST /send` with `{"text":"…"}`)
- ✅ Report printed to console + logs
- ✅ Report follows REPORT_TEMPLATE.md structure

**Report Format (NO Placeholders):**

```
**What's Working (Keep Doing It)**
- 100% uptime for Curiosity Skill (autonomous execution via crons)
- High-frequency discovery logging (60+ in 22h)

**What Needs Fixing (Priority Order)**
- Fix OpenRouter / upstream API errors (auth, rate limits, model availability)
- Optimize QMD indexing: currently slow on large knowledge base

**Innovation To Try**
- Test parallel agent execution (measure throughput vs single-threaded)
```

❌ **FORBIDDEN**: placeholders like `[(Details in full log)]`, vague items, writing to MEMORY.md, truncated analysis.

---

## ⚡ Exécution rapide

```bash
export CLAWVIS_ROOT="${CLAWVIS_ROOT:-$HOME/lab/clawvis}"
UV_CORE="$CLAWVIS_ROOT/skills/self-improvement/core"

# Mode review (analyze .learnings/ + Telegram)
uv run --directory "$UV_CORE" python -m self_improvment

# Mode protocol_audit (scan skills + lab code + PROTOCOL.md)
uv run --directory "$UV_CORE" python -m self_improvment protocol_audit
```

⚠️ Ne pas invoquer `scripts/protocol_audit.py` — il n'existe pas. Exécution via `python -m self_improvment` uniquement.

### LLM (mode `review`)

**OpenRouter uniquement** (aligné agent-service) : `OPENROUTER_API_KEY` dans `.env` racine Clawvis ou `core/.env`.
Optionnel : `OPENROUTER_MODEL`, `OPENROUTER_BASE_URL` (défaut `https://openrouter.ai/api/v1`).

---

## Quick Reference

| Situation | Action |
|-----------|--------|
| Command/operation fails | Log to `.learnings/ERRORS.md` |
| User corrects you | Log to `.learnings/LEARNINGS.md` with category `correction` |
| User wants missing feature | Log to `.learnings/FEATURE_REQUESTS.md` |
| API/external tool fails | Log to `.learnings/ERRORS.md` with integration details |
| Knowledge was outdated | Log to `.learnings/LEARNINGS.md` with category `knowledge_gap` |
| Found better approach | Log to `.learnings/LEARNINGS.md` with category `best_practice` |
| Similar to existing entry | Link with `**See Also**`, consider priority bump |
| Broadly applicable learning | Promote to CLAUDE.md, AGENTS.md, and/or Local Brain vault |
| Durable project lesson | Promote to `$BRAIN_PATH/resources/knowledge/operational/clawvis-pitfalls.md` |

---

## Workspace Layout (Clawvis)

```
${CLAWVIS_ROOT}/
├── CLAUDE.md
├── AGENTS.md
├── skills/self-improvement/.learnings/
│   ├── LEARNINGS.md
│   ├── ERRORS.md
│   └── FEATURE_REQUESTS.md
└── instances/<name>/memory/
```

```bash
mkdir -p "${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/self-improvement/.learnings"
```

### Promotion Targets

| Learning Type | Promote To |
|---------------|------------|
| Behavioral patterns | `CLAUDE.md` |
| Workflow improvements | `AGENTS.md` |
| Tool gotchas | `docs/` or `AGENTS.md` |
| Durable lessons / pitfalls | `$BRAIN_PATH/resources/knowledge/operational/clawvis-pitfalls.md` |
| Session learnings | `$BRAIN_PATH/inbox/daily/implementation/clawvis/YYYY-MM-DD-topic.md` |

---

## Telegram (cron)

1. **Single final message** per run per `REPORT_TEMPLATE.md`. No intermediate spam.
2. Use `TELEGRAM_URL` (Clawvis `telegram` service `POST /send`) with JSON `{"text":"…"}`. Chat id comes from service env.
3. For protocol audit cron: run `python -m self_improvment protocol_audit` once per schedule — don't duplicate via `review` mode in the same tick.

---

## Logging Format

### Learning Entry (`LEARNINGS.md`)

```markdown
## [LRN-YYYYMMDD-XXX] category

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high | critical
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
One-line description of what was learned

### Details
Full context: what happened, what was wrong, what's correct

### Suggested Action
Specific fix or improvement to make

### Metadata
- Source: conversation | error | user_feedback
- Related Files: path/to/file.ext
- Tags: tag1, tag2
- See Also: LRN-20250110-001 (if related)

---
```

### Error Entry (`ERRORS.md`)

```markdown
## [ERR-YYYYMMDD-XXX] skill_or_command_name

**Logged**: ISO-8601 timestamp
**Priority**: high
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
Brief description of what failed

### Error
```
Actual error message or output
```

### Context
- Command/operation attempted
- Environment details if relevant

### Suggested Fix
If identifiable

### Metadata
- Reproducible: yes | no | unknown
- Related Files: path/to/file.ext
- See Also: ERR-20250110-001 (if recurring)

---
```

### Feature Request Entry (`FEATURE_REQUESTS.md`)

```markdown
## [FEAT-YYYYMMDD-XXX] capability_name

**Logged**: ISO-8601 timestamp
**Priority**: medium
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Requested Capability
What the user wanted to do

### User Context
Why they needed it, what problem they're solving

### Complexity Estimate
simple | medium | complex

### Suggested Implementation
How this could be built

---
```

---

## ID Generation

Format: `TYPE-YYYYMMDD-XXX` (e.g., `LRN-20250115-001`, `ERR-20250115-A3F`, `FEAT-20250115-002`)

---

## Resolving Entries

When an issue is fixed, update the entry:

1. `**Status**: pending` → `**Status**: resolved`
2. Add resolution block:

```markdown
### Resolution
- **Resolved**: ISO-8601 timestamp
- **Commit/PR**: abc123 or #42
- **Notes**: Brief description of what was done
```

Other statuses: `in_progress`, `wont_fix`, `promoted`.

---

## Promoting to Project Memory

Promote when a learning applies across files/features, prevents recurring mistakes, or any contributor should know it.

### How to Promote

1. Distill into a concise rule or fact
2. Add to the appropriate target (see Promotion Targets above)
3. Update the original entry: `**Status**: promoted` + `**Promoted**: <target>`

### Priority: Local Brain vault over repo files

For lessons that will outlive the current branch or session, prefer the brain vault over CLAUDE.md:
- **Pitfalls**: `$BRAIN_PATH/resources/knowledge/operational/clawvis-pitfalls.md`
- **Session notes**: `$BRAIN_PATH/inbox/daily/implementation/clawvis/YYYY-MM-DD-topic.md`

---

## Periodic Review

### When
- Before starting a major task
- After completing a feature
- Weekly during active development

### Quick Status Check

```bash
grep -h "Status\*\*: pending" .learnings/*.md | wc -l
grep -B5 "Priority\*\*: high" .learnings/*.md | grep "^## \["
```

---

## Best Practices

1. **Log immediately** — context is freshest right after the issue
2. **Be specific** — future agents need to understand quickly
3. **Include reproduction steps** — especially for errors
4. **Suggest concrete fixes** — not just "investigate"
5. **Promote aggressively** — if in doubt, add to CLAUDE.md or Local Brain vault
6. **Review regularly** — stale learnings lose value

---

## Gitignore Options

- **Keep local** (per-developer): add `.learnings/` to `.gitignore`
- **Track in repo** (team-wide): don't add it
- **Hybrid** (track templates, ignore entries): `.learnings/*.md` in `.gitignore`, keep `.learnings/.gitkeep`
