"""КЗ: судья — модель. Совпавший вывод не принимается кодом в обход неё."""
import pytest

pytestmark = pytest.mark.unit


def test_judge_rules_do_not_treat_library_params_as_another_topic():
    from control_task_llm_judge import MATCH_RULES_RU, student_reject_reason

    assert "matches=true" in MATCH_RULES_RU
    assert "linewidth" in MATCH_RULES_RU
    assert "целиком" in MATCH_RULES_RU
    shown = student_reject_reason(
        "Задание целиком копирует пример урока, менять нечего."
    )
    assert "Причина:" in shown
    assert "копирует пример" in shown
    assert "другой темы" not in shown
    assert "Повторите попытку позже." in student_reject_reason("")

OUTPUT = "30 1.8 Алексей Смирнов True"
STARTER = """age = 30
height = 1.80
full_name = "Алексей Смирнов"
is_student = True
# Ваш код здесь"""
SOLUTION = STARTER + "\nprint(age, height, full_name, is_student)"
LOCAL = {
    "age": 30,
    "height": 1.8,
    "full_name": "Алексей Смирнов",
    "is_student": True,
}


def _task() -> dict:
    return {
        "title": "Переменные",
        "description": "Объявите переменные и выведите их.",
        "student_steps": [
            "Шаг 1: Объявите переменные age, height, full_name и is_student.",
            "Шаг 2: Выведите их значения на экран.",
        ],
        "task_code": STARTER,
        "solution_code": SOLUTION,
        "validation_mode": "llm",
        "check_variables": ["age", "height", "full_name", "is_student"],
        "check_variable": "is_student",
        "output_format": OUTPUT,
        "expected_variable_values": dict(LOCAL),
    }


def test_infer_check_variables_does_not_duplicate_or_mutate():
    from control_tasks_generator import ControlTasksGenerator

    data = _task()
    original = list(data["check_variables"])
    names = ControlTasksGenerator.infer_check_variables(data, SOLUTION, LOCAL)
    assert names == ["age", "height", "full_name", "is_student"]
    assert data["check_variables"] == original

    data["check_variable"] = "height"
    data["check_variables"] = ["age"]
    names = ControlTasksGenerator.infer_check_variables(data, SOLUTION, LOCAL)
    assert names == ["age", "height"]
    assert data["check_variables"] == ["age"]


def test_judge_prompt_forbids_invented_requirements(fake_llm):
    from control_tasks_generator import ControlTasksGenerator

    gen = ControlTasksGenerator("sk-test-not-a-real-key")
    prompt = gen.build_llm_validation_prompt(
        task_data=_task(),
        student_code=SOLUTION,
        student_stdout=OUTPUT,
        student_vars=LOCAL,
        reference_stdout=OUTPUT,
        reference_vars=LOCAL,
    )
    assert "Других требований нет" in prompt
    assert "вывод в столбик" in prompt
    assert "Если такой пункт назвать нельзя" in prompt
    assert "Вписанный готовый ответ шаг не выполняет" in prompt
    assert "Совпавшие критерии не отклоняй" not in prompt
    criteria = gen.build_validation_criteria(
        _task(),
        ["age", "height", "full_name", "is_student"],
        expected_vars=LOCAL,
    )
    text = " ".join(criteria)
    assert "других требований к оформлению нет" in text
    assert "не дословное совпадение" not in text


def test_matching_print_still_asks_the_model(fake_llm):
    from control_tasks_generator import ControlTasksGenerator

    fake_llm.use(
        "task_validate",
        {
            "is_correct": True,
            "score": 100,
            "feedback": "Шаги выполнены, формат совпал.",
            "failure_reason": "",
        },
    )
    gen = ControlTasksGenerator("sk-test-not-a-real-key")
    result = gen.validate_task_execution(SOLUTION, task_data=_task())
    assert result["is_correct"] is True
    assert result["validation_method"] == "llm"
    assert fake_llm.count("task_validate") == 1
    sent = fake_llm.calls[-1].messages
    system = sent[0]["content"]
    assert "Проверяешь контрольные задания по смыслу решения" in system
    assert "не источник дополнительных требований" in system
