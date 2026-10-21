from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.course import Course
from app.models.enrolment import Enrolment
from app.models.lecturer_course import LecturerCourse
from app.models.student import Student
from app.schemas.student import StudentCreate  # noqa: F401  (documents the expected body shape)

TEST_PASSWORD = "correct-horse-battery"
TERM = "2026-S1"


import pytest


@pytest.fixture
def school(db, make_user):
    """Two courses, two students, and two lecturers. Anna teaches CS101 and Ben teaches MATH200."""
    cs101 = Course(code="CS101", title="Intro")
    math200 = Course(code="MATH200", title="Calculus")
    student_a = Student(student_number="S1001", full_name="Student A", programme="CS")
    student_b = Student(student_number="S2002", full_name="Student B", programme="Maths")
    db.add_all([cs101, math200, student_a, student_b])
    db.flush()
    db.add(Enrolment(student_id=student_a.id, course_id=cs101.id, academic_term=TERM))
    db.add(Enrolment(student_id=student_b.id, course_id=math200.id, academic_term=TERM))
    db.commit()

    anna_id = make_user("anna", TEST_PASSWORD, "lecturer")
    ben_id = make_user("ben", TEST_PASSWORD, "lecturer")
    make_user("advisor", TEST_PASSWORD, "advisor")
    make_user("admin", TEST_PASSWORD, "administrator")

    db.add(LecturerCourse(user_id=anna_id, course_id=cs101.id))
    db.add(LecturerCourse(user_id=ben_id, course_id=math200.id))
    db.commit()

    return {
        "cs101": cs101.id,
        "math200": math200.id,
        "student_a": student_a.id,
        "student_b": student_b.id,
    }


def attendance_payload(course_id: int, status: str = "present") -> dict:
    return {"course_id": course_id, "session_date": "2026-09-01", "status": status}


def test_request_without_a_token_is_rejected(client, school):
    assert client.get("/students").status_code == 401


def test_lecturer_cannot_create_a_student(school, login_client):
    anna = login_client("anna")

    response = anna.post(
        "/students",
        json={"student_number": "S3003", "full_name": "New", "programme": "CS"},
    )

    assert response.status_code == 403


def test_administrator_cannot_record_attendance(school, login_client):
    admin = login_client("admin")

    response = admin.post(
        f"/students/{school['student_a']}/attendance",
        json=attendance_payload(school["cs101"]),
    )

    assert response.status_code == 403


def test_lecturer_records_attendance_for_own_course(school, login_client):
    anna = login_client("anna")

    response = anna.post(
        f"/students/{school['student_a']}/attendance",
        json=attendance_payload(school["cs101"]),
    )

    assert response.status_code == 201


def test_lecturer_cannot_record_for_a_student_outside_their_courses(school, login_client):
    anna = login_client("anna")

    response = anna.post(
        f"/students/{school['student_b']}/attendance",
        json=attendance_payload(school["math200"]),
    )

    assert response.status_code == 404


def test_lecturer_cannot_record_in_a_course_they_do_not_teach(school, login_client):
    anna = login_client("anna")

    response = anna.post(
        f"/students/{school['student_a']}/attendance",
        json=attendance_payload(school["math200"]),
    )

    assert response.status_code == 404


def test_roster_shows_only_the_lecturers_own_courses(school, login_client):
    anna = login_client("anna")

    own = anna.get(f"/courses/{school['cs101']}/students")
    other = anna.get(f"/courses/{school['math200']}/students")

    assert own.status_code == 200
    assert [row["student_number"] for row in own.json()] == ["S1001"]
    assert other.status_code == 404


def test_lecturer_cannot_read_a_student_outside_their_scope(school, login_client):
    anna = login_client("anna")

    response = anna.get(f"/students/{school['student_b']}")

    assert response.status_code == 404


def test_advisor_can_read_any_student(school, login_client):
    advisor = login_client("advisor")

    response = advisor.get(f"/students/{school['student_b']}")

    assert response.status_code == 200


def test_administrator_cannot_evaluate_flags(school, login_client):
    admin = login_client("admin")

    response = admin.post(
        f"/students/{school['student_a']}/flags/evaluate",
        params={"as_of": "2026-10-19"},
    )

    assert response.status_code == 403


def test_lecturer_cannot_read_follow_ups(school, login_client):
    anna = login_client("anna")

    response = anna.get("/interventions/1/follow-up")

    assert response.status_code == 403


def test_only_administrators_read_the_audit_log(school, login_client):
    advisor = login_client("advisor")
    admin = login_client("admin")

    assert advisor.get("/audit-logs").status_code == 403
    assert admin.get("/audit-logs").status_code == 200


def test_viewing_indicators_writes_an_audit_entry(school, login_client, db):
    advisor = login_client("advisor")

    response = advisor.get(
        f"/students/{school['student_a']}/indicators",
        params={"as_of": "2026-10-19"},
    )

    assert response.status_code == 200
    entries = db.scalars(select(AuditLog)).all()
    assert len(entries) == 1
    assert entries[0].action == "view"
    assert entries[0].resource == "indicators"
    assert entries[0].student_id == school["student_a"]


def test_lecturer_cannot_change_a_submission_outside_their_course(school, login_client):
    anna = login_client("anna")
    ben = login_client("ben")
    assignment_id = anna.post(
        "/assignments",
        json={
            "course_id": school["cs101"],
            "academic_term": TERM,
            "title": "Essay 1",
            "due_date": "2026-11-15",
        },
    ).json()["id"]
    submission_id = anna.get(f"/assignments/{assignment_id}/submissions").json()[0]["id"]

    response = ben.put(
        f"/submissions/{submission_id}",
        json={"status": "missing"},
    )

    assert response.status_code == 404