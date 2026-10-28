"""Основной путь ученика в настоящем ядре Jupyter (ZAP, CRS, LSN, TST, KZ, ST)."""
import pytest

from helpers import L1

pytestmark = pytest.mark.scenario


def test_ZAP_01_no_debug_output_on_start(nb):
    out = nb.start_teachai()
    assert "Traceback" not in out
    assert "ОТЛАДКА" not in out


def test_PRF_01_empty_name_does_not_create_profile(nb):
    nb.start_teachai()
    nb.click("Сохранить настройки")
    assert nb.llm_calls() == []
    assert not (nb.proj / "data" / "state.json").exists() or not nb.state()["user"].get("name")


def test_CRS_01_start_catalog_course(lesson):
    assert lesson.llm_calls() == ["plan", "lesson", "concepts"]
    st = lesson.state()
    assert st["active_course_id"] == "python-basics"
    assert "python-basics" in st["courses"]


def test_TST_07_sixty_percent_passes_but_does_not_complete(lesson):
    lesson.click("Пройти тест")
    lesson.answer_test(3)
    lesson.click("Завершить тест")
    learn = lesson.state()["learning"]
    assert learn["lesson_scores"][L1] == 60
    assert not learn.get("lesson_completion_status", {}).get(L1)
    assert lesson.buttons("Перейти к контрольным заданиям")


def test_ZAP_01_no_debug_output_on_course_start(nb):
    nb.start_teachai()
    nb.set_value("Имя", "Тест"); nb.set_value("Общее время", 3); nb.set_value("Длительность урока", 30)
    out = nb.click("Сохранить настройки") + nb.click("Начать курс")
    assert "ОТЛАДКА" not in out
    assert "Ключи" not in out


def test_KZ_18_checking_a_solution_prints_no_diagnostics(lesson):
    lesson.click("Пройти тест"); lesson.answer_test(5); lesson.click("Завершить тест")
    lesson.click("Контрольные задания")
    lesson.llm_use("task_validate", "task_validate_wrong")
    lesson.set_code("a = 2\nb = 3\ntotal = 1")
    out = lesson.click("Проверить решение")
    assert "DIAGNOSTIC" not in out
    assert "expected_output" not in out


def test_TST_02_no_option_preselected(lesson):
    lesson.click("Пройти тест")
    values = lesson.eval(
        "[w.value for w in __import__('ipywidgets').Widget.widgets.values() "
        "if type(w).__name__ == 'RadioButtons' and len(w.options) == 3][-5:]")
    assert values == [None] * 5


def test_KZ_08_wrong_solution_is_recorded_and_lesson_not_completed(lesson):
    lesson.click("Пройти тест"); lesson.answer_test(3); lesson.click("Завершить тест")
    lesson.click("Контрольные задания")
    lesson.llm_use("task_validate", "task_validate_wrong")
    lesson.set_code("a = 2\nb = 3\ntotal = 1")
    lesson.click("Проверить решение")
    st = lesson.state()
    assert st["control_tasks"][L1]["is_correct"] is False
    assert not st["learning"]["lesson_completion_status"].get(L1)


def test_KZ_09_reference_solution_not_shown_after_wrong_attempt(lesson):
    lesson.click("Пройти тест"); lesson.answer_test(3); lesson.click("Завершить тест")
    lesson.click("Контрольные задания")
    lesson.llm_use("task_validate", "task_validate_wrong")
    lesson.set_code("a = 2\nb = 3\ntotal = 1")
    lesson.click("Проверить решение")
    assert not any("Эталонное решение" in t for t in lesson.html_texts())
    assert lesson.buttons("Показать решение")


def test_KZ_10_correct_solution_completes_lesson(lesson):
    lesson.click("Пройти тест"); lesson.answer_test(3); lesson.click("Завершить тест")
    lesson.click("Контрольные задания")
    lesson.set_code("a = 2\nb = 3\ntotal = a + b")
    lesson.click("Проверить решение")
    st = lesson.state()
    assert st["control_tasks"][L1]["is_correct"] is True
    assert st["learning"]["lesson_completion_status"][L1] is True
    assert st["learning"]["lesson_pass_mode"][L1] == "normal"


def test_TST_09_continue_after_failed_test_marks_no_test(lesson):
    lesson.click("Пройти тест"); lesson.answer_test(1); lesson.click("Завершить тест")
    lesson.click("Продолжить с текущей оценкой")
    learn = lesson.state()["learning"]
    assert learn["lesson_completion_status"][L1] is True
    assert learn.get("lesson_pass_mode", {}).get(L1) == "no_test"


def test_LSN_04_opening_concepts_does_not_count_them(lesson):
    lesson.click("Объяснить подробнее")
    lesson.click("Ключевые понятия")
    assert L1 not in (lesson.state()["learning"].get("lesson_concepts") or {})


def test_LSN_10_outside_question_not_counted_as_answered(lesson):
    lesson.click("Задать вопрос")
    lesson.llm_use("relevance", "relevance_outside")
    lesson.type_into("Введите ваш вопрос", "Какая завтра погода?")
    lesson.click("Отправить вопрос")
    assert "qa" not in lesson.llm_calls()
    assert lesson.state()["learning"]["questions_count"].get(L1, 0) == 0
    assert lesson.state()["learning"]["offtopic_count"].get(L1, 0) == 1


def test_LSN_08_relevant_question_is_answered_and_counted(lesson):
    lesson.click("Задать вопрос")
    lesson.type_into("Введите ваш вопрос", "Что такое переменная?")
    lesson.click("Отправить вопрос")
    assert lesson.llm_calls()[-2:] == ["relevance", "qa"]
    assert lesson.state()["learning"]["questions_count"][L1] == 1


def test_LSN_15_back_to_courses_works_after_repeat_lesson(lesson):
    lesson.click("Пройти тест"); lesson.answer_test(1); lesson.click("Завершить тест")
    lesson.click("Повторить урок")
    before = len(lesson.buttons("Продолжить обучение"))
    lesson.click("Назад к курсам")
    assert len(lesson.buttons("Продолжить обучение")) == before + 1


def _start_custom_out_of_domain(nb):
    nb.start_teachai()
    nb.set_value("Имя", "Тест"); nb.set_value("Общее время", 3); nb.set_value("Длительность урока", 30)
    nb.click("Сохранить настройки")
    nb.choose("Своё название курса")
    nb.llm_use("domain", "domain_out")
    nb.set_value("Название", "Курс кройки и шитья")
    nb.click("Начать курс")


def test_CRS_04_out_of_domain_course_is_blocked_with_choice(nb):
    _start_custom_out_of_domain(nb)
    assert nb.buttons("Всё равно начать")
    assert nb.buttons("Выбрать другой курс")
    assert "plan" not in nb.llm_calls()
    assert not nb.state().get("courses")


def test_CRS_05_forced_out_of_domain_course_is_marked_in_state(nb):
    _start_custom_out_of_domain(nb)
    nb.click("Всё равно начать")
    st = nb.state()
    assert "plan" in nb.llm_calls()
    meta = st["courses"][st["active_course_id"]]["meta"]
    assert meta.get("domain_override") is True


def test_KZ_01_open_task_without_test_asks_confirmation_then_records_bypass(lesson):
    lesson.click("Контрольные задания")
    assert lesson.buttons("Перейти к практике без теста")
    assert "task_gen" not in lesson.llm_calls()
    lesson.click("Перейти к практике без теста")
    assert lesson.state()["learning"]["control_task_bypass"][L1] is True
    assert "task_gen" in lesson.llm_calls()


def test_KZ_02_cancel_bypass_records_nothing(lesson):
    lesson.click("Контрольные задания")
    lesson.click("Отмена")
    assert not lesson.state()["learning"].get("control_task_bypass")
    assert "task_gen" not in lesson.llm_calls()


def test_KZ_13_bypass_and_task_not_required_passes_lesson(lesson):
    """D6: тест обойдён + «Задание не требуется» => урок пройден."""
    lesson.llm_use("code_practice", "code_practice_no")
    lesson.click("Контрольные задания")
    lesson.click("Перейти к практике без теста")
    lesson.click("Перейти к следующему уроку")
    learn = lesson.state()["learning"]
    assert learn["control_task_bypass"][L1] is True
    assert learn["lesson_completion_status"][L1] is True


def test_ZAP_07_second_start_in_same_kernel_makes_no_llm_calls(lesson):
    calls_before = len(lesson.llm_calls())
    lesson.start_teachai()
    assert len(lesson.llm_calls()) == calls_before
    assert lesson.buttons("Продолжить обучение")


def test_TST_03_empty_test_is_not_accepted(lesson):
    lesson.click("Пройти тест")
    lesson.click("Завершить тест")
    assert L1 not in lesson.state()["learning"].get("lesson_attempts", {})


def test_LLM_06_bad_test_twice_shows_one_clear_message(lesson):
    bad = {"questions": [{"text": "В?", "options": ["a", "b", "c"], "correct_option": 4, "explanation": "x"}]}
    lesson.llm_use("assessment", bad)
    lesson.click("Пройти тест")
    assert lesson.llm_calls().count("assessment") == 2
    texts = lesson.eval(
        "[w.value for w in __import__('ipywidgets').Widget.widgets.values() "
        "if type(w).__name__ == 'HTML' and 'дважды' in w.value]")
    assert texts, "ученик не увидел понятного сообщения"
    assert texts[-1].count("Не удалось сгенерировать вопросы") == 1
    assert "Некорректный индекс" not in texts[-1]
    assert lesson.buttons("Вернуться к уроку")
