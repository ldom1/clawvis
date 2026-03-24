"""Tests for hub_core.update.status."""

import json


from hub_core.models import StatusResponse


def test_status_response_na_serializes():
    s = StatusResponse()
    j = s.model_dump_json()
    d = json.loads(j)
    assert "mammouth_usage" in d
    assert "last_check" in d
