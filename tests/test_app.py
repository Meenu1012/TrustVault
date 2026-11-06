
import io
import os
import uuid

from app import create_app, db
from app.models import User, Document, DocumentPermission
from werkzeug.security import generate_password_hash


def create_test_app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    return app


def unique_email(prefix):
    return f"{prefix}-{uuid.uuid4().hex}@example.com"


def create_user(name, email, password, role="user"):
    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role=role
    )
    db.session.add(user)
    db.session.commit()
    return user


def login_user(client, email, password, role="user"):
    return client.post(
        "/login",
        data={
            "email": email,
            "password": password,
            "role": role
        }
    )


# Test 1: Application starts successfully
def test_app_starts():
    app = create_test_app()
    assert app is not None


# Test 2: Homepage is publicly accessible
def test_home_page_is_accessible():
    app = create_test_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200


# Test 3: User registration works
def test_user_registration():
    app = create_test_app()
    client = app.test_client()

    email = unique_email("student")

    response = client.post(
        "/register",
        data={
            "name": "Test Student",
            "email": email,
            "password": "Student@123"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Registration successful" in response.data

    with app.app_context():
        user = User.query.filter_by(email=email).first()
        assert user is not None
        assert user.role == "user"


# Test 4: User login works
def test_user_login():
    app = create_test_app()
    client = app.test_client()

    email = unique_email("login")

    with app.app_context():
        create_user(
            "Login Student",
            email,
            "Student@123"
        )

    response = login_user(
        client,
        email,
        "Student@123"
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


# Test 5: Unauthorized users cannot view private documents
def test_unauthorized_user_cannot_view_document():
    app = create_test_app()

    owner_email = unique_email("owner")
    other_email = unique_email("other")

    with app.app_context():
        owner = create_user(
            "Document Owner",
            owner_email,
            "Owner@123"
        )

        other_user = create_user(
            "Other User",
            other_email,
            "Other@123"
        )

        unique_filename = f"private-{uuid.uuid4().hex}.pdf"

        document = Document(
            filename="private.pdf",
            stored_filename=unique_filename,
            owner_id=owner.id
        )

        db.session.add(document)
        db.session.commit()

        document_id = document.id

    client = app.test_client()

    login_response = login_user(
        client,
        other_email,
        "Other@123"
    )

    assert login_response.status_code == 302
    assert login_response.headers["Location"].endswith("/dashboard")

    response = client.get(f"/view/{document_id}")

    assert response.status_code == 403


# Test 6: User can upload an allowed document
def test_user_can_upload_document():
    app = create_test_app()
    client = app.test_client()

    email = unique_email("upload")

    with app.app_context():
        create_user(
            "Upload Student",
            email,
            "Student@123"
        )

    login_response = login_user(
        client,
        email,
        "Student@123"
    )

    assert login_response.status_code == 302
    assert login_response.headers["Location"].endswith("/dashboard")

    response = client.post(
        "/upload",
        data={
            "file": (
                io.BytesIO(b"TrustVault test document"),
                "sample.txt"
            )
        },
        content_type="multipart/form-data"
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")

    with app.app_context():
        user = User.query.filter_by(email=email).first()

        document = Document.query.filter_by(
            owner_id=user.id,
            filename="sample.txt"
        ).first()

        assert document is not None

        file_path = os.path.join(
            app.instance_path,
            "uploads",
            document.stored_filename
        )

        assert os.path.isfile(file_path)


# Test 7: View-only users cannot replace shared documents
def test_view_only_user_cannot_replace_document():
    app = create_test_app()

    owner_email = unique_email("replace-owner")
    viewer_email = unique_email("replace-viewer")

    with app.app_context():
        owner = create_user(
            "Replace Owner",
            owner_email,
            "Owner@123"
        )

        viewer = create_user(
            "View Only User",
            viewer_email,
            "Viewer@123"
        )

        unique_filename = f"view-only-{uuid.uuid4().hex}.txt"

        document = Document(
            filename=unique_filename,
            stored_filename=unique_filename,
            owner_id=owner.id
        )

        db.session.add(document)
        db.session.commit()

        document_id = document.id

        permission = DocumentPermission(
            document_id=document_id,
            user_id=viewer.id,
            permission="view"
        )

        db.session.add(permission)
        db.session.commit()

    client = app.test_client()

    login_response = login_user(
        client,
        viewer_email,
        "Viewer@123"
    )

    assert login_response.status_code == 302
    assert login_response.headers["Location"].endswith("/dashboard")

    response = client.post(
        f"/replace/{document_id}",
        data={
            "file": (
                io.BytesIO(b"Unauthorized replacement attempt"),
                "replacement.txt"
            )
        },
        content_type="multipart/form-data"
    )

    assert response.status_code == 403
