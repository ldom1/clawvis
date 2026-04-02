#!/usr/bin/env python3
"""
Morning Briefing — Compact version with Curiosity integration.
Core: 6 lines. Optional: +3-5 top discoveries from Curiosity.
Sends to Telegram via OpenClaw gateway.
"""

import json
import os
import sys
import re
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

from wikipedia_on_this_day import fetch_on_this_day

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory" / "resources" / "curiosity"
_HUB_ROOT = Path(os.environ.get("HUB_ROOT", str(Path.home() / "Lab" / "hub-ldom" / "instances" / "ldom")))
SYSTEM_JSON = _HUB_ROOT / "public" / "api" / "system.json"
KANBAN_JSON = WORKSPACE / "memory" / "kanban" / "tasks.json"
CF_URL_FILE = _HUB_ROOT / "DOMBOT_TECH_URL.txt"
TELEGRAM_TARGET_ID = os.environ.get("TELEGRAM_TARGET_ID", "")


def get_hub_url():
    """Get Cloudflare tunnel URL, fallback to localhost."""
    try:
        if CF_URL_FILE.exists():
            url = CF_URL_FILE.read_text().strip()
            if url:
                return url
    except Exception:
        pass
    return "http://localhost:8088"


def get_system_line():
    try:
        data = json.loads(SYSTEM_JSON.read_text())
        cpu, ram, disk = data["cpu_percent"], data["ram_percent"], data["disk_percent"]
        alert = ""
        if disk > 90: alert = " 🔴"
        elif disk > 80 or ram > 85: alert = " ⚠️"
        return f"⚙️ CPU {cpu}% · RAM {ram}% · Disk {disk}%{alert}"
    except Exception:
        return None


_HEADING_ANY = re.compile(r"^##\s*(?:\d+[\.)]\s*)?(.+?)\s*$")
_SKIP_HEADING = frozenset(
    x.lower()
    for x in (
        "references",
        "see also",
        "external links",
        "overview",
        "sources",
    )
)


def _first_curiosity_heading(path: Path) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in lines:
        raw = line.strip()
        m = _HEADING_ANY.match(raw)
        if not m:
            continue
        title = m.group(1).strip()
        if not title or title.lower() in _SKIP_HEADING:
            continue
        if re.fullmatch(r"\d+", title):
            continue
        return title
    return None


def get_tech_headline():
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = datetime.fromtimestamp(datetime.now().timestamp() - 86400).strftime("%Y-%m-%d")
    for day in (today, yesterday):
        for suffix in ("tech_news", "tech"):
            p = MEMORY_DIR / f"{day}-{suffix}.md"
            if not p.exists():
                continue
            title = _first_curiosity_heading(p)
            if title:
                return f"🔧 {title}"
    return None


_NEWS_FIRST = (
    re.compile(r"^##\s*1[\.)]\s+(.+)$", re.I),
    re.compile(r"^##\s*1\s+(.+)$", re.I),
    re.compile(r"^###\s*1[\.)]\s+(.+)$", re.I),
)


def get_news_headline():
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = datetime.fromtimestamp(datetime.now().timestamp() - 86400).strftime("%Y-%m-%d")
    for day in (today, yesterday):
        p = MEMORY_DIR / f"{day}-latest.md"
        if not p.exists():
            continue
        try:
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                s = line.strip()
                for pat in _NEWS_FIRST:
                    m = pat.match(s)
                    if m:
                        return f"📰 {m.group(1).strip()}"
        except OSError:
            continue
    return None


def format_wikipedia_moment() -> str | None:
    """Wikipedia On This Day — real API only; None if unavailable."""
    lang = os.environ.get("WIKIPEDIA_ON_THIS_DAY_LANG", "en").strip() or "en"
    ev = fetch_on_this_day(lang=lang)
    if not ev:
        return None
    y = f"{ev.year}: " if ev.year is not None else ""
    text = ev.text[:400] + ("…" if len(ev.text) > 400 else "")
    lines = [f"⏳ {y}{text}"]
    if ev.url:
        lines.append(f"📖 {ev.url}")
    return "\n".join(lines)


def score_discovery(title: str, source: str, category: str) -> float:
    """
    Score discovery relevance (0-10).
    Higher = more important. Filter > 7.5 for morning briefing.
    """
    score = 7.5  # Default: good signal
    
    # Boost major topics
    major_keywords = [
        "iran", "khamenei", "geopolitical",
        "aws", "outage", "infrastructure",
        "ios", "security", "vulnerability",
        "claude", "api", "anthropic",
        "breakthrough", "discovery",
    ]
    for keyword in major_keywords:
        if keyword.lower() in title.lower():
            score = 9.0
            break
    
    # Penalize low-signal sources/topics
    low_signal = [
        "random", "tweet", "meme", "spam",
        "reddit comment", "discussion",
    ]
    for phrase in low_signal:
        if phrase.lower() in (title.lower() or source.lower()):
            score = 4.0
            break
    
    # Boost trusted sources
    trusted_sources = ["france 24", "bbc", "ars technica", "github", "arxiv"]
    for trusted in trusted_sources:
        if trusted.lower() in source.lower():
            score = min(10.0, score + 0.5)
    
    return score


def parse_curiosity_files() -> list:
    """
    Extract discoveries from today's (or recent days') Curiosity files.
    Format: ## N. Title / **Source:** ... / **Résumé:** ...
    Returns: [(title, source, category, score), ...]
    
    Fallback to yesterday, then 2 days ago if today's files don't exist.
    Knowledge-consolidator runs at 23:30, so morning briefing (08:00) gets yesterday's data.
    """
    discoveries = []
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = datetime.fromtimestamp(datetime.now().timestamp() - 86400).strftime("%Y-%m-%d")
    day_before = datetime.fromtimestamp(datetime.now().timestamp() - 172800).strftime("%Y-%m-%d")
    
    categories = ["tech_news", "tech", "latest", "geopolitics", "culture", "community"]
    
    # Try yesterday first (knowledge-consolidator runs at 23:30),
    # then today (in case running late), then day before
    for date_str in [yesterday, today, day_before]:
        found_any = False
        
        for cat in categories:
            p = MEMORY_DIR / f"{date_str}-{cat}.md"
            if not p.exists():
                continue
            
            found_any = True
            
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                # ## 1. Title / ## 1) Title / ##1. Title
                items = re.split(r"^##\s*\d+[\.)]?\s+", content, flags=re.MULTILINE)[1:]
                
                for item in items:
                    lines = item.split('\n')
                    if not lines:
                        continue
                    
                    title = lines[0].strip()
                    source = cat  # Default
                    
                    for line in lines:
                        msrc = re.match(
                            r"^\s*\*\*Source\s*:\s*\**\s*(.+?)\s*$",
                            line.strip(),
                            re.I,
                        )
                        if msrc:
                            source = msrc.group(1).strip().rstrip(".")
                            break
                        if "source" in line.lower() and ":" in line and "**" in line:
                            source = re.sub(
                                r"(?i)^\s*\*\*Source\s*:\**\s*",
                                "",
                                line.strip(),
                            ).strip().rstrip(".")
                            break
                    
                    # Clean up source (remove links, keep just text)
                    source = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', source)
                    source = source[:50]  # Limit length
                    
                    if len(title) > 3:
                        score = score_discovery(title, source, cat)
                        if score > 7.5:  # Filter threshold
                            discoveries.append({
                                "title": title,
                                "source": source,
                                "category": cat,
                                "score": score,
                            })
            except Exception as e:
                continue
        
        # If we found files for this date, stop trying older dates
        if found_any and discoveries:
            break
    
    # Sort by score (descending), then category
    discoveries.sort(key=lambda x: (-x["score"], x["category"]))
    return discoveries[:5]  # Top 5


def format_discoveries(discoveries: list) -> str:
    """Format top discoveries for briefing."""
    if not discoveries:
        return ""
    
    lines = ["", "🌟 Top Discoveries (Curiosity 48h+):"]
    for i, d in enumerate(discoveries[:3], 1):  # Top 3 for briefing
        emoji = {
            "tech": "🔧",
            "tech_news": "🔧",
            "latest": "📰",
            "geopolitics": "🌍",
            "culture": "🎭",
            "community": "💬",
        }.get(d["category"], "⭐")
        
        # Shorten title if needed
        title = d["title"]
        if len(title) > 60:
            title = title[:57] + "…"
        
        lines.append(f"{i}. {emoji} {title} ({d['source']})")
    
    return "\n".join(lines)


def build_briefing():
    now = datetime.now()
    date_str = now.strftime("%d/%m")

    lines = [f"🌅 {date_str} — Bonjour Ldom"]

    sys_line = get_system_line()
    if sys_line:
        lines.append(sys_line)

    news = get_news_headline()
    if news:
        lines.append(news)

    tech = get_tech_headline()
    if tech:
        lines.append(tech)

    wiki = format_wikipedia_moment()
    if wiki:
        lines.append(wiki)

    # NEW: Add top discoveries from Curiosity
    discoveries = parse_curiosity_files()
    if discoveries:
        discovery_section = format_discoveries(discoveries)
        lines.append(discovery_section)

    lines.append(f"🔗 {get_hub_url()}")
    return "\n".join(lines)


def send_telegram(text: str) -> bool:
    """Send briefing to Telegram via OpenClaw CLI (fire-and-forget in background)."""
    try:
        import subprocess
        
        # Fire-and-forget: send to Telegram in background without waiting
        # This avoids timeout issues with the gateway
        # Only send the BRIEFING (important output), not process start/end messages
        if not TELEGRAM_TARGET_ID:
            print("⚠️ TELEGRAM_TARGET_ID not set. Briefing generated (local only).", file=sys.stderr)
            return True
        process = subprocess.Popen([
            'openclaw', 'message', 'send',
            '--channel', 'telegram',
            '--target', TELEGRAM_TARGET_ID,
            '--message', text
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Don't wait for response; assume it will deliver asynchronously
        # Log to dombot-logger + Slack instead of printing
        import subprocess as sp
        sp.run([
            'uv', 'run', '--directory', os.path.expanduser('~/.openclaw/skills/logger/core'),
            'dombot-log', 'INFO', 'cron:morning-briefing', 'system', 'message:sent',
            'Morning briefing sent to Telegram'
        ], capture_output=True, timeout=5)
        return True
    except FileNotFoundError:
        # openclaw command not found; fallback to just printing
        print("⚠️ openclaw CLI not found. Briefing generated (local only).", file=sys.stderr)
        return True  # Don't fail; briefing is still useful locally
    except Exception as e:
        print(f"⚠️ Telegram send error: {e}. Briefing generated.", file=sys.stderr)
        return True  # Don't fail; briefing is still useful


def main():
    os.chdir(WORKSPACE)
    briefing = build_briefing()
    
    # Always print briefing (for inspection + logging)
    print(briefing)
    
    # Send to Telegram (async, non-blocking)
    send_telegram(briefing)
    
    # Always exit 0; briefing was generated successfully
    sys.exit(0)


if __name__ == "__main__":
    main()
