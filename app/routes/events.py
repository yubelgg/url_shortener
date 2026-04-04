from flask import Blueprint, jsonify

from app.helpers import serialize
from app.models.event import Event

events_bp = Blueprint("events", __name__, url_prefix="/events")


@events_bp.route("", methods=["GET"])
def list_events():
    events = Event.select().order_by(Event.id)
    return jsonify([serialize(e) for e in events])
