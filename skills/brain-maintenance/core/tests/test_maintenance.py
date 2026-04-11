"""Smoke tests for brain-maintenance skill."""
from pathlib import Path


def test_brain_maintenance_module_exists():
    """Check that brain_maintenance module directory exists."""
    module = Path(__file__).parent.parent / 'brain_maintenance'
    assert module.exists(), f'Module not found: {module}'


def test_pyproject_exists():
    """Check that pyproject.toml exists in core."""
    pyproject = Path(__file__).parent.parent / 'pyproject.toml'
    assert pyproject.exists(), f'pyproject.toml not found: {pyproject}'
