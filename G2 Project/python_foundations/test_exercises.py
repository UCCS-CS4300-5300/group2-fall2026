import pytest

from python_foundations.exercises import (
    StudyGoal,
    calculate_priority,
    filter_active_items,
    normalize_tag,
    summarize_minutes,
)


def test_normalize_tag():
    assert normalize_tag("  Software Testing  ") == "software-testing"
    assert normalize_tag("CI CD") == "ci-cd"


def test_calculate_priority():
    assert calculate_priority(4, 3) == 12
    assert calculate_priority(1, 5) == 5


@pytest.mark.parametrize("importance, urgency", [(0, 3), (6, 2), (3, 0), (2, 6)])
def test_calculate_priority_rejects_out_of_range_values(importance, urgency):
    with pytest.raises(ValueError):
        calculate_priority(importance, urgency)


def test_filter_active_items():
    items = [
        {"name": "A", "active": True},
        {"name": "B", "active": False},
        {"name": "C", "active": True},
    ]
    result = filter_active_items(items)
    assert [item["name"] for item in result] == ["A", "C"]
    assert len(items) == 3


def test_summarize_minutes():
    sessions = [
        {"topic": "pytest", "minutes": 30},
        {"topic": "Django", "minutes": 45},
    ]
    assert summarize_minutes(sessions) == 75
    assert summarize_minutes([]) == 0


def test_study_goal_tracks_progress():
    goal = StudyGoal("HW1", 120)
    goal.log_minutes(45)
    goal.log_minutes(75)
    assert goal.completed_minutes == 120
    assert goal.is_complete() is True


def test_study_goal_is_not_complete_early():
    goal = StudyGoal("HW1", 120)
    goal.log_minutes(60)
    assert goal.is_complete() is False


def test_study_goal_rejects_nonpositive_minutes():
    goal = StudyGoal("HW1", 120)
    with pytest.raises(ValueError):
        goal.log_minutes(0)
    with pytest.raises(ValueError):
        goal.log_minutes(-10)
