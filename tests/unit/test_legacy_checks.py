"""Legacy *_checks.py из tests/legacy_checks/ — как есть, в изолированной среде.

Файлы не оставляем в корне; если проверка разошлась с кодом, правят её или код.
Запуск одного файла из корня репозитория:
  PYTHONPATH=. python tests/legacy_checks/course_portfolio_checks.py
"""
import importlib
import inspect
from pathlib import Path

import pytest

LEGACY = Path(__file__).resolve().parents[1] / "legacy_checks"
pytestmark = pytest.mark.unit

# Устаревшие проверки: сейчас таких нет. Если проверка разошлась с кодом, правьте её или код,
# а не добавляйте сюда запись без причины.
STALE: dict[str, str] = {}


def _cases():
    for path in sorted(LEGACY.glob("*_checks.py")):
        mod = importlib.import_module(f"tests.legacy_checks.{path.stem}")
        for name, fn in inspect.getmembers(mod, inspect.isfunction):
            if name.startswith("test_") and fn.__module__ == mod.__name__:
                case_id = f"{path.stem}::{name}"
                marks = []
                if case_id in STALE:
                    marks.append(
                        pytest.mark.xfail(
                            strict=True,
                            raises=AssertionError,
                            reason=STALE[case_id],
                        )
                    )
                yield pytest.param(fn, id=case_id, marks=marks)


@pytest.mark.parametrize("fn", list(_cases()))
def test_legacy_check(fn):
    fn()
