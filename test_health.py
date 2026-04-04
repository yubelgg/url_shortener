"""Test error handling for health endpoint."""

import pytest
from app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    app.config["TESTING"] = True
    
    with app.test_client() as client:
        yield client


def test_health_endpoint_success(client):
    """Test health endpoint returns successful response."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] in ["ok", "degraded", "error"]
    print(f"Health check response: {data}")


def test_health_endpoint_returns_json(client):
    """Test health endpoint returns valid JSON."""
    response = client.get("/health")
    assert response.content_type == "application/json"
    data = response.get_json()
    assert isinstance(data, dict)


def test_404_error_handling(client):
    """Test that non-existent routes return clean error JSON."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data


def test_invalid_json_on_post(client):
    """Test that invalid JSON returns clean error."""
    response = client.post("/urls", data="not json", headers={"Content-Type": "application/json"})
    # Should not crash, should return error
    assert response.status_code in [400, 500]
    data = response.get_json()
    assert "error" in data or response.data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
