# Importing every model here registers it with Base.metadata. Alembic reads
# that registry to generate migrations, so every model must be imported.
from app.models.assessment import Assessment
from app.models.assignment import Assignment
from app.models.attendance import Attendance
from app.models.audit_log import AuditLog
from app.models.course import Course
from app.models.enrolment import Enrolment
from app.models.flag import Flag
from app.models.intervention import Intervention
from app.models.lecturer_course import LecturerCourse
from app.models.student import Student
from app.models.submission import Submission
from app.models.user import User

__all__ = [
    "Assessment",
    "Assignment",
    "Attendance",
    "AuditLog",
    "Course",
    "Enrolment",
    "Flag",
    "Intervention",
    "LecturerCourse",
    "Student",
    "Submission",
    "User",
]