from enum import Enum

from app import db


# Central registry for core table names.
# Add new SQLAlchemy table constants here before using them in models/migrations.
USERS_TABLE = "users"
WORKFLOWS_TABLE = "workflows"
QUOTES_TABLE = "quotes"
AUDIT_LOGS_TABLE = "audit_logs"


class Role(str, Enum):
    EMPLOYEE = "EMPLOYEE"
    SUPERVISOR = "SUPERVISOR"
    FINANCE = "FINANCE"
    ADMIN = "ADMIN"

class ReportStatus(Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"


class User(db.Model):
    __tablename__ = USERS_TABLE
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    role = db.Column(db.Enum(Role), default=Role.EMPLOYEE)
    employee_approved = db.Column(db.Boolean, default=False)

    def can_access_portal(self) -> bool:
        return self.employee_approved
