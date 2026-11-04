"""Релевантность вопроса — суждение преподавателя, не сверка фраз с текстом."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from relevance_checker import RelevanceChecker


def test_relevance_prompt_is_a_teacher_judgment() -> None:
    prompt = RelevanceChecker._build_relevance_prompt(
        None,
        "какая версия питон актуальная",
        "Установка Python",
        "Шаги по установке Python на разные операционные системы.",
        ["установка", "Python"],
        "Урок про установщик и флажок Add Python to PATH.",
    )
    lowered = prompt.lower()
    assert "не сверка фраз с текстом" in lowered
    assert "точной фразы вопроса в тексте нет" in lowered
    assert "если понятие или термин из вопроса встречается" not in lowered
    assert "не рассматривается в тексте" in lowered
    assert "scope=lesson" in lowered
    assert "scope=course" in lowered
    assert "scope=outside" in lowered
    assert "близких конструкций" in lowered
    assert "в основном опирается" in lowered
    assert "в тексте или коде" in lowered
    assert "которую этот урок не вводит" in lowered
    assert "понятия, операторы, синтаксис" not in lowered
    assert "3.15" not in lowered
    assert "= и ==" not in lowered
    assert "вне тем курса" in lowered
    assert "не относится к курсу целиком" in lowered


def main() -> None:
    test_relevance_prompt_is_a_teacher_judgment()
    print("OK test_relevance_prompt_is_a_teacher_judgment")


if __name__ == "__main__":
    main()
