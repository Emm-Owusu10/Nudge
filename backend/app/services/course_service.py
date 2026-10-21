from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enrolment import Enrolment
from app.models.student import Student
from app.schemas.course import CourseCreate
from app.schemas.updates import CourseUpdate


class DuplicateCourseCodeError(Exception):
    """Raised when a course code already exists. The route turns this into HTTP 409."""


class CourseNotFoundError(Exception):
    """Raised when the course doesn't exist."""


def create_course(db: Session, data: CourseCreate) -> Course:
    """Insert a new course and return it with its generated id."""
    course = Course(**data.model_dump())
    db.add(course)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateCourseCodeError(f"Course code '{data.code}' already exists") from exc
    db.refresh(course)
    return course


def list_courses(db: Session, limit: int, offset: int) -> list[Course]:
    """Return a page of courses, ordered by id."""
    statement = select(Course).order_by(Course.id).limit(limit).offset(offset)
    return list(db.scalars(statement))


def get_course(db: Session, course_id: int) -> Course | None:
    """Return one course by id, or None if it doesn't exist."""
    return db.get(Course, course_id)


def update_course(db: Session, course_id: int, data: CourseUpdate) -> Course:
    """Change the course title. The code is locked."""
    course = db.get(Course, course_id)
    if course is None:
        raise CourseNotFoundError("Course not found")
    for field_name, value in data.model_dump(exclude_unset=True).items():
        setattr(course, field_name, value)
    db.commit()
    db.refresh(course)
    return course


def list_course_students(
    db: Session, course_id: int, academic_term: str | None = None
) -> list[Student]:
    """Return the students enrolled in a course, optionally for one term, ordered by student number."""
    if db.get(Course, course_id) is None:
        raise CourseNotFoundError("Course not found")
    statement = (
        select(Student)
        .join(Enrolment, Enrolment.student_id == Student.id)
        .where(Enrolment.course_id == course_id)
    )
    if academic_term is not None:
        statement = statement.where(Enrolment.academic_term == academic_term)
    statement = statement.distinct().order_by(Student.student_number)
    return list(db.scalars(statement))