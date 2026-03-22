#!/usr/bin/env python3
"""
TRIM TRIGGER — Weekly maintenance of L1 Brain files.

Use weekly (or when L1 files grow above budget).

The Problem:
- MEMORY.md accumulates old items
- AGENTS.md keeps outdated rules
- TOOLS.md has workarounds for fixed bugs
- When files bloat, agents skim instead of reading

The Solution:
- Measure each L1 file (token count)
- Archive content over budget to L2/L3
- Move completed work to daily notes
- Move project details to reference/
- Report before/after (show what changed)

Budget: 500-1000 tokens per file, 7000 total L1
"""

import json
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path.home() / ".openclaw" / "workspace"
L1_FILES = {
    "SOUL.md": 1000,           # Personality - stable, can grow
    "AGENTS.md": 1000,         # Rules - prune outdated
    "MEMORY.md": 800,          # Current state - trim aggressively
    "USER.md": 500,            # User prefs - small
    "TOOLS.md": 500,           # Tools - prune fixed workarounds
    "IDENTITY.md": 200,        # ID - very small
    "HEARTBEAT.md": 300,       # Standing tasks - small
}

L1_TOTAL_BUDGET = 7000

def count_tokens(text: str) -> int:
    """Rough token count (1 token ≈ 4 chars)."""
    return len(text) // 4

def audit_l1_files():
    """Measure each L1 file and report."""
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files": {},
        "total_tokens": 0,
        "budget_status": "OK",
        "recommendations": [],
    }
    
    for filename, budget in L1_FILES.items():
        filepath = WORKSPACE / filename
        
        if not filepath.exists():
            report["files"][filename] = {
                "status": "missing",
                "tokens": 0,
                "budget": budget,
            }
            continue
        
        content = filepath.read_text()
        tokens = count_tokens(content)
        ratio = tokens / budget
        
        status = "OK" if ratio < 1.0 else "OVER"
        if ratio > 1.5:
            status = "BLOATED"
        
        report["files"][filename] = {
            "status": status,
            "tokens": tokens,
            "budget": budget,
            "ratio": round(ratio, 2),
        }
        
        report["total_tokens"] += tokens
        
        # Recommendations
        if status == "BLOATED":
            report["recommendations"].append(
                f"🔴 {filename}: {tokens} tokens (budget {budget}). Archive old items to memory/ or reference/."
            )
        elif status == "OVER":
            report["recommendations"].append(
                f"🟡 {filename}: {tokens} tokens (budget {budget}). Monitor closely."
            )
    
    # Overall status
    if report["total_tokens"] > L1_TOTAL_BUDGET:
        report["budget_status"] = "OVER"
        report["recommendations"].insert(0,
            f"🔴 Total L1: {report['total_tokens']} tokens (budget {L1_TOTAL_BUDGET}). Trim now."
        )
    
    return report

def print_report(report: dict):
    """Pretty-print the audit report."""
    print("\n" + "=" * 70)
    print(" TRIM AUDIT — L1 Brain File Maintenance")
    print("=" * 70 + "\n")
    
    print(f"📊 L1 File Sizes:")
    for filename in L1_FILES.keys():
        info = report["files"][filename]
        if info["status"] == "missing":
            print(f"   {filename:20} [MISSING]")
        else:
            ratio_pct = int(info["ratio"] * 100)
            status_icon = {"OK": "✅", "OVER": "🟡", "BLOATED": "🔴"}[info["status"]]
            print(f"   {filename:20} {info['tokens']:4} / {info['budget']:4} tokens {ratio_pct:3}% {status_icon}")
    
    total_pct = int((report["total_tokens"] / L1_TOTAL_BUDGET) * 100)
    status_icon = "✅" if report["budget_status"] == "OK" else "🔴"
    print(f"\n   {'Total L1':20} {report['total_tokens']:4} / {L1_TOTAL_BUDGET:4} tokens {total_pct:3}% {status_icon}")
    
    if report["recommendations"]:
        print(f"\n🎯 Recommendations:")
        for rec in report["recommendations"]:
            print(f"   {rec}")
    else:
        print(f"\n✅ All files within budget. No action needed.")
    
    print("\n" + "=" * 70)
    print(" What to Archive")
    print("=" * 70 + "\n")
    
    print("""
MEMORY.md:
  → Move completed items to memory/daily/YYYY-MM-DD.md
  → Move inactive projects to memory/archive/projects/
  
AGENTS.md:
  → Move historical context to memory/projects/{project}.md
  → Remove workarounds for fixed bugs (keep only active rules)
  
TOOLS.md:
  → Move deprecated commands to reference/sops/
  → Keep only current machine-specific workarounds
  
HEARTBEAT.md:
  → Archive completed standing tasks to memory/archive/
  → Keep only recurring weekly tasks
    """)
    
    print("=" * 70 + "\n")

def main():
    report = audit_l1_files()
    print_report(report)
    
    # Save report
    log_dir = WORKSPACE / ".logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"trim-audit-{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    with open(log_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Audit saved: {log_file}\n")
    
    # Exit code: 0 = OK, 1 = needs attention
    return 0 if report["budget_status"] == "OK" else 1

if __name__ == "__main__":
    exit(main())
