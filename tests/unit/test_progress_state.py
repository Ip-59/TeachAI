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


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="ST-01: открытие урока кладёт его в completed_lessons (learning_progress_manager.py:47-56)")
def test_ST_01_opening_lesson_does_not_complete_it():
    sm = make_state()
    sm.update_learning_progress(section=SEC, topic=TOP, lesson="lesson-1-1-1")
    assert L1 not in sm.state["learning"]["completed_lessons"]



@pytest.mark.xfail(strict=True, raises=AssertionError, reason="KZ-12: верный результат КЗ затирается неверной пересдачей (state_manager.py:368-372)")
def test_KZ_12_wrong_resubmission_keeps_best_result():
    sm = make_state()
    sm.save_control_task_result(L1, "Сумма", True)
    sm.save_control_task_result(L1, "Сумма", False)
    assert sm.state["control_tasks"][L1]["is_correct"] is True


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="TST-08: «Повторить урок» удаляет лучший балл (learning_progress_manager.py:316-320)")
def test_TST_08_repeat_lesson_keeps_best_score():
    sm = make_state()
    sm.save_lesson_assessment(L1, 80, True)
    sm.mark_lesson_incomplete(L1)
    assert sm.get_lesson_score(L1) == 80


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="LSN-13: следующий урок ищется по позиции, а не первый незавершённый (course_data_manager.py:177)")
def test_LSN_13_next_lesson_is_first_unfinished():
    sm = make_state()
    for lid in (L1, L2):
        sm.mark_lesson_complete_manually(lid)
    sm.state["learning"]["current_lesson"] = "lesson-1-1-1"
    section, topic, lesson, _ = sm.get_next_lesson()
    assert lesson == "lesson-1-1-3"


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="PRF-05: верное КЗ добавляет лишнюю «попытку теста» (control_tasks_interface.py:535)")
def test_PRF_05_correct_task_does_not_add_test_attempt():
    from control_tasks_interface import ControlTasksInterface

    sm = make_state()
    sm.save_lesson_assessment(L1, 40, False)
    sm.save_lesson_assessment(L1, 100, True)
    li = SimpleNamespace(current_lesson_id=L1, state_manager=sm)
    fake_self = SimpleNamespace(lesson_interface=li, logger=logging.getLogger("t"))
    ControlTasksInterface._save_task_result(fake_self, {"title": "Сумма"}, True)
    assert len(sm.state["learning"]["lesson_attempts"][L1]) == 2


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="D2: понятия записываются в профиль уже при тесте >40% (learning_progress_manager.py:119-122); по D2 — только при переходе")
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


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="PRF-04: дашборд считает открытые уроки как пройденные (startup_dashboard.py:300-316, learning_progress_manager.py:47-56)")
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
