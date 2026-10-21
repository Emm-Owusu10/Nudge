# Access Control

Every endpoint requires a logged-in user, except `/health` and `/auth/login`. Each role is allowed a fixed set of actions, and lecturers are also limited to their own courses.

## Roles

| Role | Created by |
|---|---|
| `administrator` | `python manage.py create-user --role administrator` |
| `advisor` | `python manage.py create-user --role advisor` |
| `lecturer` | `python manage.py create-user --role lecturer`, then `assign-course` |

## Access matrix

| Area | Create or change | Read |
|---|---|---|
| Students | Administrator | Single student: advisor, administrator, lecturer in scope. List: advisor, administrator |
| Courses | Administrator | All logged-in users |
| Course roster | None | Lecturer (own courses only), advisor, administrator |
| Enrolments | Administrator | Advisor, administrator, lecturer in scope |
| Attendance | Lecturer, own courses only | Advisor, administrator, lecturer in scope |
| Assessments | Lecturer, own courses only | Advisor, administrator, lecturer in scope |
| Assignments and submissions | Lecturer, own courses only | Lecturer (own courses), advisor, administrator |
| Indicators | None | Advisor, administrator, lecturer in scope |
| Flags | Advisor evaluates and dismisses | Advisor, administrator, lecturer in scope |
| Interventions | Advisor records outcomes | Advisor, administrator |
| Audit log | None | Administrator |

## Response codes

| Situation | Code |
|---|---|
| No token, invalid token, or deactivated user | 401 |
| Logged in, but the role is not allowed | 403 |
| Lecturer asks for a student or course outside their scope | 404 |

Out-of-scope access returns 404, the same as a record that doesn't exist, so the API can't be used to discover which student numbers exist.

## Audit log

Each successful view, change, evaluation, dismissal, and outcome writes one entry: the user, the action, the resource, the record id, and the student involved. Failed requests write nothing.

Limitations:
- Entries are written after the action, in a separate transaction. If the audit write fails, the change still stands. This is a known gap.
- Course reads are not audited, because they contain no student data.
- Lecturer scope is based on enrolment in any term, so a student enrolled in an earlier term remains visible.