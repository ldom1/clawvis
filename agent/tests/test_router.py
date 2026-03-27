# agent/tests/test_router.py
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_health():
    from agent_service.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
