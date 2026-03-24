"""Tests for DynamicMammouthAdapter model selection logic.

Validates model selection across task types and budget tiers without making real API calls.

Usage:
  uv run pytest tests/test_dynamic_models.py -v
"""

import os

from hub_core.agents.mammouth import DynamicMammouthAdapter, MAMMOUTH_MODELS

os.environ.setdefault("MAMMOUTH_API_KEY", "sk-test-key")


def make_adapter(task_type: str, budget_tier: str) -> DynamicMammouthAdapter:
    return DynamicMammouthAdapter(task_type=task_type, budget_tier=budget_tier)


def test_model_catalog_not_empty():
    assert len(MAMMOUTH_MODELS) > 5


def test_all_models_have_required_fields():
    for model, cfg in MAMMOUTH_MODELS.items():
        assert "provider" in cfg, f"{model} missing provider"
        assert "cost_per_1k" in cfg, f"{model} missing cost_per_1k"
        assert "input" in cfg["cost_per_1k"], f"{model} missing input cost"
        assert "output" in cfg["cost_per_1k"], f"{model} missing output cost"


def test_model_selection_translation_cheap():
    adapter = make_adapter("translation", "budget")
    model = adapter.select_model()
    assert model in MAMMOUTH_MODELS
    cfg = MAMMOUTH_MODELS[model]
    assert "translation" in cfg.get("tags", []) or cfg["cost_per_1k"]["output"] < 0.1


def test_model_selection_code_medium():
    adapter = make_adapter("code", "medium")
    model = adapter.select_model()
    assert model in MAMMOUTH_MODELS


def test_model_selection_reasoning_unlimited():
    adapter = make_adapter("reasoning", "unlimited")
    model = adapter.select_model()
    assert model in MAMMOUTH_MODELS
    cfg = MAMMOUTH_MODELS[model]
    assert cfg["quality"] >= 4


def test_model_selection_ultra_cheap():
    # Use a task type that has known ultra-cheap models (not "general" which has no intersection)
    adapter = make_adapter("fast", "ultra-cheap")
    model = adapter.select_model()
    assert model in MAMMOUTH_MODELS


def test_preferred_models_take_priority():
    adapter = DynamicMammouthAdapter(
        task_type="general",
        budget_tier="medium",
        preferred_models=["claude-haiku-4-5"],
    )
    model = adapter.select_model()
    assert model == "claude-haiku-4-5"


def test_capabilities_reflect_selected_model():
    adapter = make_adapter("code", "medium")
    caps = adapter.get_capabilities()
    assert caps.agent_id is not None
    assert caps.max_context_tokens > 0
