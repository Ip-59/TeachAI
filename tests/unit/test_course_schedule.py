"""Время курса в слоте плана; профиль без обязательных часов."""
import pytest

pytestmark = pytest.mark.unit


def test_schedule_of_reads_explicit_fields():
    from course_portfolio import schedule_of

    state = {
        "courses": {
            "c1": {
                "course_plan": {
                    "total_study_hours": 4,
                    "lesson_duration_minutes": 20,
                    "total_duration_minutes": 240,
                }
            }
        }
    }
    assert schedule_of(state, "c1") == {
        "total_study_hours": 4,
        "lesson_duration_minutes": 20,
    }


def test_schedule_of_fallback_from_total_duration_and_lesson():
    from course_portfolio import schedule_of

    state = {
        "courses": {
            "old": {
                "course_plan": {
                    "total_duration_minutes": 180,
                    "sections": [
                        {
                            "topics": [
                                {"lessons": [{"duration_minutes": 45}]}
                            ]
                        }
                    ],
                }
            }
        }
    }
    assert schedule_of(state, "old") == {
        "total_study_hours": 3,
        "lesson_duration_minutes": 45,
    }


def test_schedule_of_fallback_default_lesson_30():
    from course_portfolio import schedule_of

    state = {
        "courses": {
            "old": {"course_plan": {"total_duration_minutes": 60}}
        }
    }
    assert schedule_of(state, "old") == {
        "total_study_hours": 1,
        "lesson_duration_minutes": 30,
    }


def test_schedule_of_none_without_hours_source():
    from course_portfolio import schedule_of

    state = {"courses": {"x": {"course_plan": {"sections": []}}}}
    assert schedule_of(state, "x") is None
    assert schedule_of(state, "missing") is None


def test_validate_user_profile_allows_zero_course_time():
    from state_manager import StateManager

    sm = StateManager()
    sm.state["user"]["name"] = "Тест"
    sm.state["user"]["communication_style"] = "friendly"
    sm.state["user"]["total_study_hours"] = 0
    sm.state["user"]["lesson_duration_minutes"] = 0
    ok, missing = sm.user_profile.validate_user_profile()
    assert ok is True
    assert missing == []


def test_validate_user_profile_still_requires_name():
    from state_manager import StateManager

    sm = StateManager()
    sm.state["user"]["name"] = ""
    sm.state["user"]["communication_style"] = "friendly"
    ok, missing = sm.user_profile.validate_user_profile()
    assert ok is False
    assert "name" in missing
