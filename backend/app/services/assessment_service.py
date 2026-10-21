from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.course import Course
from app.models.student import Student
from app.schemas.assessment import AssessmentCreate
from app.schemas.updates import AssessmentUpdate


class StudentNotFoundError(Exception):
    """Raised when the student in the URL doesn't exist."""


class CourseNotFoundError(Exception):
    """Raised when the course in the request body doesn't exist."""


class AssessmentNotFoundError(Exception):
    """Raised when the assessment doesn't exist for this student."""


def record_assessment(db: Session, student_id: int, data: AssessmentCreate) -> Assessment:
    """Store one assessment score after checking that the student and course exist."""
    if db.get(Student, student_id) is None:
        raise StudentNotFoundError("Student not found")
    if db.get(Course, data.course_id) is None:
        raise CourseNotFoundError("Course not found")

    assessment = Assessment(
        student_id=student_id,
        course_id=data.course_id,
        title=data.title,
        assessed_on=data.assessed_on,
        score=data.score,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def list_assessments(db: Session, student_id: int) -> list[Assessment]:
    """Return one student's assessments, oldest first."""
    statement = (
        select(Assessment)
        .where(Assessment.student_id == student_id)
        .order_by(Assessment.assessed_on, Assessment.id)
    )
    return list(db.scalars(statement))


def update_assessment(
    db: Session, student_id: int, assessment_id: int, data: AssessmentUpdate
) -> Assessment:
    """Change the title, date or score of one assessment that belongs to this student."""
    record = db.scalar(
        select(Assessment).where(
            Assessment.id == assessment_id,
            Assessment.student_id == student_id,
        )
    )
    if record is None:
        raise AssessmentNotFoundError("Assessment not found")
    for field_name, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field_name, value)
    db.commit()
    db.refresh(record)
    return record

def get_assessment(db: Session, student_id: int, assessment_id: int) -> Assessment:
    """Return one assessment that belongs to this student, or raise."""
    record = db.scalar(
        select(Assessment).where(
            Assessment.id == assessment_id,
            Assessment.student_id == student_id,
        )
    )
    if record is None:
        raise AssessmentNotFoundError("Assessment not found")
    return record