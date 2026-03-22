#!/usr/bin/env python3
"""
RECOVER TRIGGER — Full context reconstruction from last session.

Use when:
- Restarting after context loss
- Starting a new session without continuity
- Waking up from auto-compaction
- Needing to understand current state without re-explanation

Flow:
1. Find most recent session transcript / daily note
2. Extract key signals: names, topics, deals, tasks
3. Search L2 (memory/) for matching breadcrumbs
4. Follow pointers to L3 (reference/) if needed
5. Synthesize active state
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
DAILY_DIR = MEMORY_DIR / "daily"

def find_recent_context():
    """Find most recent daily note or session."""
    # Get most recent daily note
    daily_files = sorted(DAILY_DIR.glob("*.md"))
    if not daily_files:
        return None
    
    return daily_files[-1]

def extract_signals(file_path: Path) -> dict:
    """Extract key signals: topics, tasks, projects, decisions."""
    try:
        content = file_path.read_text()
    except Exception as e:
        print(f"❌ Can't read {file_path}: {e}")
        return {}
    
    lines = content.split('\n')
    
    # Extract signals manually (naive keyword extraction)
    signals = {
        "topics": [],
        "projects": [],
        "tasks": [],
        "decisions": [],
        "blockers": [],
    }
    
    current_section = None
    for line in lines:
        line = line.strip()
        
        if "## " in line:
            current_section = line.replace("## ", "").lower()
        
        if current_section == "next steps" or "task" in current_section:
            if line.startswith("- "):
                signals["tasks"].append(line.lstrip("- "))
        
        if "blocker" in current_section:
            if line.startswith("- "):
                signals["blockers"].append(line.lstrip("- "))
        
        if "project" in current_section:
            if line.startswith("- "):
                signals["projects"].append(line.lstrip("- "))
    
    return signals

def search_memory(signals: dict) -> list:
    """Search L2 (memory/) for matching breadcrumbs."""
    results = []
    
    # Search breadcrumbs.md first
    breadcrumb_file = MEMORY_DIR / "breadcrumbs.md"
    if breadcrumb_file.exists():
        content = breadcrumb_file.read_text()
        results.append({
            "file": "memory/breadcrumbs.md",
            "relevance": "high",
            "snippet": "Key facts with pointers to L3 reference files"
        })
    
    # Search daily notes matching signals
    for daily_file in sorted(DAILY_DIR.glob("*.md"))[-7:]:  # Last 7 days
        try:
            content = daily_file.read_text()
            for signal in signals.get("topics", []) + signals.get("projects", []):
                if signal.lower() in content.lower():
                    results.append({
                        "file": str(daily_file.relative_to(WORKSPACE)),
                        "relevance": "medium",
                        "snippet": f"Matches signal: {signal}"
                    })
                    break
        except Exception:
            continue
    
    return results

def synthesize_context(signals: dict, memory_results: list) -> str:
    """Synthesize active state."""
    output = []
    
    output.append("🔄 RECOVERY COMPLETE\n")
    output.append("=" * 60)
    
    if signals.get("projects"):
        output.append("\n🎯 Active Projects:")
        for p in signals["projects"][:5]:
            output.append(f"  - {p}")
    
    if signals.get("tasks"):
        output.append("\n📋 Next Steps:")
        for t in signals["tasks"][:5]:
            output.append(f"  - {t}")
    
    if signals.get("blockers"):
        output.append("\n🔴 Blockers:")
        for b in signals["blockers"]:
            output.append(f"  - {b}")
    
    output.append("\n📚 Related Memory Files:")
    for result in memory_results[:5]:
        output.append(f"  - {result['file']} ({result['relevance']})")
    
    output.append("\n💡 Tip: Run `recover` again if you need more detail.")
    output.append("For full reference docs, see `reference/sops/` or breadcrumbs pointers.\n")
    
    return "\n".join(output)

def main():
    print("🔄 Initiating RECOVER trigger...\n")
    
    # Step 1: Find recent context
    recent = find_recent_context()
    if not recent:
        print("❌ No recent session found.")
        print("Tip: Run after a session has created memory/daily/YYYY-MM-DD.md")
        sys.exit(1)
    
    print(f"📖 Most recent session: {recent.name}")
    
    # Step 2: Extract signals
    signals = extract_signals(recent)
    print(f"📍 Extracted signals: {len(signals['tasks'])} tasks, {len(signals['blockers'])} blockers")
    
    # Step 3: Search memory
    memory_results = search_memory(signals)
    print(f"🔍 Found {len(memory_results)} related memory files")
    
    # Step 4: Synthesize
    context = synthesize_context(signals, memory_results)
    print(context)
    
    # Log recovery
    log_file = WORKSPACE / ".logs" / f"recover-{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'w') as f:
        f.write(context)
    
    print(f"\n✅ Recovery logged: {log_file}")

if __name__ == "__main__":
    main()
