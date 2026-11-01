"""Общие помощники для unit-тестов."""
from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "llm"
SEC, TOP = "section-1", "topic-1-1"
L1, L2, L3 = (f"{SEC}:{TOP}:lesson-1-1-{i}" for i in (1, 2, 3))


def load_plan() -> dict:
    return json.loads((FIXTURES / "plan.json").read_text(encoding="utf-8"))


def make_state(plan_id: str = "python-basics"):
    """StateManager во временной папке с готовым планом из 3 уроков и активным курсом."""
    from state_manager import StateManager
    from course_portfolio import bind_new_plan

    sm = StateManager()
    plan = load_plan()
    plan["id"] = plan_id
    sm.state["course_plan"] = plan
    bind_new_plan(sm.state, plan)
    sm.state["learning"]["current_section"] = SEC
    sm.state["learning"]["current_topic"] = TOP
    sm.state["learning"]["current_lesson"] = "lesson-1-1-1"
    sm.save_state()
    return sm


def start_catalog_course(nb, *, name="Тест", hours=3, minutes=30):
    """Профиль (имя) -> экран курса (часы/занятие) -> «Начать курс».

    Время больше не на форме профиля: слайдеры на экране выбора курса.
    Подстроки description: «Общее время курса (часов):», «Длительность занятия (минут):».
    """
    nb.set_value("Имя", name)
    nb.click("Сохранить настройки")
    nb.set_value("Общее время курса", hours)
    nb.set_value("Длительность занятия", minutes)
    nb.click("Начать курс")

