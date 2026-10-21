TERM = "2026-S1"
STUDENT = {"student_number": "S1001", "full_name": "Test Student", "programme": "Computer Science"}
COURSE = {"code": "CS101", "title": "Introduction to Programming"}
AS_OF = "2026-10-19"


def setup_student_with_low_attendance(staff, link_lecturer):
    """Create a student whose recent attendance is 0% over five counted sessions."""
    admin = staff["admin"]
    student_id = admin.post("/students", json=STUDENT).json()["id"]
    course_id = admin.post("/courses", json=COURSE).json()["id"]
    admin.post(f"/students/{student_id}/enrolments", json={"course_id": course_id, "academic_term": TERM})
    link_lecturer(course_id)
    lecturer = staff["lecturer"]
    for day in ["2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09"]:
        lecturer.post(
            f"/students/{student_id}/attendance",
            json={"course_id": course_id, "session_date": day, "status": "absent"},
        )
    return student_id


def evaluate(advisor, student_id, as_of=AS_OF):
    return advisor.post(f"/students/{student_id}/flags/evaluate", params={"as_of": as_of})


def test_low_attendance_creates_a_monitor_flag(staff, link_lecturer):
    student_id = setup_student_with_low_attendance(staff, link_lecturer)

    response = evaluate(staff["advisor"], student_id)

    assert response.status_code == 200
    body = response.json()
    assert body["level"] == "monitor"
    assert body["status"] == "open"
    assert [factor["code"] for factor in body["factors"]] == ["low_attendance"]


def test_evaluating_the_same_date_returns_the_same_flag(staff, link_lecturer):
    student_id = setup_student_with_low_attendance(staff, link_lecturer)
    advisor = staff["advisor"]

    first = evaluate(advisor, student_id).json()
    second = evaluate(advisor, student_id).json()

    assert first["id"] == second["id"]
    assert len(advisor.get(f"/students/{student_id}/flags").json()) == 1


def test_no_concerns_returns_null(staff):
    student_id = staff["admin"].post("/students", json=STUDENT).json()["id"]

    response = evaluate(staff["advisor"], student_id)

    assert response.status_code == 200
    assert response.json() is None


def test_evaluating_missing_student_returns_404(staff):
    response = evaluate(staff["advisor"], student_id=999)

    assert response.status_code == 404


def test_dismissing_a_flag_records_the_reason(staff, link_lecturer):
    student_id = setup_student_with_low_attendance(staff, link_lecturer)
    advisor = staff["advisor"]
    flag_id = evaluate(advisor, student_id).json()["id"]

    response = advisor.post(
        f"/flags/{flag_id}/dismiss",
        json={"reason": "Student has a documented medical absence"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "dismissed"
    assert body["dismissal_reason"] == "Student has a documented medical absence"
    assert body["dismissed_at"] is not None


def test_dismissing_twice_returns_409(staff, link_lecturer):
    student_id = setup_student_with_low_attendance(staff, link_lecturer)
    advisor = staff["advisor"]
    flag_id = evaluate(advisor, student_id).json()["id"]
    advisor.post(f"/flags/{flag_id}/dismiss", json={"reason": "Reviewed"})

    response = advisor.post(f"/flags/{flag_id}/dismiss", json={"reason": "Reviewed again"})

    assert response.status_code == 409


def test_dismissal_requires_a_reason(staff, link_lecturer):
    student_id = setup_student_with_low_attendance(staff, link_lecturer)
    advisor = staff["advisor"]
    flag_id = evaluate(advisor, student_id).json()["id"]

    response = advisor.post(f"/flags/{flag_id}/dismiss", json={"reason": "   "})

    assert response.status_code == 422