from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import check_course_scope, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.submission import SubmissionRead, SubmissionUpdate
from app.services import assignment_service, audit_service
from app.services.assignment_service import SubmissionNotFoundError

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.put("/{submission_id}", response_model=SubmissionRead)
def update_submission(
    submission_id: int,
    payload: SubmissionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("lecturer")),
) -> SubmissionRead:
    """Replace a submission's status and date. The lecturer must teach the assignment's course."""
    try:
        existing = assignment_service.get_submission(db, submission_id)
    except SubmissionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    assignment = assignment_service.get_assignment(db, existing.assignment_id)
    check_course_scope(db, user, assignment.course_id, not_found_detail="Submission not found")

    submission = assignment_service.update_submission(db, submission_id, payload)
    audit_service.record(
        db, user.id, "update", "submission",
        resource_id=submission_id, student_id=submission.student_id,
    )
    return submission