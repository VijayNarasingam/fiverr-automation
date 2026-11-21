"""API tests for the Fiverr Automation Agent."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    """GET /api/health returns status and ollama health."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")
    assert "ollama" in data
    assert isinstance(data["ollama"], bool)
