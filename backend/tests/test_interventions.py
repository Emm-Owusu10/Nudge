TERM = "2026-S1"
STUDENT = {"student_number": "S1001", "full_name": "Test Student", "programme": "Computer Science"}
OTHER_STUDENT = {"student_number": "S2002", "full_name": "Other Student", "programme": "Biology"}
COURSE = {"code": "CS101", "title": "Introduction to Programming"}


def create_student(admin, details=STUDENT) -> int:
    return admin.post("/students", json=details).json()["id"]


def setup_course(staff, link_lecturer, students):
    """Create a course, enrol the students for TERM, and link the lecturer to the course."""
    admin = staff["admin"]
    course_id = admin.post("/courses", json=COURSE).json()["id"]
    for student_id in students:
        admin.post(f"/students/{student_id}/enrolments", json={"course_id": course_id, "academic_term": TERM})
    link_lecturer(course_id)
    return course_id


def record_attendance(lecturer, student_id, course_id, day, status):
    lecturer.post(
        f"/students/{student_id}/attendance",
        json={"course_id": course_id, "session_date": day, "status": status},
    )


def create_intervention(advisor, student_id, day="2026-09-01", flag_id=None):
    payload = {"intervention_type": "meeting", "intervention_date": day, "notes": "Initial meeting"}
    if flag_id is not None:
        payload["flag_id"] = flag_id
    return advisor.post(f"/students/{student_id}/interventions", json=payload)


def test_create_intervention_sets_follow_up_six_weeks_later(staff):
    student_id = create_student(staff["admin"])

    response = create_intervention(staff["advisor"], student_id, day="2026-09-01")

    assert response.status_code == 201
    body = response.json()
    assert body["outcome"] == "not_yet_reviewed"
    assert body["follow_up_due"] == "2026-10-13"  # 42 days after 2026-09-01


def test_unknown_intervention_type_is_rejected(staff):
    student_id = create_student(staff["admin"])

    response = staff["advisor"].post(
        f"/students/{student_id}/interventions",
        json={"intervention_type": "phone_call", "intervention_date": "2026-09-01"},
    )

    assert response.status_code == 422


def test_flag_from_another_student_is_rejected(staff, link_lecturer):
    admin = staff["admin"]
    advisor = staff["advisor"]
    student_id = create_student(admin)
    other_id = create_student(admin, OTHER_STUDENT)
    course_id = setup_course(staff, link_lecturer, [other_id])
    for day in ["2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09"]:
        record_attendance(staff["lecturer"], other_id, course_id, day, "absent")
    flag_id = advisor.post(
        f"/students/{other_id}/flags/evaluate", params={"as_of": "2026-10-19"}
    ).json()["id"]

    response = create_intervention(advisor, student_id, flag_id=flag_id)

    assert response.status_code == 404
    assert response.json()["detail"] == "Flag not found for this student"


def test_intervention_for_missing_student_returns_404(staff):
    response = create_intervention(staff["advisor"], student_id=999)

    assert response.status_code == 404


def test_list_interventions_most_recent_first(staff):
    advisor = staff["advisor"]
    student_id = create_student(staff["admin"])
    create_intervention(advisor, student_id, day="2026-08-01")
    create_intervention(advisor, student_id, day="2026-09-01")

    rows = advisor.get(f"/students/{student_id}/interventions").json()

    assert [row["intervention_date"] for row in rows] == ["2026-09-01", "2026-08-01"]


def test_recording_outcome_updates_the_record(staff):
    advisor = staff["advisor"]
    student_id = create_student(staff["admin"])
    intervention_id = create_intervention(advisor, student_id).json()["id"]

    response = advisor.post(f"/interventions/{intervention_id}/outcome", json={"outcome": "improving"})

    assert response.status_code == 200
    assert response.json()["outcome"] == "improving"
    assert response.json()["outcome_recorded_at"] is not None


def test_not_yet_reviewed_cannot_be_recorded_as_an_outcome(staff):
    advisor = staff["advisor"]
    student_id = create_student(staff["admin"])
    intervention_id = create_intervention(advisor, student_id).json()["id"]

    response = advisor.post(
        f"/interventions/{intervention_id}/outcome",
        json={"outcome": "not_yet_reviewed"},
    )

    assert response.status_code == 422


def test_follow_up_compares_attendance_before_and_after(staff, link_lecturer):
    student_id = create_student(staff["admin"])
    course_id = setup_course(staff, link_lecturer, [student_id])
    lecturer = staff["lecturer"]
    # Before the intervention on 2026-09-01: two present and two absent (rate 0.5).
    record_attendance(lecturer, student_id, course_id, "2026-08-10", "present")
    record_attendance(lecturer, student_id, course_id, "2026-08-11", "present")
    record_attendance(lecturer, student_id, course_id, "2026-08-12", "absent")
    record_attendance(lecturer, student_id, course_id, "2026-08-13", "absent")
    # After the follow-up on 2026-10-13: four present (rate 1.0).
    record_attendance(lecturer, student_id, course_id, "2026-10-01", "present")
    record_attendance(lecturer, student_id, course_id, "2026-10-02", "present")
    record_attendance(lecturer, student_id, course_id, "2026-10-03", "present")
    record_attendance(lecturer, student_id, course_id, "2026-10-04", "present")
    advisor = staff["advisor"]
    intervention_id = create_intervention(advisor, student_id, day="2026-09-01").json()["id"]

    body = advisor.get(f"/interventions/{intervention_id}/follow-up").json()

    assert body["before"]["attendance_recent"]["rate"] == 0.5
    assert body["after"]["attendance_recent"]["rate"] == 1.0
    assert body["is_due"] is True


def test_follow_up_is_not_due_for_a_future_date(staff):
    advisor = staff["advisor"]
    student_id = create_student(staff["admin"])
    intervention_id = create_intervention(advisor, student_id, day="2030-01-01").json()["id"]

    body = advisor.get(f"/interventions/{intervention_id}/follow-up").json()

    assert body["is_due"] is False


def test_unknown_intervention_returns_404(staff):
    advisor = staff["advisor"]

    assert advisor.post("/interventions/999/outcome", json={"outcome": "improving"}).status_code == 404
    assert advisor.get("/interventions/999/follow-up").status_code == 404