# reverse-prompt Skill — Usage Examples

## 🚀 Quick Start

### Example 1: Single Report

```bash
# Create perfect example
REPORT="# Hub Refresh

## Status
✅ SUCCESS (09:38:50)

## Metrics
- MammouthAI: \$6.94 / \$12.00 (58%)
- CPU: 7.8% | RAM: 27.1%
- Disk: 34.0%

## Result
Session tokens updated."

# Reverse-engineer the prompt
bash ~/.openclaw/skills/reverse-prompt/scripts/run.sh \
  --example "$REPORT" \
  --model claude-haiku

# Output:
# ==============================================================
# REVERSE PROMPT RESULT
# ==============================================================
#
# 📝 Reconstructed Prompt:
#
# Write a concise operational report with:
# - Status section with emoji indicator (✅/❌) and timestamp
# - Metrics section with key values (name: value format)
# - Result summary
# - Format: Markdown with # headers
# - Tone: Technical, factual
# - Length: ~100 words max
#
# 📊 Confidence: 94%
# Iterations used: 3
#
# 🎯 Detected Patterns:
#  • tone: technical
#  • structure: section-based
#  • format: markdown-headers
#  • format: emoji-indicators
#  • length: brief (<50 words)
# ==============================================================
```

---

## 📋 Example 2: Unified LabOS Agent Voice

**Problem:** 5 agents, 5 different output styles. Need consistency.

```bash
#!/bin/bash
# setup-labos-unified-voice.sh

# Step 1: Define your perfect style
PERFECT_REPORT=$(cat << 'EOF'
## Integration Results

✅ **Loki deployment** — 8h estimated
- Log aggregation: Active
- Label indexing: Configured
- Retention: 7 days

✅ **Grafana dashboards** — In progress
- Agent health: Ready
- Token tracking: 94% complete
- Budget alerts: Pending

---
**Next:** Alerting rules (Setup.6b.2)
EOF
)

# Step 2: Reverse-engineer the style
STYLE_PROMPT=$(bash ~/.openclaw/skills/reverse-prompt/scripts/run.sh \
  --example "$PERFECT_REPORT" \
  --model claude-haiku \
  --mode json | jq -r '.reconstructed_prompt')

# Step 3: Save as team standard
mkdir -p ~/.openclaw/labos/standards
echo "$STYLE_PROMPT" > ~/.openclaw/labos/standards/report-style.txt

# Step 4: Use everywhere
# In LabOS agent router:
AGENT_PROMPT=$(cat ~/.openclaw/labos/standards/report-style.txt)
ALL_AGENTS_USE="$AGENT_PROMPT"
```

---

## 🎯 Example 3: Quality Gate

**Problem:** PR summaries are inconsistent. Need scoring.

```python
# labos/quality/gate.py

from reverse_prompt.engine import ReversePromptEngine

# Load reference style
PERFECT_PR = """
**Feature:** Add Loki observability layer

**Changes:**
- Deploy Loki container
- Configure agent log pipeline
- Add Grafana dashboards

**Testing:** ✅ Unit tested | ✅ Integration tested

**Impact:** Medium (new observability, no breaking changes)
"""

engine = ReversePromptEngine()
style = engine.reverse_engineer(PERFECT_PR)

# Now score any PR against this style
def quality_score(pr_text: str) -> float:
    """Score PR for quality match."""
    analysis = engine.reverse_engineer(pr_text)
    return analysis["confidence"]

# Gate logic
pr = "Added logging feature"
if quality_score(pr) > 0.85:
    print("✅ PR passes quality gate")
    merge(pr)
else:
    print("❌ PR needs improvement")
    request_changes(pr)
```

---

## 🔄 Example 4: Training Data Generation

**Problem:** You have 1 perfect example, need 100 training samples.

```bash
#!/bin/bash
# generate-training-data.sh

# Step 1: Your perfect example
PERFECT="## Task: Database Schema

Create a normalized schema for user authentication.

**Solution:**
- Table: users (id, email, password_hash, created_at)
- Table: sessions (id, user_id, token, expires_at)
- Indexes: users(email), sessions(token)

**Reasoning:** Email is primary lookup key. Sessions need fast token validation."

# Step 2: Get the style prompt
STYLE_PROMPT=$(bash ~/.openclaw/skills/reverse-prompt/scripts/run.sh \
  --example "$PERFECT" \
  --mode json | jq -r '.reconstructed_prompt')

# Step 3: Generate 100 variations
TASKS=("user" "product" "order" "payment" "inventory")
DOMAINS=("authentication" "authorization" "caching" "auditing" "analytics")

for i in {1..100}; do
  TASK="${TASKS[$RANDOM % ${#TASKS[@]}]}"
  DOMAIN="${DOMAINS[$RANDOM % ${#DOMAINS[@]}]}"
  
  # Use style prompt to generate
  OUTPUT=$(curl -X POST http://localhost:8090/api/claude \
    -d "Task: $TASK management system for $DOMAIN
    
    $STYLE_PROMPT")
  
  # Save training example
  echo "$OUTPUT" >> training-data.jsonl
done

echo "✅ Generated 100 training examples"
```

---

## 🏗️ Example 5: Integration with LabOS

```python
# In labos/orchestration/agent_router.py

from reverse_prompt.engine import ReversePromptEngine

class AgentRouter:
    def __init__(self, style_guide_example: str):
        """Initialize router with unified style."""
        engine = ReversePromptEngine()
        result = engine.reverse_engineer(style_guide_example)
        
        self.style_prompt = result["reconstructed_prompt"]
        self.style_confidence = result["confidence"]
        
        if self.style_confidence < 0.85:
            print("⚠️ Warning: Style guide confidence low")
    
    def route_task(self, task: str, agent_id: str) -> dict:
        """Route task through agent with unified style."""
        return {
            "task": task,
            "agent_id": agent_id,
            "system_prompt": self.style_prompt,  # ← All agents use same style
            "style_confidence": self.style_confidence,
        }

# Usage:
PERFECT_LABOS_REPORT = "..."
router = AgentRouter(PERFECT_LABOS_REPORT)

# All tasks go through router → all agents write same style ✅
task = "Generate status report"
routed = router.route_task(task, "agent-hub-refresh")
```

---

## 💻 Example 6: CLI Usage (All Options)

```bash
# Basic
bash ~/.openclaw/skills/reverse-prompt/scripts/run.sh \
  --example "Your text here"

# With context
bash ~/.openclaw/skills/reverse-prompt/scripts/run.sh \
  --example "Your text" \
  --context "Target: CTOs, tone: technical"

# Custom model
bash ~/.openclaw/skills/reverse-prompt/scripts/run.sh \
  --example "Your text" \
  --model claude-opus \
  --iterations 5

# JSON output (for APIs)
bash ~/.openclaw/skills/reverse-prompt/scripts/run.sh \
  --example "Your text" \
  --mode json
  
# Result:
# {
#   "reconstructed_prompt": "...",
#   "confidence": 0.94,
#   "patterns": [...],
#   "iterations_used": 3
# }
```

---

## 🧪 Example 7: Testing

```python
# tests/test_reverse_prompt.py

from reverse_prompt.engine import ReversePromptEngine

def test_simple_example():
    """Test basic reverse prompt."""
    example = "Write a 100-word summary of AI risks."
    
    engine = ReversePromptEngine(iterations=2)
    result = engine.reverse_engineer(example)
    
    assert result["confidence"] > 0.80
    assert "write" in result["reconstructed_prompt"].lower()
    assert len(result["patterns"]) > 0

def test_pattern_detection():
    """Test pattern detection."""
    example = "# Heading\n✅ Success\n- Bullet 1\n- Bullet 2"
    
    engine = ReversePromptEngine()
    result = engine.reverse_engineer(example)
    
    assert "markdown" in str(result["patterns"]).lower()
    assert "emoji" in str(result["patterns"]).lower()

def test_context_aware():
    """Test context awareness."""
    example = "Blockchain integration complete."
    
    engine = ReversePromptEngine()
    result_tech = engine.reverse_engineer(example, context="CTOs")
    result_biz = engine.reverse_engineer(example, context="CFO")
    
    # Should generate different prompts based on context
    assert result_tech["reconstructed_prompt"] != result_biz["reconstructed_prompt"]
```

---

## 📊 Monitoring Output

```bash
# Monitor reverse-prompt runs in real-time
tail -f ~/.openclaw/logs/reverse-prompt*.log

# Check recent results
ls -lh ~/.openclaw/logs/reverse-prompt-* | tail -10

# Bulk analysis (how often is it used?)
wc -l ~/.openclaw/logs/reverse-prompt-*.log
grep "confidence" ~/.openclaw/logs/reverse-prompt-*.log | \
  awk '{print $NF}' | \
  sort -n | \
  tail -20
```

---

## Integration Checklist for LabOS

- [ ] Copy `reverse-prompt` to `~/.openclaw/skills/`
- [ ] Run `uv sync` in skill directory
- [ ] Create style guide example
- [ ] Integrate into `labos/orchestration/agent_router.py`
- [ ] Add quality gate scoring in `labos/quality/gate.py`
- [ ] Test with 3-5 real examples
- [ ] Deploy to production
- [ ] Monitor confidence scores in logs

---

**Created:** 2026-03-18  
**Status:** Ready for production  
**Next:** HTTP API endpoint + webhooks for style updates
