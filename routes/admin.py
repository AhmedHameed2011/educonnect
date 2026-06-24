from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from extensions import db
from models import User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ---------------------------
# ADMIN ACCESS ONLY
# ---------------------------
def admin_only():
    if current_user.role != "admin":
        flash("Access denied. Admins only.")
        return False
    return True


# ---------------------------
# USER MANAGEMENT DASHBOARD
# ---------------------------
@admin_bp.route("/users")
@login_required
def users():
    if not admin_only():
        return redirect(url_for("dashboard.home"))

    all_users = User.query.order_by(User.role.asc()).all()
    return render_template("admin_users.html", users=all_users)


# ---------------------------
# ADD USER
# ---------------------------
@admin_bp.route("/add-user", methods=["POST"])
@login_required
def add_user():
    if not admin_only():
        return redirect(url_for("dashboard.home"))

    username = request.form.get("username").strip()
    name = request.form.get("name").strip()
    role = request.form.get("role")
    password = request.form.get("password").strip()

    if User.query.filter_by(username=username).first():
        flash("Username already exists.")
        return redirect(url_for("admin.users"))

    new_user = User(
        username=username,
        name=name,
        role=role,
        password=generate_password_hash(password),
        avatar=""
    )

    db.session.add(new_user)
    db.session.commit()

    flash("User created successfully.")
    return redirect(url_for("admin.users"))


# ---------------------------
# DELETE USER
# ---------------------------
@admin_bp.route("/delete/<int:user_id>")
@login_required
def delete_user(user_id):
    if not admin_only():
        return redirect(url_for("dashboard.home"))

    user = User.query.get_or_404(user_id)

    if user.role == "admin" and user.id == current_user.id:
        flash("You cannot delete your own admin account.")
        return redirect(url_for("admin.users"))

    db.session.delete(user)
    db.session.commit()

    flash("User deleted successfully.")
    return redirect(url_for("admin.users"))


# ---------------------------
# RESET PASSWORD
# ---------------------------
@admin_bp.route("/reset-password/<int:user_id>", methods=["POST"])
@login_required
def reset_password(user_id):
    if not admin_only():
        return redirect(url_for("dashboard.home"))

    new_password = request.form.get("new_password").strip()
    user = User.query.get_or_404(user_id)

    user.password = generate_password_hash(new_password)
    db.session.commit()

    flash("Password reset successfully.")
    return redirect(url_for("admin.users"))
