from app.services.indicators import Indicators

# Thresholds agreed in the design. Changing them changes every flag, so they
# are kept together here and documented in docs/06-flag-rules.md.
ATTENDANCE_DECLINE_POINTS = 0.20   # recent rate at least 20 points below earlier
MIN_SESSIONS_FOR_DECLINE = 3       # each window needs this many counted sessions
LOW_ATTENDANCE_RATE = 0.70         # recent rate below 70%
MIN_SESSIONS_FOR_LOW = 5           # this many counted sessions in the recent window
MISSING_WORK_THRESHOLD = 3         # at least 3 missing among the recent assignments
GRADE_DECLINE_POINTS = 10.0        # recent average at least 10 points below earlier

# Small tolerance for floating-point subtraction, so that exactly 20 points
# is not missed because 0.9 - 0.7 is stored as 0.20000000000000007.
EPSILON = 1e-9

LEVEL_BY_FACTOR_COUNT = {1: "monitor", 2: "review recommended"}
PRIORITY_LEVEL = "priority review"


class FlagFactor:
    """One reason for a flag: a stable code for software, and a sentence for people."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message


def _attendance_decline(indicators: Indicators) -> FlagFactor | None:
    recent = indicators.attendance_recent
    earlier = indicators.attendance_earlier
    if recent.rate is None or earlier.rate is None:
        return None
    if recent.sessions_counted < MIN_SESSIONS_FOR_DECLINE or earlier.sessions_counted < MIN_SESSIONS_FOR_DECLINE:
        return None
    if earlier.rate - recent.rate >= ATTENDANCE_DECLINE_POINTS - EPSILON:
        return FlagFactor(
            "attendance_decline",
            f"Attendance fell from {earlier.rate:.0%} to {recent.rate:.0%} over the last 4 weeks",
        )
    return None


def _low_attendance(indicators: Indicators) -> FlagFactor | None:
    recent = indicators.attendance_recent
    if recent.rate is None or recent.sessions_counted < MIN_SESSIONS_FOR_LOW:
        return None
    if recent.rate < LOW_ATTENDANCE_RATE:
        return FlagFactor(
            "low_attendance",
            f"Attendance is {recent.rate:.0%} over the last 4 weeks",
        )
    return None


def _missing_work(indicators: Indicators) -> FlagFactor | None:
    work = indicators.missing_assignments
    if work.missing >= MISSING_WORK_THRESHOLD:
        return FlagFactor(
            "missing_work",
            f"{work.missing} of the last {work.considered} assignments are not submitted",
        )
    return None


def _grade_decline(indicators: Indicators) -> FlagFactor | None:
    grades = indicators.grades
    if grades.recent_average is None or grades.earlier_average is None:
        return None
    if grades.earlier_average - grades.recent_average >= GRADE_DECLINE_POINTS - EPSILON:
        return FlagFactor(
            "grade_decline",
            f"Average score fell from {grades.earlier_average:.0f} to {grades.recent_average:.0f} "
            "across the last 3 assessments",
        )
    return None


def evaluate_rules(indicators: Indicators) -> tuple[str | None, list[FlagFactor]]:
    """Return (level, factors). The level is None when no rule fires."""
    rules = (_attendance_decline, _low_attendance, _missing_work, _grade_decline)
    factors = [factor for rule in rules if (factor := rule(indicators)) is not None]

    if not factors:
        return None, []
    if len(factors) >= 3:
        return PRIORITY_LEVEL, factors
    return LEVEL_BY_FACTOR_COUNT[len(factors)], factors