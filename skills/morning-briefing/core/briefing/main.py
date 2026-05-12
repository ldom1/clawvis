"""
Morning Briefing — Curiosity + system metrics + Wikipedia.
Sends to Telegram via Clawvis telegram service HTTP (/send).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from briefing.wikipedia_on_this_day import fetch_on_this_day


def _clawvis_root() -> Path | None:
    raw = os.environ.get("CLAWVIS_ROOT", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    for p in (Path.home() / "lab" / "clawvis", Path.home() / "Lab" / "clawvis"):
        if (p / "hub-core").is_dir():
            return p.resolve()
    return None


def _memory_root() -> Path:
    m = os.environ.get("MEMORY_ROOT", "").strip()
    cr = _clawvis_root()
    if m:
        p = Path(m).expanduser()
        if cr is not None and not p.is_absolute():
            p = cr / p
        return p.resolve()
    inst = os.environ.get("INSTANCE_NAME", "example").strip() or "example"
    if cr is not None:
        return (cr / "instances" / inst / "memory").resolve()
    return (Path.home() / "lab" / "clawvis" / "instances" / inst / "memory").resolve()


def _hub_root() -> Path:
    h = os.environ.get("HUB_ROOT", "").strip()
    if h:
        return Path(h).expanduser().resolve()
    cr = _clawvis_root()
    if cr is not None and (cr / "hub" / "public" / "api" / "system.json").is_file():
        return cr / "hub"
    return Path.home() / "Lab" / "hub-ldom" / "instances" / "ldom"


MEMORY_DIR = _memory_root() / "resources" / "curiosity"
_HUB_ROOT = _hub_root()
SYSTEM_JSON = _HUB_ROOT / "public" / "api" / "system.json"
CF_URL_FILE = _HUB_ROOT / "DOMBOT_TECH_URL.txt"


def get_hub_url():
    """Get Cloudflare tunnel URL, fallback to localhost."""
    try:
        if CF_URL_FILE.exists():
            url = CF_URL_FILE.read_text().strip()
            if url:
                return url
    except OSError:
        pass
    return "http://localhost:8088"


def get_system_line():
    try:
        data = json.loads(SYSTEM_JSON.read_text())
        cpu, ram, disk = data["cpu_percent"], data["ram_percent"], data["disk_percent"]
        alert = ""
        if disk > 90:
            alert = " 🔴"
        elif disk > 80 or ram > 85:
            alert = " ⚠️"
        return f"⚙️ CPU {cpu}% · RAM {ram}% · Disk {disk}%{alert}"
    except (OSError, json.JSONDecodeError, KeyError):
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
    """Score discovery relevance; filter with score > 7.5 in parse_curiosity_files."""
    score = 8.0
    low_signal = [
        "random",
        "tweet",
        "meme",
        "spam",
        "reddit comment",
        "discussion",
    ]
    blob = f"{title} {source}".lower()
    for phrase in low_signal:
        if phrase in blob:
            return 4.0
    return score


def parse_curiosity_files() -> list:
    """
    Extract discoveries from today's (or recent days') Curiosity files.
    Fallback to yesterday, then 2 days ago if today's files don't exist.
    """
    discoveries = []
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = datetime.fromtimestamp(datetime.now().timestamp() - 86400).strftime("%Y-%m-%d")
    day_before = datetime.fromtimestamp(datetime.now().timestamp() - 172800).strftime("%Y-%m-%d")

    categories = ["tech_news", "tech", "latest", "geopolitics", "culture", "community"]

    for date_str in [yesterday, today, day_before]:
        found_any = False

        for cat in categories:
            p = MEMORY_DIR / f"{date_str}-{cat}.md"
            if not p.exists():
                continue

            found_any = True

            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                items = re.split(r"^##\s*\d+[\.)]?\s+", content, flags=re.MULTILINE)[1:]

                for item in items:
                    lines = item.split("\n")
                    if not lines:
                        continue

                    title = lines[0].strip()
                    source = cat

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

                    source = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", source)
                    source = source[:50]

                    if len(title) > 3:
                        sc = score_discovery(title, source, cat)
                        if sc > 7.5:
                            discoveries.append({
                                "title": title,
                                "source": source,
                                "category": cat,
                                "score": sc,
                            })
            except OSError:
                continue

        if found_any and discoveries:
            break

    discoveries.sort(key=lambda x: (-x["score"], x["category"]))
    return discoveries[:5]


def format_discoveries(discoveries: list) -> str:
    if not discoveries:
        return ""

    lines = ["", "🌟 Top Discoveries (Curiosity 48h+):"]
    for i, d in enumerate(discoveries[:3], 1):
        emoji = {
            "tech": "🔧",
            "tech_news": "🔧",
            "latest": "📰",
            "geopolitics": "🌍",
            "culture": "🎭",
            "community": "💬",
        }.get(d["category"], "⭐")

        title = d["title"]
        if len(title) > 60:
            title = title[:57] + "…"

        lines.append(f"{i}. {emoji} {title} ({d['source']})")

    return "\n".join(lines)


def build_briefing():
    date_str = datetime.now().strftime("%d/%m")

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

    discoveries = parse_curiosity_files()
    if discoveries:
        lines.append(format_discoveries(discoveries))

    lines.append(f"🔗 {get_hub_url()}")
    return "\n".join(lines)


def _logger_core() -> Path | None:
    cr = _clawvis_root()
    for base in ([cr] if cr else []) + [Path.home() / "lab" / "clawvis", Path.home() / "Lab" / "clawvis"]:
        if base is None:
            continue
        c = base / "skills" / "logger" / "core"
        if c.is_dir():
            return c
    return None


def send_telegram(text: str) -> bool:
    """POST briefing to Clawvis telegram /send (TELEGRAM_URL, default http://127.0.0.1:8094)."""
    url = os.environ.get("TELEGRAM_URL", "http://127.0.0.1:8094").rstrip("/") + "/send"
    body = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status != 200:
                print(
                    f"⚠️ Telegram /send HTTP {resp.status}. Briefing printed locally.",
                    file=sys.stderr,
                )
                return True
    except (urllib.error.URLError, OSError) as e:
        print(f"⚠️ Telegram send failed ({e}). Briefing generated locally.", file=sys.stderr)
        return True
    lc = _logger_core()
    if lc:
        subprocess.run(
            [
                "uv",
                "run",
                "--directory",
                str(lc),
                "dombot-log",
                "INFO",
                "cron:morning-briefing",
                "system",
                "message:sent",
                "Morning briefing sent to Telegram",
            ],
            capture_output=True,
            timeout=10,
        )
    return True


def main() -> None:
    cr = _clawvis_root()
    if cr is not None:
        os.chdir(cr)
    briefing = build_briefing()
    print(briefing)
    send_telegram(briefing)
    sys.exit(0)
