from flask import Blueprint, request, jsonify
from flask_login import login_required
from extensions import db
from models import Event
from datetime import datetime

events_bp = Blueprint("events", __name__, url_prefix="/events")


# ---------------------------
# GET EVENTS
# ---------------------------
@events_bp.route("/list")
@login_required
def list_events():
    events = Event.query.order_by(Event.date.asc()).all()
    return jsonify([
        {
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "date": e.date
        }
        for e in events
    ])


# ---------------------------
# ADD EVENT
# ---------------------------
@events_bp.route("/add", methods=["POST"])
@login_required
def add_event():
    data = request.json
    title = data.get("title")
    date = data.get("date")
    description = data.get("description", "")

    event = Event(
        title=title,
        date=date,
        description=description,
        timestamp=datetime.utcnow()
    )

    db.session.add(event)
    db.session.commit()

    return jsonify({"success": True})
