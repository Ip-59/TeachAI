"""Дополнение пакета 1 (раздел 7 инструкции): прогресс, разбор ответов LLM, доступ к уроку.

Эталонный набор эти проверки не содержал. Ожидание взято из docs/TeachAI_test_scenarios.md.
"""
import json
import logging
import os

import pytest

from helpers import L1, L2, make_state

pytestmark = pytest.mark.unit

COURSE = {"id": "python-basics", "title": "Основы Python", "description": "Тест", "source": "catalog"}
LESSON_META = {"title": "Урок 1", "description": "Переменные", "keywords": ["переменные"]}
FENCE = "```json\n{body}\n```"


def _fenced(payload: dict) -> str:
    return FENCE.format(body=json.dumps(payload, ensure_ascii=False))


def test_ST_05_switch_keeps_each_course_progress():
    from course_portfolio import begin_new_course, bind_new_plan, snapshot_active, switch_course

    sm = make_state("course-a")
    sm.state["learning"]["control_task_bypass"] = {L1: True}
    sm.state["lesson_content_cache"] = {L1: {"content": "текст A"}}
    sm.state["control_tasks"] = {L1: {"is_correct": True, "title": "A"}}
    snapshot_active(sm.state)

    plan_b = {
        "id": "course-b",
        "title": "Курс B",
        "source": "catalog",
        "sections": [{"id": "section-1", "topics": [{"id": "topic-1-1", "lessons": [{"id": "lesson-1-1-2"}]}]}],
    }
    begin_new_course(sm.state)
    sm.state["course_plan"] = plan_b
    bind_new_plan(sm.state, plan_b)
    sm.state["learning"]["current_lesson"] = "lesson-1-1-2"
    sm.state["lesson_content_cache"] = {L2: {"content": "текст B"}}
    sm.state["control_tasks"] = {}
    sm.state["learning"]["control_task_bypass"] = {}
    snapshot_active(sm.state)

    assert switch_course(sm.state, "course-a")
    assert sm.state["active_course_id"] == "course-a"
    assert sm.state["lesson_content_cache"][L1]["content"] == "текст A"
    assert sm.state["control_tasks"][L1]["is_correct"] is True
    assert sm.state["learning"]["control_task_bypass"][L1] is True

    assert switch_course(sm.state, "course-b")
    assert sm.state["learning"]["current_lesson"] == "lesson-1-1-2"
    assert sm.state["lesson_content_cache"][L2]["content"] == "текст B"
    assert L1 not in sm.state["control_tasks"]
    assert not sm.state["learning"]["control_task_bypass"]


def test_ST_11_broken_state_does_not_crash(caplog, isolated_project):
    path = isolated_project / "data" / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{битый", encoding="utf-8")
    from state_manager import StateManager

    with caplog.at_level(logging.ERROR):
        sm = StateManager()
    assert "user" in sm.state and "learning" in sm.state
    assert "Ошибка при загрузке состояния" in caplog.text


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="ST-12: save_state пишет state.json напрямую, без tmp+rename (state_manager.py:166-167)",
)
def test_ST_12_save_state_is_atomic(monkeypatch):
    renamed: list[tuple[str, str]] = []
    real_replace = os.replace

    def spy(src, dst, *args, **kwargs):
        renamed.append((str(src), str(dst)))
        return real_replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "replace", spy)
    monkeypatch.setattr(os, "rename", spy)
    sm = make_state()
    assert sm.save_state() is True
    assert renamed, "запись state не проходит через rename/replace"


def test_LSN_12_locked_lesson_is_rejected(caplog):
    from types import SimpleNamespace

    from lesson_outline import open_lesson

    sm = make_state()
    iface = SimpleNamespace(
        state_manager=sm,
        system_logger=SimpleNamespace(log_activity=lambda **_k: None),
    )
    with caplog.at_level(logging.WARNING):
        open_lesson(iface, "section-1", "topic-1-1", "lesson-1-1-3")
    assert "закрыт политикой доступа" in caplog.text
    assert sm.state["learning"]["current_lesson"] == "lesson-1-1-1"


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="CRS-10: слот пишется по id плана, а повтор ищет id каталога (course_selection_ui.py:307, course_portfolio.py:236)",
)
def test_CRS_10_plan_id_other_than_catalog_stays_one_slot(fake_llm):
    """Повторный старт каталожного курса не должен плодить слот с id из ответа модели."""
    from course_plan_generator import CoursePlanGenerator
    from course_portfolio import begin_new_course, has_course
    from helpers import load_plan
    from state_manager import StateManager

    plan = load_plan()
    plan["id"] = "llm-renamed-id"
    fake_llm.use("plan", plan)
    sm = StateManager()
    gen = CoursePlanGenerator("sk-test-not-a-real-key")

    def start_once() -> str:
        if has_course(sm.state, COURSE["id"]):
            return "resume"
        begin_new_course(sm.state)
        course_plan = gen.generate_course_plan(COURSE, 3, 30)
        course_plan["source"] = COURSE["source"]
        sm.save_course_plan(course_plan)
        sm.update_learning_progress(course=COURSE["id"])
        return "created"

    assert start_once() == "created"
    assert start_once() == "resume"
    assert len(sm.state["courses"]) == 1
    assert COURSE["id"] in sm.state["courses"]


def test_LLM_04_broken_json_is_a_clear_error(fake_llm):
    from assessment_generator import AssessmentGenerator
    from concepts_generator import ConceptsGenerator
    from content_generator import ContentGenerator
    from control_task_llm_judge import classify_lesson_subject, task_matches_lesson
    from course_domain import classify_course_topic
    from course_plan_generator import CoursePlanGenerator

    fake_llm.use("plan", "это не json")
    with pytest.raises(Exception) as plan_err:
        CoursePlanGenerator("sk-test-not-a-real-key").generate_course_plan(COURSE, 3, 30)
    assert "Не удалось сгенерировать учебный план" in str(plan_err.value)
    assert "Traceback" not in str(plan_err.value)

    fake_llm.use("assessment", "это не json")
    with pytest.raises(Exception) as test_err:
        AssessmentGenerator("sk-test-not-a-real-key").generate_assessment(
            "Курс", "Раздел", "Тема", "Урок", "Текст урока", 5
        )
    assert "Не удалось сгенерировать вопросы" in str(test_err.value)
    assert "Traceback" not in str(test_err.value)

    fake_llm.use("concepts", "это не json")
    with pytest.raises(Exception) as concepts_err:
        ConceptsGenerator("sk-test-not-a-real-key").extract_key_concepts("Текст урока", LESSON_META)
    assert "Не удалось извлечь ключевые понятия" in str(concepts_err.value)
    assert "Traceback" not in str(concepts_err.value)

    api = ContentGenerator("sk-test-not-a-real-key").lesson_gen
    fake_llm.use("subject", "это не json")
    assert classify_lesson_subject(api, lesson_title="Урок", lesson_content="текст")
    fake_llm.use("task_matches", "это не json")
    assert (
        task_matches_lesson(
            api,
            task={"title": "Сумма", "task_code": "a = 1"},
            lesson_title="Урок",
            lesson_content="текст",
            lesson_subject="основы Python",
        )
        is False
    )
    fake_llm.use("domain", "это не json")
    verdict = classify_course_topic("Курс кройки и шитья", generator=api)
    assert verdict.status == "error"
    assert "Traceback" not in verdict.reason


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="LLM-05: json.loads не снимает обёртку ```json (course_plan_generator.py:72, assessment_generator.py:94, concepts_generator.py:90)",
)
def test_LLM_05_fenced_json_for_plan_test_and_concepts(fake_llm):
    from assessment_generator import AssessmentGenerator
    from concepts_generator import ConceptsGenerator
    from course_plan_generator import CoursePlanGenerator
    from helpers import load_plan

    fake_llm.use("plan", _fenced(load_plan()))
    try:
        got = CoursePlanGenerator("sk-test-not-a-real-key").generate_course_plan(COURSE, 3, 30)
    except Exception as exc:
        assert False, f"план: {exc}"
    assert got["sections"]

    questions = {
        "questions": [
            {
                "text": "Вопрос?",
                "options": ["верно", "нет", "тоже нет"],
                "correct_option": 1,
                "explanation": "Потому что.",
            }
        ]
    }
    fake_llm.use("assessment", _fenced(questions))
    try:
        parsed = AssessmentGenerator("sk-test-not-a-real-key").generate_assessment(
            "Курс", "Раздел", "Тема", "Урок", "Текст", 1
        )
    except Exception as exc:
        assert False, f"тест: {exc}"
    assert parsed and parsed[0]["text"]

    fake_llm.use("concepts", _fenced({"concepts": [{"name": "Переменная", "brief_description": "Имя"}]}))
    try:
        extracted = ConceptsGenerator("sk-test-not-a-real-key").extract_key_concepts("Текст", LESSON_META)
    except Exception as exc:
        assert False, f"понятия: {exc}"
    assert extracted[0]["name"] == "Переменная"


def test_LLM_05_fenced_json_for_judge_and_domain(fake_llm):
    from content_generator import ContentGenerator
    from control_task_llm_judge import task_matches_lesson
    from course_domain import classify_course_topic

    api = ContentGenerator("sk-test-not-a-real-key").lesson_gen
    fake_llm.use("task_matches", _fenced({"matches": True, "reason": "По теме."}))
    assert task_matches_lesson(
        api,
        task={"title": "Сумма"},
        lesson_title="Урок",
        lesson_content="текст",
        lesson_subject="основы Python",
    )
    fake_llm.use("domain", _fenced({"in_domain": False, "reason": "Не Python."}))
    assert classify_course_topic("Кройка", generator=api).status == "out"


def test_LLM_06_correct_option_zero_and_four(fake_llm):
    """0 приводится к 1. Индекс 4 сразу даёт ошибку: повторного запроса к модели нет.

    Пакет 2: один повтор, затем понятное сообщение ученику.
    """
    from assessment_generator import AssessmentGenerator

    gen = AssessmentGenerator("sk-test-not-a-real-key")

    def questions(index: int) -> dict:
        return {
            "questions": [
                {
                    "text": "Вопрос?",
                    "options": ["a", "b", "c"],
                    "correct_option": index,
                    "explanation": "x",
                }
            ]
        }

    normalized = gen._extract_questions_from_response(questions(0))
    assert normalized[0]["correct_option"] == 1
    with pytest.raises(Exception, match="Некорректный индекс"):
        gen._extract_questions_from_response(questions(4))
