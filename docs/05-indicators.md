# Indicators

Indicators are measurements calculated from stored records. They do not decide whether a student is flagged. The flag rules (next step) will read these values and apply thresholds.

Every indicator takes an `as_of` date, so the same data always gives the same result for that date.

## Settings

| Setting | Value | Where |
|---|---|---|
| Attendance window | 28 days, compared with the 28 days before | `ATTENDANCE_WINDOW_DAYS` |
| Missing-work window | 5 most recent assignments due on or before `as_of` | `ASSIGNMENT_WINDOW_SIZE` |
| Grade group | 3 most recent scores, compared with the 3 before | `GRADE_GROUP_SIZE` |

## Definitions

**Attendance rate** (`attendance_recent`, `attendance_earlier`)
- Counted sessions: `present`, `late`, and `absent`.
- Excused sessions are excluded from the rate and the count.
- Rate = (present + late) / counted sessions.
- `rate` is `null` when no sessions were counted.

**Missing work** (`missing_assignments`)
- Takes the assignments due on or before `as_of`, newest first, up to the window size.
- `missing` counts those whose submission status is `missing`.
- `considered` is how many assignments were included, which can be fewer than five for a new student.

**Grade trend** (`grades`)
- Takes assessments dated on or before `as_of`, newest first.
- `recent_average` is the mean of the first three scores.
- `earlier_average` is the mean of the next three.
- Either average is `null` if its group has fewer than three scores.

## Principles

- **Unknown is not zero.** A missing value is returned as `null`. It is never treated as a poor result.
- **Excused means excused.** Excused absences do not lower attendance.
- **Dates decide windows.** Attendance windows use session dates, and the other indicators use due dates or assessment dates.

## Limitations

- Indicators combine all of a student's courses. A per-course view may be needed later.
- The windows are fixed. They should be reviewed with advisors before real use.
- Students who are enrolled after an assignment is created have no submission row for it, so they are not counted in its missing total.