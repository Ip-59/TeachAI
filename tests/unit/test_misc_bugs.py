"""Известные баги без Jupyter: конфиг, парсинг примеров, ретраи LLM, выполнение кода (ZAP, LSN, LLM, SEC, KZ)."""
import os
import pytest

pytestmark = pytest.mark.unit


def test_ZAP_02_sample_env_not_overwritten(isolated_project):
    from config import ConfigManager

    sample = isolated_project / ".env.sample"
    sample.write_text("МОЁ СОДЕРЖИМОЕ", encoding="utf-8")
    ConfigManager().create_sample_env()
    assert sample.read_text(encoding="utf-8") == "МОЁ СОДЕРЖИМОЕ"


def test_LSN_06_one_line_example_is_kept():
    from examples_html_utils import executable_examples

    payload = {"examples": [{"title": "Тип", "description": "", "code": "print(type(3.5))"}]}
    assert len(executable_examples(payload)) == 1


@pytest.mark.parametrize("code", ["pip install numpy", "python --version", "$ pip install pandas"])
def test_LSN_06_one_line_terminal_commands_are_still_dropped(code):
    from examples_html_utils import executable_examples

    payload = {"examples": [{"title": "Установка", "description": "", "code": code}]}
    assert executable_examples(payload) == []


def test_LSN_06_one_line_example_passes_quality_check():
    from examples_validation import ExamplesValidation

    checker = ExamplesValidation("sk-test-not-a-real-key")
    assert checker.validate_examples_quality(
        [{"title": "Тип", "description": "", "code": "print(type(3.5))"}]
    )


def test_LLM_01_401_is_not_retried(fake_llm, monkeypatch):
    import time
    from course_plan_generator import CoursePlanGenerator

    monkeypatch.setattr(time, "sleep", lambda *_: None)
    fake_llm.use("plan", Exception("Error code: 401 - invalid_api_key"))
    gen = CoursePlanGenerator("sk-test-not-a-real-key")
    with pytest.raises(Exception) as err:
        gen.make_api_request_with_retries(
            messages=[{"role": "system", "content": "Ты - опытный методист образовательных программ."},
                      {"role": "user", "content": "x"}])
    assert fake_llm.count("plan") == 1
    assert "прокси" not in str(err.value).lower()
    assert "ключ" in str(err.value).lower()


def test_SEC_04_no_eval_on_program_output():
    from result_checker import extract_numpy_arrays

    extract_numpy_arrays("[__import__('os').__setattr__('TEACHAI_EVAL_PROBE', 1)]")
    try:
        assert not hasattr(os, "TEACHAI_EVAL_PROBE")
    finally:
        if hasattr(os, "TEACHAI_EVAL_PROBE"):
            del os.TEACHAI_EVAL_PROBE


def test_SEC_02_student_code_cannot_read_api_key():
    from control_tasks_generator import ControlTasksGenerator

    out, _ = ControlTasksGenerator.execute_code("import os\nprint(os.environ.get('OPENAI_API_KEY', 'НЕТ КЛЮЧА'))")
    assert "sk-test" not in out


def test_SEC_01_student_code_cannot_touch_project_files(isolated_project):
    from control_tasks_generator import ControlTasksGenerator

    marker = isolated_project / "student_wrote_this.txt"
    ControlTasksGenerator.execute_code("open('student_wrote_this.txt', 'w').write('x')")
    assert not marker.exists()


def test_KZ_16_infinite_loop_is_stopped():
    from control_tasks_generator import ControlTasksGenerator

    with pytest.raises(Exception) as ei:
        ControlTasksGenerator.execute_code("while True:\n    pass")
    assert "Код выполнялся слишком долго" in str(ei.value)
