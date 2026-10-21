from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record(
    db: Session,
    user_id: int,
    action: str,
    resource: str,
    resource_id: int | None = None,
    student_id: int | None = None,
) -> None:
    """Store one audit entry. Call this only after the action has succeeded."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        student_id=student_id,
    )
    db.add(entry)
    db.commit()


def list_entries(db: Session, student_id: int | None, limit: int) -> list[AuditLog]:
    """Return the most recent audit entries, optionally for one student."""
    statement = select(AuditLog)
    if student_id is not None:
        statement = statement.where(AuditLog.student_id == student_id)
    statement = statement.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit)
    return list(db.scalars(statement))