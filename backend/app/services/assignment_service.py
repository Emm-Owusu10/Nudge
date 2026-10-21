from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.course import Course
from app.models.enrolment import Enrolment
from app.models.submission import Submission
from app.schemas.assignment import AssignmentCreate
from app.schemas.submission import SubmissionUpdate


class CourseNotFoundError(Exception):
    """Raised when the course for the assignment doesn't exist."""


class AssignmentNotFoundError(Exception):
    """Raised when the assignment doesn't exist."""


class SubmissionNotFoundError(Exception):
    """Raised when the submission doesn't exist."""


class DuplicateAssignmentError(Exception):
    """Raised when the same title already exists for this course and term."""


def create_assignment(db: Session, data: AssignmentCreate) -> Assignment:
    """Create an assignment and a 'missing' submission for every enrolled student."""
    if db.get(Course, data.course_id) is None:
        raise CourseNotFoundError("Course not found")

    assignment = Assignment(
        course_id=data.course_id,
        academic_term=data.academic_term,
        title=data.title,
        due_date=data.due_date,
    )
    try:
        db.add(assignment)
        # flush() sends the INSERT and assigns assignment.id, but doesn't commit.
        # Both inserts below stay in one transaction: either all of them are saved, or none are.
        db.flush()

        # Find students enrolled in this course for this term only.
        enrolled_student_ids = db.scalars(
            select(Enrolment.student_id).where(
                Enrolment.course_id == data.course_id,
                Enrolment.academic_term == data.academic_term,
            )
        ).all()

        db.add_all(
            [
                Submission(assignment_id=assignment.id, student_id=student_id, status="missing")
                for student_id in enrolled_student_ids
            ]
        )
        db.commit()
    except IntegrityError as exc:
        # Duplicate title for this course and term. Undo everything in this transaction.
        db.rollback()
        raise DuplicateAssignmentError(
            f"Assignment '{data.title}' already exists for this course and term"
        ) from exc

    db.refresh(assignment)
    return assignment


def get_assignment(db: Session, assignment_id: int) -> Assignment:
    """Return one assignment, or raise if it doesn't exist."""
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise AssignmentNotFoundError("Assignment not found")
    return assignment


def list_submissions(db: Session, assignment_id: int) -> list[Submission]:
    """Return every submission row for one assignment, ordered by student."""
    get_assignment(db, assignment_id)  # raises if the assignment doesn't exist
    statement = (
        select(Submission)
        .where(Submission.assignment_id == assignment_id)
        .order_by(Submission.student_id)
    )
    return list(db.scalars(statement))


def update_submission(db: Session, submission_id: int, data: SubmissionUpdate) -> Submission:
    """Set the status and date of one submission."""
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise SubmissionNotFoundError("Submission not found")

    submission.status = data.status
    submission.submitted_on = data.submitted_on
    db.commit()
    db.refresh(submission)
    return submission

def get_submission(db: Session, submission_id: int) -> Submission:
    """Return one submission row, or raise if it doesn't exist."""
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise SubmissionNotFoundError("Submission not found")
    return submission