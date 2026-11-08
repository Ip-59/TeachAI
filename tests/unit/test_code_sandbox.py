"""D9: изолированное выполнение кода ученика (code_sandbox)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_sandbox_timeout_message():
    from code_sandbox import TIMEOUT_MESSAGE, run_student_code

    result = run_student_code("while True:\n    pass", timeout=2)
    assert result.timed_out
    assert result.error == TIMEOUT_MESSAGE


def test_sandbox_env_without_api_key():
    from code_sandbox import run_student_code

    assert "OPENAI_API_KEY" in os.environ
    result = run_student_code(
        "import os\nprint(os.environ.get('OPENAI_API_KEY', 'НЕТ КЛЮЧА'))"
    )
    assert result.success
    assert "sk-test" not in (result.stdout or "")
    assert "НЕТ КЛЮЧА" in (result.stdout or "")


def test_sandbox_cwd_isolation(tmp_path, monkeypatch):
    from code_sandbox import run_student_code

    monkeypatch.chdir(tmp_path)
    marker = tmp_path / "student_wrote_this.txt"
    result = run_student_code("open('student_wrote_this.txt', 'w').write('x')")
    assert result.success
    assert not marker.exists()


def test_sandbox_variable_return():
    from code_sandbox import run_student_code

    result = run_student_code("a = 21\nb = a * 2")
    assert result.success
    assert result.variables["a"] == 21
    assert result.variables["b"] == 42


def test_sandbox_non_serializable_value_uses_repr_flag():
    from code_sandbox import run_student_code

    result = run_student_code("class Box:\n    pass\nobj = Box()")
    assert result.success
    assert isinstance(result.variables["obj"], str)
    assert "Box" in result.variables["obj"]


def test_sandbox_heavy_import_timeout_selection():
    from code_sandbox import (
        DEFAULT_TIMEOUT_SEC,
        HEAVY_TIMEOUT_SEC,
        choose_timeout,
    )

    assert choose_timeout("print(1)") == DEFAULT_TIMEOUT_SEC
    assert choose_timeout("import sklearn\nprint(1)") == DEFAULT_TIMEOUT_SEC
    assert choose_timeout("import tensorflow as tf") == HEAVY_TIMEOUT_SEC
    assert choose_timeout("from tensorflow import keras") == HEAVY_TIMEOUT_SEC
    assert choose_timeout("import torch\nx=1") == HEAVY_TIMEOUT_SEC


def test_sandbox_examples_path_runs():
    """Путь примеров: examples_validation.validate_examples_execute через sandbox."""
    import logging

    from examples_validation import ExamplesValidation

    validator = ExamplesValidation.__new__(ExamplesValidation)
    validator.logger = logging.getLogger("test_sandbox_examples")
    ok = validator.validate_examples_execute(
        [{"title": "t", "description": "d", "code": "print('ok-example')"}]
    )
    assert ok is True


def test_example_run_html_shows_print_value_and_empty():
    from examples_display import format_example_run_html

    printed = format_example_run_html("30 1.8\n", "", None)
    assert "Результат запуска" in printed
    assert "30 1.8" in printed

    value = format_example_run_html("", "", 42)
    assert "42" in value

    empty = format_example_run_html("   ", "", None)
    assert "вывода нет" in empty


def test_sandbox_examples_path_rejects_bad_code():
    import logging

    from examples_validation import ExamplesValidation

    validator = ExamplesValidation.__new__(ExamplesValidation)
    validator.logger = logging.getLogger("test_sandbox_examples_bad")
    ok = validator.validate_examples_execute(
        [{"title": "t", "description": "d", "code": "raise ValueError('boom')"}]
    )
    assert ok is False


def test_sandbox_stdin_closed():
    from code_sandbox import run_student_code

    result = run_student_code("input('> ')")
    assert not result.success
    assert result.exception_type == "EOFError"

def test_sandbox_matplotlib_figure_captured():
    pytest.importorskip("matplotlib")
    from code_sandbox import run_student_code

    result = run_student_code(
        """import matplotlib.pyplot as plt
plt.plot([1, 2, 3], [1, 4, 9])
plt.show()
print('ok')
"""
    )
    assert result.success
    assert "ok" in (result.stdout or "")
    assert len(result.images) == 1
    assert result.images[0].startswith("iVBOR")
    assert "FigureCanvasAgg" not in (result.stderr or "")


def test_sandbox_no_images_without_matplotlib_import():
    from code_sandbox import run_student_code

    result = run_student_code("print(123)")
    assert result.success
    assert result.images == []


def test_sandbox_matplotlib_figure_count_cap():
    pytest.importorskip("matplotlib")
    from code_sandbox import MAX_SANDBOX_FIGURES, run_student_code

    lines = ["import matplotlib.pyplot as plt"]
    for i in range(MAX_SANDBOX_FIGURES + 5):
        lines.append("plt.figure()")
        lines.append(f"plt.plot([0, 1], [0, {i}])")
    lines.append("print('drawn')")
    result = run_student_code("\n".join(lines))
    assert result.success
    assert len(result.images) == MAX_SANDBOX_FIGURES
    assert "Часть графиков не показана" in (result.stdout or "")


def test_sandbox_image_widgets_helper():
    pytest.importorskip("matplotlib")
    ipywidgets = pytest.importorskip("ipywidgets")
    from code_sandbox import image_widgets, run_student_code

    result = run_student_code(
        """import matplotlib.pyplot as plt
plt.plot([1, 2], [3, 4])
"""
    )
    widgets_list = image_widgets(result.images)
    assert len(widgets_list) == 1
    assert widgets_list[0].format == "png"
    assert len(image_widgets([])) == 0
    assert len(image_widgets(None)) == 0


def test_sandbox_two_show_calls_two_images():
    """plt.show() сохраняет и закрывает фигуры — два show → два PNG."""
    pytest.importorskip("matplotlib")
    from code_sandbox import run_student_code

    result = run_student_code(
        """import matplotlib.pyplot as plt
plt.plot([1, 2], [1, 2])
plt.show()
plt.plot([1, 4, 9])
plt.show()
print("done")
"""
    )
    assert result.success
    assert len(result.images) == 2
    assert all(img.startswith("iVBOR") for img in result.images)


def test_sandbox_figure_without_show_captured_at_end():
    pytest.importorskip("matplotlib")
    from code_sandbox import run_student_code

    result = run_student_code(
        """import matplotlib.pyplot as plt
plt.plot([1, 2, 3])
print("noshow")
"""
    )
    assert result.success
    assert len(result.images) == 1


def test_sandbox_no_duplicate_after_show():
    pytest.importorskip("matplotlib")
    from code_sandbox import run_student_code

    result = run_student_code(
        """import matplotlib.pyplot as plt
plt.plot([1, 2])
plt.show()
print("only_one")
"""
    )
    assert result.success
    assert len(result.images) == 1


def test_sandbox_figure_plus_exception_returns_image():
    pytest.importorskip("matplotlib")
    from code_sandbox import SandboxExecutionError, run_or_raise, run_student_code

    result = run_student_code(
        """import matplotlib.pyplot as plt
plt.plot([1, 2])
1 / 0
"""
    )
    assert not result.success
    assert result.exception_type == "ZeroDivisionError"
    assert len(result.images) == 1

    with pytest.raises(SandboxExecutionError) as ei:
        run_or_raise(
            """import matplotlib.pyplot as plt
plt.plot([1, 2])
1 / 0
"""
        )
    assert len(ei.value.images) == 1


def test_sandbox_error_paths_expose_images_to_display_helpers():
    """Сайты отображения: image_widgets на ошибке; interactive_cell_logic возвращает images."""
    pytest.importorskip("matplotlib")
    ipywidgets = pytest.importorskip("ipywidgets")
    from code_sandbox import image_widgets, run_student_code
    from interactive_cell_logic import execute_student_code

    result = run_student_code(
        """import matplotlib.pyplot as plt
plt.plot([1, 2])
1 / 0
"""
    )
    widgets_list = image_widgets(result.images)
    assert len(widgets_list) == 1
    assert widgets_list[0].format == "png"

    ns: dict = {}
    _res, output, success, images = execute_student_code(
        """import matplotlib.pyplot as plt
plt.plot([1, 2])
1 / 0
""",
        ns,
    )
    assert success is False
    assert "ZeroDivision" in output or "division" in output.lower()
    assert len(images) == 1
    assert len(image_widgets(images)) == 1


def test_stdout_html_shows_type_print_as_text():
    from code_sandbox import format_execution_stdout_html

    raw = "<class 'int'>\n<class 'float'>\n<class 'str'>\n<class 'bool'>"
    html = format_execution_stdout_html(raw)
    assert "<class " not in html
    assert "&lt;class" in html
    assert "int" in html
    assert "float" in html
    assert "str" in html
    assert "bool" in html
    assert "pre-wrap" in html


def test_control_execute_shows_type_print(monkeypatch):
    """Кнопка «Выполнить код»: <class 'int'> остаётся видимым текстом."""
    import logging
    from types import SimpleNamespace

    from code_sandbox import SandboxResult
    from control_tasks_interface import ControlTasksInterface

    ui = ControlTasksInterface.__new__(ControlTasksInterface)
    ui.logger = logging.getLogger("test_control_stdout")
    ui.lesson_interface = SimpleNamespace(current_course_info={})
    ui._solution_revealed = False
    monkeypatch.setattr(
        "code_sandbox.run_student_code",
        lambda code, capture_variables=False: SandboxResult(
            stdout="<class 'int'>\n<class 'float'>\n<class 'str'>\n<class 'bool'>\n",
            success=True,
        ),
    )
    box = ui._create_task_interface(
        {"title": "Типы", "task_code": "a = 7", "hints": []}
    )

    def buttons(node):
        found = []
        if type(node).__name__ == "Button":
            found.append(node)
        for child in getattr(node, "children", ()) or ():
            found.extend(buttons(child))
        return found

    run = next(b for b in buttons(box) if "Выполнить" in b.description)
    run.click()
    shown = box.children[-1].children[0].value
    assert "Код выполнен успешно" in shown
    assert "<class " not in shown
    assert "&lt;class" in shown
    assert "bool" in shown


def test_check_panel_shows_type_print():
    """«Ваш вывод» после проверки тоже не прячет <class '...'>."""
    import logging
    from types import SimpleNamespace

    import ipywidgets as widgets

    from control_tasks_interface import ControlTasksInterface

    ui = ControlTasksInterface.__new__(ControlTasksInterface)
    ui.logger = logging.getLogger("test_control_check_stdout")
    ui.is_checking = False
    ui._solution_revealed = False
    ui._save_task_result = lambda *_a, **_k: None
    ui._create_success_buttons = lambda: []
    ui.tasks_generator = SimpleNamespace(
        validate_task_execution=lambda *_a, **_k: {
            "is_correct": True,
            "actual_output": "<class 'int'>",
            "feedback": "",
        }
    )
    out = widgets.VBox()
    ui._check_solution("print(type(1))", {}, out)
    shown = out.children[0].value
    assert "Ваш вывод" in shown
    assert "<class " not in shown
    assert "int" in shown


def test_name_error_hint_for_student():
    from code_sandbox import (
        NAME_ERROR_HINT_RU,
        format_execution_error_html,
        name_error_student_hint,
        with_name_error_hint,
    )

    msg = "NameError: name 'my_var' is not defined"
    assert name_error_student_hint(msg) == NAME_ERROR_HINT_RU
    assert "с нуля" in with_name_error_hint(msg)
    assert name_error_student_hint("ValueError: x") == ""
    html = format_execution_error_html(msg)
    assert "#6c757d" in html
    assert "my_var" in html
    assert NAME_ERROR_HINT_RU in html
    # идемпотентность
    assert name_error_student_hint(with_name_error_hint(msg)) == ""

