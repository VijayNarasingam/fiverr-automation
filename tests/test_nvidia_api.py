"""Tests for the NVIDIA API endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_nvidia_health():
    """GET /api/nvidia/health returns status and nvidia health."""
    response = client.get("/api/nvidia/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")
    assert "nvidia" in data
    assert isinstance(data["nvidia"], bool)
    assert "model" in data
    assert "base_url" in data


def test_nvidia_settings():
    """GET /api/nvidia/settings returns NVIDIA configuration."""
    response = client.get("/api/nvidia/settings")
    assert response.status_code == 200
    data = response.json()
    assert "nvidia_base_url" in data
    assert "nvidia_model" in data
    assert "nvidia_api_key_configured" in data
    assert isinstance(data["nvidia_api_key_configured"], bool)
    assert "nvidia_api_key_masked" in data


def test_nvidia_generate_missing_messages():
    """POST /api/nvidia/generate without messages returns 400."""
    response = client.post("/api/nvidia/generate", json={})
    assert response.status_code == 400
    assert "messages" in response.json()["detail"].lower()


def test_nvidia_generate_empty_messages():
    """POST /api/nvidia/generate with empty messages returns 400."""
    response = client.post(
        "/api/nvidia/generate", json={"messages": []}
    )
    assert response.status_code == 400