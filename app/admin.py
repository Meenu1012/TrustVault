
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    abort,
    redirect,
    url_for,
    flash,
    current_app
)

from flask_login import login_required, current_user

from app import db

from app.models import (
    User,
    Document,
    DocumentPermission,
    AuditLog
)


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# Admin authorization
def admin_required(view_function):

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):

        if (
            not current_user.is_authenticated
            or (current_user.role or "").strip().lower() != "admin"
        ):
            abort(403)

        return view_function(*args, **kwargs)

    return wrapped_view


# Admin dashboard
@admin_bp.route("/")
@login_required
@admin_required
def dashboard():

    # Get all registered users
    users = User.query.order_by(
        User.created_at.desc()
    ).all()

    # Calculate user statistics
    total_users = len(users)

    total_admins = sum(
        1 for user in users
        if (user.role or "").strip().lower() == "admin"
    )

    total_normal_users = sum(
        1 for user in users
        if (user.role or "").strip().lower() == "user"
    )

    # Get all uploaded documents
    documents = Document.query.order_by(
        Document.uploaded_at.desc()
    ).all()

    # Count audit activities
    total_audit_logs = AuditLog.query.count()

    # Get latest 100 audit activities
    audit_logs = AuditLog.query.order_by(
        AuditLog.created_at.desc()
    ).limit(100).all()

    return render_template(
        "admin.html",
        users=users,
        documents=documents,
        audit_logs=audit_logs,
        total_users=total_users,
        total_admins=total_admins,
        total_normal_users=total_normal_users,
        total_documents=len(documents),
        total_audit_logs=total_audit_logs
    )
# Promote normal user to administrator
@admin_bp.route(
    "/promote-user/<int:user_id>",
    methods=["POST"]
)
@login_required
@admin_required
def promote_user(user_id):

    user = db.session.get(User, user_id)

    if user is None:
        flash("User not found.", "danger")
        return redirect(url_for("admin.dashboard"))

    if user.id == current_user.id:
        flash("You cannot promote your own account.", "danger")
        return redirect(url_for("admin.dashboard"))

    if (user.role or "").strip().lower() != "user":
        flash("Only normal users can be promoted.", "danger")
        return redirect(url_for("admin.dashboard"))

    username = user.name
    user_email = user.email

    try:
        user.role = "admin"

        promotion_log = AuditLog(
            user_id=current_user.id,
            action="USER_PROMOTION",
            details=(
                f"Promoted {username} ({user_email}, "
                f"ID: {user.id}) to administrator."
            )
        )

        db.session.add(promotion_log)
        db.session.commit()

        flash(
            f"{username} has been promoted to administrator.",
            "success"
        )

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "User promotion failed"
        )

        flash(
            "Could not promote user. Please check application logs.",
            "danger"
        )

    return redirect(url_for("admin.dashboard"))

# Delete normal user account
@admin_bp.route(
    "/delete-user/<int:user_id>",
    methods=["POST"]
)
@login_required
@admin_required
def delete_user(user_id):

    # Find user
    user = db.session.get(User, user_id)

    if user is None:
        flash("User not found.", "danger")
        return redirect(url_for("admin.dashboard"))

    # Prevent deleting own account
    if user.id == current_user.id:
        flash(
            "You cannot delete your own account.",
            "danger"
        )
        return redirect(url_for("admin.dashboard"))

    # Allow deletion only for normal users
    if (user.role or "").strip().lower() != "user":
        flash(
            "Only normal user accounts can be deleted.",
            "danger"
        )
        return redirect(url_for("admin.dashboard"))

    username = user.name
    user_email = user.email
    user_id_to_delete = user.id

    try:

        # Count documents before transferring ownership
        document_count = Document.query.filter_by(
            owner_id=user_id_to_delete
        ).count()

        # Transfer documents to current admin
        Document.query.filter_by(
            owner_id=user_id_to_delete
        ).update(
            {"owner_id": current_user.id},
            synchronize_session=False
        )

        # Remove permissions belonging to deleted user
        DocumentPermission.query.filter_by(
            user_id=user_id_to_delete
        ).delete(
            synchronize_session=False
        )

        # Preserve audit history and identify former user
        old_audit_logs = AuditLog.query.filter_by(
            user_id=user_id_to_delete
        ).all()

        for log in old_audit_logs:

            previous_details = log.details or ""

            log.details = (
                f"[Former user: {username}, {user_email}] "
                f"{previous_details}"
            )

            log.user_id = None

        # Record deletion activity under admin account
        deletion_log = AuditLog(
            user_id=current_user.id,
            action="USER_DELETE",
            details=(
                f"Deleted user: {username} "
                f"({user_email}, ID: {user_id_to_delete}). "
                f"{document_count} document(s) transferred "
                "to admin. Previous audit history preserved."
            )
        )

        db.session.add(deletion_log)

        # Delete user account
        db.session.delete(user)

        # Save all changes
        db.session.commit()

        flash(
            f"User {username} deleted successfully. "
            f"{document_count} document(s) transferred to admin.",
            "success"
        )

    except Exception:

        db.session.rollback()

        current_app.logger.exception(
            "User deletion failed"
        )

        flash(
            "Could not delete user. Please check the application logs.",
            "danger"
        )

    return redirect(url_for("admin.dashboard"))
