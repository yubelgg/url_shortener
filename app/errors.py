"""Error handling utilities for clean JSON responses."""

from flask import jsonify
from werkzeug.exceptions import HTTPException


class APIError(Exception):
    """Base API error class."""
    
    def __init__(self, message, status_code=500, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["error"] = self.message
        return rv


class ValidationError(APIError):
    """400 - Bad request/validation error."""
    
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=400, payload=payload)


class NotFoundError(APIError):
    """404 - Resource not found."""
    
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=404, payload=payload)


class InternalError(APIError):
    """500 - Internal server error."""
    
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=500, payload=payload)


class ServiceUnavailableError(APIError):
    """503 - Service unavailable."""
    
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=503, payload=payload)


def handle_api_error(error):
    """Handle APIError and return JSON response."""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def register_error_handlers(app):
    """Register global error handlers for the Flask app."""
    
    @app.errorhandler(APIError)
    def handle_api_errors(error):
        return handle_api_error(error)
    
    @app.errorhandler(404)
    def handle_404(error):
        response = jsonify({"error": "Resource not found"})
        response.status_code = 404
        return response
    
    @app.errorhandler(500)
    def handle_500(error):
        response = jsonify({"error": "Internal server error"})
        response.status_code = 500
        return response
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Catch unhandled exceptions and return clean JSON."""
        if isinstance(error, HTTPException):
            response = jsonify({"error": error.description})
            response.status_code = error.code
            return response

        import traceback

        # Log the error for debugging
        traceback.print_exc()

        response = jsonify({
            "error": "An unexpected error occurred",
            "type": error.__class__.__name__
        })
        response.status_code = 500
        return response
