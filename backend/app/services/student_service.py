from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.student import Student
from app.schemas.student import StudentCreate
from app.schemas.updates import StudentUpdate


class DuplicateStudentNumberError(Exception):
    """Raised when a student number already exists. The route turns this into HTTP 409."""


class StudentNotFoundError(Exception):
    """Raised when the student doesn't exist."""


def create_student(db: Session, data: StudentCreate) -> Student:
    """Insert a new student and return it with its generated id and created_at."""
    # model_dump() turns the validated Pydantic object into a plain dictionary.
    # The ** operator passes each key-value pair as a keyword argument to Student.
    student = Student(**data.model_dump())
    db.add(student)
    try:
        db.commit()
    except IntegrityError as exc:
        # The unique constraint on student_number was violated. Roll back so the
        # session is usable again, then raise a domain-specific error.
        db.rollback()
        raise DuplicateStudentNumberError(
            f"Student number '{data.student_number}' already exists"
        ) from exc
    db.refresh(student)
    return student


def list_students(db: Session, limit: int, offset: int) -> list[Student]:
    """Return a page of students, ordered by id."""
    statement = select(Student).order_by(Student.id).limit(limit).offset(offset)
    return list(db.scalars(statement))


def get_student(db: Session, student_id: int) -> Student | None:
    """Return one student by id, or None if no such student exists."""
    return db.get(Student, student_id)


def update_student(db: Session, student_id: int, data: StudentUpdate) -> Student:
    """Change only the fields the client sent, then return the updated student."""
    student = db.get(Student, student_id)
    if student is None:
        raise StudentNotFoundError("Student not found")
    # exclude_unset=True leaves out any field the client did not send.
    for field_name, value in data.model_dump(exclude_unset=True).items():
        setattr(student, field_name, value)
    db.commit()
    db.refresh(student)
    return student