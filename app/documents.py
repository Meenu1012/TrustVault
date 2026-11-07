
import os
import io
import uuid
import mimetypes

import pymupdf

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_file,
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

STORAGE_BUCKET = "trustvault-documents"


# Local upload folder
def get_upload_folder():

    folder = os.path.join(
        current_app.instance_path,
        "uploads"
    )

    os.makedirs(folder, exist_ok=True)

    return folder


# Check whether Supabase Storage should be used
def use_supabase_storage():

    return (
        bool(current_app.extensions.get("supabase"))
        and not os.environ.get("TESTING")
    )


# Save a document to Supabase or local storage
def store_file(stored_filename, data, content_type=None, upsert=False):

    if use_supabase_storage():

        bucket = current_app.extensions["supabase"].storage.from_(
            STORAGE_BUCKET
        )

        bucket.upload(
            stored_filename,
            data,
            file_options={
                "content-type": content_type or "application/octet-stream",
                "upsert": str(upsert).lower()
            }
        )

    else:

        path = os.path.join(
            get_upload_folder(),
            stored_filename
        )

        with open(path, "wb") as file:
            file.write(data)


# Read a document from Supabase or local storage
def read_file(stored_filename):

    if use_supabase_storage():

        bucket = current_app.extensions["supabase"].storage.from_(
            STORAGE_BUCKET
        )

        return bucket.download(stored_filename)

    path = os.path.join(
        get_upload_folder(),
        stored_filename
    )

    with open(path, "rb") as file:
        return file.read()


# Delete a document from Supabase or local storage
def delete_file(stored_filename):

    if use_supabase_storage():

        bucket = current_app.extensions["supabase"].storage.from_(
            STORAGE_BUCKET
        )

        bucket.remove([stored_filename])

    else:

        path = os.path.join(
            get_upload_folder(),
            stored_filename
        )

        if os.path.exists(path):
            os.remove(path)


# Read document bytes safely
def get_document_bytes(stored_filename):

    try:

        return read_file(stored_filename)

    except Exception:

        current_app.logger.exception(
            "Could not read stored document: %s",
            stored_filename
        )

        abort(404)


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

    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        user_id=current_user.id
    ).first()

    return permission is not None


# Check document edit permission
def can_edit_document(document):

    if document.owner_id == current_user.id:
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

    uploaded = False

    try:

        file_data = file.read()

        store_file(
            stored_filename,
            file_data,
            content_type=file.mimetype
        )

        uploaded = True

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

        if uploaded:

            try:
                delete_file(stored_filename)

            except Exception:
                current_app.logger.exception(
                    "Could not clean up failed upload"
                )

        current_app.logger.exception("Document upload failed")

        flash("Document upload failed.", "danger")

    return redirect(url_for("documents.dashboard"))


# View document
@documents_bp.route("/view/<int:document_id>")
@login_required
def view_document(document_id):

    document = get_document(document_id)

    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        user_id=current_user.id
    ).first()

    current_app.logger.warning(
        "ACCESS CHECK: user_id=%s, role=%s, owner_id=%s, permission=%s",
        current_user.id,
        current_user.role,
        document.owner_id,
        permission.permission if permission else "NONE"
    )

    if not can_access_document(document):
        abort(403)

    file_data = get_document_bytes(
        document.stored_filename
    )

    log_activity(
        "VIEW",
        f"Viewed document: {document.filename}"
    )

    db.session.commit()

    content_type = (
        mimetypes.guess_type(document.filename)[0]
        or "application/octet-stream"
    )

    return send_file(
        io.BytesIO(file_data),
        mimetype=content_type,
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

    file_data = get_document_bytes(
        document.stored_filename
    )

    log_activity(
        "DOWNLOAD",
        f"Downloaded document: {document.filename}"
    )

    db.session.commit()

    return send_file(
        io.BytesIO(file_data),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name=document.filename
    )


# Replace document
@documents_bp.route(
    "/replace/<int:document_id>",
    methods=["GET", "POST"]
)
@login_required
def replace_document(document_id):

    document = get_document(document_id)

    if not can_edit_document(document):
        abort(403)

    if request.method == "GET":

        flash(
            "Please use the replacement form to upload a file.",
            "info"
        )

        if document.owner_id == current_user.id:
            return redirect(url_for("documents.dashboard"))

        return redirect(url_for("documents.shared_documents"))

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

    new_stored_filename = (
        str(uuid.uuid4()) + "_" + new_original_filename
    )

    old_stored_filename = document.stored_filename

    uploaded = False

    try:

        file_data = file.read()

        store_file(
            new_stored_filename,
            file_data,
            content_type=file.mimetype
        )

        uploaded = True

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

        if uploaded:

            try:
                delete_file(new_stored_filename)

            except Exception:
                current_app.logger.exception(
                    "Could not clean up replacement file"
                )

        current_app.logger.exception(
            "Document replacement failed"
        )

        flash("Could not replace the document.", "danger")

        if document.owner_id == current_user.id:
            return redirect(url_for("documents.dashboard"))

        return redirect(url_for("documents.shared_documents"))

    try:

        delete_file(old_stored_filename)

    except Exception:

        current_app.logger.exception(
            "Could not remove old document"
        )

    flash("Document replaced successfully.", "success")

    if document.owner_id == current_user.id:
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

    stored_filename = document.stored_filename
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

    except Exception:

        db.session.rollback()

        current_app.logger.exception("Document deletion failed")

        flash("Could not delete document.", "danger")

        return redirect(url_for("documents.dashboard"))

    try:

        delete_file(stored_filename)

    except Exception:

        current_app.logger.exception(
            "Document database record deleted, but storage cleanup failed"
        )

    flash("Document deleted successfully.", "success")

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

    original_data = get_document_bytes(
        document.stored_filename
    )

    if request.method == "GET":

        try:

            content = original_data.decode("utf-8")

        except UnicodeDecodeError:

            flash("Unsupported text file encoding.", "danger")
            return redirect(url_for("documents.shared_documents"))

        return render_template(
            "edit_document.html",
            document=document,
            content=content
        )

    new_content = request.form.get("content", "")

    try:

        new_data = new_content.encode("utf-8")

        store_file(
            document.stored_filename,
            new_data,
            content_type="text/plain",
            upsert=True
        )

        log_activity(
            "DOCUMENT_EDIT",
            f"Edited TXT document: {document.filename}"
        )

        db.session.commit()

        flash("Document changes saved successfully.", "success")

        if document.owner_id == current_user.id:
            return redirect(url_for("documents.dashboard"))

        return redirect(url_for("documents.shared_documents"))

    except Exception:

        db.session.rollback()

        try:

            store_file(
                document.stored_filename,
                original_data,
                content_type="text/plain",
                upsert=True
            )

        except Exception:

            current_app.logger.exception(
                "Could not restore original TXT document"
            )

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

    # Check edit permission
    if not can_edit_document(document):
        abort(403)

    if not document.filename.lower().endswith(".pdf"):
        abort(400, description="Only PDF files can be edited.")

    original_data = get_document_bytes(
        document.stored_filename
    )

    try:

        with pymupdf.open(
            stream=original_data,
            filetype="pdf"
        ) as pdf:

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

            try:

                with pymupdf.open(
                    stream=original_data,
                    filetype="pdf"
                ) as pdf:

                    page = pdf[page_number - 1]

                    # Find the lowest existing text position.
                    # This prevents new text from being placed
                    # over the document heading or body.
                    existing_blocks = page.get_text("blocks")

                    if existing_blocks:

                        last_text_position = max(
                            block[3]
                            for block in existing_blocks
                            if block[6] == 0
                        ) if any(
                            block[6] == 0
                            for block in existing_blocks
                        ) else 72

                    else:

                        last_text_position = 72

                    # Place new text below the existing content.
                    start_y = max(
                        72,
                        last_text_position + 25
                    )

                    text_rect = pymupdf.Rect(
                        72,
                        start_y,
                        page.rect.width - 36,
                        page.rect.height - 36
                    )

                    if text_rect.height < 40:

                        raise ValueError(
                            "There is not enough blank space below "
                            "the existing content on this page. "
                            "Please select another page."
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
                            "The text is too long for the available "
                            "blank space. Please shorten the text "
                            "or select another page."
                        )

                    edited_data = pdf.tobytes(
                        garbage=4,
                        deflate=True
                    )

                # Save the edited PDF
                store_file(
                    document.stored_filename,
                    edited_data,
                    content_type="application/pdf",
                    upsert=True
                )

                log_activity(
                    "PDF_EDIT",
                    f"Edited PDF document: {document.filename}"
                )

                db.session.commit()

                flash(
                    "PDF updated successfully.",
                    "success"
                )

                if document.owner_id == current_user.id:
                    return redirect(url_for("documents.dashboard"))

                return redirect(url_for("documents.shared_documents"))

            except ValueError as error:

                flash(str(error), "danger")

            except Exception:

                db.session.rollback()

                try:

                    store_file(
                        document.stored_filename,
                        original_data,
                        content_type="application/pdf",
                        upsert=True
                    )

                except Exception:

                    current_app.logger.exception(
                        "Could not restore original PDF"
                    )

                current_app.logger.exception(
                    "PDF editing failed"
                )

                flash(
                    "Could not save PDF changes.",
                    "danger"
                )

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
