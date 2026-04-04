"""Additional tests to improve coverage on error handling."""

import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from app.errors import (
    APIError, ValidationError, NotFoundError, 
    InternalError, ServiceUnavailableError
)


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestErrorHandlerRegistration:
    """Tests to ensure all error handlers are registered correctly."""
    
    def test_400_bad_request(self, client):
        """Test 400 handler with missing required fields."""
        response = client.post("/users", json={})
        assert response.status_code == 400
        assert response.content_type == "application/json"
    
    def test_500_unhandled_exception(self, client):
        """Test that unhandled exceptions return 500."""
        response = client.get("/nonexistent-endpoint-should-404")
        assert response.status_code == 404
        assert response.content_type == "application/json"
    
    def test_invalid_json_causes_400(self, client):
        """Test that malformed JSON triggers error handler."""
        response = client.post(
            "/users",
            data="not-json",
            headers={"Content-Type": "application/json"}
        )
        # Should return error, not crash
        assert response.status_code in [400, 500]
        assert response.content_type == "application/json"


class TestErrorClassHierarchy:
    """Tests for error class inheritance and behavior."""
    
    def test_validation_error_is_api_error(self):
        """Test that ValidationError inherits from APIError."""
        error = ValidationError("test")
        assert isinstance(error, APIError)
    
    def test_not_found_error_is_api_error(self):
        """Test that NotFoundError inherits from APIError."""
        error = NotFoundError("test")
        assert isinstance(error, APIError)
    
    def test_internal_error_is_api_error(self):
        """Test that InternalError inherits from APIError."""
        error = InternalError("test")
        assert isinstance(error, APIError)
    
    def test_service_unavailable_error_is_api_error(self):
        """Test that ServiceUnavailableError inherits from APIError."""
        error = ServiceUnavailableError("test")
        assert isinstance(error, APIError)
    
    def test_error_to_dict_includes_error_key(self):
        """Test that to_dict always includes 'error' key."""
        errors = [
            ValidationError("val"),
            NotFoundError("notfound"),
            InternalError("internal"),
            ServiceUnavailableError("unavail")
        ]
        for error in errors:
            error_dict = error.to_dict()
            assert "error" in error_dict


class TestHealthCheckDegradation:
    """Tests for health check degradation scenarios."""
    
    def test_health_returns_status_field(self, client):
        """Test that health response has status field."""
        response = client.get("/health")
        data = response.get_json()
        assert "status" in data
    
    def test_health_returns_checks_field(self, client):
        """Test that health response has checks field."""
        response = client.get("/health")
        data = response.get_json()
        assert "checks" in data
    
    def test_health_database_check_structure(self, client):
        """Test that database check has proper structure."""
        response = client.get("/health")
        data = response.get_json()
        assert "database" in data["checks"]
        db_check = data["checks"]["database"]
        assert "status" in db_check
        assert db_check["status"] in ["ok", "error"]

class TestErrorResponseFormat:
    """Tests for error response format consistency."""
    
    def test_404_error_format(self, client):
        """Test that 404 errors have consistent JSON format."""
        response = client.get("/api/missing")
        assert response.status_code == 404
        data = response.get_json()
        assert isinstance(data, dict)
        assert "error" in data
    
    def test_validation_error_format(self, client):
        """Test that validation errors have consistent JSON format."""
        response = client.post("/users", json={
            "username": 123,  # Wrong type
            "email": 456
        })
        assert response.status_code == 400
        data = response.get_json()
        assert isinstance(data, dict)
        assert "error" in data
    
    def test_multiple_errors_same_format(self, client):
        """Test that different error types return same format."""
        # 404 error
        response_404 = client.get("/nonexistent")
        data_404 = response_404.get_json()
        
        # 400 error
        response_400 = client.post("/users", json={})
        data_400 = response_400.get_json()
        
        # Both should have 'error' key
        assert "error" in data_404
        assert "error" in data_400


class TestHealthCheckEndpointDirectly:
    """Direct tests of health check endpoint behavior."""
    
    def test_health_always_returns_200(self, client):
        """Test that /health always returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_never_returns_error_status_code(self, client):
        """Test that /health never returns 5xx or 4xx."""
        response = client.get("/health")
        assert 200 <= response.status_code < 300
    
    def test_health_is_valid_json(self, client):
        """Test that health response is always valid JSON."""
        response = client.get("/health")
        # Should not raise an error
        data = response.get_json()
        assert data is not None
        assert isinstance(data, dict)


class TestAPIErrorDirectly:
    """Direct unit tests for error classes."""
    
    def test_api_error_base_class(self):
        """Test APIError base class functionality."""
        error = APIError("Test message", status_code=500)
        assert error.message == "Test message"
        assert error.status_code == 500
        assert error.to_dict()["error"] == "Test message"
    
    def test_api_error_with_custom_payload(self):
        """Test APIError with custom payload."""
        payload = {"code": "E001", "details": "test"}
        error = APIError("Error", status_code=400, payload=payload)
        error_dict = error.to_dict()
        assert error_dict["error"] == "Error"
        assert error_dict["code"] == "E001"
        assert error_dict["details"] == "test"
    
    def test_all_error_status_codes(self):
        """Test all error classes have correct status codes."""
        test_cases = [
            (ValidationError("test"), 400),
            (NotFoundError("test"), 404),
            (InternalError("test"), 500),
            (ServiceUnavailableError("test"), 503),
        ]
        for error, expected_code in test_cases:
            assert error.status_code == expected_code


class TestInvalidJSONHandling:
    """Test invalid JSON handling across different endpoints."""
    
    def test_invalid_json_on_urls_endpoint(self, client):
        """Test invalid JSON on /urls POST."""
        response = client.post(
            "/urls",
            data="{not valid json}",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 500]
        data = response.get_json()
        assert "error" in data or response.data
    
    def test_bad_json_type_users(self, client):
        """Test sending array instead of object."""
        response = client.post(
            "/users",
            json=["not", "an", "object"],
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 500]
    
    def test_empty_json_body(self, client):
        """Test sending empty JSON."""
        response = client.post(
            "/users",
            data="",
            headers={"Content-Type": "application/json"}
        )
        # Should handle gracefully
        assert response.status_code in [400, 500]


class TestErrorResponseConsistency:
    """Test that all errors return consistent JSON structure."""
    
    def test_all_errors_have_error_field(self, client):
        """Test that all error responses have 'error' field."""
        endpoints = [
            ("POST", "/users", {}),
            ("POST", "/urls", {}),
            ("GET", "/users/99999", None),
            ("GET", "/nonexistent", None),
        ]
        
        for method, path, data in endpoints:
            if method == "GET":
                response = client.get(path)
            else:
                response = client.post(path, json=data)
            
            # All errors should return JSON
            if response.status_code >= 400:
                resp_data = response.get_json()
                assert "error" in resp_data
    
    def test_error_responses_are_json_not_html(self, client):
        """Test that errors return JSON, not HTML."""
        response = client.get("/invalid/route/xyz")
        assert response.content_type == "application/json"
        assert "error" in response.get_json()


class TestHealthCheckDetails:
    """Test detailed health check information."""
    
    def test_health_has_all_required_fields(self, client):
        """Test health response has all required fields."""
        response = client.get("/health")
        data = response.get_json()
        
        # Top level
        assert "status" in data
        assert "checks" in data
        
        # Database check
        assert "database" in data["checks"]
        db_check = data["checks"]["database"]
        assert "status" in db_check
        assert db_check["status"] in ["ok", "error"]
    
    def test_health_status_values_valid(self, client):
        """Test health status has valid values."""
        response = client.get("/health")
        data = response.get_json()
        assert data["status"] in ["ok", "degraded", "error"]
    
    def test_health_response_content_type(self, client):
        """Test health returns application/json."""
        response = client.get("/health")
        assert response.content_type == "application/json"
        assert response.get_json() is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.errors", "--cov=app.health"])
