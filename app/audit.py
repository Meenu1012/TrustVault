
from app import db
from app.models import AuditLog


# Function to record user activities
def record_activity(user_id, action, details):

    # Create a new activity record
    new_log = AuditLog(
        user_id=user_id,
        action=action,
        details=details
    )

    # Save the activity in the database
    db.session.add(new_log)
    db.session.commit()
