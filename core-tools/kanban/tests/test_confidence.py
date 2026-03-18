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
