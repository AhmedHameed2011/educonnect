from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Notification
from datetime import datetime

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


# ---------------------------
# GET NOTIFICATIONS
# ---------------------------
@notifications_bp.route("/list")
@login_required
def list_notifications():
    notifs = Notification.query.order_by(Notification.timestamp.desc()).all()
    return jsonify([
        {
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "priority": n.priority,
            "timestamp": n.timestamp.strftime("%Y-%m-%d %H:%M")
        }
        for n in notifs
    ])


# ---------------------------
# CREATE BROADCAST
# ---------------------------
@notifications_bp.route("/broadcast", methods=["POST"])
@login_required
def broadcast():
    data = request.json
    title = data.get("title")
    content = data.get("content")
    priority = data.get("priority", "normal")

    notif = Notification(
        title=title,
        content=content,
        priority=priority,
        timestamp=datetime.utcnow()
    )

    db.session.add(notif)
    db.session.commit()

    return jsonify({"success": True})
