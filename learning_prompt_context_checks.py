"""Проверки текстовых блоков контекста обучения."""

from __future__ import annotations

from learning_prompt_context import (
    control_task_runtime_rules_ru,
    lesson_context_block,
    practice_runtime_rules_ru,
)


def test_runtime_rules_mention_exec() -> None:
    text = practice_runtime_rules_ru().lower()
    assert "терминал" in text
    assert "exec" in text or "jupyter" in text


def test_control_rules_mention_lesson() -> None:
    text = control_task_runtime_rules_ru("Типы данных")
    assert "Типы данных" in text


def test_lesson_context_block() -> None:
    block = lesson_context_block("тело урока")
    assert "тело урока" in block
    assert "ПОЛНЫЙ ТЕКСТ УРОКА" in block


def main() -> None:
    for fn in (
        test_runtime_rules_mention_exec,
        test_control_rules_mention_lesson,
        test_lesson_context_block,
    ):
        fn()
        print(f"OK {fn.__name__}")
    print("Контекст обучения: проверки прошли.")


if __name__ == "__main__":
    main()
