from flask import Blueprint, jsonify, request

from app.helpers import serialize
from app.models.event import Event
from app.models.url import Url
from app.models.user import User

events_bp = Blueprint("events", __name__, url_prefix="/events")


@events_bp.route("", methods=["GET"])
def list_events():
    query = Event.select().order_by(Event.id)

    url_id = request.args.get("url_id", type=int)
    event_type = request.args.get("event_type")
    if url_id:
        query = query.where(Event.url_id == url_id)
    if event_type:
        query = query.where(Event.event_type == event_type)

    return jsonify([serialize(e) for e in query])


@events_bp.route("", methods=["POST"])
def create_event():
    ct = request.content_type or ""
    if "application/json" not in ct:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body must be a JSON object"}), 400

    url_id = data.get("url_id")
    event_type = data.get("event_type")

    if url_id is None or event_type is None:
        return jsonify({"error": "url_id and event_type are required"}), 400
    if type(url_id) is bool or not isinstance(url_id, int):
        return jsonify({"error": "url_id must be an integer"}), 400
    if not isinstance(event_type, str) or not event_type.strip():
        return jsonify({"error": "event_type must be a non-empty string"}), 400

    user_id = data.get("user_id")
    if user_id is not None:
        if type(user_id) is bool or not isinstance(user_id, int):
            return jsonify({"error": "user_id must be an integer or null"}), 400
        try:
            User.get_by_id(user_id)
        except User.DoesNotExist:
            return jsonify({"error": "User not found"}), 404

    details = data.get("details")
    if details is not None and not isinstance(details, dict):
        return jsonify({"error": "details must be an object or null"}), 400

    try:
        Url.get_by_id(url_id)
    except Url.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404

    event = Event.create(
        url_id=url_id,
        user_id=user_id,
        event_type=event_type,
        details=details,
    )
    return jsonify(serialize(event)), 201
