from datetime import date

from app.services.indicators import GradeTrend, Indicators, MissingWork, WindowRate
from app.services.rules import evaluate_rules


def make_indicators(
    recent_rate=None, recent_n=0,
    earlier_rate=None, earlier_n=0,
    missing=0, considered=0,
    recent_avg=None, earlier_avg=None,
) -> Indicators:
    """Build an Indicators object directly, so the rules can be tested without a database."""
    return Indicators(
        student_id=1,
        as_of=date(2026, 10, 19),
        attendance_recent=WindowRate(rate=recent_rate, sessions_counted=recent_n),
        attendance_earlier=WindowRate(rate=earlier_rate, sessions_counted=earlier_n),
        missing_assignments=MissingWork(missing=missing, considered=considered),
        grades=GradeTrend(recent_average=recent_avg, earlier_average=earlier_avg),
    )


def codes(factors):
    return [factor.code for factor in factors]


def test_no_data_gives_no_flag():
    level, factors = evaluate_rules(make_indicators())

    assert level is None
    assert factors == []


def test_attendance_decline_fires_at_twenty_points():
    indicators = make_indicators(
        earlier_rate=0.90, earlier_n=4,
        recent_rate=0.70, recent_n=4,
    )

    _, factors = evaluate_rules(indicators)

    assert "attendance_decline" in codes(factors)


def test_attendance_decline_needs_three_sessions_in_each_window():
    indicators = make_indicators(
        earlier_rate=1.00, earlier_n=2,
        recent_rate=0.50, recent_n=2,
    )

    _, factors = evaluate_rules(indicators)

    assert "attendance_decline" not in codes(factors)


def test_low_attendance_fires_below_seventy_percent():
    _, factors = evaluate_rules(make_indicators(recent_rate=0.60, recent_n=5))

    assert codes(factors) == ["low_attendance"]


def test_low_attendance_needs_five_sessions():
    _, factors = evaluate_rules(make_indicators(recent_rate=0.00, recent_n=4))

    assert "low_attendance" not in codes(factors)


def test_missing_work_fires_at_three():
    level, factors = evaluate_rules(make_indicators(missing=3, considered=5))

    assert codes(factors) == ["missing_work"]
    assert level == "monitor"


def test_missing_work_below_three_does_not_fire():
    _, factors = evaluate_rules(make_indicators(missing=2, considered=5))

    assert "missing_work" not in codes(factors)


def test_grade_decline_fires_at_ten_points():
    _, factors = evaluate_rules(make_indicators(recent_avg=62.0, earlier_avg=72.0))

    assert "grade_decline" in codes(factors)


def test_two_factors_give_review_recommended():
    level, factors = evaluate_rules(
        make_indicators(missing=3, considered=5, recent_avg=50.0, earlier_avg=70.0)
    )

    assert len(factors) == 2
    assert level == "review recommended"


def test_three_factors_give_priority_review():
    level, factors = evaluate_rules(
        make_indicators(
            recent_rate=0.60, recent_n=5,
            missing=3, considered=5,
            recent_avg=50.0, earlier_avg=70.0,
        )
    )

    assert len(factors) == 3
    assert level == "priority review"