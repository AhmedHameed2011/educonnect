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

    # --- START OF ADJUSTMENT: ROLE-BASED PRIVACY RULES ---
    
    # 1. Employee/Teacher Role Restrictions
    if current_user.role == "teacher":
        # Teachers can only see messages with Admins, other Teachers, or Parents
        if other_user.role not in ["admin", "teacher", "parent"]:
            return jsonify({"error": "Access denied. Unauthorized conversation space."}), 403

    # 2. Parent Role Restrictions
    elif current_user.role == "parent":
        # Parents can only see messages with Teachers or Admins (no other parents)
        if other_user.role not in ["admin", "teacher"]:
            return jsonify({"error": "Access denied. Unauthorized conversation space."}), 403

    # --- END OF ADJUSTMENT ---

    # Your original working logic remains completely untouched below
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

    # Optional: You can replicate the same safety check here if needed to prevent 
    # unauthorized users from manually pushing a POST request to send data.

    msg = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=content,
        timestamp=datetime.utcnow()
    )

    db.session.add(msg)
    db.session.commit()

    return jsonify({"success": True})

# ---------------------------
# DELETE MESSAGE
# ---------------------------
@messages_bp.route("/delete/<int:message_id>", methods=["DELETE"])
@login_required
def delete_message(message_id):
    msg = Message.query.get_or_404(message_id)

    # Security check: Only allow the sender to delete their own message
    if msg.sender_id != current_user.id:
        return jsonify({"error": "Unauthorized action"}), 403

    db.session.delete(msg)
    db.session.commit()

    return jsonify({"success": True})