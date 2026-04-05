from flask import Blueprint, jsonify, request
from peewee import IntegrityError

from app.helpers import serialize
from app.models.event import Event
from app.models.url import Url, generate_short_code
from app.models.user import User

urls_bp = Blueprint("urls", __name__, url_prefix="/urls")


@urls_bp.route("", methods=["POST"])
def create_url():
    data = request.get_json(force=True)

    user_id = data.get("user_id")
    original_url = data.get("original_url")
    title = data.get("title")

    if not user_id or not original_url:
        return jsonify({"error": "user_id and original_url are required"}), 400

    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
        return jsonify({"error": "User not found"}), 404

    # Generate unique short_code with retry
    for _ in range(10):
        short_code = generate_short_code()
        try:
            url = Url.create(
                user_id=user,
                short_code=short_code,
                original_url=original_url,
                title=title,
            )
            break
        except IntegrityError:
            continue
    else:
        return jsonify({"error": "Could not generate unique short_code"}), 500

    # Auto-create event
    Event.create(
        url_id=url,
        user_id=user.id,
        event_type="created",
        details={
            "short_code": url.short_code,
            "original_url": url.original_url,
        },
    )

    return jsonify(serialize(url)), 201


@urls_bp.route("", methods=["GET"])
def list_urls():
    query = Url.select().where(Url.is_active == True).order_by(Url.id)

    user_id = request.args.get("user_id", type=int)
    if user_id:
        query = query.where(Url.user_id == user_id)

    return jsonify([serialize(u) for u in query])


@urls_bp.route("/<int:url_id>", methods=["GET"])
def get_url(url_id):
    try:
        url = Url.get_by_id(url_id)
    except Url.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404
    if not url.is_active:
        return jsonify({"error": "URL not found"}), 404
    return jsonify(serialize(url))


@urls_bp.route("/<int:url_id>", methods=["PUT"])
def update_url(url_id):
    try:
        url = Url.get_by_id(url_id)
    except Url.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404

    data = request.get_json(force=True)
    if "title" in data:
        url.title = data["title"]
    if "is_active" in data:
        url.is_active = data["is_active"]
    if "original_url" in data:
        url.original_url = data["original_url"]
    url.save()

    return jsonify(serialize(url))
