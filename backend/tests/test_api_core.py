import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_live(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "Housing Society CMS" in data["app"]
    assert "X-Request-ID" in response.headers


def test_openapi_docs_generated(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["info"]["title"] == "Housing Society CMS"
    assert "/api/v1/complaints" in spec["paths"]
    assert "/api/v1/incidents" in spec["paths"]
    assert "/api/v1/assignments" in spec["paths"]
    assert "/api/v1/dashboard/summary" in spec["paths"]


def test_unauthenticated_requests_return_401(client):
    response = client.get("/api/v1/me")
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "UNAUTHORIZED"
    assert "X-Request-ID" in response.headers
