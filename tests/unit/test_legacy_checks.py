"""Существующие проверки в корне проекта (*_checks.py) запускаются как есть, но в изолированной среде.

Файлы *_checks.py не двигаем; если проверка разошлась с кодом, её правят осознанно (так было с relevance_prompt_checks в пакете 2).
"""
import importlib
import inspect
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.unit

# Устаревшие проверки: сейчас таких нет. Если проверка разошлась с кодом, правьте её или код,
# а не добавляйте сюда запись без причины.
STALE: dict[str, str] = {}


def _cases():
    for path in sorted(ROOT.glob("*_checks.py")):
        mod = importlib.import_module(path.stem)
        for name, fn in inspect.getmembers(mod, inspect.isfunction):
            if name.startswith("test_") and fn.__module__ == path.stem:
                case_id = f"{path.stem}::{name}"
                marks = []
                if case_id in STALE:
                    marks.append(pytest.mark.xfail(strict=True, raises=AssertionError, reason=STALE[case_id]))
                yield pytest.param(fn, id=case_id, marks=marks)


@pytest.mark.parametrize("fn", list(_cases()))
def test_legacy_check(fn):
    fn()
