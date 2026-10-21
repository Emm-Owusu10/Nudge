from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import check_course_scope, require_roles, student_scope
from app.db.session import get_db
from app.models.user import User
from app.schemas.assessment import AssessmentCreate, AssessmentRead
from app.schemas.updates import AssessmentUpdate
from app.services import assessment_service, audit_service
from app.services.assessment_service import (
    AssessmentNotFoundError,
    CourseNotFoundError,
    StudentNotFoundError,
)

router = APIRouter(prefix="/students/{student_id}/assessments", tags=["assessments"])


@router.post(
    "",
    response_model=AssessmentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(student_scope)],
)
def record_assessment(
    student_id: int,
    payload: AssessmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("lecturer")),
) -> AssessmentRead:
    """Record an assessment score. Lecturers only, and only for their own courses."""
    check_course_scope(db, user, payload.course_id)
    try:
        assessment = assessment_service.record_assessment(db, student_id, payload)
    except (StudentNotFoundError, CourseNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    audit_service.record(db, user.id, "create", "assessment", resource_id=assessment.id, student_id=student_id)
    return assessment


@router.get("", response_model=list[AssessmentRead], dependencies=[Depends(student_scope)])
def list_assessments(
    student_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("advisor", "administrator", "lecturer")),
) -> list[AssessmentRead]:
    """List a student's assessment scores."""
    rows = assessment_service.list_assessments(db, student_id)
    audit_service.record(db, user.id, "view", "assessments", student_id=student_id)
    return rows


@router.patch(
    "/{assessment_id}",
    response_model=AssessmentRead,
    dependencies=[Depends(student_scope)],
)
def update_assessment(
    student_id: int,
    assessment_id: int,
    payload: AssessmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("lecturer")),
) -> AssessmentRead:
    """Correct an assessment. The lecturer must teach the assessment's course."""
    try:
        existing = assessment_service.get_assessment(db, student_id, assessment_id)
    except AssessmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    check_course_scope(db, user, existing.course_id)
    assessment = assessment_service.update_assessment(db, student_id, assessment_id, payload)
    audit_service.record(db, user.id, "update", "assessment", resource_id=assessment_id, student_id=student_id)
    return assessment