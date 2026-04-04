"""Health check utilities."""

from app.database import db
from app.errors import ServiceUnavailableError


def check_database():
    """Check if database is accessible."""
    try:
        db.connection()
        return {"status": "ok", "type": "database"}
    except Exception as e:
        raise ServiceUnavailableError(f"Database unavailable: {str(e)}")


def perform_health_check():
    """Perform comprehensive health checks."""
    health_status = {
        "status": "ok",
        "checks": {}
    }
    
    try:
        check_database()
        health_status["checks"]["database"] = {"status": "ok"}
    except ServiceUnavailableError as e:
        health_status["checks"]["database"] = {"status": "error", "message": str(e)}
        health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["database"] = {"status": "error", "message": f"Unknown error: {str(e)}"}
        health_status["status"] = "degraded"
    
    return health_status
