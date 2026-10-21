from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.course import Course
from app.models.student import Student
from app.schemas.attendance import AttendanceCreate
from app.schemas.updates import AttendanceUpdate


class StudentNotFoundError(Exception):
    """Raised when the student in the URL doesn't exist."""


class CourseNotFoundError(Exception):
    """Raised when the course in the request body doesn't exist."""


class DuplicateAttendanceError(Exception):
    """Raised when a record already exists for this student, course and session date."""


class AttendanceNotFoundError(Exception):
    """Raised when the attendance record doesn't exist for this student."""


def record_attendance(db: Session, student_id: int, data: AttendanceCreate) -> Attendance:
    """Store one attendance record after checking that the student and course exist."""
    if db.get(Student, student_id) is None:
        raise StudentNotFoundError("Student not found")
    if db.get(Course, data.course_id) is None:
        raise CourseNotFoundError("Course not found")

    record = Attendance(
        student_id=student_id,
        course_id=data.course_id,
        session_date=data.session_date,
        status=data.status,
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError as exc:
        # The unique constraint blocked a second record for the same session.
        db.rollback()
        raise DuplicateAttendanceError(
            f"Attendance already recorded for {data.session_date.isoformat()}"
        ) from exc
    db.refresh(record)
    return record


def list_attendance(db: Session, student_id: int) -> list[Attendance]:
    """Return one student's attendance records, oldest session first."""
    statement = (
        select(Attendance)
        .where(Attendance.student_id == student_id)
        .order_by(Attendance.session_date, Attendance.id)
    )
    return list(db.scalars(statement))


def update_attendance(
    db: Session, student_id: int, attendance_id: int, data: AttendanceUpdate
) -> Attendance:
    """Change the status of one attendance record that belongs to this student."""
    # Filtering by student_id as well means a record belonging to another student
    # is reported as not found, rather than being editable through this URL.
    record = db.scalar(
        select(Attendance).where(
            Attendance.id == attendance_id,
            Attendance.student_id == student_id,
        )
    )
    if record is None:
        raise AttendanceNotFoundError("Attendance record not found")
    for field_name, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field_name, value)
    db.commit()
    db.refresh(record)
    return record

def get_attendance(db: Session, student_id: int, attendance_id: int) -> Attendance:
    """Return one attendance record that belongs to this student, or raise."""
    record = db.scalar(
        select(Attendance).where(
            Attendance.id == attendance_id,
            Attendance.student_id == student_id,
        )
    )
    if record is None:
        raise AttendanceNotFoundError("Attendance record not found")
    return record