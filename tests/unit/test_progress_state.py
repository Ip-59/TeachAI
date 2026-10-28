"""Прогресс, завершённость урока, результаты КЗ (сценарии ST, TST, KZ, LSN, PRF)."""
import logging
from types import SimpleNamespace

import pytest

from helpers import L1, L2, L3, SEC, TOP, make_state

pytestmark = pytest.mark.unit


def test_ST_02_test_passed_without_task_is_not_completed():
    sm = make_state()
    sm.save_lesson_assessment(L1, 60, True)
    assert sm.is_test_passed(L1)
    assert not sm.is_lesson_completed(L1)


def test_ST_03_test_and_correct_task_complete_lesson():
    sm = make_state()
    sm.save_lesson_assessment(L1, 60, True)
    sm.save_control_task_result(L1, "Сумма", True)
    assert sm.is_lesson_completed(L1)


def test_ST_04_bypass_and_correct_task_complete_lesson():
    sm = make_state()
    sm.mark_test_bypassed(L1)
    sm.save_control_task_result(L1, "Сумма", True)
    assert sm.is_lesson_completed(L1)


def test_TST_06_forty_percent_is_not_passed():
    sm = make_state()
    sm.state["learning"]["lesson_scores"] = {L1: 40}
    assert not sm.is_test_passed(L1)
    sm.state["learning"]["lesson_scores"] = {L1: 60}
    assert sm.is_test_passed(L1)


def test_ST_01_opening_lesson_does_not_complete_it():
    sm = make_state()
    sm.update_learning_progress(section=SEC, topic=TOP, lesson="lesson-1-1-1")
    assert L1 not in sm.state["learning"]["completed_lessons"]
    assert L1 in sm.state["learning"]["visited_lessons"]
    assert not sm.is_lesson_completed(L1)



def test_KZ_12_wrong_resubmission_keeps_best_result():
    sm = make_state()
    sm.save_control_task_result(L1, "Сумма", True)
    sm.save_control_task_result(L1, "Сумма", False)
    assert sm.state["control_tasks"][L1]["is_correct"] is True
    assert sm.state["control_tasks"][L1]["best_is_correct"] is True
    assert len(sm.state["control_tasks"][L1]["attempts"]) == 2


def test_TST_08_repeat_lesson_keeps_best_score():
    sm = make_state()
    sm.save_lesson_assessment(L1, 80, True)
    sm.mark_lesson_incomplete(L1)
    assert sm.get_lesson_score(L1) == 80


def test_LSN_13_next_lesson_is_first_unfinished():
    sm = make_state()
    for lid in (L1, L2):
        sm.mark_lesson_complete_manually(lid)
    sm.state["learning"]["current_lesson"] = "lesson-1-1-1"
    section, topic, lesson, _ = sm.get_next_lesson()
    assert lesson == "lesson-1-1-3"


def test_PRF_05_correct_task_does_not_add_test_attempt():
    from control_tasks_interface import ControlTasksInterface

    sm = make_state()
    sm.save_lesson_assessment(L1, 40, False)
    sm.save_lesson_assessment(L1, 100, True)
    li = SimpleNamespace(current_lesson_id=L1, state_manager=sm)
    fake_self = SimpleNamespace(lesson_interface=li, logger=logging.getLogger("t"))
    ControlTasksInterface._save_task_result(fake_self, {"title": "Сумма"}, True)
    assert len(sm.state["learning"]["lesson_attempts"][L1]) == 2


def test_D2_concepts_not_counted_on_test_pass():
    sm = make_state()
    sm.state["lesson_content_cache"] = {L1: {"concepts": [{"name": "Переменная", "description": "x"}]}}
    sm.save_lesson_assessment(L1, 80, True)
    assert L1 not in (sm.state["learning"].get("lesson_concepts") or {})


def test_D2_concepts_counted_on_forced_transition():
    sm = make_state()
    sm.state["lesson_content_cache"] = {L1: {"concepts": [{"name": "Переменная", "description": "x"}]}}
    sm.mark_lesson_complete_manually(L1)
    assert L1 in sm.state["learning"]["lesson_concepts"]


def test_PRF_04_dashboard_progress_ignores_opened_lessons():
    from startup_dashboard import StartupDashboard

    sm = make_state()
    sm.update_learning_progress(section="section-1", topic="topic-1-1", lesson="lesson-1-1-1")
    stats = StartupDashboard(sm, None)._get_progress_statistics()
    assert stats["completed_lessons_count"] == 0
    assert stats["progress_percent"] == 0


def test_PRF_03_dashboard_counts_completed_lesson():
    from startup_dashboard import StartupDashboard

    sm = make_state()
    sm.save_lesson_assessment(L1, 60, True)
    sm.save_control_task_result(L1, "Сумма", True)
    sm.mark_lesson_complete_manually(L1)
    stats = StartupDashboard(sm, None)._get_progress_statistics()
    assert stats["total_lessons_count"] == 3


def test_ST_16_migration_moves_opened_lessons_to_visited(isolated_project):
    """Старый state: completed_lessons = открытые. После загрузки — visited + реально пройденные."""
    import json
    from state_manager import StateManager

    path = isolated_project / "data" / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = {
        "user": {"name": "Игорь", "total_study_hours": 3, "lesson_duration_minutes": 30,
                 "communication_style": "friendly"},
        "learning": {
            "current_course": "python-basics",
            "current_section": SEC,
            "current_topic": TOP,
            "current_lesson": "lesson-1-1-1",
            "completed_lessons": [L1, L2],  # оба «открыты», реально пройден только L1
            "lesson_scores": {L1: 80},
            "lesson_attempts": {},
            "lesson_completion_status": {L1: True},
            "control_task_bypass": {},
            "questions_count": {},
            "average_score": 0,
            "total_assessments": 0,
            "total_score": 0,
            "course_progress_percent": 0,
        },
        "course_plan": {"id": "python-basics", "title": "Основы", "sections": []},
        "active_course_id": "python-basics",
        "courses": {},
        "control_tasks": {},
        "lesson_content_cache": {},
        "system": {"first_run": False, "last_access": "2026-01-01T00:00:00", "version": "1.0.0"},
    }
    path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    sm = StateManager()
    learn = sm.state["learning"]
    assert L1 in learn["visited_lessons"] and L2 in learn["visited_lessons"]
    assert L1 in learn["completed_lessons"]
    assert L2 not in learn["completed_lessons"]
    assert learn.get("_schema_version") == 2
