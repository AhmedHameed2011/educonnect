from routes.admin import admin_bp
from flask import Flask
from config import Config
from extensions import db, login_manager
from models import User
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.messages import messages_bp
from routes.notifications import notifications_bp
from routes.events import events_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(admin_bp)

    # Create DB tables
    with app.app_context():
        db.create_all()

    return app

# CREATE THE INSTANCE GLOBALLY SO GUNICORN CAN SEE IT
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)