import csv
import io

from flask import Blueprint, jsonify, request
from peewee import IntegrityError, chunked

from app.database import db
from app.helpers import serialize
from app.models.user import User

users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.route("/bulk", methods=["POST"])
def bulk_create_users():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    stream = io.StringIO(file.stream.read().decode("utf-8"))
    reader = csv.DictReader(stream)
    rows = [{k.strip().lower(): v for k, v in row.items()} for row in reader]

    with db.atomic():
        for batch in chunked(rows, 100):
            User.insert_many(batch).execute()

    return jsonify({"count": len(rows)}), 201


@users_bp.route("", methods=["GET"])
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = User.select().order_by(User.id)
    users = query.paginate(page, per_page)
    return jsonify([serialize(u) for u in users])


@users_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
        return jsonify({"error": "User not found"}), 404
    return jsonify(serialize(user))


@users_bp.route("", methods=["POST"])
def create_user():
    data = request.get_json(force=True)

    if not data or not isinstance(data.get("username"), str) or not isinstance(data.get("email"), str):
        return jsonify({"error": "Invalid data. username and email must be strings"}), 400

    username = data.get("username")
    email = data.get("email")
    
    existing_user = User.select().where(
        (User.username == username) | (User.email == email)
    ).first()
    if existing_user:
        return jsonify({"error": "Username or email already exists"}), 400

    try:
        user = User.create(
            username=data["username"],
            email=data["email"],
        )
    except IntegrityError:
        return jsonify({"error": "Username or email already exists"}), 400

    return jsonify(serialize(user)), 201


@users_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(force=True)
    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]
    user.save()

    return jsonify(serialize(user))
