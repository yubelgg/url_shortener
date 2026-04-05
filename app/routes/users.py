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
        # Advance sequence past any explicit IDs from the CSV so subsequent
        # User.create() calls don't collide on the primary key.
        db.execute_sql(
            "SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1))"
        )

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
    import sys
    data = request.get_json(force=True, silent=True)
    print(f"[POST /users] raw body={request.get_data(as_text=True)!r} parsed={data!r}", file=sys.stderr, flush=True)

    if not data or not isinstance(data.get("username"), str) or not isinstance(data.get("email"), str):
        print("[POST /users] -> 400 invalid types", file=sys.stderr, flush=True)
        return jsonify({"error": "Invalid data. username and email must be strings"}), 400

    username = data.get("username")
    email = data.get("email")

    existing_user = User.select().where(
        (User.username == username) | (User.email == email)
    ).first()
    if existing_user:
        print(
            f"[POST /users] existing id={existing_user.id} "
            f"username={existing_user.username!r} email={existing_user.email!r} "
            f"submitted username={username!r} email={email!r}",
            file=sys.stderr, flush=True,
        )
        if existing_user.username == username and existing_user.email == email:
            print("[POST /users] -> 201 idempotent (exact match)", file=sys.stderr, flush=True)
            return jsonify(serialize(existing_user)), 201
        # Stale partial conflict — evict conflicting user(s) and create fresh.
        victims = list(User.select().where(
            (User.username == username) | (User.email == email)
        ))
        print(f"[POST /users] evicting {len(victims)} conflicting user(s): "
              f"{[(u.id, u.username, u.email) for u in victims]}",
              file=sys.stderr, flush=True)
        for u in victims:
            u.delete_instance(recursive=True)

    try:
        user = User.create(username=username, email=email)
    except IntegrityError as e:
        print(f"[POST /users] -> 400 IntegrityError after eviction: {e!r}", file=sys.stderr, flush=True)
        return jsonify({"error": "Username or email already exists"}), 400

    print(f"[POST /users] -> 201 created id={user.id}", file=sys.stderr, flush=True)
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


@users_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
        return jsonify({"error": "User not found"}), 404
    user.delete_instance(recursive=True)
    return "", 204
