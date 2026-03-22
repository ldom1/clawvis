"""On-demand context reconstruction from last daily note."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from brain_maintenance.logging import log_info

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
DAILY_DIR = MEMORY_DIR / "daily"


def find_recent_context() -> Path | None:
    daily_files = sorted(DAILY_DIR.glob("*.md"))
    return daily_files[-1] if daily_files else None


def extract_signals(file_path: Path) -> dict:
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"❌ Can't read {file_path}: {e}")
        return {"topics": [], "projects": [], "tasks": [], "decisions": [], "blockers": []}
    lines = content.split("\n")
    signals: dict = {"topics": [], "projects": [], "tasks": [], "decisions": [], "blockers": []}
    current: str | None = None
    for line in lines:
        line = line.strip()
        if "## " in line:
            current = line.replace("## ", "").lower()
        if current and "task" in current and line.startswith("- "):
            signals["tasks"].append(line.lstrip("- "))
        if current and "blocker" in current and line.startswith("- "):
            signals["blockers"].append(line.lstrip("- "))
        if current and "project" in current and line.startswith("- "):
            signals["projects"].append(line.lstrip("- "))
    return signals


def search_memory(signals: dict) -> list[dict]:
    results: list[dict] = []
    if (MEMORY_DIR / "breadcrumbs.md").exists():
        results.append({
            "file": "memory/breadcrumbs.md",
            "relevance": "high",
            "snippet": "Key facts with pointers to L3",
        })
    for daily_file in sorted(DAILY_DIR.glob("*.md"))[-7:]:
        try:
            content = daily_file.read_text(encoding="utf-8")
            for signal in signals.get("topics", []) + signals.get("projects", []):
                if signal.lower() in content.lower():
                    results.append({
                        "file": str(daily_file.relative_to(WORKSPACE)),
                        "relevance": "medium",
                        "snippet": f"Matches: {signal}",
                    })
                    break
        except OSError:
            continue
    return results


def synthesize_context(signals: dict, memory_results: list[dict]) -> str:
    out = ["🔄 RECOVERY COMPLETE\n", "=" * 60]
    if signals.get("projects"):
        out.append("\n🎯 Active Projects:")
        for p in signals["projects"][:5]:
            out.append(f"  - {p}")
    if signals.get("tasks"):
        out.append("\n📋 Next Steps:")
        for t in signals["tasks"][:5]:
            out.append(f"  - {t}")
    if signals.get("blockers"):
        out.append("\n🔴 Blockers:")
        for b in signals["blockers"]:
            out.append(f"  - {b}")
    out.append("\n📚 Related Memory:")
    for r in memory_results[:5]:
        out.append(f"  - {r['file']} ({r['relevance']})")
    out.append("\n")
    return "\n".join(out)


def main() -> int:
    log_info("recover:start", "Context reconstruction")
    recent = find_recent_context()
    if not recent:
        print("❌ No recent session found.")
        log_info("recover:skip", "No daily note")
        return 1
    print(f"📖 Most recent: {recent.name}")
    signals = extract_signals(recent)
    memory_results = search_memory(signals)
    context = synthesize_context(signals, memory_results)
    print(context)
    log_dir = WORKSPACE / ".logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"recover-{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.log"
    log_file.write_text(context, encoding="utf-8")
    log_info("recover:complete", str(log_file))
    print(f"\n✅ Logged: {log_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
