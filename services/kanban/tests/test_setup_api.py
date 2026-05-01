import kanban_api.setup_api as setup_api
from fastapi.testclient import TestClient
from kanban_api.server import app


def test_setup_routes_in_openapi():
    paths = app.openapi()["paths"]
    assert "/setup/context" in paths
    assert "/setup/sync-skills" in paths
    assert "/setup/sync-memory" in paths
    assert "/setup/provider" in paths


def test_post_setup_provider_writes_env(tmp_path, monkeypatch):
    monkeypatch.setattr(setup_api, "_CLAWVIS_ROOT", tmp_path)
    client = TestClient(app)
    env_path = tmp_path / ".env"
    env_path.write_text("FOO=bar\n", encoding="utf-8")

    r = client.post("/setup/provider", json={"provider": "cli"})
    assert r.status_code == 200
    assert "PRIMARY_AI_PROVIDER=cli" in env_path.read_text(encoding="utf-8")


def test_post_setup_provider_invalid_400():
    client = TestClient(app)
    r = client.post("/setup/provider", json={"provider": "not-a-real-provider"})
    assert r.status_code == 400
