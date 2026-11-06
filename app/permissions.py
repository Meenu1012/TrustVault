
from app.models import DocumentPermission


# Check whether a user can access a document
def can_access_document(user, document):

    # Admin can access all documents
    if user.role == "admin":
        return True

    # Document owner can access their document
    if document.owner_id == user.id:
        return True

    # Check whether document is shared with this user
    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        user_id=user.id
    ).first()

    # Allow access if permission exists
    if permission:
        return True

    # Otherwise deny access
    return False


# Check whether a user can edit a document
def can_edit_document(user, document):

    # Admin can edit all documents
    if user.role == "admin":
        return True

    # Owner can edit their document
    if document.owner_id == user.id:
        return True

    # Check user's permission
    permission = DocumentPermission.query.filter_by(
        document_id=document.id,
        user_id=user.id
    ).first()

    # Only editor permission allows editing
    if permission and permission.permission == "edit":
        return True

    return False
