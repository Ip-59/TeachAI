# Задача для Cursor: пакет 4в — правки графиков (plt.show + картинки при ошибке)

Скопируй файл целиком в чат Cursor. Исполнитель — Cursor-агент в проекте TeachAI на локальном компьютере. Работа от коммита **`2120786`** (пакет 4а+4б закрыт). Все правки ниже **проверены в прототипе** на копии `2120786` (Linux, Python 3.13, venv_box): после этапа набор даёт **`137 passed, 1 deselected`** (было `132 passed, 1 deselected`). `content_utils.py` **не менялся**.

Все номера строк — по `2120786`. Диффы сняты против него; применяй как есть. Если контекст не совпал — **остановись и напиши**, не подгоняй.

## 0. Жёсткие правила

1. Менять только то, что описано. Без «заодно»-рефакторинга сверх явно помеченной части B (неиспользуемые импорты).
2. **Не трогать** прогресс/state (D1–D8), `content_utils.py`, `data/`, `.env`, `.env.sample`, `TeachAI_test_scenarios.md`.
3. Один этап — один коммит, один пуш. После: полный `python -m pytest -q -rx`, отчёт мне; **`git push` только по моей команде**.
4. Venv текущей машины: **`venv_W_L` / `venv_H_L`**. Новых зависимостей нет.
5. Ключ не печатать. Тесты — `sk-test-not-a-real-key`.
6. Новых `xfail` без согласования не добавлять.
7. После прогона `git status` чист от `data/`, `.env`.

## 1. Что не так (ручной прогон Игоря)

1. **`plt.show()` был no-op.** Два вызова `plt.plot(...); plt.show()` рисовали обе кривые на **одной** фигуре (захват только в конце). Нужна семантика Jupyter inline: каждый `show()` сохраняет открытые фигуры в PNG и **закрывает** их; в конце прогона — оставшиеся без `show`.
2. **`plt.plot([1,2]); 1/0`** — только текст «❌ Ошибка выполнения: …», без картинки. Worker **уже** клал PNG в `images` после exception; терялось на родителе: `run_or_raise` поднимал исключение **без** `images`, а сайты КЗ/примеров в `except` рисовали только текст.

Дополнительно: импорт-хук патчил `pyplot.show` слишком рано (модуль ещё грузится) → matplotlib перезаписывал `show`. Патч нужно ставить, когда атрибут `show` уже есть, и повторять, если его снова затёрли.

## 2. Решение

| Место | Правка |
|---|---|
| Worker в `code_sandbox.py` | `_FIG_STATE` + `_capture_open_figures()`; `plt.show = _patched_show` (capture+close); в конце — оставшиеся фигуры; лимиты 10 / ~5 МБ на весь run |
| `SandboxExecutionError` | `RuntimeError` с полями `.result` / `.images`; `run_or_raise` кидает его вместо голого `RuntimeError` |
| КЗ «Запустить», examples, interactive_cell_logic, validate КЗ | `run_student_code` (не `run_or_raise`) → на ошибке тоже `image_widgets(...)` / возврат `images` |
| `cell_widget_base` | уже сохранял `_last_sandbox_images` и показывал на обоих путях — без смены логики (только чистка импортов в части B) |

## 3. Состав и приёмка

Один коммит. Ожидаемый pytest: **`137 passed, 1 deselected`** (+5 unit-тестов про show/ошибку).


## ЭТАП 4в


### A. `code_sandbox.py` — show + SandboxExecutionError

```diff
--- a/code_sandbox.py
+++ b/code_sandbox.py
@@ -91,6 +91,15 @@
         super().__init__(message)
 
 
+class SandboxExecutionError(RuntimeError):
+    """Ошибка в коде ученика; сохраняет SandboxResult (в т.ч. images)."""
+
+    def __init__(self, message: str, result: "SandboxResult") -> None:
+        super().__init__(message)
+        self.result = result
+        self.images = list(result.images or [])
+
+
 @dataclass
 class SandboxResult:
     stdout: str = ""
@@ -351,42 +360,30 @@
     return value
 
 
-def _patch_pyplot_show():
-    plt = sys.modules.get("matplotlib.pyplot")
-    if plt is None or getattr(plt, "_teachai_show_patched", False):
-        return
-    plt.show = lambda *a, **k: None
-    plt._teachai_show_patched = True
-
+# Накопитель PNG за весь прогон (лимиты на весь run).
+_FIG_STATE = {
+    "images": [],
+    "truncated": False,
+    "total_bytes": 0,
+    "max_figures": 10,
+    "max_bytes": 5 * 1024 * 1024,
+}
 
-_real_import = __import__
 
-def _teachai_import(name, globals=None, locals=None, fromlist=(), level=0):
-    mod = _real_import(name, globals, locals, fromlist, level)
-    if name == "matplotlib.pyplot" or name.startswith("matplotlib."):
-        _patch_pyplot_show()
-    elif name == "matplotlib" and fromlist:
-        _patch_pyplot_show()
-    return mod
-
-
-def capture_matplotlib_images(max_figures, max_total_bytes):
-    images = []
-    truncated = False
+def _capture_open_figures():
+    """Сохранить открытые фигуры в _FIG_STATE и закрыть их (семантика plt.show)."""
     if "matplotlib.pyplot" not in sys.modules:
-        return images, truncated
+        return
     plt = sys.modules.get("matplotlib.pyplot")
     if plt is None:
-        return images, truncated
-    _patch_pyplot_show()
-    total = 0
+        return
     try:
         fignums = list(plt.get_fignums())
     except Exception:
-        return images, truncated
-    for idx, num in enumerate(fignums):
-        if idx >= max_figures:
-            truncated = True
+        return
+    for num in fignums:
+        if len(_FIG_STATE["images"]) >= _FIG_STATE["max_figures"]:
+            _FIG_STATE["truncated"] = True
             break
         try:
             fig = plt.figure(num)
@@ -395,16 +392,44 @@
             data = buf.getvalue()
         except Exception:
             continue
-        if total + len(data) > max_total_bytes:
-            truncated = True
+        if _FIG_STATE["total_bytes"] + len(data) > _FIG_STATE["max_bytes"]:
+            _FIG_STATE["truncated"] = True
             break
-        total += len(data)
-        images.append(base64.b64encode(data).decode("ascii"))
+        _FIG_STATE["total_bytes"] += len(data)
+        _FIG_STATE["images"].append(base64.b64encode(data).decode("ascii"))
     try:
         plt.close("all")
     except Exception:
         pass
-    return images, truncated
+
+
+def _patched_show(*a, **k):
+    """Как inline-backend Jupyter: показать (=захватить PNG) и закрыть фигуры."""
+    _capture_open_figures()
+
+
+def _patch_pyplot_show():
+    """Ставить наш show; пропускать, пока pyplot ещё грузится без атрибута show."""
+    plt = sys.modules.get("matplotlib.pyplot")
+    if plt is None:
+        return
+    current = getattr(plt, "show", None)
+    if current is None:
+        return
+    if getattr(current, "__name__", None) == "_patched_show":
+        return
+    plt.show = _patched_show
+
+
+_real_import = __import__
+
+def _teachai_import(name, globals=None, locals=None, fromlist=(), level=0):
+    mod = _real_import(name, globals, locals, fromlist, level)
+    if name == "matplotlib.pyplot" or name.startswith("matplotlib."):
+        _patch_pyplot_show()
+    elif name == "matplotlib" and fromlist:
+        _patch_pyplot_show()
+    return mod
 
 
 def main():
@@ -419,6 +444,11 @@
     max_out = int(job.get("max_output_chars") or 100000)
     max_figures = int(job.get("max_figures") or 10)
     max_images_bytes = int(job.get("max_images_bytes") or (5 * 1024 * 1024))
+    _FIG_STATE["images"] = []
+    _FIG_STATE["truncated"] = False
+    _FIG_STATE["total_bytes"] = 0
+    _FIG_STATE["max_figures"] = max_figures
+    _FIG_STATE["max_bytes"] = max_images_bytes
 
     try:
         import builtins
@@ -472,13 +502,14 @@
         payload["error"] = "%s: %s" % (type(exc).__name__, exc)
         traceback.print_exc(file=stderr_buf)
 
+    # Оставшиеся фигуры (без plt.show) + после исключения; уже показанные закрыты.
     try:
-        images, truncated = capture_matplotlib_images(max_figures, max_images_bytes)
-        payload["images"] = images
-        payload["images_truncated"] = truncated
+        _capture_open_figures()
+        payload["images"] = list(_FIG_STATE["images"])
+        payload["images_truncated"] = bool(_FIG_STATE["truncated"])
     except Exception:
-        payload["images"] = []
-        payload["images_truncated"] = False
+        payload["images"] = list(_FIG_STATE.get("images") or [])
+        payload["images_truncated"] = bool(_FIG_STATE.get("truncated"))
 
     out = stdout_buf.getvalue()
     err = stderr_buf.getvalue()
@@ -688,7 +719,7 @@
         raise SandboxTimeoutError(result.error or TIMEOUT_MESSAGE)
     if not result.success:
         msg = result.error or result.stderr or "Ошибка выполнения кода"
-        raise RuntimeError(msg)
+        raise SandboxExecutionError(msg, result)
     return result
 
 

```

### B. Сайты отображения (картинки и при ошибке)

#### B1. `control_tasks_interface.py` — кнопка «Запустить»

```diff
--- a/control_tasks_interface.py
+++ b/control_tasks_interface.py
@@ -270,23 +270,35 @@
             results_output.children = []
             
             try:
-                from code_sandbox import image_widgets, run_or_raise
+                from code_sandbox import image_widgets, run_student_code
 
                 full_code = ControlTasksGenerator.resolve_executable_code(
                     task_data.get("task_code", ""), code_input.value
                 )
-                sandbox_result = run_or_raise(full_code, capture_variables=False)
+                sandbox_result = run_student_code(full_code, capture_variables=False)
                 output = sandbox_result.stdout or ""
                 imgs = image_widgets(sandbox_result.images)
 
-                if output.strip():
+                if sandbox_result.timed_out or not sandbox_result.success:
+                    msg = (
+                        sandbox_result.error
+                        or sandbox_result.stderr
+                        or "Ошибка выполнения кода"
+                    )
+                    error_html = widgets.HTML(
+                        value=f"<p style='color: red;'>❌ Ошибка выполнения: {msg}</p>"
+                    )
+                    results_output.children = [error_html, *imgs]
+                elif output.strip():
                     result_html = widgets.HTML(
                         value=f"<p style='color: green;'>✅ Код выполнен успешно!</p><pre style='background: #f8f9fa; padding: 10px; border-radius: 4px;'>{output}</pre>"
                     )
+                    results_output.children = [result_html, *imgs]
                 elif imgs:
                     result_html = widgets.HTML(
                         value="<p style='color: green;'>✅ Код выполнен успешно! График ниже.</p>"
                     )
+                    results_output.children = [result_html, *imgs]
                 else:
                     result_html = widgets.HTML(
                         value=(
@@ -295,7 +307,7 @@
                             "Для проверки задания нажмите «✓ Проверить решение».</p>"
                         )
                     )
-                results_output.children = [result_html, *imgs]
+                    results_output.children = [result_html]
 
             except Exception as e:
                 error_html = widgets.HTML(

```

#### B2. `control_tasks_generator.py` — validate + снятие неиспользуемых импортов

```diff
--- a/control_tasks_generator.py
+++ b/control_tasks_generator.py
@@ -4,12 +4,10 @@
 Создает практические задачи с эталонным кодом для проверки знаний.
 """
 
-import io
 import logging
 import json
 import os
 import re
-from contextlib import redirect_stdout
 from typing import Dict, List, Any, Optional, Tuple
 
 from content_utils import BaseContentGenerator
@@ -1079,15 +1077,22 @@
         execution_error: Optional[str] = None
 
         try:
-            from code_sandbox import run_or_raise
+            from code_sandbox import run_student_code
 
             full_code = self.resolve_executable_code(task_code, user_code)
-            sandbox = run_or_raise(
+            sandbox = run_student_code(
                 self.stabilize_sklearn_code(full_code), capture_variables=True
             )
-            student_stdout = (sandbox.stdout or "").strip()
-            local_vars = sandbox.variables
             student_images = list(sandbox.images or [])
+            if sandbox.timed_out or not sandbox.success:
+                execution_error = (
+                    sandbox.error or sandbox.stderr or "Ошибка выполнения кода"
+                )
+                student_stdout = (sandbox.stdout or "").strip()
+                local_vars = sandbox.variables or {}
+            else:
+                student_stdout = (sandbox.stdout or "").strip()
+                local_vars = sandbox.variables
         except Exception as exc:
             execution_error = str(exc)
             student_stdout = ""

```

#### B3. `examples_display.py`

```diff
--- a/examples_display.py
+++ b/examples_display.py
@@ -8,9 +8,7 @@
 from __future__ import annotations
 
 import html
-import io
 import time
-from contextlib import redirect_stdout
 from typing import Any, Dict, List
 
 import ipywidgets as widgets
@@ -46,18 +44,29 @@
             return
         busy_until["t"] = now + 1.0
         try:
-            from code_sandbox import image_widgets, run_or_raise
+            from code_sandbox import image_widgets, run_student_code
 
-            sandbox = run_or_raise(code_area.value, capture_variables=False)
-            text = sandbox.stdout or ""
-            body = text if text.strip() else "Код выполнен успешно."
-            html_w = widgets.HTML(
-                value=(
-                    "<pre style='white-space:pre-wrap;margin:8px 0;'>"
-                    f"{html.escape(body)}</pre>"
+            sandbox = run_student_code(code_area.value, capture_variables=False)
+            imgs = image_widgets(sandbox.images)
+            if sandbox.timed_out or not sandbox.success:
+                msg = sandbox.error or sandbox.stderr or "Ошибка выполнения кода"
+                html_w = widgets.HTML(
+                    value=(
+                        "<pre style='white-space:pre-wrap;margin:8px 0;color:#721c24;'>"
+                        f"{html.escape(msg)}</pre>"
+                    )
                 )
-            )
-            result_box.children = (html_w, *image_widgets(sandbox.images))
+                result_box.children = (html_w, *imgs)
+            else:
+                text = sandbox.stdout or ""
+                body = text if text.strip() else "Код выполнен успешно."
+                html_w = widgets.HTML(
+                    value=(
+                        "<pre style='white-space:pre-wrap;margin:8px 0;'>"
+                        f"{html.escape(body)}</pre>"
+                    )
+                )
+                result_box.children = (html_w, *imgs)
         except Exception as exc:
             result_box.children = (
                 widgets.HTML(

```

#### B4. `interactive_cell_logic.py`

```diff
--- a/interactive_cell_logic.py
+++ b/interactive_cell_logic.py
@@ -23,16 +23,22 @@
         Кортеж (результат, вывод, успех_выполнения, images_base64)
     """
     try:
-        from code_sandbox import run_or_raise
+        from code_sandbox import run_student_code
 
         # В дочерний процесс передаём только JSON-сериализуемые значения.
-        sandbox = run_or_raise(
+        sandbox = run_student_code(
             student_code,
             initial_vars=execution_namespace,
             capture_variables=True,
         )
-        execution_namespace.clear()
-        execution_namespace.update(sandbox.variables)
+        images = list(sandbox.images or [])
+        if sandbox.variables:
+            execution_namespace.clear()
+            execution_namespace.update(sandbox.variables)
+
+        if sandbox.timed_out or not sandbox.success:
+            msg = sandbox.error or sandbox.stderr or "Ошибка выполнения кода"
+            return None, msg, False, images
 
         result = None
         result_vars = [
@@ -50,7 +56,7 @@
                 result = execution_namespace[var_name]
                 break
 
-        return result, sandbox.stdout or "", True, list(sandbox.images or [])
+        return result, sandbox.stdout or "", True, images
 
     except Exception as e:
         return None, str(e), False, []

```

#### B5. `examples_validation.py` — только unused imports

```diff
--- a/examples_validation.py
+++ b/examples_validation.py
@@ -6,9 +6,7 @@
 """
 
 import ast
-import io
 import logging
-from contextlib import redirect_stdout
 from typing import Dict, List
 
 from content_utils import BaseContentGenerator

```

#### B6. `cell_widget_base.py` — только unused imports (`io`/`sys`/`redirect_*`; логика display уже ок)

```diff
--- a/cell_widget_base.py
+++ b/cell_widget_base.py
@@ -5,10 +5,6 @@
 
 import ipywidgets as widgets
 from IPython.display import display, clear_output
-import sys
-import io
-import traceback
-from contextlib import redirect_stdout, redirect_stderr
 from typing import Any, Optional, Dict, Tuple
 
 

```

### C. Тесты

```diff
--- a/tests/unit/test_code_sandbox.py
+++ b/tests/unit/test_code_sandbox.py
@@ -161,3 +161,106 @@
     assert widgets_list[0].format == "png"
     assert len(image_widgets([])) == 0
     assert len(image_widgets(None)) == 0
+
+def test_sandbox_two_show_calls_two_images():
+    """plt.show() сохраняет и закрывает фигуры — два show → два PNG."""
+    pytest.importorskip("matplotlib")
+    from code_sandbox import run_student_code
+
+    result = run_student_code(
+        """import matplotlib.pyplot as plt
+plt.plot([1, 2], [1, 2])
+plt.show()
+plt.plot([1, 4, 9])
+plt.show()
+print("done")
+"""
+    )
+    assert result.success
+    assert len(result.images) == 2
+    assert all(img.startswith("iVBOR") for img in result.images)
+
+
+def test_sandbox_figure_without_show_captured_at_end():
+    pytest.importorskip("matplotlib")
+    from code_sandbox import run_student_code
+
+    result = run_student_code(
+        """import matplotlib.pyplot as plt
+plt.plot([1, 2, 3])
+print("noshow")
+"""
+    )
+    assert result.success
+    assert len(result.images) == 1
+
+
+def test_sandbox_no_duplicate_after_show():
+    pytest.importorskip("matplotlib")
+    from code_sandbox import run_student_code
+
+    result = run_student_code(
+        """import matplotlib.pyplot as plt
+plt.plot([1, 2])
+plt.show()
+print("only_one")
+"""
+    )
+    assert result.success
+    assert len(result.images) == 1
+
+
+def test_sandbox_figure_plus_exception_returns_image():
+    pytest.importorskip("matplotlib")
+    from code_sandbox import SandboxExecutionError, run_or_raise, run_student_code
+
+    result = run_student_code(
+        """import matplotlib.pyplot as plt
+plt.plot([1, 2])
+1 / 0
+"""
+    )
+    assert not result.success
+    assert result.exception_type == "ZeroDivisionError"
+    assert len(result.images) == 1
+
+    with pytest.raises(SandboxExecutionError) as ei:
+        run_or_raise(
+            """import matplotlib.pyplot as plt
+plt.plot([1, 2])
+1 / 0
+"""
+        )
+    assert len(ei.value.images) == 1
+
+
+def test_sandbox_error_paths_expose_images_to_display_helpers():
+    """Сайты отображения: image_widgets на ошибке; interactive_cell_logic возвращает images."""
+    pytest.importorskip("matplotlib")
+    ipywidgets = pytest.importorskip("ipywidgets")
+    from code_sandbox import image_widgets, run_student_code
+    from interactive_cell_logic import execute_student_code
+
+    result = run_student_code(
+        """import matplotlib.pyplot as plt
+plt.plot([1, 2])
+1 / 0
+"""
+    )
+    widgets_list = image_widgets(result.images)
+    assert len(widgets_list) == 1
+    assert widgets_list[0].format == "png"
+
+    ns: dict = {}
+    _res, output, success, images = execute_student_code(
+        """import matplotlib.pyplot as plt
+plt.plot([1, 2])
+1 / 0
+""",
+        ns,
+    )
+    assert success is False
+    assert "ZeroDivision" in output or "division" in output.lower()
+    assert len(images) == 1
+    assert len(image_widgets(images)) == 1
+

```

### Приёмка 4в

`python -m pytest -q -rx` → **`137 passed, 1 deselected`**.
Покажи хвост pytest, `git status`, `git diff --stat`. Пуш — только по моей команде.


## 4. Ручной re-check для Игоря (тот же ноутбук, HEAD после 4в)

1. Ячейка как раньше:
   ```python
   import numpy as np
   import matplotlib.pyplot as plt
   x = np.linspace(0, 2*np.pi, 200)
   plt.plot(x, np.cos(x)); plt.title("cos"); plt.show()
   plt.plot([1, 4, 9]); plt.title("pts"); plt.show()
   ```
   Ожидание: **два** отдельных PNG под выводом.
2. `plt.plot([1, 2]); 1/0` → «Запустить»: красный текст ошибки **и** PNG под ним.
3. Без `show`: `plt.plot([1,2,3])` → один PNG в конце.
4. Быстрый «Проверить» на заведомо неверном коде с графиком — картинка в блоке результата, если код успел нарисовать до падения/неверного ответа.

# Что сообщить мне в конце

1. Хвост `pytest -q -rx` vs **137 passed, 1 deselected**.
2. `git status` / `git diff --stat`; `data/`, `.env`, `content_utils.py` не тронуты.
3. Места, где дифф не лёг.
