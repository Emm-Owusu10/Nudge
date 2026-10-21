from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    """One audit entry as returned to an administrator."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    action: str
    resource: str
    resource_id: int | None
    student_id: int | None
    created_at: datetime