from app.main import health


def test_health():
    data = health()
    assert data["ok"] is True
    assert data["project"] == "{{cookiecutter.project_slug}}"
