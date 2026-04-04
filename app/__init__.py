from dotenv import load_dotenv
from flask import Flask, jsonify

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

    @app.route("/seed")
    def seed():
        """Temporary endpoint to create tables and load CSV seed data."""
        import csv
        import json
        import os
        from peewee import chunked

        results = {}

        # Create tables
        db.connect(reuse_if_open=True)
        db.create_tables([User, Url, Event])
        results["tables"] = "created"

        # Load users
        csv_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(csv_dir, "users.csv"), newline="") as f:
            rows = list(csv.DictReader(f))
        with db.atomic():
            for batch in chunked(rows, 100):
                User.insert_many(batch).execute()
        results["users"] = len(rows)

        # Load urls
        with open(os.path.join(csv_dir, "urls.csv"), newline="") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            row["is_active"] = row["is_active"].strip() == "True"
        with db.atomic():
            for batch in chunked(rows, 100):
                Url.insert_many(batch).execute()
        results["urls"] = len(rows)

        # Load events
        with open(os.path.join(csv_dir, "events.csv"), newline="") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            row["details"] = json.loads(row["details"])
        with db.atomic():
            for batch in chunked(rows, 100):
                Event.insert_many(batch).execute()
        results["events"] = len(rows)

        # Reset sequences
        for table, seq in [("users", "users_id_seq"), ("urls", "urls_id_seq"), ("events", "events_id_seq")]:
            db.execute_sql(f"SELECT setval('{seq}', (SELECT MAX(id) FROM {table}))")
        results["sequences"] = "reset"

        return jsonify(results)

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

    return app
