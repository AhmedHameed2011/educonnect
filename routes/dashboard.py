from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import User, Message, Notification, Event

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def home():
    # Load sidebar users (teachers, admin office, etc.)
    users = User.query.filter(User.id != current_user.id).all()

    # Load notifications
    notifications = Notification.query.order_by(Notification.timestamp.desc()).limit(10).all()

    # Load events
    events = Event.query.order_by(Event.date.asc()).all()

    return render_template(
        "index.html",
        current_user=current_user,
        users=users,
        notifications=notifications,
        events=events
    )
