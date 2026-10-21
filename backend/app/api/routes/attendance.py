from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import check_course_scope, require_roles, student_scope
from app.db.session import get_db
from app.models.user import User
from app.schemas.attendance import AttendanceCreate, AttendanceRead
from app.schemas.updates import AttendanceUpdate
from app.services import attendance_service, audit_service
from app.services.attendance_service import (
    AttendanceNotFoundError,
    CourseNotFoundError,
    DuplicateAttendanceError,
    StudentNotFoundError,
)

router = APIRouter(prefix="/students/{student_id}/attendance", tags=["attendance"])


@router.post(
    "",
    response_model=AttendanceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(student_scope)],
)
def record_attendance(
    student_id: int,
    payload: AttendanceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("lecturer")),
) -> AttendanceRead:
    """Record attendance. Lecturers only, and only for their own courses."""
    check_course_scope(db, user, payload.course_id)
    try:
        record = attendance_service.record_attendance(db, student_id, payload)
    except (StudentNotFoundError, CourseNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DuplicateAttendanceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    audit_service.record(db, user.id, "create", "attendance", resource_id=record.id, student_id=student_id)
    return record


@router.get("", response_model=list[AttendanceRead], dependencies=[Depends(student_scope)])
def list_attendance(
    student_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("advisor", "administrator", "lecturer")),
) -> list[AttendanceRead]:
    """List a student's attendance. Administrators can read but not change it."""
    rows = attendance_service.list_attendance(db, student_id)
    audit_service.record(db, user.id, "view", "attendance", student_id=student_id)
    return rows


@router.patch(
    "/{attendance_id}",
    response_model=AttendanceRead,
    dependencies=[Depends(student_scope)],
)
def update_attendance(
    student_id: int,
    attendance_id: int,
    payload: AttendanceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("lecturer")),
) -> AttendanceRead:
    """Correct an attendance status. The lecturer must teach the record's course."""
    try:
        existing = attendance_service.get_attendance(db, student_id, attendance_id)
    except AttendanceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    check_course_scope(db, user, existing.course_id)
    record = attendance_service.update_attendance(db, student_id, attendance_id, payload)
    audit_service.record(db, user.id, "update", "attendance", resource_id=attendance_id, student_id=student_id)
    return record