
import os
import uuid
import pymupdf

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_from_directory,
    abort
)

from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models import Document, DocumentPermission, User, AuditLog


# Create documents blueprint
documents_bp = Blueprint("documents", __name__)


# Allowed document extensions
ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "txt",
    "png", "jpg", "jpeg",
    "xlsx", "xls", "ppt", "pptx"
}


# Upload folder
def get_upload_folder():

    folder = os.path.join(
        current_app.instance_path,
        "uploads"
    )

    os.makedirs(folder, exist_ok=True)

    return folder


# Check allowed file extensions
def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# Record audit activity
def log_activity(action, details=""):

    log = AuditLog(
        user_id=current_user.id,
        action=action,
        details=details
    )

    db.session.add(log)


# Check document access
def can_access_document(document):

    if document.owner_id == current_user.id:
        return True

    if current_user.role == "admin":
        return True

    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        user_id=current_user.id
    ).first()

    return permission is not None


# Check document edit permission
def can_edit_document(document):

    if document.owner_id == current_user.id:
        return True

    if current_user.role == "admin":
        return True

    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        user_id=current_user.id
    ).first()

    return (
        permission is not None
        and permission.permission == "edit"
    )


# Get document or return 404
def get_document(document_id):

    document = db.session.get(Document, document_id)

    if document is None:
        abort(404)

    return document


# User dashboard
@documents_bp.route("/dashboard")
@login_required
def dashboard():

    documents = Document.query.filter_by(
        owner_id=current_user.id
    ).order_by(
        Document.uploaded_at.desc()
    ).all()

    permissions = DocumentPermission.query.filter_by(
        user_id=current_user.id
    ).all()

    shared_documents = [
        permission.document
        for permission in permissions
        if permission.document is not None
    ]

    return render_template(
        "dashboard.html",
        documents=documents,
        shared_documents=shared_documents
    )


# Upload document
@documents_bp.route("/upload", methods=["POST"])
@login_required
def upload_document():

    if "file" not in request.files:

        flash("No file selected.", "danger")
        return redirect(url_for("documents.dashboard"))

    file = request.files["file"]

    if file.filename == "":

        flash("Please select a file.", "danger")
        return redirect(url_for("documents.dashboard"))

    if not allowed_file(file.filename):

        flash("File type not allowed.", "danger")
        return redirect(url_for("documents.dashboard"))

    original_filename = secure_filename(file.filename)

    if not original_filename:

        flash("Invalid filename.", "danger")
        return redirect(url_for("documents.dashboard"))

    stored_filename = str(uuid.uuid4()) + "_" + original_filename

    upload_folder = get_upload_folder()

    file_path = os.path.join(
        upload_folder,
        stored_filename
    )

    try:

        file.save(file_path)

        document = Document(
            filename=original_filename,
            stored_filename=stored_filename,
            owner_id=current_user.id
        )

        db.session.add(document)
        db.session.flush()

        log_activity(
            "UPLOAD",
            f"Uploaded document: {original_filename}"
        )

        db.session.commit()

        flash("Document uploaded successfully.", "success")

    except Exception:

        db.session.rollback()

        if os.path.exists(file_path):
            os.remove(file_path)

        current_app.logger.exception("Document upload failed")

        flash("Document upload failed.", "danger")

    return redirect(url_for("documents.dashboard"))


# View document
@documents_bp.route("/view/<int:document_id>")
@login_required
def view_document(document_id):

    document = get_document(document_id)

    if not can_access_document(document):
        abort(403)

    upload_folder = get_upload_folder()

    file_path = os.path.join(
        upload_folder,
        document.stored_filename
    )

    if not os.path.isfile(file_path):
        abort(404)

    log_activity(
        "VIEW",
        f"Viewed document: {document.filename}"
    )

    db.session.commit()

    return send_from_directory(
        upload_folder,
        document.stored_filename,
        as_attachment=False,
        download_name=document.filename
    )


# Download document
@documents_bp.route("/download/<int:document_id>")
@login_required
def download_document(document_id):

    document = get_document(document_id)

    if not can_access_document(document):
        abort(403)

    upload_folder = get_upload_folder()

    file_path = os.path.join(
        upload_folder,
        document.stored_filename
    )

    if not os.path.isfile(file_path):
        abort(404)

    log_activity(
        "DOWNLOAD",
        f"Downloaded document: {document.filename}"
    )

    db.session.commit()

    return send_from_directory(
        upload_folder,
        document.stored_filename,
        as_attachment=True,
        download_name=document.filename
    )


# Replace document
@documents_bp.route(
    "/replace/<int:document_id>",
    methods=["POST"]
)
@login_required
def replace_document(document_id):

    document = get_document(document_id)

    if not can_edit_document(document):
        abort(403)

    if "file" not in request.files:

        flash("Please select a replacement file.", "danger")
        return redirect(url_for("documents.shared_documents"))

    file = request.files["file"]

    if file.filename == "":

        flash("Please select a replacement file.", "danger")
        return redirect(url_for("documents.shared_documents"))

    if not allowed_file(file.filename):

        flash("File type not allowed.", "danger")
        return redirect(url_for("documents.shared_documents"))

    new_original_filename = secure_filename(file.filename)

    if not new_original_filename:

        flash("Invalid filename.", "danger")
        return redirect(url_for("documents.shared_documents"))

    upload_folder = get_upload_folder()

    new_stored_filename = (
        str(uuid.uuid4()) + "_" + new_original_filename
    )

    new_file_path = os.path.join(
        upload_folder,
        new_stored_filename
    )

    old_file_path = os.path.join(
        upload_folder,
        document.stored_filename
    )

    old_stored_filename = document.stored_filename

    try:

        file.save(new_file_path)

        document.filename = new_original_filename
        document.stored_filename = new_stored_filename

        log_activity(
            "DOCUMENT_REPLACE",
            f"Replaced document ID {document.id} "
            f"with updated file: {new_original_filename}"
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        if os.path.isfile(new_file_path):
            os.remove(new_file_path)

        current_app.logger.exception(
            "Document replacement failed"
        )

        flash("Could not replace the document.", "danger")

        if (
            document.owner_id == current_user.id
            or current_user.role == "admin"
        ):
            return redirect(url_for("documents.dashboard"))

        return redirect(url_for("documents.shared_documents"))

    try:

        if os.path.isfile(old_file_path):
            os.remove(old_file_path)

    except OSError:

        current_app.logger.exception(
            "Could not remove old document"
        )

    flash("Document replaced successfully.", "success")

    if (
        document.owner_id == current_user.id
        or current_user.role == "admin"
    ):
        return redirect(url_for("documents.dashboard"))

    return redirect(url_for("documents.shared_documents"))


# Delete document
@documents_bp.route("/delete/<int:document_id>", methods=["POST"])
@login_required
def delete_document(document_id):

    document = get_document(document_id)

    if (
        document.owner_id != current_user.id
        and current_user.role != "admin"
    ):
        abort(403)

    upload_folder = get_upload_folder()

    file_path = os.path.join(
        upload_folder,
        document.stored_filename
    )

    filename = document.filename

    try:

        DocumentPermission.query.filter_by(
            document_id=document.id
        ).delete(synchronize_session=False)

        log_activity(
            "DOCUMENT_DELETE",
            f"Deleted document: {filename}"
        )

        db.session.delete(document)
        db.session.commit()

        if os.path.isfile(file_path):
            os.remove(file_path)

        flash("Document deleted successfully.", "success")

    except Exception:

        db.session.rollback()

        current_app.logger.exception("Document deletion failed")

        flash("Could not delete document.", "danger")

    return redirect(url_for("documents.dashboard"))


# Share document
@documents_bp.route("/share/<int:document_id>", methods=["POST"])
@login_required
def share_document(document_id):

    document = get_document(document_id)

    if (
        document.owner_id != current_user.id
        and current_user.role != "admin"
    ):
        abort(403)

    email = request.form.get("email", "").strip().lower()

    permission_type = request.form.get(
        "permission",
        "view"
    ).strip().lower()

    if permission_type not in ["view", "edit"]:

        flash("Invalid permission type.", "danger")
        return redirect(url_for("documents.dashboard"))

    if not email:

        flash("Please enter a user email.", "danger")
        return redirect(url_for("documents.dashboard"))

    recipient = User.query.filter_by(
        email=email
    ).first()

    if recipient is None:

        flash("User not found.", "danger")
        return redirect(url_for("documents.dashboard"))

    if recipient.id == document.owner_id:

        flash("You cannot share with the document owner.", "warning")
        return redirect(url_for("documents.dashboard"))

    try:

        existing_permission = DocumentPermission.query.filter_by(
            document_id=document.id,
            user_id=recipient.id
        ).first()

        if existing_permission:

            existing_permission.permission = permission_type

        else:

            new_permission = DocumentPermission(
                document_id=document.id,
                user_id=recipient.id,
                permission=permission_type
            )

            db.session.add(new_permission)

        log_activity(
            "SHARE",
            f"Shared {document.filename} with {email} "
            f"({permission_type} permission)"
        )

        db.session.commit()

        flash("Document shared successfully.", "success")

    except Exception:

        db.session.rollback()

        current_app.logger.exception("Document sharing failed")

        flash("Could not share document.", "danger")

    return redirect(url_for("documents.dashboard"))


# Edit a TXT document
@documents_bp.route(
    "/edit/<int:document_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_text_document(document_id):

    document = get_document(document_id)

    if not can_edit_document(document):
        abort(403)

    if not document.filename.lower().endswith(".txt"):

        flash(
            "Direct editing is currently available for TXT files only.",
            "warning"
        )

        return redirect(url_for("documents.shared_documents"))

    upload_folder = get_upload_folder()

    file_path = os.path.join(
        upload_folder,
        document.stored_filename
    )

    if not os.path.isfile(file_path):
        abort(404)

    if request.method == "GET":

        try:

            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

        except UnicodeDecodeError:

            flash("Unsupported text file encoding.", "danger")
            return redirect(url_for("documents.shared_documents"))

        return render_template(
            "edit_document.html",
            document=document,
            content=content
        )

    new_content = request.form.get("content", "")

    temp_path = file_path + "." + str(uuid.uuid4()) + ".tmp"
    backup_path = file_path + "." + str(uuid.uuid4()) + ".bak"

    try:

        with open(
            temp_path,
            "w",
            encoding="utf-8",
            newline=""
        ) as file:

            file.write(new_content)

        os.replace(file_path, backup_path)

        try:

            os.replace(temp_path, file_path)

            log_activity(
                "DOCUMENT_EDIT",
                f"Edited TXT document: {document.filename}"
            )

            db.session.commit()

        except Exception:

            db.session.rollback()

            if os.path.exists(file_path):
                os.remove(file_path)

            os.replace(backup_path, file_path)

            raise

        if os.path.exists(backup_path):
            os.remove(backup_path)

        flash("Document changes saved successfully.", "success")

        if (
            document.owner_id == current_user.id
            or current_user.role == "admin"
        ):
            return redirect(url_for("documents.dashboard"))

        return redirect(url_for("documents.shared_documents"))

    except Exception:

        db.session.rollback()

        if os.path.exists(temp_path):
            os.remove(temp_path)

        current_app.logger.exception(
            "TXT document editing failed"
        )

        flash("Could not save document changes.", "danger")

        return redirect(
            url_for(
                "documents.edit_text_document",
                document_id=document.id
            )
        )


# Edit a PDF document
@documents_bp.route(
    "/edit-pdf/<int:document_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_pdf_document(document_id):

    document = get_document(document_id)

    if not can_edit_document(document):
        abort(403)

    if not document.filename.lower().endswith(".pdf"):
        abort(400, description="Only PDF files can be edited.")

    upload_folder = get_upload_folder()

    file_path = os.path.join(
        upload_folder,
        document.stored_filename
    )

    if not os.path.isfile(file_path):
        abort(404)

    try:

        with pymupdf.open(file_path) as pdf:
            page_count = pdf.page_count

    except Exception:

        abort(400, description="Unable to open this PDF.")

    if request.method == "POST":

        text = request.form.get("text", "").strip()

        try:
            page_number = int(request.form.get("page_number", ""))
        except (TypeError, ValueError):
            abort(400, description="Invalid page number.")

        if not text:
            flash("Please enter text.", "danger")

        elif len(text) > 2000:
            flash("Text must be 2000 characters or fewer.", "danger")

        elif page_number < 1 or page_number > page_count:
            flash("Invalid page number.", "danger")

        else:

            temp_path = os.path.join(
                upload_folder,
                str(uuid.uuid4()) + "_edited.pdf"
            )

            try:

                with pymupdf.open(file_path) as pdf:

                    page = pdf[page_number - 1]

                    text_rect = pymupdf.Rect(
                        72,
                        72,
                        page.rect.width - 36,
                        min(200, page.rect.height - 36)
                    )

                    remaining = page.insert_textbox(
                        text_rect,
                        text,
                        fontsize=12,
                        fontname="helv",
                        color=(0, 0, 0)
                    )

                    if remaining < 0:
                        raise ValueError(
                            "Text is too long for the selected area."
                        )

                    pdf.save(
                        temp_path,
                        garbage=4,
                        deflate=True
                    )

                os.replace(temp_path, file_path)

                log_activity(
                    "PDF_EDIT",
                    f"Edited PDF document: {document.filename}"
                )

                db.session.commit()

                flash("PDF updated successfully.", "success")

                if (
                    document.owner_id == current_user.id
                    or current_user.role == "admin"
                ):
                    return redirect(url_for("documents.dashboard"))

                return redirect(url_for("documents.shared_documents"))

            except ValueError as error:

                if os.path.exists(temp_path):
                    os.remove(temp_path)

                flash(str(error), "danger")

            except Exception:

                db.session.rollback()

                if os.path.exists(temp_path):
                    os.remove(temp_path)

                current_app.logger.exception(
                    "PDF editing failed"
                )

                flash("Could not save PDF changes.", "danger")

    return render_template(
        "edit_pdf.html",
        document=document,
        page_count=page_count
    )


# View documents shared with current user
@documents_bp.route("/shared")
@login_required
def shared_documents():

    permissions = DocumentPermission.query.filter_by(
        user_id=current_user.id
    ).all()

    documents = [
        permission.document
        for permission in permissions
        if permission.document is not None
    ]

    return render_template(
        "shared_documents.html",
        documents=documents,
        permissions=permissions
    )


# Update document permission
@documents_bp.route(
    "/permission/<int:document_id>/<int:user_id>",
    methods=["POST"]
)
@login_required
def update_permission(document_id, user_id):

    document = get_document(document_id)

    if (
        document.owner_id != current_user.id
        and current_user.role != "admin"
    ):
        abort(403)

    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        user_id=user_id
    ).first()

    if permission is None:
        abort(404)

    new_permission = request.form.get(
        "permission",
        ""
    ).strip().lower()

    if new_permission not in ["view", "edit"]:

        flash("Invalid permission.", "danger")
        return redirect(url_for("documents.dashboard"))

    permission.permission = new_permission

    log_activity(
        "PERMISSION_UPDATE",
        f"Changed permission for document {document.filename} "
        f"to {new_permission}"
    )

    db.session.commit()

    flash("Permission updated successfully.", "success")

    return redirect(url_for("documents.dashboard"))


# Remove document sharing permission
@documents_bp.route(
    "/unshare/<int:document_id>/<int:user_id>",
    methods=["POST"]
)
@login_required
def unshare_document(document_id, user_id):

    document = get_document(document_id)

    if (
        document.owner_id != current_user.id
        and current_user.role != "admin"
    ):
        abort(403)

    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        user_id=user_id
    ).first()

    if permission is None:
        abort(404)

    try:

        db.session.delete(permission)

        log_activity(
            "UNSHARE",
            f"Removed sharing access for document {document.filename}"
        )

        db.session.commit()

        flash("Document sharing access removed.", "success")

    except Exception:

        db.session.rollback()

        current_app.logger.exception(
            "Removing document sharing failed"
        )

        flash("Could not remove document sharing access.", "danger")

    return redirect(url_for("documents.dashboard"))
