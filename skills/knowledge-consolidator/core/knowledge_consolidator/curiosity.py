"""Curiosity agent: fetch external knowledge, save to memory/resources/curiosity/."""

from __future__ import annotations

import html
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

DOMBOT_MAIL_CORE = Path.home() / ".openclaw" / "skills" / "dombot-mail" / "core"

from knowledge_consolidator.logging import log_info, log_warning

UA = "Mozilla/5.0 (compatible; DomBot-Curiosity/1.0)"
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory" / "resources" / "curiosity"


def _log(level: str, action: str, message: str) -> None:
    if level == "WARN":
        log_warning(action, message)
    else:
        log_info(action, message)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {message}")


class CuriosityAgent:
    def __init__(self, session_type: str) -> None:
        self.session_type = session_type
        self.discoveries: list[dict[str, Any]] = []
        self.memory_dir = MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, level: str = "INFO") -> None:
        _log(level, f"curiosity:{self.session_type}", message)

    def _curl(self, url: str, timeout: int = 12) -> str:
        try:
            r = subprocess.run(
                ["curl", "-s", "-m", str(timeout), "-L", "-A", UA, url],
                capture_output=True,
                timeout=timeout + 3,
                check=False,
            )
            if r.returncode == 0 and r.stdout:
                for enc in ("utf-8", "latin-1", "cp1252"):
                    try:
                        return r.stdout.decode(enc)
                    except UnicodeDecodeError:
                        continue
                return r.stdout.decode("utf-8", errors="replace")
        except Exception as e:
            self.log(f"curl failed for {url}: {e}", "WARN")
        return ""

    def fetch_json(self, url: str, timeout: int = 12) -> Any:
        raw = self._curl(url, timeout)
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            self.log(f"JSON parse failed for {url}: {e}", "WARN")
            return {}

    def fetch_rss(self, url: str, source: str, n: int = 3) -> list[dict[str, Any]]:
        self.log(f"Fetching RSS: {source}")
        raw = self._curl(url, timeout=15)
        if not raw:
            return []
        raw = re.sub(
            r"<!\[CDATA\[(.*?)\]\]>",
            lambda m: m.group(1)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"),
            raw,
            flags=re.DOTALL,
        )
        raw = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#\w+;)", "&amp;", raw)
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as e:
            self.log(f"RSS parse error for {source}: {e}", "WARN")
            return []
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//item") or root.findall(".//atom:entry", ns)
        results = []
        for item in items[:n]:
            title = (
                item.findtext("title") or item.findtext("atom:title", namespaces=ns) or ""
            ).strip()
            link_el = item.find("atom:link", ns)
            link = (
                item.findtext("link")
                or (link_el.get("href", "") if link_el is not None else "")
                or ""
            ).strip()
            desc = (
                item.findtext("description")
                or item.findtext("atom:summary", namespaces=ns)
                or ""
            ).strip()[:250]
            if title:
                results.append({
                    "title": title,
                    "source": source,
                    "url": link,
                    "summary": desc,
                    "relevance_score": 7.0,
                    "learned": f"Découverte via {source}",
                })
        self.log(f"Found {len(results)} items from {source}")
        return results

    def fetch_github_trending(self, topic: str = "ai") -> list[dict[str, Any]]:
        self.log(f"Fetching GitHub trending (topic={topic})")
        data = self.fetch_json(
            f"https://api.github.com/search/repositories"
            f"?q=topic:{topic}&sort=stars&order=desc&per_page=5"
        )
        results = []
        for r in data.get("items", [])[:3]:
            results.append({
                "title": r.get("name", ""),
                "source": "GitHub Trending",
                "url": r.get("html_url", ""),
                "summary": r.get("description", ""),
                "relevance_score": min(r.get("stargazers_count", 0) / 1000, 10),
                "learned": f"⭐ {r.get('stargazers_count', 0)} stars — {r.get('language', '')}",
            })
        self.log(f"Found {len(results)} GitHub repos")
        return results

    def fetch_dev_to(self) -> list[dict[str, Any]]:
        self.log("Fetching Dev.to top articles")
        data = self.fetch_json("https://dev.to/api/articles?per_page=5&top=1")
        articles = data if isinstance(data, list) else []
        results = []
        for a in articles[:3]:
            results.append({
                "title": a.get("title", ""),
                "source": "Dev.to",
                "url": a.get("url", ""),
                "summary": a.get("description", ""),
                "relevance_score": min(a.get("positive_reactions_count", 0) / 100, 10),
                "learned": f"Tags: {', '.join(a.get('tag_list', [])[:3])}",
            })
        self.log(f"Found {len(results)} Dev.to articles")
        return results

    def fetch_wikipedia_onthisday(self, lang: str = "en") -> list[dict[str, Any]]:
        self.log(f"Fetching Wikipedia On This Day ({lang})")
        data = self.fetch_json(
            f"https://{lang}.wikipedia.org/api/rest_v1/feed/onthisday/events/"
            f"{datetime.now().month:02d}/{datetime.now().day:02d}"
        )
        results = []
        for event in data.get("events", [])[:3]:
            page = (event.get("pages") or [{}])[0]
            title = event.get("text", "")
            if title:
                results.append({
                    "title": title,
                    "source": f"Wikipedia On This Day ({lang.upper()})",
                    "url": page.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    "summary": f"An {event.get('year', '?')}: {title}",
                    "relevance_score": 7.5,
                    "learned": "Le contexte historique éclaire le présent",
                })
        self.log(f"Found {len(results)} Wikipedia events")
        return results

    def fetch_wikipedia_featured(self, lang: str = "fr") -> dict[str, Any] | None:
        self.log(f"Fetching Wikipedia featured article ({lang})")
        d = datetime.now()
        data = self.fetch_json(
            f"https://{lang}.wikipedia.org/api/rest_v1/feed/featured"
            f"/{d.year}/{d.month:02d}/{d.day:02d}"
        )
        tfa = data.get("tfa", {})
        if not tfa:
            return None
        return {
            "title": tfa.get("displaytitle", tfa.get("title", "")),
            "source": f"Wikipedia Article du jour ({lang.upper()})",
            "url": tfa.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "summary": tfa.get("extract", "")[:300],
            "relevance_score": 8.5,
            "learned": "Article mis en lumière par la communauté Wikipédia",
        }

    def fetch_gutenberg_popular(self) -> list[dict[str, Any]]:
        self.log("Fetching Gutenberg popular books")
        data = self.fetch_json("https://gutendex.com/books/?sort=popular")
        results = []
        for b in data.get("results", [])[:3]:
            authors = ", ".join(a["name"] for a in b.get("authors", [])[:2])
            results.append({
                "title": b.get("title", ""),
                "source": "Project Gutenberg",
                "url": f"https://www.gutenberg.org/ebooks/{b.get('id', '')}",
                "summary": f"Par {authors}" if authors else "",
                "relevance_score": 7.0,
                "learned": "Littérature classique en accès libre",
            })
        self.log(f"Found {len(results)} Gutenberg books")
        return results

    def fetch_france24_culture(self) -> list[dict[str, Any]]:
        return self.fetch_rss(
            "https://www.france24.com/fr/culture/rss", "France 24 Culture", n=3
        )

    def fetch_figaro_culture(self) -> list[dict[str, Any]]:
        return self.fetch_rss(
            "https://www.lefigaro.fr/rss/figaro_culture.xml", "Le Figaro Culture", n=3
        )

    def fetch_openculture(self) -> list[dict[str, Any]]:
        return self.fetch_rss("https://www.openculture.com/feed", "Open Culture", n=3)

    def fetch_lemonde_culture(self) -> list[dict[str, Any]]:
        return self.fetch_rss(
            "https://www.lemonde.fr/culture/rss_full.xml", "Le Monde Culture", n=3
        )

    def fetch_latest_news(self) -> list[dict[str, Any]]:
        return self.fetch_rss(
            "https://www.france24.com/fr/rss", "France 24", n=3
        ) + self.fetch_rss(
            "https://feeds.bbci.co.uk/news/world/rss.xml", "BBC World", n=3
        )

    def fetch_tldr_tech(self) -> list[dict[str, Any]]:
        return self.fetch_rss("https://tldr.tech/newsletter/rss", "TLDR Tech", n=5)

    def fetch_tech_news(self) -> list[dict[str, Any]]:
        items = self.fetch_tldr_tech()
        if not items:
            items = self.fetch_rss(
                "https://feeds.arstechnica.com/arstechnica/technology-lab",
                "Ars Technica",
                n=5,
            )
        return items

    def _run_dombot_mail(self, *args: str) -> str:
        cmd = ["uv", "run", "--directory", str(DOMBOT_MAIL_CORE), "dombot-mail", *args]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
            return r.stdout or ""
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.log(f"dombot-mail not available: {e}", "WARN")
            return ""

    def _fetch_and_archive_mail(self, limit_per_folder: int = 10) -> Path | None:
        """Fetch mails from INBOX + Promotions (and SocialNetworks), save to curiosity, archive."""
        if not DOMBOT_MAIL_CORE.exists() or not (DOMBOT_MAIL_CORE / "pyproject.toml").exists():
            self.log("dombot-mail skill not found, skip mail collect", "WARN")
            return None
        out = self._run_dombot_mail("list-inbox", "--limit", str(limit_per_folder))
        if not out.strip():
            return None
        try:
            data = json.loads(out)
        except json.JSONDecodeError as e:
            self.log(f"list-inbox JSON error: {e}", "WARN")
            return None
        by_folder = data.get("by_folder") or {}
        lines = [
            f"# Mail · {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            f"**Folders:** INBOX, Promotions, SocialNetworks",
            "",
            "---",
            "",
        ]
        archived = 0
        for folder, list_result in by_folder.items():
            if not list_result.get("ok") or not list_result.get("messages"):
                continue
            for msg in list_result["messages"]:
                uid = msg.get("uid")
                if not uid:
                    continue
                read_out = self._run_dombot_mail("read", "--folder", folder, "--uid", uid)
                try:
                    read_data = json.loads(read_out) if read_out.strip() else {}
                except json.JSONDecodeError:
                    read_data = {}
                body = (read_data.get("message") or {}).get("text") or (read_data.get("message") or {}).get("snippet") or msg.get("snippet", "")
                if len(body) > 2000:
                    body = body[:2000] + "\n...[truncated]..."
                lines.append(f"## [{folder}] {msg.get('subject', 'No subject')}")
                lines.append("")
                lines.append(f"- **From:** {msg.get('sender', '')}  ")
                lines.append(f"- **Date:** {msg.get('date', '')}  ")
                lines.append("")
                lines.append(body.replace("\r", "").strip())
                lines.append("")
                lines.append("---")
                lines.append("")
                ar = self._run_dombot_mail("archive", "--folder", folder, "--uid", uid)
                try:
                    if ar.strip() and json.loads(ar).get("ok"):
                        archived += 1
                except json.JSONDecodeError:
                    pass
        if archived == 0 and not any(
            (list_result.get("messages") for list_result in by_folder.values())
        ):
            return None
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = self.memory_dir / f"{date_str}-mail.md"
        filename.write_text("\n".join(lines), encoding="utf-8")
        self.log(f"Saved {archived} archived mails to {filename}")
        return filename

    def fetch_reddit(self, subreddit: str) -> list[dict[str, Any]]:
        self.log(f"Fetching Reddit r/{subreddit}")
        data = self.fetch_json(
            f"https://www.reddit.com/r/{subreddit}/top.json?t=day&limit=5",
            timeout=15,
        )
        results = []
        for post_wrapper in data.get("data", {}).get("children", [])[:3]:
            post = post_wrapper.get("data", {})
            title = post.get("title", "")
            if title:
                results.append({
                    "title": title,
                    "source": f"Reddit r/{subreddit}",
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "summary": post.get("selftext", "")[:200],
                    "relevance_score": min(post.get("score", 0) / 1000, 10),
                    "learned": "Community insights from peer discussions",
                })
        self.log(f"Found {len(results)} posts from r/{subreddit}")
        return results

    def collect(self) -> list[dict[str, Any]]:
        self.log(f"Starting collection for session: {self.session_type}")
        raw: list[dict[str, Any]] = []
        if self.session_type == "mail":
            self._fetch_and_archive_mail()
            self.discoveries = []
            return []
        if self.session_type == "tech":
            raw = (
                self.fetch_github_trending("ai")
                + self.fetch_github_trending("devops")
                + self.fetch_dev_to()
            )
        elif self.session_type == "geopolitics":
            raw = (
                self.fetch_wikipedia_onthisday("en")
                + self.fetch_wikipedia_onthisday("fr")
                + self.fetch_reddit("worldnews")
                + self.fetch_reddit("geopolitics")
            )
        elif self.session_type == "culture":
            featured = self.fetch_wikipedia_featured("fr")
            if featured:
                raw.append(featured)
            raw += (
                self.fetch_france24_culture()
                + self.fetch_figaro_culture()
                + self.fetch_gutenberg_popular()
                + self.fetch_openculture()
                + self.fetch_lemonde_culture()
            )
        elif self.session_type == "community":
            raw = (
                self.fetch_reddit("ClaudeAI")
                + self.fetch_reddit("LocalLLaMA")
                + self.fetch_reddit("MachineLearning")
            )
        elif self.session_type == "latest":
            raw = self.fetch_latest_news()
        elif self.session_type == "tech_news":
            raw = self.fetch_tech_news()

        raw = [d for d in raw if d and d.get("title")]
        raw.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        self.discoveries = raw[:5]
        self.log(f"Consolidated {len(self.discoveries)} discoveries")
        return self.discoveries

    def save_to_memory(self) -> Path:
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M")
        filename = self.memory_dir / f"{date_str}-{self.session_type}.md"
        lines = [
            f"# Curiosity · {self.session_type.title()} · {date_str} {time_str}",
            "",
            f"**Session:** {self.session_type} | **Découvertes:** {len(self.discoveries)}",
            "",
            "---",
            "",
        ]
        if not self.discoveries:
            lines.append("*Aucune découverte cette session.*")
        else:
            for i, d in enumerate(self.discoveries, 1):
                lines.append(f"## {i}. {d.get('title', 'Sans titre')}")
                lines.append("")
                lines.append(f"**Source :** {d.get('source', '?')}  ")
                if d.get("url"):
                    lines.append(f"**Lien :** <{d['url']}>  ")
                if d.get("summary"):
                    clean = html.unescape(d["summary"]).replace("\n", " ").strip()
                    lines.append(f"**Résumé :** {clean}  ")
                if d.get("learned"):
                    lines.append(f"**Insight :** {d['learned']}  ")
                lines.append("")
        filename.write_text("\n".join(lines), encoding="utf-8")
        self.log(f"Saved to {filename}")
        return filename

    def update_memory_md(self) -> None:
        if not self.discoveries:
            return
        memory_file = WORKSPACE / "MEMORY.md"
        section = (
            f"\n## 🌟 Curiosity · {self.session_type.title()} · "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            + "\n".join(
                f"- **{d['title']}** ({d.get('source', '?')}) → <{d.get('url', '#')}>"
                for d in self.discoveries[:3]
            )
            + f"\n\n> {self.discoveries[0].get('learned', '')}\n"
        )
        try:
            with open(memory_file, "a", encoding="utf-8") as f:
                f.write(section)
            self.log("Updated MEMORY.md")
        except OSError as e:
            self.log(f"MEMORY.md update failed: {e}", "WARN")

    def run(self) -> None:
        self.log(f"Starting Curiosity Agent ({self.session_type})")
        if self.session_type == "mail":
            self._fetch_and_archive_mail()
            self.log("✅ Mail collect complete")
            return
        self.collect()
        self.save_to_memory()
        self.update_memory_md()
        self.log(f"✅ Complete: {len(self.discoveries)} discoveries")
