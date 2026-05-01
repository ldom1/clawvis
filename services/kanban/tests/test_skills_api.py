from kanban_api.server import app


def test_skills_route_in_openapi():
    paths = app.openapi()["paths"]
    assert "/skills" in paths
    assert "get" in paths["/skills"]
