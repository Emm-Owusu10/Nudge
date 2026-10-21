import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.audit_log import AuditLog
from app.models.course import Course
from app.models.enrolment import Enrolment
from app.models.lecturer_course import LecturerCourse
from app.models.student import Student
from app.models.user import User
from app.services import audit_service
from app.services.access_service import (
    AccessDeniedError,
    ensure_course_access,
    ensure_student_access,
)


def build_school(db):
    """Two courses and two students. Anna teaches CS101 and Ben teaches MATH200."""
    cs101 = Course(code="CS101", title="Intro")
    math200 = Course(code="MATH200", title="Calculus")
    student_a = Student(student_number="S1001", full_name="Student A", programme="CS")
    student_b = Student(student_number="S2002", full_name="Student B", programme="Maths")
    db.add_all([cs101, math200, student_a, student_b])
    db.flush()

    db.add(Enrolment(student_id=student_a.id, course_id=cs101.id, academic_term="2026-S1"))
    db.add(Enrolment(student_id=student_b.id, course_id=math200.id, academic_term="2026-S1"))

    anna = User(username="anna", password_hash="unused", role="lecturer")
    ben = User(username="ben", password_hash="unused", role="lecturer")
    advisor = User(username="advisor", password_hash="unused", role="advisor")
    db.add_all([anna, ben, advisor])
    db.flush()

    db.add(LecturerCourse(user_id=anna.id, course_id=cs101.id))
    db.add(LecturerCourse(user_id=ben.id, course_id=math200.id))
    db.commit()

    return {
        "cs101": cs101.id,
        "math200": math200.id,
        "student_a": student_a.id,
        "student_b": student_b.id,
        "anna": anna.id,
        "ben": ben.id,
        "advisor": advisor.id,
    }


def test_lecturer_can_see_a_student_in_their_course(db):
    ids = build_school(db)
    anna = db.get(User, ids["anna"])

    ensure_student_access(db, anna, ids["student_a"])  # raises if denied


def test_lecturer_cannot_see_a_student_outside_their_courses(db):
    ids = build_school(db)
    anna = db.get(User, ids["anna"])

    with pytest.raises(AccessDeniedError):
        ensure_student_access(db, anna, ids["student_b"])


def test_advisor_can_see_every_student(db):
    ids = build_school(db)
    advisor = db.get(User, ids["advisor"])

    ensure_student_access(db, advisor, ids["student_a"])
    ensure_student_access(db, advisor, ids["student_b"])


def test_lecturer_cannot_act_on_a_course_they_do_not_teach(db):
    ids = build_school(db)
    anna = db.get(User, ids["anna"])

    ensure_course_access(db, anna, ids["cs101"])  # her own course: allowed
    with pytest.raises(AccessDeniedError):
        ensure_course_access(db, anna, ids["math200"])


def test_audit_entry_records_who_did_what_and_to_whom(db):
    ids = build_school(db)

    audit_service.record(
        db,
        user_id=ids["advisor"],
        action="view",
        resource="indicators",
        student_id=ids["student_a"],
    )

    entries = db.scalars(select(AuditLog)).all()
    assert len(entries) == 1
    assert entries[0].user_id == ids["advisor"]
    assert entries[0].action == "view"
    assert entries[0].resource == "indicators"
    assert entries[0].student_id == ids["student_a"]
    assert entries[0].created_at is not None


def test_audit_rejects_an_unknown_action(db):
    ids = build_school(db)

    with pytest.raises(IntegrityError):
        audit_service.record(db, user_id=ids["advisor"], action="delete", resource="student")