"""TDD: confidence field on Task model (Kahneman-inspired 0-1 scale)."""
import pytest
from pydantic import ValidationError
from kanban_api.models import Task, TaskCreate, TaskUpdate


def make_task(**kw):
    return Task(id="test-1", title="Test task", **kw)


def test_task_confidence_none_by_default():
    assert make_task().confidence is None


def test_task_confidence_valid():
    assert make_task(confidence=0.75).confidence == 0.75


def test_task_confidence_zero():
    assert make_task(confidence=0.0).confidence == 0.0


def test_task_confidence_one():
    assert make_task(confidence=1.0).confidence == 1.0


def test_task_confidence_above_one_rejected():
    with pytest.raises(ValidationError):
        make_task(confidence=1.01)


def test_task_confidence_below_zero_rejected():
    with pytest.raises(ValidationError):
        make_task(confidence=-0.01)


def test_task_create_has_confidence():
    tc = TaskCreate(title="T", confidence=0.8)
    assert tc.confidence == 0.8


def test_task_create_confidence_default_none():
    assert TaskCreate(title="T").confidence is None


def test_task_update_confidence():
    assert TaskUpdate(confidence=0.3).confidence == 0.3


def test_task_update_confidence_default_none():
    assert TaskUpdate().confidence is None


def test_blocked_status_is_valid():
    from kanban_api.models import Task
    t = Task(id="x", title="T", status="Blocked")
    assert t.status == "Blocked"


def test_blocked_status_in_statuses_list():
    from kanban_api.models import STATUSES
    from kanban_api.core import STATUSES as CORE_STATUSES
    assert "Blocked" in STATUSES
    assert "Blocked" in CORE_STATUSES
    # Blocked doit être entre In Progress et Review
    idx_blocked = STATUSES.index("Blocked")
    idx_ip = STATUSES.index("In Progress")
    idx_review = STATUSES.index("Review")
    assert idx_ip < idx_blocked < idx_review
    # Same check for core (now they're the same object since imported)
    assert STATUSES is CORE_STATUSES  # unified — same object


def test_blocked_skips_dependency_check():
    """Passer en Blocked ne déclenche pas _check_dependencies."""
    from kanban_api.core import _check_dependencies, DependencyBlockedError
    data = {
        "tasks": [
            {"id": "dep-1", "title": "Dep", "status": "To Start"},
        ]
    }
    task = {"id": "t-1", "title": "T", "dependencies": ["dep-1"]}
    # Ne doit pas lever DependencyBlockedError
    try:
        _check_dependencies(data, task, "Blocked")
    except DependencyBlockedError:
        pytest.fail("_check_dependencies levé pour status Blocked — ne doit pas arriver")
