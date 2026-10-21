from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enrolment import Enrolment
from app.models.student import Student
from app.schemas.enrolment import EnrolmentCreate


class StudentNotFoundError(Exception):
    """Raised when the student in the URL doesn't exist."""


class CourseNotFoundError(Exception):
    """Raised when the course in the request body doesn't exist."""


class DuplicateEnrolmentError(Exception):
    """Raised when the student is already enrolled in this course for this term."""


def create_enrolment(db: Session, student_id: int, data: EnrolmentCreate) -> Enrolment:
    """Enrol a student in a course for a term, after checking both exist."""
    # Check the parents first so the client gets a clear 404, not a raw
    # foreign-key error from PostgreSQL.
    if db.get(Student, student_id) is None:
        raise StudentNotFoundError("Student not found")
    if db.get(Course, data.course_id) is None:
        raise CourseNotFoundError("Course not found")

    enrolment = Enrolment(
        student_id=student_id,
        course_id=data.course_id,
        academic_term=data.academic_term,
    )
    db.add(enrolment)
    try:
        db.commit()
    except IntegrityError as exc:
        # The unique constraint on (student, course, term) was violated.
        db.rollback()
        raise DuplicateEnrolmentError(
            f"Student is already enrolled in course {data.course_id} for term {data.academic_term}"
        ) from exc
    db.refresh(enrolment)
    return enrolment


def list_enrolments(db: Session, student_id: int) -> list[Enrolment]:
    """Return all enrolments for one student, ordered by term and then id."""
    statement = (
        select(Enrolment)
        .where(Enrolment.student_id == student_id)
        .order_by(Enrolment.academic_term, Enrolment.id)
    )
    return list(db.scalars(statement))