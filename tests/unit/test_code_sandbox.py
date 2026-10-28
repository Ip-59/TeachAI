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
