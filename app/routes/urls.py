from flask import Blueprint, jsonify, redirect, request
from peewee import IntegrityError

from app.helpers import serialize
from app.models.event import Event
from app.models.url import Url, generate_short_code
from app.models.user import User

urls_bp = Blueprint("urls", __name__, url_prefix="/urls")


def _require_json_object():
    ct = request.content_type or ""
    if "application/json" not in ct:
        return None, (jsonify({"error": "Content-Type must be application/json"}), 400)
    data = request.get_json(silent=True)
    if data is None:
        return None, (jsonify({"error": "Invalid or empty JSON body"}), 400)
    if not isinstance(data, dict):
        return None, (jsonify({"error": "JSON body must be a JSON object"}), 400)
    return data, None


@urls_bp.route("", methods=["POST"])
def create_url():
    data, err = _require_json_object()
    if err:
        return err

    user_id = data.get("user_id")
    original_url = data.get("original_url")
    title = data.get("title")

    if user_id is None or original_url is None:
        return jsonify({"error": "user_id and original_url are required"}), 400
    if type(user_id) is bool or not isinstance(user_id, int):
        return jsonify({"error": "user_id must be an integer"}), 400
    if not isinstance(original_url, str) or not original_url.strip():
        return jsonify({"error": "original_url must be a non-empty string"}), 400
    if title is not None and not isinstance(title, str):
        return jsonify({"error": "title must be a string or null"}), 400

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

    data, err = _require_json_object()
    if err:
        return err

    if "title" in data:
        t = data["title"]
        if t is not None and not isinstance(t, str):
            return jsonify({"error": "title must be a string or null"}), 400
        url.title = t
    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            return jsonify({"error": "is_active must be a boolean"}), 400
        url.is_active = data["is_active"]
    if "original_url" in data:
        ou = data["original_url"]
        if not isinstance(ou, str) or not ou.strip():
            return jsonify({"error": "original_url must be a non-empty string"}), 400
        url.original_url = ou
    url.save()

    return jsonify(serialize(url))


@urls_bp.route("/<int:url_id>", methods=["DELETE"])
def delete_url(url_id):
    try:
        url = Url.get_by_id(url_id)
    except Url.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404
    url.delete_instance(recursive=True)
    return "", 204


@urls_bp.route("/<string:short_code>/redirect", methods=["GET"])
def redirect_short_code(short_code):
    try:
        url = Url.get(Url.short_code == short_code)
    except Url.DoesNotExist:
        return jsonify({"error": "Short code not found"}), 404
    if not url.is_active:
        return jsonify({"error": "URL is inactive"}), 410
    try:
        Event.create(
            url_id=url,
            user_id=None,
            event_type="click",
            details={"short_code": short_code},
        )
    except Exception:
        pass
    return redirect(url.original_url, code=301)
