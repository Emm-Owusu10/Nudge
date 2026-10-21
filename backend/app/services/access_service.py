from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enrolment import Enrolment
from app.models.lecturer_course import LecturerCourse
from app.models.user import User


class AccessDeniedError(Exception):
    """Raised when a logged-in user may not see or change the requested record."""


def lecturer_teaches_course(db: Session, user_id: int, course_id: int) -> bool:
    """True if this lecturer is linked to the course."""
    link = db.scalar(
        select(LecturerCourse.id).where(
            LecturerCourse.user_id == user_id,
            LecturerCourse.course_id == course_id,
        )
    )
    return link is not None


def lecturer_can_see_student(db: Session, user_id: int, student_id: int) -> bool:
    """True if the student is enrolled in at least one course this lecturer teaches."""
    statement = (
        select(Enrolment.id)
        .join(LecturerCourse, LecturerCourse.course_id == Enrolment.course_id)
        .where(
            LecturerCourse.user_id == user_id,
            Enrolment.student_id == student_id,
        )
        .limit(1)
    )
    return db.scalar(statement) is not None


def ensure_student_access(db: Session, user: User, student_id: int) -> None:
    """Raise AccessDeniedError unless this user may see the student's records."""
    if user.role in ("advisor", "administrator"):
        return
    if user.role == "lecturer" and lecturer_can_see_student(db, user.id, student_id):
        return
    raise AccessDeniedError("You do not have access to this student")


def ensure_course_access(db: Session, user: User, course_id: int) -> None:
    """Raise AccessDeniedError if a lecturer tries to act on a course they don't teach."""
    if user.role != "lecturer":
        # Role checks on the route decide whether non-lecturers may write at all.
        return
    if not lecturer_teaches_course(db, user.id, course_id):
        raise AccessDeniedError("You do not teach this course")