"""Tests for hub_core.fetch.provider_data (Mammouth only)."""

from unittest.mock import patch


from hub_core.fetch.provider_data import get_providers_response
from hub_core.models import MammouthUsage, ProvidersResponse


@patch("hub_core.fetch.provider_data.get_mammouth_credits")
def test_get_providers_response_structure(mock_mammouth):
    mock_mammouth.return_value = MammouthUsage()
    r = get_providers_response(write=False)
    assert isinstance(r, ProvidersResponse)
    assert r.mammouth_ai is not None
    assert "timestamp" in r.timestamp or r.timestamp
