
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect


# Initialize database
db = SQLAlchemy()

# Initialize login manager
login_manager = LoginManager()

# Initialize CSRF protection
csrf = CSRFProtect()


def create_app():

    app = Flask(
        __name__,
        instance_relative_config=True
    )

    # Application security settings
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY",
        "dev-secret-key-change-before-deployment"
    )

    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" +
        os.path.join(app.instance_path, "trustvault.db")
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Maximum upload request size: 16 MB
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    # Session cookie security
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Enable secure cookies in production
    app.config["SESSION_COOKIE_SECURE"] = (
        os.environ.get("FLASK_ENV") == "production"
    )

    # Create instance folder
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    login_manager.init_app(app)

    csrf.init_app(app)

    # Login configuration
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."

    # Register application routes
    from app.auth import auth_bp
    from app.documents import documents_bp
    from app.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(admin_bp)

    # Create database tables if they do not exist
    with app.app_context():

        from app import models

        db.create_all()

    return app


# Load logged-in user
@login_manager.user_loader
def load_user(user_id):

    from app.models import User

    try:
        return db.session.get(User, int(user_id))

    except (ValueError, TypeError):
        return None
