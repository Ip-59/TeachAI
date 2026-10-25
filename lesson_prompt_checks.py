"""Промпт урока не подсказывает чужие темы по словам в названии курса."""

from __future__ import annotations

from lesson_generator import LessonGenerator


def test_ide_lesson_prompt_stays_on_lesson() -> None:
    prompt = LessonGenerator._build_lesson_prompt(
        None,
        "Основы Python",
        "Введение в Python",
        "Установка и настройка окружения",
        "Настройка IDE",
        "Игорь",
        "brief",
    )
    lowered = prompt.lower()
    assert "настройка ide" in lowered
    assert "только этот урок" in lowered
    for needle in ("append", "insert", "remove", "load_iris"):
        assert needle not in lowered, needle


def main() -> None:
    test_ide_lesson_prompt_stays_on_lesson()
    print("OK test_ide_lesson_prompt_stays_on_lesson")


if __name__ == "__main__":
    main()
