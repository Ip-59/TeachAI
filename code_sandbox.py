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
