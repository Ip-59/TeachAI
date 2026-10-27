"""Дополнение пакета 1 (раздел 7): сценарии в ядре Jupyter."""
import json

import pytest

from helpers import L1
from nbdriver import NotebookSession

pytestmark = pytest.mark.scenario


def _open_first_lesson(nb: NotebookSession) -> None:
    nb.start_teachai()
    nb.set_value("Имя", "Тест")
    nb.set_value("Общее время", 3)
    nb.set_value("Длительность урока", 30)
    nb.click("Сохранить настройки")
    nb.click("Начать курс")


def test_TST_05_double_submit_records_one_attempt(lesson):
    lesson.click("Пройти тест")
    lesson.answer_test(3)
    lesson.click("Завершить тест")
    try:
        lesson.click("Завершить тест")
    except AssertionError:
        pass
    attempts = lesson.state()["learning"]["lesson_attempts"][L1]
    assert len(attempts) == 1


def test_LSN_02_cached_lesson_makes_no_llm_calls(tmp_path):
    (tmp_path / "first").mkdir()
    (tmp_path / "second").mkdir()
    first = NotebookSession(tmp_path / "first")
    try:
        _open_first_lesson(first)
        assert "lesson" in first.llm_calls()
        saved = first.state()
        cached = next(iter(saved["lesson_content_cache"].values()))["content"]
        assert not first.harness_errors()
    finally:
        first.close()

    second = NotebookSession(tmp_path / "second")
    try:
        data_dir = second.proj / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "state.json").write_text(
            json.dumps(saved, ensure_ascii=False), encoding="utf-8"
        )
        second.start_teachai()
        second.click("Продолжить обучение")
        assert second.llm_calls() == []
        assert any("Переменные" in text for text in second.html_texts())
        again = next(iter(second.state()["lesson_content_cache"].values()))["content"]
        assert again == cached
        assert not second.harness_errors()
    finally:
        second.close()


def test_LSN_09_course_question_is_answered_with_note(lesson):
    lesson.click("Задать вопрос")
    lesson.llm_use("relevance", "relevance_course")
    lesson.type_into("Введите ваш вопрос", "Что было в прошлом уроке курса?")
    lesson.click("Отправить вопрос")
    assert "Не тема этого урока" in " ".join(lesson.html_texts())
    assert lesson.llm_calls()[-2:] == ["relevance", "qa"]
    assert lesson.state()["learning"]["questions_count"][L1] == 1


def test_KZ_14_broken_validation_uses_structured_fallback(lesson):
    lesson.click("Пройти тест")
    lesson.answer_test(3)
    lesson.click("Завершить тест")
    lesson.click("Контрольные задания")
    lesson.llm_use("task_validate", "task_validate_broken")
    lesson.set_code("a = 2\nb = 3\ntotal = a + b")
    lesson.click("Проверить решение")
    text = " ".join(lesson.html_texts()).lower()
    assert "нейросеть" in text
    assert lesson.state()["control_tasks"][L1]["is_correct"] is True
