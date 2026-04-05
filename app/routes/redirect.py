from flask import Blueprint, jsonify, redirect

from app.models.event import Event
from app.models.url import Url

redirect_bp = Blueprint("redirect", __name__)


@redirect_bp.route("/r/<short_code>", methods=["GET"])
def follow_short_code(short_code):
    if not short_code or len(short_code) > 10:
        return jsonify({"error": "Invalid short code"}), 400

    try:
        url = Url.get(Url.short_code == short_code)
    except Url.DoesNotExist:
        return jsonify({"error": "URL not found"}), 404

    if not url.is_active:
        return jsonify({"error": "URL not found"}), 404

    Event.create(
        url_id=url,
        user_id=url.user_id_id,
        event_type="clicked",
        details={"short_code": url.short_code},
    )

    return redirect(url.original_url, code=302)
