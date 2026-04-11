"""Smoke tests for morning-briefing skill."""
from pathlib import Path


def test_morning_briefing_script_exists():
    """Check that morning-briefing.py script exists."""
    script = Path(__file__).parent.parent.parent / 'morning-briefing.py'
    assert script.exists(), f'Script not found: {script}'


def test_wikipedia_on_this_day_script_exists():
    """Check that wikipedia_on_this_day.py script exists."""
    script = Path(__file__).parent.parent.parent / 'wikipedia_on_this_day.py'
    assert script.exists(), f'Script not found: {script}'


def test_briefing_template_exists():
    """Check that BRIEFING_TEMPLATE.md exists."""
    template = Path(__file__).parent.parent.parent / 'BRIEFING_TEMPLATE.md'
    assert template.exists(), f'Template not found: {template}'
