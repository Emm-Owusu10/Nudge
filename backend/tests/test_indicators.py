import pytest

TERM = "2026-S1"
AS_OF = "2026-10-19"
STUDENT = {"student_number": "S1001", "full_name": "Test Student", "programme": "Computer Science"}
COURSE = {"code": "CS101", "title": "Introduction to Programming"}


def setup_student_and_course(staff, link_lecturer):
    """Create a student and a course, enrol the student, and link the lecturer to the course."""
    admin = staff["admin"]
    student_id = admin.post("/students", json=STUDENT).json()["id"]
    course_id = admin.post("/courses", json=COURSE).json()["id"]
    admin.post(f"/students/{student_id}/enrolments", json={"course_id": course_id, "academic_term": TERM})
    link_lecturer(course_id)
    return student_id, course_id


def record_attendance(lecturer, student_id, course_id, day, status):
    lecturer.post(
        f"/students/{student_id}/attendance",
        json={"course_id": course_id, "session_date": day, "status": status},
    )


def record_assessment(lecturer, student_id, course_id, title, day, score):
    lecturer.post(
        f"/students/{student_id}/assessments",
        json={"course_id": course_id, "title": title, "assessed_on": day, "score": score},
    )


def get_indicators(advisor, student_id, as_of=AS_OF):
    return advisor.get(f"/students/{student_id}/indicators", params={"as_of": as_of})


def test_attendance_rate_compares_recent_and_earlier_windows(staff, link_lecturer):
    student_id, course_id = setup_student_and_course(staff, link_lecturer)
    lecturer = staff["lecturer"]
    # Recent window: 2026-09-21 to 2026-10-19. Earlier: 2026-08-24 to 2026-09-21.
    record_attendance(lecturer, student_id, course_id, "2026-10-05", "present")
    record_attendance(lecturer, student_id, course_id, "2026-10-07", "late")
    record_attendance(lecturer, student_id, course_id, "2026-10-12", "absent")
    record_attendance(lecturer, student_id, course_id, "2026-09-01", "present")
    record_attendance(lecturer, student_id, course_id, "2026-09-08", "present")

    body = get_indicators(staff["advisor"], student_id).json()

    assert body["attendance_recent"]["rate"] == pytest.approx(2 / 3)
    assert body["attendance_recent"]["sessions_counted"] == 3
    assert body["attendance_earlier"]["rate"] == 1.0


def test_excused_sessions_are_not_counted(staff, link_lecturer):
    student_id, course_id = setup_student_and_course(staff, link_lecturer)
    lecturer = staff["lecturer"]
    record_attendance(lecturer, student_id, course_id, "2026-10-05", "present")
    record_attendance(lecturer, student_id, course_id, "2026-10-07", "excused")
    record_attendance(lecturer, student_id, course_id, "2026-10-12", "excused")

    body = get_indicators(staff["advisor"], student_id).json()

    assert body["attendance_recent"]["rate"] == 1.0
    assert body["attendance_recent"]["sessions_counted"] == 1


def test_no_attendance_gives_none_not_zero(staff, link_lecturer):
    student_id, _ = setup_student_and_course(staff, link_lecturer)

    body = get_indicators(staff["advisor"], student_id).json()

    assert body["attendance_recent"]["rate"] is None
    assert body["attendance_recent"]["sessions_counted"] == 0


def test_missing_work_counts_only_the_five_most_recent_assignments(staff, link_lecturer):
    student_id, course_id = setup_student_and_course(staff, link_lecturer)
    lecturer = staff["lecturer"]
    assignment_ids = []
    for i in range(6):
        response = lecturer.post(
            "/assignments",
            json={
                "course_id": course_id,
                "academic_term": TERM,
                "title": f"Task {i + 1}",
                "due_date": f"2026-10-0{i + 1}",
            },
        )
        assignment_ids.append(response.json()["id"])
    # Leave the oldest assignment missing, and submit the other five.
    for assignment_id in assignment_ids[1:]:
        row = lecturer.get(f"/assignments/{assignment_id}/submissions").json()[0]
        lecturer.put(f"/submissions/{row['id']}", json={"status": "submitted", "submitted_on": "2026-10-10"})

    body = get_indicators(staff["advisor"], student_id).json()

    assert body["missing_assignments"] == {"missing": 0, "considered": 5}


def test_grade_trend_compares_last_three_with_previous_three(staff, link_lecturer):
    student_id, course_id = setup_student_and_course(staff, link_lecturer)
    lecturer = staff["lecturer"]
    for day, score in [("2026-10-01", 50), ("2026-10-02", 50), ("2026-10-03", 50)]:
        record_assessment(lecturer, student_id, course_id, f"Earlier {day}", day, score)
    for day, score in [("2026-10-10", 80), ("2026-10-11", 80), ("2026-10-12", 80)]:
        record_assessment(lecturer, student_id, course_id, f"Recent {day}", day, score)

    body = get_indicators(staff["advisor"], student_id).json()

    assert body["grades"]["recent_average"] == 80.0
    assert body["grades"]["earlier_average"] == 50.0


def test_incomplete_grade_group_gives_none(staff, link_lecturer):
    student_id, course_id = setup_student_and_course(staff, link_lecturer)
    lecturer = staff["lecturer"]
    for day, score in [("2026-10-01", 60), ("2026-10-10", 70), ("2026-10-11", 75), ("2026-10-12", 80)]:
        record_assessment(lecturer, student_id, course_id, f"Test {day}", day, score)

    body = get_indicators(staff["advisor"], student_id).json()

    assert body["grades"]["recent_average"] == pytest.approx(75.0)
    assert body["grades"]["earlier_average"] is None


def test_assessments_after_as_of_are_ignored(staff, link_lecturer):
    student_id, course_id = setup_student_and_course(staff, link_lecturer)
    record_assessment(staff["lecturer"], student_id, course_id, "Future", "2026-11-01", 10)

    body = get_indicators(staff["advisor"], student_id).json()

    assert body["grades"]["recent_average"] is None


def test_indicators_for_missing_student_return_404(staff):
    response = get_indicators(staff["advisor"], student_id=999)

    assert response.status_code == 404