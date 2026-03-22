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


def get_tech_headline():
    today = datetime.now().strftime("%Y-%m-%d")
    for suffix in ["tech_news", "tech"]:
        p = MEMORY_DIR / f"{today}-{suffix}.md"
        if not p.exists():
            continue
        try:
            for line in p.read_text().split("\n"):
                if line.startswith("## "):
                    title = line.lstrip("# ").strip()
                    if title[0].isdigit():
                        title = ". ".join(title.split(". ")[1:])
                    return f"🔧 {title}"
        except Exception:
            continue
    return None


def get_news_headline():
    today = datetime.now().strftime("%Y-%m-%d")
    p = MEMORY_DIR / f"{today}-latest.md"
    if not p.exists():
        return None
    try:
        for line in p.read_text().split("\n"):
            if line.startswith("## 1"):
                return f"📰 {line.replace('## 1.', '').strip()}"
    except Exception:
        pass
    return None


def get_wikipedia_line():
    try:
        import requests
        now = datetime.now()
        url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/events/{now.month}/{now.day}"
        data = requests.get(url, timeout=5).json()
        ev = data.get("events", [{}])[0]
        return f"⏳ {ev['year']}: {ev['text'][:80]}"
    except Exception:
        return None


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
                content = p.read_text()
                
                # Parse: ## N. Title ... **Source:** ... **Résumé:** ...
                items = re.split(r'^##\s+\d+\.\s+', content, flags=re.MULTILINE)[1:]  # Skip header
                
                for item in items:
                    lines = item.split('\n')
                    if not lines:
                        continue
                    
                    title = lines[0].strip()
                    source = cat  # Default
                    
                    # Find **Source:** line (may have extra formatting)
                    for line in lines:
                        if 'Source' in line:
                            # Extract: "**Source :** GitHub Trending" → "GitHub Trending"
                            source = re.sub(r'\*\*Source\s*:\s*\*\*', '', line).strip()
                            source = source.rstrip('.')
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

    wiki = get_wikipedia_line()
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
