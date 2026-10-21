from sqlalchemy import select  # noqa: F401  (kept for parity with other test modules)

AS_OF = "2026-10-19"
TERM = "2026-S1"


def make_low_attendance_student(staff, link_lecturer, course_code="CS101", number="S1001"):
    """A student with five absences in one course, linked to the test lecturer."""
    admin = staff["admin"]
    student_id = admin.post(
        "/students",
        json={"student_number": number, "full_name": f"Student {number}", "programme": "CS"},
    ).json()["id"]
    course_id = admin.post("/courses", json={"code": course_code, "title": "Intro"}).json()["id"]
    admin.post(f"/students/{student_id}/enrolments", json={"course_id": course_id, "academic_term": TERM})
    link_lecturer(course_id)
    for day in ["2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09"]:
        staff["lecturer"].post(
            f"/students/{student_id}/attendance",
            json={"course_id": course_id, "session_date": day, "status": "absent"},
        )
    return student_id


def test_queue_lists_open_flags_with_student_details(staff, link_lecturer):
    student_id = make_low_attendance_student(staff, link_lecturer)
    staff["advisor"].post(f"/students/{student_id}/flags/evaluate", params={"as_of": AS_OF})

    rows = staff["advisor"].get("/flags", params={"as_of": AS_OF}).json()

    assert len(rows) == 1
    assert rows[0]["student_number"] == "S1001"
    assert rows[0]["full_name"] == "Student S1001"
    assert rows[0]["level"] == "monitor"
    assert rows[0]["status"] == "open"
    assert [factor["code"] for factor in rows[0]["factors"]] == ["low_attendance"]


def test_dismissed_flags_leave_the_open_queue(staff, link_lecturer):
    advisor = staff["advisor"]
    student_id = make_low_attendance_student(staff, link_lecturer)
    flag_id = advisor.post(
        f"/students/{student_id}/flags/evaluate", params={"as_of": AS_OF}
    ).json()["id"]
    advisor.post(f"/flags/{flag_id}/dismiss", json={"reason": "Reviewed"})

    assert advisor.get("/flags", params={"as_of": AS_OF}).json() == []


def test_dismissed_filter_shows_dismissed_flags(staff, link_lecturer):
    advisor = staff["advisor"]
    student_id = make_low_attendance_student(staff, link_lecturer)
    flag_id = advisor.post(
        f"/students/{student_id}/flags/evaluate", params={"as_of": AS_OF}
    ).json()["id"]
    advisor.post(f"/flags/{flag_id}/dismiss", json={"reason": "Reviewed"})

    rows = advisor.get("/flags", params={"as_of": AS_OF, "status": "dismissed"}).json()

    assert [row["flag_id"] for row in rows] == [flag_id]


def test_lecturer_cannot_read_the_flag_queue(staff):
    response = staff["lecturer"].get("/flags", params={"as_of": AS_OF})

    assert response.status_code == 403


def test_viewing_the_queue_is_audited(staff, link_lecturer):
    make_low_attendance_student(staff, link_lecturer)
    staff["advisor"].get("/flags", params={"as_of": AS_OF})

    entries = staff["admin"].get("/audit-logs", params={"limit": 200}).json()

    assert any(entry["resource"] == "flag_queue" for entry in entries)


def test_lecturer_sees_only_their_own_courses(staff, link_lecturer):
    admin = staff["admin"]
    own_id = admin.post("/courses", json={"code": "CS101", "title": "Intro"}).json()["id"]
    admin.post("/courses", json={"code": "MATH200", "title": "Calculus"})
    link_lecturer(own_id)

    response = staff["lecturer"].get("/me/courses")

    assert response.status_code == 200
    assert [course["code"] for course in response.json()] == ["CS101"]


def test_advisor_cannot_use_my_courses(staff):
    response = staff["advisor"].get("/me/courses")

    assert response.status_code == 403