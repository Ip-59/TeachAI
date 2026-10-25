"""Релевантность вопроса — суждение преподавателя, не сверка фраз с текстом."""

from __future__ import annotations

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
    assert "как преподаватель" in lowered
    assert "точной фразы в тексте может не быть" in lowered
    assert "если понятие или термин из вопроса встречается" not in lowered
    assert "не рассматривается в тексте" in lowered
    assert "scope=course" in lowered
    assert "3.15" not in lowered


def main() -> None:
    test_relevance_prompt_is_a_teacher_judgment()
    print("OK test_relevance_prompt_is_a_teacher_judgment")


if __name__ == "__main__":
    main()
