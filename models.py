from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Boolean, Enum as SQLALchemyEnum
from sqlalchemy.orm import Mapped

# Import the initialized db from your main app
from app import db

# Table name constants
# This MUST match the Expenses app to share the same user pool
USERS_TABLE = "users"
WORKFLOWS_TABLE = "workflows"
QUOTES_TABLE = "quotes"
AUDIT_LOGS_TABLE = "audit_logs"
POD_SUBMISSIONS_TABLE = "pod_submissions"

class Role(str, Enum):
    """Matches the enum values in the Expenses app user_role type."""
    EMPLOYEE = "EMPLOYEE"
    SUPERVISOR = "SUPERVISOR"
    FINANCE = "FINANCE"
    ADMIN = "ADMIN"

class User(db.Model):
    """
    Paperwork Portal User model.
    Inherits the schema from the Expenses App to allow shared authentication.
    """
    __tablename__ = USERS_TABLE

    # Core identification (Shared with Expenses App)
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    
    # Name fields (Shared with Expenses App)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    name = db.Column(db.String(120))  # Full name field used in some Expenses views
    
    # Authentication & Access (Shared with Expenses App)
    password_hash = db.Column(db.String(255), nullable=False)
    role: Mapped[str] = db.Column(
        SQLALchemyEnum(
            "EMPLOYEE",
            "SUPERVISOR",
            "FINANCE",
            "ADMIN",
            name="user_role", # Must match the existing Postgres enum type name
        ),
        nullable=False,
        default="EMPLOYEE",
    )
    employee_approved: Mapped[bool] = db.Column(Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def can_access_portal(self) -> bool:
        """Standard FSI guard check."""
        return self.employee_approved and self.is_active


class PodSubmission(db.Model):
    """Persists POD metadata and uploaded file URI for audit/history purposes."""

    __tablename__ = POD_SUBMISSIONS_TABLE

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(f"{USERS_TABLE}.id"), nullable=False, index=True)
    pod_reference = db.Column(db.String(120), nullable=False)
    uploaded_file_uri = db.Column(db.String(1024), nullable=False)
    pod_picture_url = db.Column(db.String(1024), nullable=True)
    captured_signature_url = db.Column(db.String(1024), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
