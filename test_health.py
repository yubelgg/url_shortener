"""Test error handling for health endpoint and error utilities."""

import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from app.errors import (
    APIError, ValidationError, NotFoundError, 
    InternalError, ServiceUnavailableError, handle_api_error
)
from app.health import check_database, perform_health_check


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    app.config["TESTING"] = True
    
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Tests for /health endpoint."""
    
    def test_health_endpoint_success(self, client):
        """Test health endpoint returns successful response."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] in ["ok", "degraded", "error"]
        assert "checks" in data
    
    def test_health_endpoint_returns_json(self, client):
        """Test health endpoint returns valid JSON."""
        response = client.get("/health")
        assert response.content_type == "application/json"
        data = response.get_json()
        assert isinstance(data, dict)
    
    def test_health_endpoint_has_database_check(self, client):
        """Test that health endpoint includes database check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert "checks" in data
        assert "database" in data["checks"]
        assert "status" in data["checks"]["database"]


class TestErrorHandlers:
    """Tests for global error handlers."""
    
    def test_404_error_handling(self, client):
        """Test that non-existent routes return clean error JSON."""
        response = client.get("/nonexistent-route-xyz")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
    
    def test_404_returns_json(self, client):
        """Test that 404 returns JSON not HTML."""
        response = client.get("/nonexistent")
        assert response.content_type == "application/json"
    
    def test_invalid_json_on_post(self, client):
        """Test that invalid JSON returns clean error."""
        response = client.post("/urls", data="not json", 
                              headers={"Content-Type": "application/json"})
        assert response.status_code in [400, 500]
        data = response.get_json()
        assert "error" in data
    
    def test_invalid_json_users_endpoint(self, client):
        """Test invalid JSON on users endpoint."""
        response = client.post("/users", data="invalid", 
                              headers={"Content-Type": "application/json"})
        assert response.status_code == 400
        assert "error" in response.get_json()


class TestErrorClasses:
    """Tests for custom error classes."""
    
    def test_validation_error(self):
        """Test ValidationError returns 400 status code."""
        error = ValidationError("Invalid input")
        assert error.status_code == 400
        assert error.message == "Invalid input"
        assert error.to_dict()["error"] == "Invalid input"
    
    def test_not_found_error(self):
        """Test NotFoundError returns 404 status code."""
        error = NotFoundError("Resource not found")
        assert error.status_code == 404
        assert error.message == "Resource not found"
        assert error.to_dict()["error"] == "Resource not found"
    
    def test_internal_error(self):
        """Test InternalError returns 500 status code."""
        error = InternalError("Server error")
        assert error.status_code == 500
        assert error.message == "Server error"
        assert error.to_dict()["error"] == "Server error"
    
    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError returns 503 status code."""
        error = ServiceUnavailableError("Service down")
        assert error.status_code == 503
        assert error.message == "Service down"
        assert error.to_dict()["error"] == "Service down"
    
    def test_api_error_with_payload(self):
        """Test APIError with custom payload."""
        error = APIError("Error", status_code=400, payload={"code": "ERR001"})
        error_dict = error.to_dict()
        assert error_dict["error"] == "Error"
        assert error_dict["code"] == "ERR001"
    
    def test_handle_api_error(self):
        """Test handle_api_error function."""
        error = ValidationError("Test error")
        response_dict = handle_api_error(error)
        # Response should be a Flask response object
        assert response_dict.status_code == 400


class TestHealthChecks:
    """Tests for health check utilities."""
    
    def test_check_database_success(self):
        """Test database check succeeds when DB is up."""
        result = check_database()
        assert result["status"] == "ok"
        assert result["type"] == "database"
    
    @patch('app.health.db')
    def test_check_database_failure(self, mock_db):
        """Test that database check fails when DB is down."""
        mock_db.connection.side_effect = Exception("Connection refused")
        
        with pytest.raises(Exception):
            check_database()
    
    def test_perform_health_check_all_ok(self):
        """Test full health check when everything is OK."""
        health = perform_health_check()
        assert health["status"] in ["ok", "degraded"]
        assert "checks" in health
        assert "database" in health["checks"]
    
    @patch('app.health.check_database')
    def test_perform_health_check_db_down(self, mock_check):
        """Test health check returns degraded when DB is down."""
        from app.errors import ServiceUnavailableError
        mock_check.side_effect = ServiceUnavailableError("DB error")
        
        health = perform_health_check()
        assert health["status"] == "degraded"
        assert health["checks"]["database"]["status"] == "error"
        assert "message" in health["checks"]["database"]


class TestErrorIntegration:
    """Integration tests for error handling."""
    
    def test_api_error_handler_catches_validation_error(self, client):
        """Test that API error handler catches ValidationError."""
        # Trigger a validation error by missing fields
        response = client.post("/users", json={"username": "test"})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
    
    def test_health_provides_detailed_info(self, client):
        """Test that health endpoint provides detailed check info."""
        response = client.get("/health")
        data = response.get_json()
        
        # Should have status
        assert "status" in data
        # Should have checks
        assert "checks" in data
        # Database check should be present
        assert "database" in data["checks"]
        # Database check should have status
        assert "status" in data["checks"]["database"]
    
    def test_multiple_404_requests(self, client):
        """Test that multiple 404 requests all return clean JSON."""
        for route in ["/invalid", "/bad/route", "/404/test"]:
            response = client.get(route)
            assert response.status_code == 404
            data = response.get_json()
            assert "error" in data
            assert response.content_type == "application/json"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
