"""Структурные проверки starter КЗ (не педагогическое угадывание темы)."""

from __future__ import annotations

from control_task_quality import (
    ensure_starter_without_solution,
    task_code_contains_ready_solution,
)


def test_starter_strips_solution_tail() -> None:
    raw = (
        "fruits = ['apple']\n"
        "# Ваш код здесь\n"
        "fruits.append('date')\n"
        "fruits.remove('apple')\n"
    )
    assert task_code_contains_ready_solution(raw) is True
    clean = ensure_starter_without_solution(raw)
    assert clean.endswith("# Ваш код здесь")
    assert "append" not in clean
    assert task_code_contains_ready_solution(clean) is False


def main() -> None:
    test_starter_strips_solution_tail()
    print("OK test_starter_strips_solution_tail")
    print("Качество КЗ: starter OK.")


if __name__ == "__main__":
    main()
