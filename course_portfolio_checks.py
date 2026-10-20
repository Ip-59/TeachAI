"""Проверки портфеля курсов без Jupyter (запуск: python course_portfolio_checks.py)."""

from __future__ import annotations

from course_portfolio import (
    begin_new_course,
    bind_new_plan,
    delete_course,
    empty_learning,
    empty_plan,
    has_course,
    list_user_courses,
    mark_active_completed,
    migrate_state,
    snapshot_active,
    switch_course,
)


def _base_state() -> dict:
    return {
        "learning": empty_learning(),
        "course_plan": empty_plan(),
        "lesson_content_cache": {},
        "control_tasks": {},
        "system": {"first_run": False},
    }


def _fill_course(state: dict, course_id: str, lesson: str, percent: float) -> None:
    state["learning"]["current_course"] = course_id
    state["learning"]["current_section"] = "s1"
    state["learning"]["current_topic"] = "t1"
    state["learning"]["current_lesson"] = lesson
    state["learning"]["course_progress_percent"] = percent
    state["course_plan"] = {
        "id": course_id,
        "title": f"Курс {course_id}",
        "description": "",
        "source": "catalog",
        "total_duration_minutes": 60,
        "sections": [{"id": "s1", "topics": [{"id": "t1", "lessons": [{"id": lesson}]}]}],
    }
    state["control_tasks"] = {f"s1:t1:{lesson}": {"is_correct": True}}
    state["lesson_content_cache"] = {f"s1:t1:{lesson}": {"title": lesson, "content": "x"}}
    state["active_course_id"] = course_id
    snapshot_active(state)


def test_migrate_single_slot() -> None:
    state = _base_state()
    state["learning"]["current_course"] = "python-basics"
    state["learning"]["current_lesson"] = "l2"
    state["course_plan"]["id"] = "python-basics"
    state["course_plan"]["title"] = "Python"
    state["course_plan"]["sections"] = [{"id": "s"}]
    assert migrate_state(state) is True
    assert has_course(state, "python-basics")
    assert state["active_course_id"] == "python-basics"
    assert state["courses"]["python-basics"]["learning"]["current_lesson"] == "l2"
    assert migrate_state(state) is False


def test_begin_new_preserves_previous() -> None:
    state = _base_state()
    _fill_course(state, "course-a", "lesson-3", 40)
    begin_new_course(state)
    assert state["active_course_id"] == ""
    assert state["learning"]["current_lesson"] == ""
    assert has_course(state, "course-a")
    assert state["courses"]["course-a"]["learning"]["current_lesson"] == "lesson-3"
    plan_b = {
        "id": "course-b",
        "title": "Курс B",
        "source": "user",
        "sections": [{"id": "s1"}],
    }
    state["course_plan"] = plan_b
    bind_new_plan(state, plan_b, source="user")
    assert state["active_course_id"] == "course-b"
    assert has_course(state, "course-a")
    assert has_course(state, "course-b")
    switch_course(state, "course-a")
    assert state["learning"]["current_lesson"] == "lesson-3"
    assert state["control_tasks"]["s1:t1:lesson-3"]["is_correct"] is True


def test_switch_isolates_control_tasks() -> None:
    state = _base_state()
    _fill_course(state, "course-a", "l1", 10)
    begin_new_course(state)
    _fill_course(state, "course-b", "l1", 20)
    assert "s1:t1:l1" in state["control_tasks"]
    switch_course(state, "course-a")
    assert state["active_course_id"] == "course-a"
    assert state["learning"]["current_lesson"] == "l1"
    switch_course(state, "course-b")
    assert state["learning"]["course_progress_percent"] == 20


def test_delete_does_not_restore() -> None:
    state = _base_state()
    _fill_course(state, "course-a", "l1", 10)
    begin_new_course(state)
    _fill_course(state, "course-b", "l9", 90)
    assert delete_course(state, "course-b") is True
    assert not has_course(state, "course-b")
    assert state["active_course_id"] == "course-a"
    assert state["learning"]["current_lesson"] == "l1"
    assert delete_course(state, "course-a") is True
    assert state["courses"] == {}
    assert state["active_course_id"] == ""
    assert state["learning"]["current_lesson"] == ""


def test_list_and_completed() -> None:
    state = _base_state()
    _fill_course(state, "course-a", "l1", 100)
    mark_active_completed(state)
    rows = list_user_courses(state)
    assert len(rows) == 1
    assert rows[0]["is_active"] is True
    assert rows[0]["status"] == "completed"


def main() -> None:
    tests = [
        test_migrate_single_slot,
        test_begin_new_preserves_previous,
        test_switch_isolates_control_tasks,
        test_delete_does_not_restore,
        test_list_and_completed,
    ]
    for fn in tests:
        fn()
        print(f"OK {fn.__name__}")
    print("Все проверки портфеля прошли.")


if __name__ == "__main__":
    main()
