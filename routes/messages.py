from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Message, User
from datetime import datetime

messages_bp = Blueprint("messages", __name__, url_prefix="/messages")


# ---------------------------
# GET CHAT HISTORY
# ---------------------------
@messages_bp.route("/history/<int:user_id>")
@login_required
def chat_history(user_id):
    other_user = User.query.get_or_404(user_id)

    msgs = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()

    return jsonify([
        {
            "id": m.id,
            "sender": m.sender_id,
            "receiver": m.receiver_id,
            "content": m.content,
            "attachment": m.attachment,
            "timestamp": m.timestamp.strftime("%Y-%m-%d %H:%M")
        }
        for m in msgs
    ])


# ---------------------------
# SEND MESSAGE
# ---------------------------
@messages_bp.route("/send", methods=["POST"])
@login_required
def send_message():
    data = request.json
    receiver_id = data.get("receiver_id")
    content = data.get("content")

    if not receiver_id or not content:
        return jsonify({"error": "Missing fields"}), 400

    msg = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=content,
        timestamp=datetime.utcnow()
    )

    db.session.add(msg)
    db.session.commit()

    return jsonify({"success": True})
