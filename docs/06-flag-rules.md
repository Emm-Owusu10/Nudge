# Flag Rules

Flags are raised by rules that read the indicators (see `docs/05-indicators.md`). Each rule adds one factor, and the number of factors sets the level. A rule never fires on missing data, so `null` cannot create a flag.

Flags describe patterns that may need human review. They do not predict failure or dropout.

## Rules

| Code | Condition | Example message |
|---|---|---|
| `attendance_decline` | Recent attendance rate is at least 20 percentage points below the earlier rate, and each window has at least 3 counted sessions | "Attendance fell from 88% to 61% over the last 4 weeks" |
| `low_attendance` | Recent attendance rate is below 70%, with at least 5 counted sessions | "Attendance is 62% over the last 4 weeks" |
| `missing_work` | At least 3 of the 5 most recent assignments are missing | "3 of the last 5 assignments are not submitted" |
| `grade_decline` | Recent average is at least 10 points below the earlier average | "Average score fell from 72 to 58 across the last 3 assessments" |

## Levels

| Factors | Level |
|---|---|
| 0 | No flag |
| 1 | `monitor` |
| 2 | `review recommended` |
| 3 or more | `priority review` |

## Notes

- Thresholds are defined in `app/services/rules.py`. They were agreed with the design and should be reviewed with advisors before real use.
- A small tolerance (`EPSILON`) prevents floating-point arithmetic from missing a threshold that is exactly met.
- Each flag stores the factors as they were when raised, so later changes to the rules do not rewrite history.
- Evaluating the same student and date twice returns the existing flag.