from dotenv import load_dotenv
from flask import Flask, jsonify

from app.database import db, init_db
from app.routes import register_routes


def create_app():
    load_dotenv()

    app = Flask(__name__)

    init_db(app)

    from app.models import User, Url, Event  # noqa: F401

    with app.app_context():
        db.connect(reuse_if_open=True)
        db.create_tables([User, Url, Event])
        if not db.is_closed():
            db.close()

    register_routes(app)

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    return app
