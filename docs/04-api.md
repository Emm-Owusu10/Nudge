# API Reference

The API is built with FastAPI. While the server runs, interactive documentation is at `http://127.0.0.1:8000/docs`. It is generated from the code, so it always matches the endpoints. This page adds the rules the generated documentation doesn't show.

## Authentication

Log in with `POST /auth/login` and send the returned token on later requests:

```
Authorization: Bearer <token>
```

Tokens last 60 minutes by default (`ACCESS_TOKEN_MINUTES`). In Swagger UI, log in, copy only the `access_token` value, and paste it into **Authorize**.

Accounts are created on the server with `python manage.py create-user`. There is no HTTP endpoint for creating users, by design.

## Roles

| Role | Typical use |
|---|---|
| `administrator` | Manages students, courses and enrolments. Reads the audit log |
| `advisor` | Evaluates flags, records interventions, reads student indicators |
| `lecturer` | Records attendance, assessments, assignments and submissions for their own courses |

Lecturers see only students enrolled in courses they teach, and only courses they teach. Assignments are scoped the same way.

## Common responses

| Status | Meaning |
|---|---|
| 200 | Success (read or update) |
| 201 | Record created |
| 401 | No token, invalid or expired token, or the account is deactivated |
| 403 | Logged in, but the role is not allowed to do this |
| 404 | Record not found, **or** a lecturer asking about a record outside their courses |
| 409 | Conflicts with an existing record (for example a duplicate code or a second record for the same session) |
| 422 | Input failed validation. The response names the field and the rule |
| 503 | Database unreachable (health check only) |

A 404 for an out-of-scope record is deliberate. It matches the response for a record that doesn't exist, so the API can't be used to discover which student numbers exist.

Error bodies have the form `{"detail": "..."}`. Validation errors list each problem.

## Endpoints

Roles in the last column are the roles allowed. "In scope" means a lecturer may use it only for students or courses they teach.

### Health and authentication

| Method | Path | Purpose | Success | Roles |
|---|---|---|---|---|
| GET | `/health` | Check the API and database | 200 | Anyone |
| POST | `/auth/login` | Exchange username and password for a token | 200 | Anyone |
| GET | `/auth/me` | Return the logged-in user | 200 | Any logged-in user |

**Browser access.** The API accepts browser requests only from `http://localhost:5173` and `http://127.0.0.1:5173`, the React development server. Requests carry the token in the `Authorization` header, not in cookies.

### Students and courses

| Method | Path | Purpose | Success | Roles |
|---|---|---|---|---|
| POST | `/students` | Create a student | 201 | administrator |
| GET | `/students` | List students (paged: `limit` 1 to 100, `offset`) | 200 | advisor, administrator |
| GET | `/students/{student_id}` | Get one student | 200 | advisor, administrator, lecturer (in scope) |
| PATCH | `/students/{student_id}` | Correct `full_name` or `programme` | 200 | administrator |
| POST | `/courses` | Create a course | 201 | administrator |
| GET | `/courses` | List courses (paged) | 200 | Any logged-in user |
| GET | `/courses/{course_id}` | Get one course | 200 | Any logged-in user |
| PATCH | `/courses/{course_id}` | Correct `title` | 200 | administrator |
| GET | `/courses/{course_id}/students` | Course roster, optional `academic_term` | 200 | lecturer (own courses), advisor, administrator |

### Enrolments

| Method | Path | Purpose | Success | Roles |
|---|---|---|---|---|
| POST | `/students/{student_id}/enrolments` | Enrol a student in a course for a term | 201 | administrator |
| GET | `/students/{student_id}/enrolments` | List a student's enrolments | 200 | advisor, administrator, lecturer (in scope) |

Enrolments cannot yet be edited or withdrawn.

### Attendance

| Method | Path | Purpose | Success | Roles |
|---|---|---|---|---|
| POST | `/students/{student_id}/attendance` | Record one session | 201 | lecturer (own course) |
| GET | `/students/{student_id}/attendance` | List a student's attendance | 200 | advisor, administrator, lecturer (in scope) |
| PATCH | `/students/{student_id}/attendance/{attendance_id}` | Correct `status` | 200 | lecturer (own course) |

### Assessments

| Method | Path | Purpose | Success | Roles |
|---|---|---|---|---|
| POST | `/students/{student_id}/assessments` | Record a score | 201 | lecturer (own course) |
| GET | `/students/{student_id}/assessments` | List a student's assessments | 200 | advisor, administrator, lecturer (in scope) |
| PATCH | `/students/{student_id}/assessments/{assessment_id}` | Correct `title`, `assessed_on` or `score` | 200 | lecturer (own course) |

### Assignments and submissions

| Method | Path | Purpose | Success | Roles |
|---|---|---|---|---|
| POST | `/assignments` | Create an assignment and a `missing` row for each enrolled student | 201 | lecturer (own course) |
| GET | `/assignments/{assignment_id}` | Get one assignment | 200 | lecturer (own course), advisor, administrator |
| GET | `/assignments/{assignment_id}/submissions` | Submission status for each student | 200 | lecturer (own course), advisor, administrator |
| PUT | `/submissions/{submission_id}` | Replace a submission's status and date | 200 | lecturer (own course) |

### Indicators, flags and interventions

| Method | Path | Purpose | Success | Roles |
|---|---|---|---|---|
| GET | `/students/{student_id}/indicators?as_of=YYYY-MM-DD` | Attendance, missing-work and grade indicators | 200 | advisor, administrator, lecturer (in scope) |
| POST | `/students/{student_id}/flags/evaluate?as_of=YYYY-MM-DD` | Evaluate and store a flag if a rule fires. Returns `null` if none fires | 200 | advisor |
| GET | `/students/{student_id}/flags` | List a student's flags | 200 | advisor, administrator, lecturer (in scope) |
| POST | `/flags/{flag_id}/dismiss` | Dismiss a flag with a required reason | 200 | advisor |
| POST | `/students/{student_id}/interventions` | Record an intervention (follow-up due 42 days later) | 201 | advisor |
| GET | `/students/{student_id}/interventions` | List a student's interventions | 200 | advisor, administrator |
| POST | `/interventions/{intervention_id}/outcome` | Record `improving`, `no_change` or `referred_elsewhere` | 200 | advisor |
| GET | `/interventions/{intervention_id}/follow-up` | Compare indicators at the intervention and follow-up dates | 200 | advisor, administrator |

| GET | `/flags?as_of=YYYY-MM-DD&status=open` | Flag queue across all students, most urgent first. `status` may be `open` or `dismissed` | 200 | advisor, administrator |
| GET | `/me/courses` | Courses the logged-in lecturer teaches | 200 | lecturer |

### Audit log

| Method | Path | Purpose | Success | Roles |
|---|---|---|---|---|
| GET | `/audit-logs?student_id=&limit=` | Recent audit entries, optionally for one student | 200 | administrator |

| GET | `/flags?as_of=YYYY-MM-DD&status=open` | Flag queue across all students, most urgent first | 200 | advisor, administrator |
| GET | `/me/courses` | Courses the logged-in lecturer teaches | 200 | lecturer |

## Request notes

**Paging.** `GET /students` and `GET /courses` accept `limit` (1 to 100, default 20) and `offset` (0 or more). Other lists return all matching rows. This needs paging before real data grows.

**Corrections (PATCH).** Send only the fields to change. An empty body, an explicit `null`, or a locked field returns 422. Locked fields are `student_number`, the course `code`, and the student, course and date of an attendance record.

**Submission update (PUT).** Requires `status` every time.
- `"missing"` must not include `submitted_on`.
- `"submitted"` or `"late"` must include `submitted_on`, for example `"2026-11-14"`.

**Identifiers.** Student numbers and course codes use letters, digits and hyphens, up to 20 characters. Surrounding spaces are removed.

**Terms.** Format `YYYY-S1`, for example `2026-S1`.

**Attendance status.** `present`, `absent`, `late` or `excused`. Excused sessions are left out of attendance rates.

**Assessment score.** An integer from 0 to 100.

**Indicators.** `as_of` is optional and defaults to today. Values are `null` when there is not enough data. See `05-indicators.md`.

**Unknown fields.** Request bodies with undocumented fields return 422.

## Audit log

Every successful view, change, evaluation, dismissal and outcome writes one entry. Failed requests write nothing. Entries are written in a separate transaction after the action, so if the write fails the change still stands. This is a known gap. See `08-access-control.md`.

## Known limitations

- Enrolments cannot be edited or withdrawn yet.
- Students enrolled after an assignment is created have no submission row for it.
- Only students and courses are paged.
- Lecturer scope ignores academic terms, so a student from an earlier term stays visible.
- There are no delete endpoints for any resource, by design. Records are corrected, not erased.