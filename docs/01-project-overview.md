# Early Intervention Decision-Support System: Project Overview

## Purpose

This system helps academic advisors notice students who may need support before they fail a course. It stores attendance, assignment, assessment, and enrolment records, and will flag patterns that warrant human review.

## Problem

Lecturers and advisors currently identify struggling students by hand, usually late. Warning signs such as falling attendance, missing work, and declining scores are spread across different records and are easy to miss.

## Objectives

1. Keep a single, validated record of students, courses, enrolments, attendance, and assessments.
2. Measure changes over time for each student.
3. Flag students who may need review, with plain-language reasons for each flag.
4. Let advisors record interventions and track what happened afterwards.

## What the system does not do

- It does not predict that a student will fail or drop out.
- It does not make intervention decisions. Advisors do.
- It does not replace the student records held by the university.

## Intended users

- **Academic advisors:** review flags, record interventions, and track follow-up.
- **Lecturers:** record attendance and assessment scores (planned).
- **Department administrators:** manage courses and enrolments.

Students are not users of this system. Their data is protected, and they are not shown flags.

## Scope of the coursework version

- Synthetic data only. No real student records are used.
- Single department, single institution.
- Manual data entry through the API. No import from university systems.

## Known limitations

These are recorded so they can be discussed in the report. Each one is a deliberate trade-off or a known gap.

- **Submission rows for late enrolments.** A student enrolled after an assignment is created has no submission row for it, so they are not counted in its missing total.
- **Paging.** Only the students and courses lists are paged, and both are capped at 100 per request. Other lists return every matching row.
- **Audit writes.** An audit entry is written in a separate transaction after the action. If the audit write fails, the change still stands. Writing both in one transaction would need a larger refactor.
- **Term-blind lecturer scope.** A lecturer keeps access to a student from any term in which they taught the student's course, not only the current term.
- **Read-only dismissal.** A dismissed flag cannot be reopened. Re-evaluation raises a new flag for a new date.
- **Enrolments are not editable.** Withdrawal and transfer are not supported yet.
- **No deletion.** No resource can be deleted through the API, by design. Records are corrected, not erased.
- **Local deployment only.** The API listens on 127.0.0.1, and the interface runs on the Vite development server.
- **Synthetic data only.** The seed script creates demonstration records. No real student data has been used.

## Current status

| Area | Status |
|---|---|
| Configuration, database connection, health check | Complete |
| Migrations (Alembic) | Complete |
| Students, courses, enrolments | Complete, tested |
| Attendance and assessments | Complete, tested |
| Assignments and submissions | Complete, tested |
| Indicators | Complete, tested |
| Flag rules, storage, dismissal | Complete, tested |
| Interventions and follow-up | Complete, tested |
| Corrections (PATCH) | Complete, tested |
| Authentication, roles, lecturer scope, audit log | Complete, tested |
| Web interface: advisor dashboard | Complete |
| Web interface: lecturer dashboard | Complete |
| Web interface: administrator console | Complete |
| Documentation | Complete |

Automated tests: 125 passing.

## Technology

- Python 3.12, FastAPI, Uvicorn
- PostgreSQL 18
- SQLAlchemy 2.0 (database access), Alembic (migrations), Pydantic (validation)
- pytest and FastAPI's TestClient (automated tests)
- pandas (indicator calculations, planned)
- Streamlit (advisor interface, planned)

The reasons for these choices are recorded in the design discussion and summarised in the setup guide.

| Assignments and submissions | Complete, tested |
| Indicators and flag rules | Complete, tested |
| Interventions and follow-up | Planned |
| Authentication, roles, audit log | Planned |
| Advisor interface (Streamlit) | Planned |
| Seed data | Planned |