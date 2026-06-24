from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ---------------------------
# LOGIN
# ---------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful.")
            return redirect(url_for("dashboard.home"))
        else:
            flash("Invalid username or password.")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


# ---------------------------
# LOGOUT
# ---------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.")
    return redirect(url_for("auth.login"))


# ---------------------------
# OPTIONAL: CREATE ADMIN USER
# ---------------------------
@auth_bp.route("/create-admin")
def create_admin():
    """Run once to create the first admin user."""
    if User.query.filter_by(username="admin").first():
        return "Admin already exists."

    admin = User(
        username="admin",
        name="School Admin",
        role="admin",
        password=generate_password_hash("admin123"),
        avatar="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80"
    )

    db.session.add(admin)
    db.session.commit()

    return "Admin user created successfully."
