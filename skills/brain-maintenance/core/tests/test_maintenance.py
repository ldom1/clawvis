"""Smoke tests for brain-maintenance skill."""
from pathlib import Path

from brain_maintenance.recalibrate import L1_NAMES, read_l1_files
from brain_maintenance.trim import L1_FILES, L1_TOTAL_BUDGET


def test_brain_maintenance_module_exists():
    """Check that brain_maintenance module directory exists."""
    module = Path(__file__).parent.parent / "brain_maintenance"
    assert module.exists(), f"Module not found: {module}"


def test_pyproject_exists():
    """Check that pyproject.toml exists in core."""
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    assert pyproject.exists(), f"pyproject.toml not found: {pyproject}"


def test_l1_trim_keys_are_clawvis_docs():
    expected = {"CLAUDE.md", "AGENTS.md", "README.md"}
    assert set(L1_FILES.keys()) == expected
    assert sum(L1_FILES.values()) <= L1_TOTAL_BUDGET


def test_l1_recalibrate_names_match_trim():
    assert set(L1_NAMES) == set(L1_FILES.keys())


def test_read_l1_files_returns_expected_keys():
    l1 = read_l1_files()
    for name in L1_NAMES:
        assert name in l1
