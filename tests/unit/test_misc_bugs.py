"""Известные баги без Jupyter: конфиг, парсинг примеров, ретраи LLM, выполнение кода (ZAP, LSN, LLM, SEC, KZ)."""
import os
import pytest

pytestmark = pytest.mark.unit


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="ZAP-02: create_sample_env перезаписывает существующий .env.sample (config.py:139-149)")
def test_ZAP_02_sample_env_not_overwritten(isolated_project):
    from config import ConfigManager

    sample = isolated_project / ".env.sample"
    sample.write_text("МОЁ СОДЕРЖИМОЕ", encoding="utf-8")
    ConfigManager().create_sample_env()
    assert sample.read_text(encoding="utf-8") == "МОЁ СОДЕРЖИМОЕ"


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="LSN-06: однострочный пример отбрасывается (examples_html_utils.py:158)")
def test_LSN_06_one_line_example_is_kept():
    from examples_html_utils import executable_examples

    payload = {"examples": [{"title": "Тип", "description": "", "code": "print(type(3.5))"}]}
    assert len(executable_examples(payload)) == 1


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="LLM-01: 401 повторяется 3 раза и объясняется «прокси» (content_utils.py:588-632)")
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


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="SEC-04: eval на выводе программы (result_checker.py:358)")
def test_SEC_04_no_eval_on_program_output():
    from result_checker import extract_numpy_arrays

    extract_numpy_arrays("[__import__('os').__setattr__('TEACHAI_EVAL_PROBE', 1)]")
    try:
        assert not hasattr(os, "TEACHAI_EVAL_PROBE")
    finally:
        if hasattr(os, "TEACHAI_EVAL_PROBE"):
            del os.TEACHAI_EVAL_PROBE


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="SEC-02: код ученика читает OPENAI_API_KEY (control_tasks_generator.py:64, exec в процессе ядра)")
def test_SEC_02_student_code_cannot_read_api_key():
    from control_tasks_generator import ControlTasksGenerator

    out, _ = ControlTasksGenerator.execute_code("import os\nprint(os.environ.get('OPENAI_API_KEY', 'НЕТ КЛЮЧА'))")
    assert "sk-test" not in out


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="SEC-01: код ученика пишет в файлы текущей папки (control_tasks_generator.py:64)")
def test_SEC_01_student_code_cannot_touch_project_files(isolated_project):
    from control_tasks_generator import ControlTasksGenerator

    marker = isolated_project / "student_wrote_this.txt"
    ControlTasksGenerator.execute_code("open('student_wrote_this.txt', 'w').write('x')")
    assert not marker.exists()


@pytest.mark.skip(reason="KZ-16: `while True` повесит тест, пока нет таймаута (пакет 4, D9). После D9 снять skip и ожидать сообщение «Код выполнялся слишком долго…»")
def test_KZ_16_infinite_loop_is_stopped():
    from control_tasks_generator import ControlTasksGenerator

    ControlTasksGenerator.execute_code("while True:\n    pass")
