from flask import Blueprint, jsonify, request

from app.helpers import serialize
from app.models.event import Event
from app.models.url import Url

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
    data = request.get_json(force=True) or {}

    url_id = data.get("url_id")
    event_type = data.get("event_type")
    if not url_id or not event_type:
        return jsonify({"error": "url_id and event_type are required"}), 400

    try:
        Url.get_by_id(url_id)
    except Url.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404

    event = Event.create(
        url_id=url_id,
        user_id=data.get("user_id"),
        event_type=event_type,
        details=data.get("details"),
    )
    return jsonify(serialize(event)), 201
