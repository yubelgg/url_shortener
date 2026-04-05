from dotenv import load_dotenv
from flask import Flask, jsonify
import os

from app.database import db, init_db
from app.errors import register_error_handlers
from app.health import perform_health_check
from app.routes import register_routes


def create_app():
    load_dotenv()

    app = Flask(__name__)

    init_db(app)

    from app.models import User, Url, Event  # noqa: F401

    with app.app_context():
        db.connect(reuse_if_open=True)
        try:
            db.create_tables([User, Url, Event])
        except Exception:
            pass  # Tables may already exist or user lacks CREATE permission
        if not db.is_closed():
            db.close()

    register_routes(app)
    register_error_handlers(app)

    @app.route("/health")
    def health():
        """Health check endpoint with database validation."""
        try:
            health_status = perform_health_check()
            
            if health_status["status"] == "ok":
                return jsonify(health_status), 200
            else:
                # Degraded state - still return 200 but indicate issues
                return jsonify(health_status), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 503

    # Register test-only route if in testing mode
    if os.environ.get("FLASK_TESTING") == "true" or app.config.get("TESTING"):
        @app.route("/test-500-error")
        def test_500_error():
            """Test-only endpoint to trigger 500 error handling."""
            raise Exception("Test unhandled exception")

    return app
