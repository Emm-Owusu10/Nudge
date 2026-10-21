# Database Structure

The database is PostgreSQL. Tables are defined as SQLAlchemy models in `backend/app/models/`, and schema changes are applied through Alembic migrations in `backend/alembic/versions/`.

## Tables

### students

One row per student.

| Column | Type | Constraints |
|---|---|---|
| id | integer | Primary key, generated |
| student_number | varchar(20) | Unique, required. Letters, digits and hyphens only |
| full_name | varchar(120) | Required |
| programme | varchar(120) | Required |
| created_at | timestamp with time zone | Required, set by PostgreSQL |

### courses

One row per course or module.

| Column | Type | Constraints |
|---|---|---|
| id | integer | Primary key, generated |
| code | varchar(20) | Unique, required. Letters, digits and hyphens only (e.g. `CS101`) |
| title | varchar(200) | Required |

### enrolments

A student taking a course in a given term.

| Column | Type | Constraints |
|---|---|---|
| id | integer | Primary key, generated |
| student_id | integer | Foreign key to `students.id`, required |
| course_id | integer | Foreign key to `courses.id`, required |
| academic_term | varchar(20) | Required. Format `YYYY-S1` (e.g. `2026-S1`) |

- Unique constraint `uq_enrolment_student_course_term` on (student_id, course_id, academic_term). A student can take the same course once per term.

### attendance

One record per student, course, and session date.

| Column | Type | Constraints |
|---|---|---|
| id | integer | Primary key, generated |
| student_id | integer | Foreign key to `students.id`, required |
| course_id | integer | Foreign key to `courses.id`, required |
| session_date | date | Required |
| status | varchar(10) | Required, one of `present`, `absent`, `late`, `excused` |

- Unique constraint `uq_attendance_student_course_session` on (student_id, course_id, session_date) blocks duplicate entries.
- Check constraint `ck_attendance_status` rejects any other status value.
- `excused` absences are stored separately so they can be excluded from absence counts.

### assessments

A scored assessment for one student in one course.

| Column | Type | Constraints |
|---|---|---|
| id | integer | Primary key, generated |
| student_id | integer | Foreign key to `students.id`, required |
| course_id | integer | Foreign key to `courses.id`, required |
| title | varchar(120) | Required (e.g. `Midterm`) |
| assessed_on | date | Required |
| score | integer | Required. Check constraint `ck_assessment_score_range` allows 0 to 100 |

### assignments

One piece of assessed work in a course for one term.

| Column | Type | Constraints |
|---|---|---|
| id | integer | Primary key, generated |
| course_id | integer | Foreign key to `courses.id`, required |
| academic_term | varchar(20) | Required. Must match the term used in enrolments |
| title | varchar(120) | Required |
| due_date | date | Required |

- Unique constraint `uq_assignment_course_term_title` on (course_id, academic_term, title).

### submissions

One row per student per assignment. Rows are created as `missing` when the assignment is created, so a missing submission is recorded data, not an absent row.

| Column | Type | Constraints |
|---|---|---|
| id | integer | Primary key, generated |
| assignment_id | integer | Foreign key to `assignments.id`, required |
| student_id | integer | Foreign key to `students.id`, required |
| status | varchar(10) | Required, one of `submitted`, `missing`, `late` |
| submitted_on | date | Empty when `missing`. Required when `submitted` or `late` |

- Unique constraint `uq_submission_assignment_student` on (assignment_id, student_id).
- Check constraint `ck_submission_status` rejects any other status value.
- The date rule (`submitted_on` empty for `missing`, present otherwise) is enforced by the API schema, not by the database.

**Known limitation:** rows are created only for students enrolled when the assignment is created. A student enrolled later has no submission row for existing assignments. This needs a decision on how enrolment changes should propagate, and is planned for a later step.

### flags

A review flag raised for one student on one evaluation date.

| Column | Type | Constraints |
|---|---|---|
| id | integer | Primary key, generated |
| student_id | integer | Foreign key to `students.id`, required |
| as_of | date | Required, the date the evaluation used |
| level | varchar(30) | Required, one of `monitor`, `review recommended`, `priority review` |
| status | varchar(10) | Required, one of `open`, `dismissed` |
| factors | JSON | Required, list of `{"code", "message"}` objects, stored as raised |
| created_at | timestamp with time zone | Required, set by PostgreSQL |
| dismissal_reason | text | Empty until dismissed |
| dismissed_at | timestamp with time zone | Empty until dismissed |

- Unique constraint `uq_flag_student_as_of` on (student_id, as_of). Re-evaluating the same date returns the existing flag.
- Check constraints `ck_flag_level` and `ck_flag_status` restrict the allowed values.
- Dismissal updates the row rather than deleting it, so the history is kept.

## Relationships

```
students    1 ──< enrolments    >── 1 courses
students    1 ──< attendance    >── 1 courses
students    1 ──< assessments   >── 1 courses
courses     1 ──< assignments
assignments 1 ──< submissions   >── 1 students
```

Each foreign key points from the child table to its parent. In the ORM, `Student.enrolments` and `Enrolment.student` are two views of the same link.

## Constraints and where they are enforced

Validation happens in three layers, in order:

1. **Pydantic schemas** (`app/schemas/`) reject bad input with a 422 response before any database code runs.
2. **Services** (`app/services/`) check that parent records exist and return 404 or 409 responses where appropriate.
3. **Database constraints** (unique, foreign key, check) are the final guard, so the rules hold even if application code has a bug.

## Deletion policy

## Deletion and correction policy

No endpoint deletes records. Academic records are corrected, not erased, so mistakes are fixed with PATCH endpoints. Foreign keys do not cascade, so a student cannot be removed while enrolments, attendance, or submissions refer to them.

Locked fields: `student_number`, the course code, and the student, course, and session date of attendance records. These identify a record, so changing them would in effect create a different record. Enrolments are not yet editable. Withdrawal support is planned.

If a record is ever to be removed, it should use a soft-delete flag and be recorded in the audit log.

## Migrations

| Revision | Description |
|---|---|
| `194bbd05ef82` | Creates `students`, `courses`, `enrolments` |
| `dd75aebe73b5` | Creates `attendance`, `assessments` |
| `5616ff122958` | Creates `assignments`, `submissions` |
| `46b28e53fd41` | Creates `flags` |
| `4fdd6391687b` | Creates `Interventions` |

To change the schema:

1. Edit or add a model in `backend/app/models/`, and register it in `app/models/__init__.py`.
2. From `backend`, run `alembic revision --autogenerate -m "describe the change"`.
3. Open the new file in `backend/alembic/versions/` and check it. Autogenerate can miss renames and data changes.
4. Run `alembic upgrade head`.

Never edit a migration that has already been applied. Create a new one instead.

## Test database

`early_intervention_test` is built from the models by the test fixtures (`Base.metadata.create_all`), not by Alembic. The tests truncate every table before each test. Never store data there that you want to keep.