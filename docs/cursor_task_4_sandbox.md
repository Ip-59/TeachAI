# Задача для Cursor: пакет 4 — D9 песочница (выполнение кода ученика)

Скопируй файл целиком в чат Cursor. Исполнитель — Cursor-агент в проекте TeachAI на локальном компьютере. Работа от коммита **`3697da1`** (пакет 3 закрыт). Все правки ниже **проверены в прототипе** на копии `3697da1` (Linux, Python 3.13, venv_box): после **4а** — `126 passed, 1 deselected`; после **4б** — **`132 passed, 1 deselected`** (0 skipped, 0 xfailed). `content_utils.py` **не менялся**.

Все номера строк — по `3697da1` (для 4а) или по состоянию после 4а (для 4б). Диффы проверены; применяй как есть. Если контекст не совпал — **остановись и напиши**, не подгоняй.

## 0. Жёсткие правила

1. Менять только то, что описано. Без «заодно»-рефакторинга и форматирования.
2. **Не трогать** прогресс/state (D1–D8), `content_utils.py`, `data/`, `.env`, `.env.sample`, `TeachAI_test_scenarios.md`.
3. Два этапа — два коммита, два пуша. После каждого: полный `python -m pytest -q -rx`, отчёт мне; **`git push` только по моей команде**.
4. Venv текущей машины: **`venv_W_L` / `venv_H_L`**. Новых зависимостей нет. `matplotlib` и `seaborn` уже в `requirements.txt` (≥3.10.3 / ≥0.13.2). Тесты графиков используют `pytest.importorskip("matplotlib")`.
5. Ключ не печатать. Тесты — `sk-test-not-a-real-key`.
6. Когда баг исправлен, снять `xfail`/`skip`. Новых `xfail` без согласования не добавлять.
7. После прогона `git status` чист от `data/`, `.env`.

## 1. Решение D9 (итог)

Общий модуль **`code_sandbox.py`**. Код ученика/примера выполняется в **дочернем процессе** того же `sys.executable`:

| Параметр | Значение |
|---|---|
| Вход | только текст кода (+ опционально JSON-сериализуемые `initial_vars`) |
| Выход | stdout, stderr, переменные (JSON); несериализуемое → `repr` с флагом; **в 4б — ещё `images` (base64 PNG)** |
| Таймаут | **10 с** по умолчанию; **60 с**, если AST видит тяжёлый импорт (`tensorflow`/`torch`/`jax`/`keras`/`transformers`/…) |
| При таймауте | kill **группы** процессов (Linux: `start_new_session` + `killpg`; Windows: `CREATE_NEW_PROCESS_GROUP` + `kill`), сообщение **`Код выполнялся слишком долго, возможно, бесконечный цикл`**, TeachAI продолжает работать |
| cwd | временная папка, удаляется после |
| env | **allowlist** + всегда `MPLBACKEND=Agg` (с 4б); без секретов/proxy |
| stdin | `DEVNULL` → `input()` даёт `EOFError` |
| Вывод | обрезка по 100 000 символов |
| Переменные между запусками ячейки | только JSON-сериализуемые; ячейка самодостаточна; **без** долгоживущего worker и **без** pickle |

**KZ-27.** В venv_box: `sklearn≈0.8 с`, `tensorflow≈3–10 с`. Pre-warm **не** делаем — 60 с для heavy.

**Накладные** пустого прогона: **≈20–25 мс**.

**Графики (этап 4б, вариант «а»).** В ребёнке `MPLBACKEND=Agg`. После exec (и после исключения; **не** после kill по таймауту): если `matplotlib.pyplot` уже в `sys.modules` (сами не импортируем), сохранить открытые фигуры в PNG (`savefig`, `bbox_inches='tight'`, `dpi=100`) → base64; лимит **10 фигур** и **~5 МБ** суммарно, иначе пометка в stdout; `plt.close('all')`. `plt.show()` — harmless no-op; warning Agg подавлен. Родитель показывает через `ipywidgets.Image` / `IPython.display.Image`. **Seaborn** работает через matplotlib. **Plotly / интерактивные backend’ы — вне объёма**: в ноутбуке не отобразятся.

**ZAP-08.** Мёртвый `demo_cell_widget` убран; `CELLS_AVAILABLE=False` как раньше.

## 2. Состав этапов

| Этап | Что | Ожидаемый pytest |
|---|---|---|
| **4а** | `code_sandbox.py` + КЗ (`generator`/`interface`) + SEC/KZ-16 + 7 unit-тестов sandbox | **`126 passed, 1 deselected`** |
| **4б** | остальные exec/eval + ZAP-08 + **перехват matplotlib** + показ картинок + 6 доп. тестов | **`132 passed, 1 deselected`** |

База `3697da1`: `116 passed, 1 skipped (KZ-16), 1 deselected, 2 xfailed (SEC-01, SEC-02)`.


## ЭТАП 4а. Ядро песочницы + контрольные задания


### A. Новый файл `code_sandbox.py`

Создать в корне проекта рядом с `control_tasks_generator.py`. Полный файл (без графиков — они в 4б):

```python
"""Изолированное выполнение кода ученика в дочернем процессе (D9).

В родительский процесс возвращаются только stdout/stderr и JSON-сериализуемые
значения переменных. Секреты из окружения не передаются (allowlist).
"""
from __future__ import annotations

import ast
import json
import os
import signal
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

DEFAULT_TIMEOUT_SEC = 10
HEAVY_TIMEOUT_SEC = 60
MAX_OUTPUT_CHARS = 100_000
TIMEOUT_MESSAGE = "Код выполнялся слишком долго, возможно, бесконечный цикл"

HEAVY_IMPORT_ROOTS = frozenset(
    {
        "tensorflow",
        "torch",
        "jax",
        "jaxlib",
        "keras",
        "transformers",
        "tensorboard",
    }
)

# Allowlist окружения дочернего процесса (не denylist).
_ENV_ALLOW_EXACT = frozenset(
    {
        "PATH",
        "HOME",
        "USER",
        "LOGNAME",
        "LANG",
        "LANGUAGE",
        "LC_ALL",
        "LC_CTYPE",
        "LC_MESSAGES",
        "LC_NUMERIC",
        "LC_TIME",
        "TZ",
        "TMPDIR",
        "TEMP",
        "TMP",
        "PYTHONIOENCODING",
        "PYTHONUTF8",
        "PYTHONHASHSEED",
        "SYSTEMROOT",
        "SYSTEMDRIVE",
        "WINDIR",
        "COMSPEC",
        "PATHEXT",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "PROGRAMDATA",
        "PROGRAMFILES",
        "NUMBER_OF_PROCESSORS",
        "OS",
        "COMPUTERNAME",
        "USERNAME",
        "HOMEDRIVE",
        "HOMEPATH",
    }
)
_ENV_ALLOW_PREFIXES: Tuple[str, ...] = (
    "PROCESSOR_",
    "LC_",
)


class SandboxTimeoutError(TimeoutError):
    """Таймаут выполнения кода ученика."""

    def __init__(self, message: str = TIMEOUT_MESSAGE) -> None:
        super().__init__(message)


@dataclass
class SandboxResult:
    stdout: str = ""
    stderr: str = ""
    variables: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = False
    timed_out: bool = False
    error: Optional[str] = None
    exception_type: Optional[str] = None


def choose_timeout(code: str, override: Optional[int] = None) -> int:
    """10 с по умолчанию; 60 с, если AST видит тяжёлый импорт (KZ-27)."""
    if override is not None:
        return max(1, int(override))
    if _code_has_heavy_import(code):
        return HEAVY_TIMEOUT_SEC
    return DEFAULT_TIMEOUT_SEC


def _code_has_heavy_import(code: str) -> bool:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = (alias.name or "").split(".", 1)[0]
                if root in HEAVY_IMPORT_ROOTS:
                    return True
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            root = mod.split(".", 1)[0]
            if root in HEAVY_IMPORT_ROOTS:
                return True
    return False


def build_child_env(base: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
    """Окружение ребёнка: только allowlist + явные безопасные значения."""
    src = dict(base) if base is not None else os.environ
    env: Dict[str, str] = {}
    for key, value in src.items():
        if key in _ENV_ALLOW_EXACT or key.startswith(_ENV_ALLOW_PREFIXES):
            env[key] = value
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # Не протаскиваем PYTHONPATH/VIRTUAL_ENV — ребёнок стартует тем же
    # sys.executable, site-packages подтянутся сами.
    return env


def _encode_value(value: Any, depth: int = 0) -> Any:
    """В JSON; несериализуемое → {"__type__":"repr",...}."""
    if depth > 8:
        return {"__type__": "repr", "repr": "<max depth>"}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, complex):
        return {"__type__": "complex", "real": value.real, "imag": value.imag}
    try:
        import numpy as np

        if isinstance(value, np.ndarray):
            return {
                "__type__": "ndarray",
                "dtype": str(value.dtype),
                "shape": list(value.shape),
                "data": value.tolist(),
            }
        if isinstance(value, np.generic):
            return value.item()
    except Exception:
        pass
    if isinstance(value, (list, tuple)):
        return [_encode_value(v, depth + 1) for v in value]
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            out[str(k)] = _encode_value(v, depth + 1)
        return out
    if _looks_like_sklearn(value):
        snap: Dict[str, Any] = {
            "__type__": "object",
            "class": type(value).__name__,
            "__has_predict__": hasattr(value, "predict"),
        }
        for attr in (
            "n_features_in_",
            "n_clusters",
            "n_classes_",
            "classes_",
            "n_iter_",
            "labels_",
            "coef_",
            "intercept_",
            "cluster_centers_",
            "feature_importances_",
        ):
            if hasattr(value, attr):
                try:
                    snap[attr] = _encode_value(getattr(value, attr), depth + 1)
                except Exception:
                    pass
        return snap
    try:
        text = repr(value)
    except Exception:
        text = f"<unreprable {type(value).__name__}>"
    if len(text) > 2000:
        text = text[:2000] + "..."
    return {"__type__": "repr", "repr": text, "class": type(value).__name__}


def _looks_like_sklearn(value: Any) -> bool:
    return hasattr(value, "fit") or hasattr(value, "predict") or hasattr(value, "transform")


def _decode_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_decode_value(v) for v in value]
    if not isinstance(value, dict) or "__type__" not in value:
        if isinstance(value, dict):
            return {k: _decode_value(v) for k, v in value.items()}
        return value
    kind = value.get("__type__")
    if kind == "ndarray":
        try:
            import numpy as np

            return np.array(value.get("data"), dtype=value.get("dtype", None))
        except Exception:
            return value.get("data")
    if kind == "complex":
        return complex(value.get("real", 0.0), value.get("imag", 0.0))
    if kind == "object":
        data = {
            k: _decode_value(v)
            for k, v in value.items()
            if k not in {"__type__", "class", "__has_predict__"}
        }
        ns = SimpleNamespace(**data)
        if value.get("__has_predict__"):
            # values_equal ищет hasattr(..., "predict")
            ns.predict = lambda *a, **k: None  # noqa: E731
        return ns
    if kind == "repr":
        # Флаг несериализуемого: оставляем строку-repr как значение.
        return value.get("repr", "")
    return value


def _truncate(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[truncated {len(text) - limit} chars]"


_WORKER_CODE = r'''
import json
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
import io

def encode_value(value, depth=0):
    if depth > 8:
        return {"__type__": "repr", "repr": "<max depth>"}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, complex):
        return {"__type__": "complex", "real": value.real, "imag": value.imag}
    try:
        import numpy as np
        if isinstance(value, np.ndarray):
            return {"__type__": "ndarray", "dtype": str(value.dtype),
                    "shape": list(value.shape), "data": value.tolist()}
        if isinstance(value, np.generic):
            return value.item()
    except Exception:
        pass
    if isinstance(value, (list, tuple)):
        return [encode_value(v, depth + 1) for v in value]
    if isinstance(value, dict):
        return {str(k): encode_value(v, depth + 1) for k, v in value.items()}
    if hasattr(value, "fit") or hasattr(value, "predict") or hasattr(value, "transform"):
        snap = {"__type__": "object", "class": type(value).__name__,
                "__has_predict__": hasattr(value, "predict")}
        for attr in ("n_features_in_", "n_clusters", "n_classes_", "classes_",
                     "n_iter_", "labels_", "coef_", "intercept_",
                     "cluster_centers_", "feature_importances_"):
            if hasattr(value, attr):
                try:
                    snap[attr] = encode_value(getattr(value, attr), depth + 1)
                except Exception:
                    pass
        return snap
    try:
        text = repr(value)
    except Exception:
        text = "<unreprable %s>" % type(value).__name__
    if len(text) > 2000:
        text = text[:2000] + "..."
    return {"__type__": "repr", "repr": text, "class": type(value).__name__}


def decode_value(value):
    if isinstance(value, list):
        return [decode_value(v) for v in value]
    if not isinstance(value, dict) or "__type__" not in value:
        if isinstance(value, dict):
            return {k: decode_value(v) for k, v in value.items()}
        return value
    kind = value.get("__type__")
    if kind == "ndarray":
        try:
            import numpy as np
            return np.array(value.get("data"), dtype=value.get("dtype", None))
        except Exception:
            return value.get("data")
    if kind == "complex":
        return complex(value.get("real", 0.0), value.get("imag", 0.0))
    if kind == "object":
        class _Snap:
            pass
        obj = _Snap()
        for k, v in value.items():
            if k in ("__type__", "class", "__has_predict__"):
                continue
            setattr(obj, k, decode_value(v))
        if value.get("__has_predict__"):
            obj.predict = lambda *a, **k: None
        return obj
    if kind == "repr":
        return value.get("repr", "")
    return value

def main():
    job_path = sys.argv[1]

    result_path = sys.argv[2]
    with open(job_path, "r", encoding="utf-8") as f:
        job = json.load(f)
    code = job.get("code") or ""
    initial_vars = job.get("initial_vars") or {}
    capture_variables = bool(job.get("capture_variables", True))
    eval_last = bool(job.get("eval_last_expression", False))
    max_out = int(job.get("max_output_chars") or 100000)

    local_vars = {}
    for k, v in initial_vars.items():
        local_vars[k] = decode_value(v)

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    payload = {
        "stdout": "",
        "stderr": "",
        "variables": {},
        "result": None,
        "success": False,
        "error": None,
        "exception_type": None,
    }
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(compile(code, "<student>", "exec"), local_vars, local_vars)
            if eval_last:
                lines = [ln.strip() for ln in code.strip().split("\n") if ln.strip()]
                if lines:
                    last = lines[-1]
                    if (
                        last
                        and not last.startswith(
                            ("print", "import", "from", "def", "class",
                             "if", "for", "while", "try", "with", "#")
                        )
                        and "=" not in last
                        and not last.endswith(":")
                        and "+=" not in last and "-=" not in last
                        and "*=" not in last and "append(" not in last
                    ):
                        try:
                            payload["result"] = encode_value(eval(last, local_vars, local_vars))
                        except Exception:
                            pass
        payload["success"] = True
    except BaseException as exc:
        payload["success"] = False
        payload["exception_type"] = type(exc).__name__
        payload["error"] = "%s: %s" % (type(exc).__name__, exc)
        traceback.print_exc(file=stderr_buf)

    out = stdout_buf.getvalue()
    err = stderr_buf.getvalue()
    if len(out) > max_out:
        out = out[:max_out] + "\n...[truncated %d chars]" % (len(out) - max_out)
    if len(err) > max_out:
        err = err[:max_out] + "\n...[truncated %d chars]" % (len(err) - max_out)
    payload["stdout"] = out
    payload["stderr"] = err

    if capture_variables and payload["success"]:
        variables = {}
        for name, value in local_vars.items():
            if name.startswith("_"):
                continue
            if name in ("__builtins__",):
                continue
            # пропускаем модули и callables (кроме простых данных)
            if isinstance(value, type(sys)):
                continue
            if callable(value) and not (
                hasattr(value, "fit") or hasattr(value, "predict")
                or hasattr(value, "transform")
            ):
                continue
            try:
                variables[name] = encode_value(value)
            except Exception:
                variables[name] = {"__type__": "repr", "repr": "<encode failed>",
                                   "class": type(value).__name__}
        payload["variables"] = variables

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
'''


def _kill_process_tree(proc: subprocess.Popen) -> None:
    """Убить процесс и группу. На Windows — terminate/kill без killpg."""
    if proc.poll() is not None:
        return
    try:
        if sys.platform == "win32":
            proc.kill()
        else:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                try:
                    proc.kill()
                except Exception:
                    pass
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def run_student_code(
    code: str,
    *,
    timeout: Optional[int] = None,
    initial_vars: Optional[Mapping[str, Any]] = None,
    capture_variables: bool = True,
    eval_last_expression: bool = False,
    env: Optional[Mapping[str, str]] = None,
) -> SandboxResult:
    """Запустить `code` в дочернем Python-процессе.

    stdin закрыт; cwd — временная папка (удаляется после); env — allowlist.
    """
    timeout_sec = choose_timeout(code, timeout)
    encoded_initial: Dict[str, Any] = {}
    if initial_vars:
        for key, value in initial_vars.items():
            if key.startswith("_"):
                continue
            try:
                json.dumps(_encode_value(value))
                encoded_initial[key] = _encode_value(value)
            except Exception:
                continue

    tmp_dir = tempfile.mkdtemp(prefix="teachai_sandbox_")
    job_path = os.path.join(tmp_dir, "job.json")
    result_path = os.path.join(tmp_dir, "result.json")
    worker_path = os.path.join(tmp_dir, "_teachai_worker.py")

    job = {
        "code": code,
        "initial_vars": encoded_initial,
        "capture_variables": capture_variables,
        "eval_last_expression": eval_last_expression,
        "max_output_chars": MAX_OUTPUT_CHARS,
    }
    try:
        with open(job_path, "w", encoding="utf-8") as f:
            json.dump(job, f, ensure_ascii=False)
        with open(worker_path, "w", encoding="utf-8") as f:
            f.write(_WORKER_CODE)

        child_env = build_child_env(env)
        popen_kwargs: Dict[str, Any] = {
            "cwd": tmp_dir,
            "env": child_env,
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
        }
        if sys.platform == "win32":
            # Новая группа процессов; timeout через subprocess, не signal.
            popen_kwargs["creationflags"] = getattr(
                subprocess, "CREATE_NEW_PROCESS_GROUP", 0
            )
        else:
            popen_kwargs["start_new_session"] = True

        proc = subprocess.Popen(
            [sys.executable, worker_path, job_path, result_path],
            **popen_kwargs,
        )
        try:
            proc.communicate(timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            _kill_process_tree(proc)
            try:
                proc.communicate(timeout=2)
            except Exception:
                pass
            return SandboxResult(
                success=False,
                timed_out=True,
                error=TIMEOUT_MESSAGE,
                exception_type="SandboxTimeoutError",
            )

        if not os.path.exists(result_path):
            err = ""
            if proc.stderr:
                try:
                    err = proc.stderr.read().decode("utf-8", errors="replace")  # type: ignore[union-attr]
                except Exception:
                    err = ""
            return SandboxResult(
                success=False,
                error=err or f"sandbox worker failed (exit {proc.returncode})",
                exception_type="SandboxWorkerError",
            )

        with open(result_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        variables = {
            k: _decode_value(v) for k, v in (payload.get("variables") or {}).items()
        }
        result_val = _decode_value(payload.get("result"))
        return SandboxResult(
            stdout=_truncate(payload.get("stdout") or ""),
            stderr=_truncate(payload.get("stderr") or ""),
            variables=variables,
            result=result_val,
            success=bool(payload.get("success")),
            timed_out=False,
            error=payload.get("error"),
            exception_type=payload.get("exception_type"),
        )
    finally:
        # Всегда убираем временный cwd.
        try:
            import shutil

            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass


def run_or_raise(
    code: str,
    *,
    timeout: Optional[int] = None,
    initial_vars: Optional[Mapping[str, Any]] = None,
    capture_variables: bool = True,
    eval_last_expression: bool = False,
) -> SandboxResult:
    """Как run_student_code, но таймаут и ошибки студента — исключениями."""
    result = run_student_code(
        code,
        timeout=timeout,
        initial_vars=initial_vars,
        capture_variables=capture_variables,
        eval_last_expression=eval_last_expression,
    )
    if result.timed_out:
        raise SandboxTimeoutError(result.error or TIMEOUT_MESSAGE)
    if not result.success:
        msg = result.error or result.stderr or "Ошибка выполнения кода"
        raise RuntimeError(msg)
    return result

```

### B. `control_tasks_generator.py` — `execute_code` через sandbox

```diff
--- a/control_tasks_generator.py
+++ b/control_tasks_generator.py
@@ -58,11 +58,11 @@
 
     @staticmethod
     def execute_code(code: str) -> Tuple[str, Dict[str, Any]]:
-        output_buffer = io.StringIO()
-        local_vars: Dict[str, Any] = {}
-        with redirect_stdout(output_buffer):
-            exec(code, {}, local_vars)
-        return output_buffer.getvalue().strip(), local_vars
+        """Выполняет код ученика в дочернем процессе (D9 / code_sandbox)."""
+        from code_sandbox import run_or_raise
+
+        result = run_or_raise(code, capture_variables=True)
+        return (result.stdout or "").strip(), result.variables
 
     @classmethod
     def _inject_random_state(cls, func_name: str, args: str) -> str:

```

### C. `control_tasks_interface.py` — кнопка «Запустить»

```diff
--- a/control_tasks_interface.py
+++ b/control_tasks_interface.py
@@ -270,24 +270,13 @@
             results_output.children = []
             
             try:
-                # Создаем пространство имен для выполнения
-                namespace = {}
-                
-                # Создаем буферы для захвата вывода
-                import io
-                import sys
-                from contextlib import redirect_stdout
-                
-                output_buffer = io.StringIO()
+                from code_sandbox import run_or_raise
+
                 full_code = ControlTasksGenerator.resolve_executable_code(
                     task_data.get("task_code", ""), code_input.value
                 )
-
-                with redirect_stdout(output_buffer):
-                    exec(full_code, namespace)
-                
-                # Получаем результат
-                output = output_buffer.getvalue()
+                sandbox_result = run_or_raise(full_code, capture_variables=False)
+                output = sandbox_result.stdout or ""
                 
                 # Создаем виджет для отображения результата
                 if output.strip():

```

### D. Тесты этапа 4а

1. Снять `xfail` с SEC-01/SEC-02, снять `skip` с KZ-16 и добавить проверку сообщения:

```diff
--- a/tests/unit/test_misc_bugs.py
+++ b/tests/unit/test_misc_bugs.py
@@ -65,7 +65,6 @@
             del os.TEACHAI_EVAL_PROBE
 
 
-@pytest.mark.xfail(strict=True, raises=AssertionError, reason="SEC-02: код ученика читает OPENAI_API_KEY (control_tasks_generator.py:64, exec в процессе ядра)")
 def test_SEC_02_student_code_cannot_read_api_key():
     from control_tasks_generator import ControlTasksGenerator
 
@@ -73,7 +72,6 @@
     assert "sk-test" not in out
 
 
-@pytest.mark.xfail(strict=True, raises=AssertionError, reason="SEC-01: код ученика пишет в файлы текущей папки (control_tasks_generator.py:64)")
 def test_SEC_01_student_code_cannot_touch_project_files(isolated_project):
     from control_tasks_generator import ControlTasksGenerator
 
@@ -82,8 +80,9 @@
     assert not marker.exists()
 
 
-@pytest.mark.skip(reason="KZ-16: `while True` повесит тест, пока нет таймаута (пакет 4, D9). После D9 снять skip и ожидать сообщение «Код выполнялся слишком долго…»")
 def test_KZ_16_infinite_loop_is_stopped():
     from control_tasks_generator import ControlTasksGenerator
 
-    ControlTasksGenerator.execute_code("while True:\n    pass")
+    with pytest.raises(Exception) as ei:
+        ControlTasksGenerator.execute_code("while True:\n    pass")
+    assert "Код выполнялся слишком долго" in str(ei.value)

```

2. Новый файл `tests/unit/test_code_sandbox.py` (7 тестов; путь examples и matplotlib — в 4б):

```python
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




def test_sandbox_stdin_closed():
    from code_sandbox import run_student_code

    result = run_student_code("input('> ')")
    assert not result.success
    assert result.exception_type == "EOFError"

```

### Приёмка 4а

`python -m pytest -q -rx` → **`126 passed, 1 deselected`** (0 skipped, 0 xfailed).
Покажи хвост pytest, `git status`, `git diff --stat`. Пуш — только по моей команде.


## ЭТАП 4б. Остальные сайты + ZAP-08 + графики matplotlib


### E. Заменить `code_sandbox.py` целиком

Файл после 4а заменить на версию с `images`, `MPLBACKEND=Agg`, захватом PNG, `image_widgets` / `display_images`:

```python
"""Изолированное выполнение кода ученика в дочернем процессе (D9).

В родительский процесс возвращаются только stdout/stderr и JSON-сериализуемые
значения переменных. Секреты из окружения не передаются (allowlist).
"""
from __future__ import annotations

import ast
import json
import os
import signal
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

DEFAULT_TIMEOUT_SEC = 10
HEAVY_TIMEOUT_SEC = 60
MAX_OUTPUT_CHARS = 100_000
MAX_SANDBOX_FIGURES = 10
MAX_SANDBOX_IMAGES_BYTES = 5 * 1024 * 1024  # ~5 МБ суммарно
TIMEOUT_MESSAGE = "Код выполнялся слишком долго, возможно, бесконечный цикл"
IMAGES_TRUNCATED_NOTE = (
    "Часть графиков не показана: слишком много фигур или превышен лимит размера."
)

HEAVY_IMPORT_ROOTS = frozenset(
    {
        "tensorflow",
        "torch",
        "jax",
        "jaxlib",
        "keras",
        "transformers",
        "tensorboard",
    }
)

# Allowlist окружения дочернего процесса (не denylist).
_ENV_ALLOW_EXACT = frozenset(
    {
        "PATH",
        "HOME",
        "USER",
        "LOGNAME",
        "LANG",
        "LANGUAGE",
        "LC_ALL",
        "LC_CTYPE",
        "LC_MESSAGES",
        "LC_NUMERIC",
        "LC_TIME",
        "TZ",
        "TMPDIR",
        "TEMP",
        "TMP",
        "PYTHONIOENCODING",
        "PYTHONUTF8",
        "PYTHONHASHSEED",
        "SYSTEMROOT",
        "SYSTEMDRIVE",
        "WINDIR",
        "COMSPEC",
        "PATHEXT",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "PROGRAMDATA",
        "PROGRAMFILES",
        "NUMBER_OF_PROCESSORS",
        "OS",
        "COMPUTERNAME",
        "USERNAME",
        "HOMEDRIVE",
        "HOMEPATH",
    }
)
_ENV_ALLOW_PREFIXES: Tuple[str, ...] = (
    "PROCESSOR_",
    "LC_",
)


class SandboxTimeoutError(TimeoutError):
    """Таймаут выполнения кода ученика."""

    def __init__(self, message: str = TIMEOUT_MESSAGE) -> None:
        super().__init__(message)


@dataclass
class SandboxResult:
    stdout: str = ""
    stderr: str = ""
    variables: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    images: list = field(default_factory=list)  # base64 PNG
    success: bool = False
    timed_out: bool = False
    error: Optional[str] = None
    exception_type: Optional[str] = None


def choose_timeout(code: str, override: Optional[int] = None) -> int:
    """10 с по умолчанию; 60 с, если AST видит тяжёлый импорт (KZ-27)."""
    if override is not None:
        return max(1, int(override))
    if _code_has_heavy_import(code):
        return HEAVY_TIMEOUT_SEC
    return DEFAULT_TIMEOUT_SEC


def _code_has_heavy_import(code: str) -> bool:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = (alias.name or "").split(".", 1)[0]
                if root in HEAVY_IMPORT_ROOTS:
                    return True
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            root = mod.split(".", 1)[0]
            if root in HEAVY_IMPORT_ROOTS:
                return True
    return False


def build_child_env(base: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
    """Окружение ребёнка: только allowlist + явные безопасные значения."""
    src = dict(base) if base is not None else os.environ
    env: Dict[str, str] = {}
    for key, value in src.items():
        if key in _ENV_ALLOW_EXACT or key.startswith(_ENV_ALLOW_PREFIXES):
            env[key] = value
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # Agg: графики без GUI; PNG забираем из фигур после exec (этап 4б).
    env["MPLBACKEND"] = "Agg"
    # Не протаскиваем PYTHONPATH/VIRTUAL_ENV — ребёнок стартует тем же
    # sys.executable, site-packages подтянутся сами.
    return env


def _encode_value(value: Any, depth: int = 0) -> Any:
    """В JSON; несериализуемое → {"__type__":"repr",...}."""
    if depth > 8:
        return {"__type__": "repr", "repr": "<max depth>"}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, complex):
        return {"__type__": "complex", "real": value.real, "imag": value.imag}
    try:
        import numpy as np

        if isinstance(value, np.ndarray):
            return {
                "__type__": "ndarray",
                "dtype": str(value.dtype),
                "shape": list(value.shape),
                "data": value.tolist(),
            }
        if isinstance(value, np.generic):
            return value.item()
    except Exception:
        pass
    if isinstance(value, (list, tuple)):
        return [_encode_value(v, depth + 1) for v in value]
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            out[str(k)] = _encode_value(v, depth + 1)
        return out
    if _looks_like_sklearn(value):
        snap: Dict[str, Any] = {
            "__type__": "object",
            "class": type(value).__name__,
            "__has_predict__": hasattr(value, "predict"),
        }
        for attr in (
            "n_features_in_",
            "n_clusters",
            "n_classes_",
            "classes_",
            "n_iter_",
            "labels_",
            "coef_",
            "intercept_",
            "cluster_centers_",
            "feature_importances_",
        ):
            if hasattr(value, attr):
                try:
                    snap[attr] = _encode_value(getattr(value, attr), depth + 1)
                except Exception:
                    pass
        return snap
    try:
        text = repr(value)
    except Exception:
        text = f"<unreprable {type(value).__name__}>"
    if len(text) > 2000:
        text = text[:2000] + "..."
    return {"__type__": "repr", "repr": text, "class": type(value).__name__}


def _looks_like_sklearn(value: Any) -> bool:
    return hasattr(value, "fit") or hasattr(value, "predict") or hasattr(value, "transform")


def _decode_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_decode_value(v) for v in value]
    if not isinstance(value, dict) or "__type__" not in value:
        if isinstance(value, dict):
            return {k: _decode_value(v) for k, v in value.items()}
        return value
    kind = value.get("__type__")
    if kind == "ndarray":
        try:
            import numpy as np

            return np.array(value.get("data"), dtype=value.get("dtype", None))
        except Exception:
            return value.get("data")
    if kind == "complex":
        return complex(value.get("real", 0.0), value.get("imag", 0.0))
    if kind == "object":
        data = {
            k: _decode_value(v)
            for k, v in value.items()
            if k not in {"__type__", "class", "__has_predict__"}
        }
        ns = SimpleNamespace(**data)
        if value.get("__has_predict__"):
            # values_equal ищет hasattr(..., "predict")
            ns.predict = lambda *a, **k: None  # noqa: E731
        return ns
    if kind == "repr":
        # Флаг несериализуемого: оставляем строку-repr как значение.
        return value.get("repr", "")
    return value


def _truncate(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[truncated {len(text) - limit} chars]"


_WORKER_CODE = r'''
import base64
import io
import json
import os
import sys
import traceback
import warnings
from contextlib import redirect_stdout, redirect_stderr

os.environ.setdefault("MPLBACKEND", "Agg")
warnings.filterwarnings(
    "ignore",
    message=r".*FigureCanvasAgg is non-interactive.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r".*non-interactive.*cannot be shown.*",
    category=UserWarning,
)

def encode_value(value, depth=0):
    if depth > 8:
        return {"__type__": "repr", "repr": "<max depth>"}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, complex):
        return {"__type__": "complex", "real": value.real, "imag": value.imag}
    try:
        import numpy as np
        if isinstance(value, np.ndarray):
            return {"__type__": "ndarray", "dtype": str(value.dtype),
                    "shape": list(value.shape), "data": value.tolist()}
        if isinstance(value, np.generic):
            return value.item()
    except Exception:
        pass
    if isinstance(value, (list, tuple)):
        return [encode_value(v, depth + 1) for v in value]
    if isinstance(value, dict):
        return {str(k): encode_value(v, depth + 1) for k, v in value.items()}
    if hasattr(value, "fit") or hasattr(value, "predict") or hasattr(value, "transform"):
        snap = {"__type__": "object", "class": type(value).__name__,
                "__has_predict__": hasattr(value, "predict")}
        for attr in ("n_features_in_", "n_clusters", "n_classes_", "classes_",
                     "n_iter_", "labels_", "coef_", "intercept_",
                     "cluster_centers_", "feature_importances_"):
            if hasattr(value, attr):
                try:
                    snap[attr] = encode_value(getattr(value, attr), depth + 1)
                except Exception:
                    pass
        return snap
    try:
        text = repr(value)
    except Exception:
        text = "<unreprable %s>" % type(value).__name__
    if len(text) > 2000:
        text = text[:2000] + "..."
    return {"__type__": "repr", "repr": text, "class": type(value).__name__}


def decode_value(value):
    if isinstance(value, list):
        return [decode_value(v) for v in value]
    if not isinstance(value, dict) or "__type__" not in value:
        if isinstance(value, dict):
            return {k: decode_value(v) for k, v in value.items()}
        return value
    kind = value.get("__type__")
    if kind == "ndarray":
        try:
            import numpy as np
            return np.array(value.get("data"), dtype=value.get("dtype", None))
        except Exception:
            return value.get("data")
    if kind == "complex":
        return complex(value.get("real", 0.0), value.get("imag", 0.0))
    if kind == "object":
        class _Snap:
            pass
        obj = _Snap()
        for k, v in value.items():
            if k in ("__type__", "class", "__has_predict__"):
                continue
            setattr(obj, k, decode_value(v))
        if value.get("__has_predict__"):
            obj.predict = lambda *a, **k: None
        return obj
    if kind == "repr":
        return value.get("repr", "")
    return value


def _patch_pyplot_show():
    plt = sys.modules.get("matplotlib.pyplot")
    if plt is None or getattr(plt, "_teachai_show_patched", False):
        return
    plt.show = lambda *a, **k: None
    plt._teachai_show_patched = True


_real_import = __import__

def _teachai_import(name, globals=None, locals=None, fromlist=(), level=0):
    mod = _real_import(name, globals, locals, fromlist, level)
    if name == "matplotlib.pyplot" or name.startswith("matplotlib."):
        _patch_pyplot_show()
    elif name == "matplotlib" and fromlist:
        _patch_pyplot_show()
    return mod


def capture_matplotlib_images(max_figures, max_total_bytes):
    images = []
    truncated = False
    if "matplotlib.pyplot" not in sys.modules:
        return images, truncated
    plt = sys.modules.get("matplotlib.pyplot")
    if plt is None:
        return images, truncated
    _patch_pyplot_show()
    total = 0
    try:
        fignums = list(plt.get_fignums())
    except Exception:
        return images, truncated
    for idx, num in enumerate(fignums):
        if idx >= max_figures:
            truncated = True
            break
        try:
            fig = plt.figure(num)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
            data = buf.getvalue()
        except Exception:
            continue
        if total + len(data) > max_total_bytes:
            truncated = True
            break
        total += len(data)
        images.append(base64.b64encode(data).decode("ascii"))
    try:
        plt.close("all")
    except Exception:
        pass
    return images, truncated


def main():
    job_path = sys.argv[1]
    result_path = sys.argv[2]
    with open(job_path, "r", encoding="utf-8") as f:
        job = json.load(f)
    code = job.get("code") or ""
    initial_vars = job.get("initial_vars") or {}
    capture_variables = bool(job.get("capture_variables", True))
    eval_last = bool(job.get("eval_last_expression", False))
    max_out = int(job.get("max_output_chars") or 100000)
    max_figures = int(job.get("max_figures") or 10)
    max_images_bytes = int(job.get("max_images_bytes") or (5 * 1024 * 1024))

    try:
        import builtins
        builtins.__import__ = _teachai_import
    except Exception:
        pass

    local_vars = {}
    for k, v in initial_vars.items():
        local_vars[k] = decode_value(v)

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    payload = {
        "stdout": "",
        "stderr": "",
        "variables": {},
        "result": None,
        "images": [],
        "images_truncated": False,
        "success": False,
        "error": None,
        "exception_type": None,
    }
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(compile(code, "<student>", "exec"), local_vars, local_vars)
            if eval_last:
                lines = [ln.strip() for ln in code.strip().split("\n") if ln.strip()]
                if lines:
                    last = lines[-1]
                    if (
                        last
                        and not last.startswith(
                            ("print", "import", "from", "def", "class",
                             "if", "for", "while", "try", "with", "#")
                        )
                        and "=" not in last
                        and not last.endswith(":")
                        and "+=" not in last and "-=" not in last
                        and "*=" not in last and "append(" not in last
                    ):
                        try:
                            payload["result"] = encode_value(eval(last, local_vars, local_vars))
                        except Exception:
                            pass
        payload["success"] = True
    except BaseException as exc:
        payload["success"] = False
        payload["exception_type"] = type(exc).__name__
        payload["error"] = "%s: %s" % (type(exc).__name__, exc)
        traceback.print_exc(file=stderr_buf)

    try:
        images, truncated = capture_matplotlib_images(max_figures, max_images_bytes)
        payload["images"] = images
        payload["images_truncated"] = truncated
    except Exception:
        payload["images"] = []
        payload["images_truncated"] = False

    out = stdout_buf.getvalue()
    err = stderr_buf.getvalue()
    if payload.get("images_truncated"):
        note = (
            "Часть графиков не показана: слишком много фигур или превышен лимит размера."
        )
        out = (out + "\n" + note) if out else note
    if len(out) > max_out:
        out = out[:max_out] + "\n...[truncated %d chars]" % (len(out) - max_out)
    if len(err) > max_out:
        err = err[:max_out] + "\n...[truncated %d chars]" % (len(err) - max_out)
    payload["stdout"] = out
    payload["stderr"] = err

    if capture_variables and payload["success"]:
        variables = {}
        for name, value in local_vars.items():
            if name.startswith("_"):
                continue
            if name in ("__builtins__",):
                continue
            if isinstance(value, type(sys)):
                continue
            if callable(value) and not (
                hasattr(value, "fit") or hasattr(value, "predict")
                or hasattr(value, "transform")
            ):
                continue
            try:
                variables[name] = encode_value(value)
            except Exception:
                variables[name] = {"__type__": "repr", "repr": "<encode failed>",
                                   "class": type(value).__name__}
        payload["variables"] = variables

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

if __name__ == "__main__":
    main()

'''


def _kill_process_tree(proc: subprocess.Popen) -> None:
    """Убить процесс и группу. На Windows — terminate/kill без killpg."""
    if proc.poll() is not None:
        return
    try:
        if sys.platform == "win32":
            proc.kill()
        else:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                try:
                    proc.kill()
                except Exception:
                    pass
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def run_student_code(
    code: str,
    *,
    timeout: Optional[int] = None,
    initial_vars: Optional[Mapping[str, Any]] = None,
    capture_variables: bool = True,
    eval_last_expression: bool = False,
    env: Optional[Mapping[str, str]] = None,
) -> SandboxResult:
    """Запустить `code` в дочернем Python-процессе.

    stdin закрыт; cwd — временная папка (удаляется после); env — allowlist.
    """
    timeout_sec = choose_timeout(code, timeout)
    encoded_initial: Dict[str, Any] = {}
    if initial_vars:
        for key, value in initial_vars.items():
            if key.startswith("_"):
                continue
            try:
                json.dumps(_encode_value(value))
                encoded_initial[key] = _encode_value(value)
            except Exception:
                continue

    tmp_dir = tempfile.mkdtemp(prefix="teachai_sandbox_")
    job_path = os.path.join(tmp_dir, "job.json")
    result_path = os.path.join(tmp_dir, "result.json")
    worker_path = os.path.join(tmp_dir, "_teachai_worker.py")

    job = {
        "code": code,
        "initial_vars": encoded_initial,
        "capture_variables": capture_variables,
        "eval_last_expression": eval_last_expression,
        "max_output_chars": MAX_OUTPUT_CHARS,
        "max_figures": MAX_SANDBOX_FIGURES,
        "max_images_bytes": MAX_SANDBOX_IMAGES_BYTES,
    }
    try:
        with open(job_path, "w", encoding="utf-8") as f:
            json.dump(job, f, ensure_ascii=False)
        with open(worker_path, "w", encoding="utf-8") as f:
            f.write(_WORKER_CODE)

        child_env = build_child_env(env)
        popen_kwargs: Dict[str, Any] = {
            "cwd": tmp_dir,
            "env": child_env,
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
        }
        if sys.platform == "win32":
            # Новая группа процессов; timeout через subprocess, не signal.
            popen_kwargs["creationflags"] = getattr(
                subprocess, "CREATE_NEW_PROCESS_GROUP", 0
            )
        else:
            popen_kwargs["start_new_session"] = True

        proc = subprocess.Popen(
            [sys.executable, worker_path, job_path, result_path],
            **popen_kwargs,
        )
        try:
            proc.communicate(timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            _kill_process_tree(proc)
            try:
                proc.communicate(timeout=2)
            except Exception:
                pass
            return SandboxResult(
                success=False,
                timed_out=True,
                error=TIMEOUT_MESSAGE,
                exception_type="SandboxTimeoutError",
            )

        if not os.path.exists(result_path):
            err = ""
            if proc.stderr:
                try:
                    err = proc.stderr.read().decode("utf-8", errors="replace")  # type: ignore[union-attr]
                except Exception:
                    err = ""
            return SandboxResult(
                success=False,
                error=err or f"sandbox worker failed (exit {proc.returncode})",
                exception_type="SandboxWorkerError",
            )

        with open(result_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        variables = {
            k: _decode_value(v) for k, v in (payload.get("variables") or {}).items()
        }
        result_val = _decode_value(payload.get("result"))
        images = list(payload.get("images") or [])
        return SandboxResult(
            stdout=_truncate(payload.get("stdout") or ""),
            stderr=_truncate(payload.get("stderr") or ""),
            variables=variables,
            result=result_val,
            images=images,
            success=bool(payload.get("success")),
            timed_out=False,
            error=payload.get("error"),
            exception_type=payload.get("exception_type"),
        )
    finally:
        # Всегда убираем временный cwd.
        try:
            import shutil

            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass


def run_or_raise(
    code: str,
    *,
    timeout: Optional[int] = None,
    initial_vars: Optional[Mapping[str, Any]] = None,
    capture_variables: bool = True,
    eval_last_expression: bool = False,
) -> SandboxResult:
    """Как run_student_code, но таймаут и ошибки студента — исключениями."""
    result = run_student_code(
        code,
        timeout=timeout,
        initial_vars=initial_vars,
        capture_variables=capture_variables,
        eval_last_expression=eval_last_expression,
    )
    if result.timed_out:
        raise SandboxTimeoutError(result.error or TIMEOUT_MESSAGE)
    if not result.success:
        msg = result.error or result.stderr or "Ошибка выполнения кода"
        raise RuntimeError(msg)
    return result


def image_widgets(images):
    """Список ipywidgets.Image из base64 PNG (для VBox в интерфейсе)."""
    import base64

    import ipywidgets as widgets

    out = []
    for b64 in images or []:
        try:
            raw = base64.b64decode(b64)
        except Exception:
            continue
        if not raw:
            continue
        out.append(
            widgets.Image(
                value=raw,
                format="png",
                layout=widgets.Layout(max_width="100%", margin="4px 0"),
            )
        )
    return out


def display_images(images) -> None:
    """Показать PNG через IPython.display.Image (для Output-области ячеек)."""
    import base64

    from IPython.display import Image, display

    for b64 in images or []:
        try:
            raw = base64.b64decode(b64)
        except Exception:
            continue
        if raw:
            display(Image(data=raw))


```

### F. `control_tasks_generator.py` — картинки при проверке КЗ

```diff
--- a/control_tasks_generator.py
+++ b/control_tasks_generator.py
@@ -1075,13 +1075,19 @@
 
         student_stdout = ""
         local_vars: Dict[str, Any] = {}
+        student_images: list = []
         execution_error: Optional[str] = None
 
         try:
+            from code_sandbox import run_or_raise
+
             full_code = self.resolve_executable_code(task_code, user_code)
-            student_stdout, local_vars = self.execute_code(
-                self.stabilize_sklearn_code(full_code)
+            sandbox = run_or_raise(
+                self.stabilize_sklearn_code(full_code), capture_variables=True
             )
+            student_stdout = (sandbox.stdout or "").strip()
+            local_vars = sandbox.variables
+            student_images = list(sandbox.images or [])
         except Exception as exc:
             execution_error = str(exc)
             student_stdout = ""
@@ -1153,4 +1159,5 @@
             "failure_reason": failure_reason,
             "feedback": feedback,
             "validation_method": validation_method,
+            "images": student_images,
         }

```

### G. `control_tasks_interface.py` — показ PNG под выводом (Запустить и Проверить)

```diff
--- a/control_tasks_interface.py
+++ b/control_tasks_interface.py
@@ -270,37 +270,37 @@
             results_output.children = []
             
             try:
-                from code_sandbox import run_or_raise
+                from code_sandbox import image_widgets, run_or_raise
 
                 full_code = ControlTasksGenerator.resolve_executable_code(
                     task_data.get("task_code", ""), code_input.value
                 )
                 sandbox_result = run_or_raise(full_code, capture_variables=False)
                 output = sandbox_result.stdout or ""
-                
-                # Создаем виджет для отображения результата
+                imgs = image_widgets(sandbox_result.images)
+
                 if output.strip():
                     result_html = widgets.HTML(
                         value=f"<p style='color: green;'>✅ Код выполнен успешно!</p><pre style='background: #f8f9fa; padding: 10px; border-radius: 4px;'>{output}</pre>"
                     )
+                elif imgs:
+                    result_html = widgets.HTML(
+                        value="<p style='color: green;'>✅ Код выполнен успешно! График ниже.</p>"
+                    )
                 else:
                     result_html = widgets.HTML(
                         value=(
                             "<p style='color: green;'>✅ Код выполнен успешно! (без текстового вывода)</p>"
-                            "<p style='color:#666;font-size:14px;'>Если строился график — он появится "
-                            "в области вывода ноутбука выше или ниже этого блока. "
+                            "<p style='color:#666;font-size:14px;'>"
                             "Для проверки задания нажмите «✓ Проверить решение».</p>"
                         )
                     )
-                
-                # Добавляем результат в контейнер
-                results_output.children = [result_html]
-                
+                results_output.children = [result_html, *imgs]
+
             except Exception as e:
                 error_html = widgets.HTML(
                     value=f"<p style='color: red;'>❌ Ошибка выполнения: {str(e)}</p>"
                 )
-                # Добавляем ошибку в контейнер
                 results_output.children = [error_html]
 
         def on_check_button_clicked(b):
@@ -469,7 +469,10 @@
                 retry_buttons = self._create_retry_buttons()
                 result_widgets.extend(retry_buttons)
 
-            # ИСПРАВЛЕНО: Добавляем все виджеты в контейнер результатов
+            # Графики из sandbox (matplotlib → PNG), если ученик их строил.
+            from code_sandbox import image_widgets
+
+            result_widgets.extend(image_widgets(validation_result.get("images") or []))
             results_output.children = result_widgets
 
         except Exception as e:

```

### H. `interactive_cell_logic.py`

```diff
--- a/interactive_cell_logic.py
+++ b/interactive_cell_logic.py
@@ -11,7 +11,7 @@
 
 def execute_student_code(
     student_code: str, execution_namespace: Dict[str, Any]
-) -> Tuple[Any, str, bool]:
+) -> Tuple[Any, str, bool, list]:
     """
     Выполняет код студента и возвращает результат.
 
@@ -20,13 +20,20 @@
         execution_namespace: Пространство имен для выполнения
 
     Returns:
-        Кортеж (результат, вывод, успех_выполнения)
+        Кортеж (результат, вывод, успех_выполнения, images_base64)
     """
     try:
-        # Выполняем код студента
-        exec(student_code, execution_namespace)
+        from code_sandbox import run_or_raise
+
+        # В дочерний процесс передаём только JSON-сериализуемые значения.
+        sandbox = run_or_raise(
+            student_code,
+            initial_vars=execution_namespace,
+            capture_variables=True,
+        )
+        execution_namespace.clear()
+        execution_namespace.update(sandbox.variables)
 
-        # Ищем результат в пространстве имен
         result = None
         result_vars = [
             "result",
@@ -38,17 +45,15 @@
             "data",
             "values",
         ]
-
-        # Ищем переменные по имени
         for var_name in result_vars:
             if var_name in execution_namespace:
                 result = execution_namespace[var_name]
                 break
 
-        return result, "", True
+        return result, sandbox.stdout or "", True, list(sandbox.images or [])
 
     except Exception as e:
-        return None, str(e), False
+        return None, str(e), False, []
 
 
 def find_result_in_namespace(

```

### I. `interactive_cell_widget.py`

```diff
--- a/interactive_cell_widget.py
+++ b/interactive_cell_widget.py
@@ -171,9 +171,10 @@
 
         try:
             # Выполняем код студента через логику модуль
-            result, output, success = execute_student_code(
+            result, output, success, images = execute_student_code(
                 student_code, self.execution_namespace
             )
+            self._last_sandbox_images = images
             execution_time_ms = (time.time() - start_time) * 1000
 
             if success:
@@ -236,6 +237,13 @@
                 )
                 self._update_stats_display()
 
+            try:
+                from code_sandbox import display_images
+
+                display_images(getattr(self, "_last_sandbox_images", None))
+            except Exception:
+                pass
+
         except Exception as e:
             update_status_widget(
                 self.status_widget, f"❌ Неожиданная ошибка: {e}", "error"

```

### J. `cell_widget_base.py`

```diff
--- a/cell_widget_base.py
+++ b/cell_widget_base.py
@@ -109,7 +109,7 @@
 
     def execute_code(self, code: str) -> Tuple[Any, str, bool]:
         """
-        Выполняет Python код и возвращает результат.
+        Выполняет Python код в дочернем процессе (D9) и возвращает результат.
 
         Args:
             code: Строка с Python кодом для выполнения
@@ -120,82 +120,32 @@
         if not code.strip():
             return None, "Пустой код", False
 
-        # Захват stdout и stderr
-        old_stdout = sys.stdout
-        old_stderr = sys.stderr
-
-        stdout_capture = io.StringIO()
-        stderr_capture = io.StringIO()
-
-        result = None
-        success = True
-
-        try:
-            # Перенаправляем вывод
-            sys.stdout = stdout_capture
-            sys.stderr = stderr_capture
-
-            # Используем персистентное пространство имен для ячейки
-            if not hasattr(self, "execution_namespace") or not self.execution_namespace:
-                self.execution_namespace = {}
-                # Добавляем основные встроенные функции
-                self.execution_namespace.update(__builtins__)
-
-            # Выполняем код в персистентном пространстве имен
-            exec(code, self.execution_namespace, self.execution_namespace)
-
-            # Пытаемся получить результат из последней строки (если это выражение)
-            lines = code.strip().split("\n")
-            if lines:
-                last_line = lines[-1].strip()
-                if (
-                    last_line
-                    and not last_line.startswith(
-                        (
-                            "print",
-                            "import",
-                            "from",
-                            "def",
-                            "class",
-                            "if",
-                            "for",
-                            "while",
-                            "try",
-                            "with",
-                            "#",
-                        )
-                    )
-                    and "=" not in last_line
-                    and not last_line.endswith(":")
-                    and "+=" not in last_line
-                    and "-=" not in last_line
-                    and "*=" not in last_line
-                    and "append(" not in last_line
-                ):
-                    try:
-                        result = eval(last_line, self.execution_namespace)
-                    except:
-                        pass
-
-        except Exception as e:
-            success = False
-            stderr_capture.write(f"Ошибка: {str(e)}\n")
-            stderr_capture.write(traceback.format_exc())
-
-        finally:
-            # Восстанавливаем stdout и stderr
-            sys.stdout = old_stdout
-            sys.stderr = old_stderr
-
-        # Получаем захваченный вывод
-        stdout_content = stdout_capture.getvalue()
-        stderr_content = stderr_capture.getvalue()
-
-        output = stdout_content
-        if stderr_content:
-            output += f"\n{stderr_content}" if output else stderr_content
+        from code_sandbox import run_student_code
+
+        if not hasattr(self, "execution_namespace") or self.execution_namespace is None:
+            self.execution_namespace = {}
+
+        sandbox = run_student_code(
+            code,
+            initial_vars=self.execution_namespace,
+            capture_variables=True,
+            eval_last_expression=True,
+        )
+        self._last_sandbox_images = list(sandbox.images or [])
+        if sandbox.timed_out:
+            return None, sandbox.error or "Код выполнялся слишком долго, возможно, бесконечный цикл", False
+        if sandbox.variables:
+            self.execution_namespace.update(sandbox.variables)
+
+        output = sandbox.stdout or ""
+        if sandbox.stderr:
+            output = f"{output}\n{sandbox.stderr}" if output else sandbox.stderr
+
+        if not sandbox.success:
+            return None, (sandbox.error or output or "Ошибка выполнения"), False
+
+        return sandbox.result, output, True
 
-        return result, output, success
 
     def display_result(self, result: Any, output: str, success: bool):
         """
@@ -229,6 +179,10 @@
                 if result_lines:
                     print("\n".join(result_lines))
 
+            from code_sandbox import display_images
+
+            display_images(getattr(self, "_last_sandbox_images", None))
+
     def clear_output(self):
         """Очищает область вывода результатов."""
         with self.output_area:

```

### K. `examples_display.py`

```diff
--- a/examples_display.py
+++ b/examples_display.py
@@ -37,7 +37,7 @@
     )
     # Не widgets.Output: его поток в Jupyter дописывается по числу активных
     # областей вывода, и один щелчок печатает результат несколько раз.
-    result = widgets.HTML(value="")
+    result_box = widgets.VBox()
     busy_until = {"t": 0.0}
 
     def _on_run(_button: widgets.Button) -> None:
@@ -45,24 +45,31 @@
         if now < busy_until["t"]:
             return
         busy_until["t"] = now + 1.0
-        buffer = io.StringIO()
         try:
-            with redirect_stdout(buffer):
-                exec(code_area.value, {})
-            text = buffer.getvalue()
+            from code_sandbox import image_widgets, run_or_raise
+
+            sandbox = run_or_raise(code_area.value, capture_variables=False)
+            text = sandbox.stdout or ""
             body = text if text.strip() else "Код выполнен успешно."
-            result.value = (
-                "<pre style='white-space:pre-wrap;margin:8px 0;'>"
-                f"{html.escape(body)}</pre>"
+            html_w = widgets.HTML(
+                value=(
+                    "<pre style='white-space:pre-wrap;margin:8px 0;'>"
+                    f"{html.escape(body)}</pre>"
+                )
             )
+            result_box.children = (html_w, *image_widgets(sandbox.images))
         except Exception as exc:
-            result.value = (
-                "<pre style='white-space:pre-wrap;margin:8px 0;color:#721c24;'>"
-                f"{html.escape(str(exc))}</pre>"
+            result_box.children = (
+                widgets.HTML(
+                    value=(
+                        "<pre style='white-space:pre-wrap;margin:8px 0;color:#721c24;'>"
+                        f"{html.escape(str(exc))}</pre>"
+                    )
+                ),
             )
 
     run_button.on_click(_on_run)
-    return widgets.VBox([code_area, run_button, result])
+    return widgets.VBox([code_area, run_button, result_box])
 
 
 def _create_code_widget(code: str, cell_adapter: Any) -> widgets.Widget | None:

```

### L. `examples_validation.py`

```diff
--- a/examples_validation.py
+++ b/examples_validation.py
@@ -96,22 +96,28 @@
                 self.logger.warning("Пример %s без кода", index)
                 return False
             try:
-                with redirect_stdout(io.StringIO()):
-                    exec(code, {})
-            except ModuleNotFoundError as exc:
-                self.logger.info(
-                    "Пример %s: модуль не установлен (%s) — это не повод для fallback",
-                    index,
-                    exc,
-                )
-                return False
-            except ImportError as exc:
-                self.logger.info(
-                    "Пример %s: ImportError (%s) — покажем код от LLM без exec",
-                    index,
-                    exc,
-                )
-                return False
+                from code_sandbox import run_student_code
+
+                sandbox = run_student_code(code, capture_variables=False)
+                if sandbox.timed_out:
+                    self.logger.warning(
+                        "Пример %s: таймаут (%s)", index, sandbox.error
+                    )
+                    return False
+                if not sandbox.success:
+                    exc_type = sandbox.exception_type or ""
+                    if exc_type in {"ModuleNotFoundError", "ImportError"}:
+                        self.logger.info(
+                            "Пример %s: %s (%s) — покажем код от LLM без exec",
+                            index,
+                            exc_type,
+                            sandbox.error,
+                        )
+                        return False
+                    self.logger.warning(
+                        "Пример %s не выполняется: %s", index, sandbox.error
+                    )
+                    return False
             except Exception as exc:
                 self.logger.warning("Пример %s не выполняется: %s", index, exc)
                 return False

```

### M. `cell_integration.py` — ZAP-08

```diff
--- a/cell_integration.py
+++ b/cell_integration.py
@@ -9,16 +9,19 @@
 from IPython.display import display
 import ipywidgets as widgets
 
-# Импорты системы ячеек
+# ZAP-08/D9: модуля demo_cell_widget в репозитории нет — мёртвый импорт убран.
+# Раньше ImportError из-за него держал CELLS_AVAILABLE=False; сохраняем False,
+# чтобы не включать давно не гонявшийся UI integrate_cells / create_demo_cell.
+# Примеры выполняются через examples_display._create_fallback_code_widget + sandbox.
+CELLS_AVAILABLE = False
+
 try:
-    from demo_cell_widget import create_demo_cell
-    from interactive_cell_widget import create_interactive_cell
-    from result_checker import check_result
-
-    CELLS_AVAILABLE = True
-except ImportError as e:
-    logging.warning(f"Система ячеек недоступна: {e}")
-    CELLS_AVAILABLE = False
+    # Оставлено для прямого использования interactive-ячеек вне adapter.demo-пути.
+    from interactive_cell_widget import create_interactive_cell  # noqa: F401
+    from result_checker import check_result  # noqa: F401
+except ImportError:
+    create_interactive_cell = None  # type: ignore
+    check_result = None  # type: ignore
 
 
 class CellIntegrationAdapter:
@@ -183,36 +186,10 @@
         self, code_blocks: List[Dict[str, Any]]
     ) -> List[widgets.Widget]:
         """
-        Создает демонстрационные ячейки из блоков кода (только для Python-кода).
+        Демо-ячейки через отсутствующий demo_cell_widget больше не создаём (ZAP-08).
+        examples_display использует fallback-виджет с code_sandbox.
         """
-        if not self.cells_available:
-            return []
-        demo_cells = []
-        for i, block in enumerate(code_blocks):
-            if not self.is_python_code(block["code"]):
-                continue
-            try:
-                # ИСПРАВЛЕНО: Декодируем HTML-кодировку в коде блока
-                decoded_block_code = (
-                    block["code"].replace("&lt;", "<")
-                    .replace("&gt;", ">")
-                    .replace("&amp;", "&")
-                    .replace("&quot;", '"')
-                    .replace("&#x27;", "'")
-                )
-                
-                cell = create_demo_cell(
-                    code=decoded_block_code,
-                    title=f"Пример кода {i+1}",
-                    description="Запустите код, чтобы увидеть результат",
-                    show_code=True,
-                    auto_run=False,
-                )
-                demo_cells.append(cell)
-                self.logger.info(f"Создана демонстрационная ячейка {i+1}")
-            except Exception as e:
-                self.logger.error(f"Ошибка создания демонстрационной ячейки {i+1}: {e}")
-        return demo_cells
+        return []
 
     def generate_interactive_tasks(
         self, lesson_content: str, lesson_title: str

```

### N. Тесты этапа 4б

Заменить `tests/unit/test_code_sandbox.py` целиком (13 тестов: прежние 7 + examples×2 + matplotlib×4):

```python
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

```

### Приёмка 4б

`python -m pytest -q -rx` → **`132 passed, 1 deselected`** (0 skipped, 0 xfailed).
`content_utils.py` не трогать. Покажи хвост pytest, `git status`, `git diff --stat`. Пуш — только по моей команде.


## 3. Ручной чеклист для Игоря (настоящий ноутбук)

После пуша 4б, в своём Jupyter / `TeachAI.ipynb`:

1. **КЗ → «▶ Запустить»** на `print(1+1)` — зелёный вывод `2`.
2. **КЗ → «✓ Проверить решение»** — верный/неверный код как раньше, ядро живо.
3. **Бесконечный цикл:** `while True:\n    pass` → «Запустить» → через ~10 с сообщение про долгий код, UI отвечает.
4. **График:** в КЗ или примерах выполнить
   ```python
   import matplotlib.pyplot as plt
   plt.plot([1, 2, 3], [1, 4, 9])
   plt.title("demo")
   plt.show()
   ```
   Под текстовым выводом должен появиться PNG-график (не пусто и не только warning).
5. **Примеры:** «Показать примеры» → «▶ Запустить» — текст + при наличии plot — картинка.
6. (Опционально) `import os; print(os.environ.get("OPENAI_API_KEY"))` — без реального ключа.
7. (Опционально) `open("pwn.txt","w").write("x")` — файла в каталоге проекта нет.

# Что сообщить мне в конце каждого этапа

1. Хвост `pytest -q -rx` и сравнение с ожидаемым числом.
2. `git status` / `git diff --stat`; подтверждение, что `data/`, `.env` не изменены и `content_utils.py` не тронут.
3. Места, где дифф не лёг.
4. Любая правка вне этого файла — только с моим согласием.

# Что дальше

- Пакет 4 закрывает D9 / SEC-01 / SEC-02 / KZ-16 / ZAP-08 + показ matplotlib/seaborn.
- Вне объёма: Plotly и прочие non-mpl бэкенды; возврат фигур после kill по таймауту (процесс уже убит).
