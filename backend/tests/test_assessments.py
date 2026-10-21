TERM = "2026-S1"
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


def test_record_assessment_returns_201(staff, link_lecturer):
    student_id, course_id = setup_student_and_course(staff, link_lecturer)

    response = staff["lecturer"].post(
        f"/students/{student_id}/assessments",
        json={"course_id": course_id, "title": "Midterm", "assessed_on": "2026-10-01", "score": 72},
    )

    assert response.status_code == 201
    assert response.json()["score"] == 72


def test_score_above_100_is_rejected(staff, link_lecturer):
    student_id, course_id = setup_student_and_course(staff, link_lecturer)

    response = staff["lecturer"].post(
        f"/students/{student_id}/assessments",
        json={"course_id": course_id, "title": "Midterm", "assessed_on": "2026-10-01", "score": 101},
    )

    assert response.status_code == 422


def test_negative_score_is_rejected(staff, link_lecturer):
    student_id, course_id = setup_student_and_course(staff, link_lecturer)

    response = staff["lecturer"].post(
        f"/students/{student_id}/assessments",
        json={"course_id": course_id, "title": "Midterm", "assessed_on": "2026-10-01", "score": -1},
    )

    assert response.status_code == 422


def test_assessment_in_missing_course_returns_404(staff, link_lecturer):
    student_id, _ = setup_student_and_course(staff, link_lecturer)

    response = staff["lecturer"].post(
        f"/students/{student_id}/assessments",
        json={"course_id": 999, "title": "Midterm", "assessed_on": "2026-10-01", "score": 60},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Course not found"


def test_list_assessments_is_ordered_by_date(staff, link_lecturer):
    student_id, course_id = setup_student_and_course(staff, link_lecturer)
    lecturer = staff["lecturer"]
    for title, day, score in [("Essay", "2026-11-01", 65), ("Midterm", "2026-10-01", 72)]:
        lecturer.post(
            f"/students/{student_id}/assessments",
            json={"course_id": course_id, "title": title, "assessed_on": day, "score": score},
        )

    rows = lecturer.get(f"/students/{student_id}/assessments").json()

    assert [row["title"] for row in rows] == ["Midterm", "Essay"]