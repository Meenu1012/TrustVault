
import os

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from supabase import create_client


# Load environment variables from .env
load_dotenv()

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
    database_url = os.environ.get("DATABASE_URL")

    if database_url and not os.environ.get("TESTING"):
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1
            )

        app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    else:
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

    app.config["SESSION_COOKIE_SECURE"] = (
        os.environ.get("FLASK_ENV") == "production"
        or os.environ.get("RENDER") == "true"
    )

    # Create instance folder
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize Supabase Storage client
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if supabase_url and supabase_key and not os.environ.get("TESTING"):
        app.extensions["supabase"] = create_client(
            supabase_url,
            supabase_key
        )

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
    # Health check endpoint for Render
    @app.route("/api/health")
    def health_check():
        return {"status": "OK", "message": "TrustVault is running"}, 200

    # Create database tables
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
