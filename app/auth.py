
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from app import db
from app.models import User
from app.audit import record_activity


# Create authentication blueprint
auth_bp = Blueprint("auth", __name__)


# Public TrustVault Home Page
@auth_bp.route("/")
def home():

    if current_user.is_authenticated:

        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))

        return redirect(url_for("documents.dashboard"))

    return render_template("home.html")


# User Registration
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("auth.register"))

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "error"
            )
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            flash("Email is already registered.", "error")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password_hash=hashed_password,
            role="user"
        )

        db.session.add(new_user)
        db.session.commit()

        record_activity(
            new_user.id,
            "REGISTER",
            "New user registered"
        )

        flash(
            "Registration successful. Please log in.",
            "success"
        )

        return redirect(url_for("auth.login"))

    return render_template("register.html")


# User and Admin Login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get("password", "")

        selected_role = request.form.get(
            "role", ""
        ).strip().lower()

        if selected_role not in ["user", "admin"]:
            flash("Please select a valid login type.", "error")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password_hash, password
        ):

            if user.role != selected_role:
                flash(
                    "Incorrect account type selected.",
                    "error"
                )
                return redirect(url_for("auth.login"))

            login_user(user)

            record_activity(
                user.id,
                "LOGIN",
                "User logged in"
            )

            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))

            return redirect(url_for("documents.dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


# User Logout
@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():

    user_id = current_user.id

    logout_user()

    record_activity(
        user_id,
        "LOGOUT",
        "User logged out"
    )

    flash(
        "You have logged out successfully.",
        "success"
    )

    return redirect(url_for("auth.login"))
