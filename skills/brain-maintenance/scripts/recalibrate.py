#!/usr/bin/env python3
"""
RECALIBRATE TRIGGER — Agent drift detection & correction.

The Problem:
Over weeks/months of operation, agents drift. They:
- Stop following SOUL.md (personality changes)
- Ignore AGENTS.md rules
- Develop habits not supported by files

The drift is subtle. You don't notice until the agent feels "wrong".

The Solution:
1. Re-read every L1 file word-for-word
2. Compare recent behavior against what files actually say
3. Report: where drift occurred + what to correct
4. ALWAYS include specific example (can't just say "recalibrated")

This is how you keep agents aligned over months of continuous operation.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

WORKSPACE = Path.home() / ".openclaw" / "workspace"

def read_l1_files() -> dict:
    """Read all L1 Brain files."""
    l1 = {}
    
    l1_files = ["SOUL.md", "AGENTS.md", "MEMORY.md", "USER.md", "TOOLS.md", "IDENTITY.md", "HEARTBEAT.md"]
    
    for filename in l1_files:
        filepath = WORKSPACE / filename
        if filepath.exists():
            l1[filename] = filepath.read_text()
        else:
            l1[filename] = None
    
    return l1

def get_recent_session_log() -> str:
    """Get recent session messages for behavior analysis."""
    # In real use, this would pull from session history
    # For now, return placeholder
    return """
[Recent behavior examples]
- Last message: Direct, concise, no fluff
- Tool usage: Chose read over web_search when local file available
- Error handling: Apologized briefly, proposed fix
- Communication: Used French + English code-switching naturally
"""

def detect_drift(l1: dict, recent_behavior: str) -> dict:
    """Analyze for drift between files and recent behavior."""
    
    drift_analysis = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "soul_alignment": "ALIGNED",  # Personality match
        "agents_compliance": "COMPLIANT",  # Rule following
        "behavior_examples": [],
        "drift_detected": [],
        "corrections_needed": [],
    }
    
    # Parse SOUL.md for expectations
    soul = l1.get("SOUL.md", "")
    
    # Check for key personality traits
    soul_traits = {
        "concise": "Économie de Verbe" in soul or "Concis" in soul,
        "autonomous": "Autonomie" in soul,
        "curious": "Curiosité" in soul,
        "opinionated": "Opinions Assumées" in soul,
    }
    
    # Behavior checks (in real impl, use NLP/semantic analysis)
    behavior_traits = {
        "concise": len(recent_behavior.split('\n')) < 20,  # Rough heuristic
        "autonomous": "I'll implement" in recent_behavior or "I'll create" in recent_behavior,
        "curious": "interesting" in recent_behavior.lower() or "pattern" in recent_behavior.lower(),
        "opinionated": "I think" in recent_behavior or "best is" in recent_behavior.lower(),
    }
    
    # Detect drift
    for trait, soul_says in soul_traits.items():
        behavior_shows = behavior_traits.get(trait, False)
        
        if soul_says and not behavior_shows:
            drift_analysis["drift_detected"].append(
                f"⚠️ {trait.upper()}: SOUL.md says yes, behavior says no"
            )
            drift_analysis["corrections_needed"].append(
                f"Reinforce {trait} in next 3 responses"
            )
    
    # Parse AGENTS.md for rules
    agents = l1.get("AGENTS.md", "")
    
    # Example rules check
    if "never repeat errors" in agents.lower() and "documented it" not in recent_behavior:
        drift_analysis["drift_detected"].append(
            "⚠️ LEARNING: Failed to document error for future avoidance"
        )
    
    return drift_analysis

def generate_report(l1: dict, drift: dict) -> str:
    """Generate recalibration report."""
    
    output = []
    output.append("\n" + "=" * 70)
    output.append(" RECALIBRATE — Agent Drift Detection & Correction")
    output.append("=" * 70 + "\n")
    
    # L1 Re-read Summary
    output.append("📖 L1 Files Re-read:")
    for filename, content in l1.items():
        if content:
            lines = len(content.split('\n'))
            output.append(f"   ✅ {filename:20} ({lines} lines)")
        else:
            output.append(f"   ❌ {filename:20} [MISSING]")
    
    # Drift Detection
    output.append("\n" + "=" * 70)
    output.append(" Drift Analysis")
    output.append("=" * 70 + "\n")
    
    if drift["drift_detected"]:
        output.append("🚨 Drift Detected:")
        for issue in drift["drift_detected"]:
            output.append(f"   {issue}")
        
        output.append("\n✅ Corrections Needed:")
        for correction in drift["corrections_needed"]:
            output.append(f"   {correction}")
    else:
        output.append("✅ NO DRIFT DETECTED")
        output.append("   Agent behavior aligns with SOUL.md + AGENTS.md")
        output.append("   Recent example: Concise, autonomous, curious, opinionated ✓")
    
    output.append("\n" + "=" * 70)
    output.append(" Action Items")
    output.append("=" * 70 + "\n")
    
    if drift["drift_detected"]:
        output.append("1. Review SOUL.md + AGENTS.md once more (word-for-word)")
        output.append("2. Identify which behaviors contradict the files")
        output.append("3. Consciously correct in next 5 responses")
        output.append("4. Re-run RECALIBRATE in 1 week to verify correction\n")
    else:
        output.append("✅ Agent is well-calibrated. Check again in 2 weeks.\n")
    
    return "\n".join(output)

def main():
    print("🔄 Initiating RECALIBRATE trigger...\n")
    
    # Step 1: Re-read L1
    print("📖 Re-reading L1 Brain files...")
    l1 = read_l1_files()
    
    # Step 2: Get recent behavior
    print("📊 Analyzing recent behavior...")
    recent_behavior = get_recent_session_log()
    
    # Step 3: Detect drift
    print("🔍 Detecting drift...\n")
    drift = detect_drift(l1, recent_behavior)
    
    # Step 4: Report
    report = generate_report(l1, drift)
    print(report)
    
    # Save report
    log_dir = WORKSPACE / ".logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"recalibrate-{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    with open(log_file, 'w') as f:
        json.dump({
            "timestamp": drift["timestamp"],
            "drift_detected": len(drift["drift_detected"]) > 0,
            "issues": drift["drift_detected"],
            "corrections": drift["corrections_needed"],
        }, f, indent=2)
    
    print(f"✅ Report saved: {log_file}\n")

if __name__ == "__main__":
    main()
