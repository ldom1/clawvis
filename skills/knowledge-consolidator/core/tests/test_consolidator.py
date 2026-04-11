"""Smoke tests for knowledge-consolidator skill."""
from pathlib import Path


def test_collect_script_exists():
    """Check that collect.sh script exists."""
    script = Path(__file__).parent.parent.parent / 'scripts' / 'collect.sh'
    assert script.exists(), f'Script not found: {script}'


def test_consolidate_script_exists():
    """Check that consolidate.sh script exists."""
    script = Path(__file__).parent.parent.parent / 'scripts' / 'consolidate.sh'
    assert script.exists(), f'Script not found: {script}'


def test_knowledge_consolidator_module_exists():
    """Check that knowledge_consolidator module directory exists."""
    module = Path(__file__).parent.parent / 'knowledge_consolidator'
    assert module.exists(), f'Module not found: {module}'
