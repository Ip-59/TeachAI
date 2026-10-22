"""Структурные правки starter КЗ и текст антикопипасты для промпта.

Педагогические решения (тема / терминал / копипаста примеров) — в
``control_task_llm_judge``, не здесь.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

_MARKER = "# Ваш код здесь"


def split_starter_and_tail(task_code: str) -> tuple[str, str]:
    """Разделяет task_code на заготовку до маркера и хвост после него."""
    text = task_code or ""
    if _MARKER not in text:
        return text.strip(), ""
    before, after = text.split(_MARKER, 1)
    starter = before.rstrip() + "\n" + _MARKER
    return starter, after.strip()


def ensure_starter_without_solution(task_code: str) -> str:
    """Оставляет только импорты/данные и один маркер в конце."""
    starter, _tail = split_starter_and_tail(task_code)
    if _MARKER not in starter:
        starter = (starter.rstrip() + "\n" + _MARKER) if starter.strip() else _MARKER
    parts = starter.split(_MARKER)
    head = parts[0].rstrip()
    return (head + "\n" + _MARKER) if head else _MARKER


def task_code_contains_ready_solution(task_code: str) -> bool:
    """True, если после маркера уже есть исполняемый код студента."""
    _starter, tail = split_starter_and_tail(task_code)
    if not tail:
        body = (task_code or "").strip()
        if not body:
            return False
        if _MARKER not in body and _looks_like_student_actions(body):
            return True
        return False
    return _looks_like_student_actions(tail)


def _looks_like_student_actions(code: str) -> bool:
    lines = [
        ln.strip()
        for ln in code.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    if not lines:
        return False
    action_hints = (
        ".append(",
        ".remove(",
        ".pop(",
        "del ",
        "print(",
        ".fit(",
        ".predict(",
        "+=",
        "-=",
    )
    for ln in lines:
        if any(h in ln for h in action_hints):
            return True
    return len(lines) >= 2


def anti_copy_rules_ru() -> str:
    """Блок промпта: вариации вместо копипасты примеров урока."""
    return (
        "=== АНТИКОПИПАСТА (обязательно) ===\n"
        "- Урок — источник ТЕМЫ и приёмов, НЕ готовый текст задания.\n"
        "- ЗАПРЕЩЕНО копировать примеры из урока дословно: те же имена "
        "переменных и те же строковые/числовые литералы.\n"
        "- Придумай ДРУГИЕ имена и значения той же структуры "
        "(другой список/словарь/числа, не клон примера из текста).\n"
        "- task_code = только заготовка: импорты + начальные данные + "
        "РОВНО одна строка «# Ваш код здесь» В КОНЦЕ. "
        "После маркера НЕ должно быть ни одной строки кода.\n"
        "- solution_code = полное решение ОТДЕЛЬНО (заготовка + действия ученика).\n"
        "- Студент должен сам дописать действия (append/remove/новые ключи и т.д.), "
        "а не видеть уже готовое решение в редакторе.\n"
    )
