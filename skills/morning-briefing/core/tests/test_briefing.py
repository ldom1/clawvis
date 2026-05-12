"""Tests for morning-briefing skill package."""
from datetime import datetime, timedelta
from pathlib import Path

from briefing.main import parse_curiosity_files, score_discovery


def test_briefing_package_importable():
    import briefing

    assert briefing.__doc__


def test_wikipedia_module_importable():
    from briefing.wikipedia_on_this_day import fetch_on_this_day

    assert callable(fetch_on_this_day)


def test_briefing_template_exists():
    template = Path(__file__).parent.parent.parent / "BRIEFING_TEMPLATE.md"
    assert template.exists(), f"Template not found: {template}"


def test_score_discovery_default_passes_filter():
    assert score_discovery("Some real title", "src", "tech") > 7.5


def test_score_discovery_low_signal():
    assert score_discovery("random tweet thread", "x", "tech") <= 7.5


def test_parse_curiosity_files_reads_yesterday_file(tmp_path, monkeypatch):
    y = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    cur = tmp_path / "curiosity"
    cur.mkdir(parents=True)
    f = cur / f"{y}-tech.md"
    f.write_text(
        "## 1. Quantum paper published\n\n**Source:** arXiv\n\nSummary here.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("briefing.main.MEMORY_DIR", cur)
    out = parse_curiosity_files()
    assert len(out) >= 1
    assert "Quantum" in out[0]["title"]
