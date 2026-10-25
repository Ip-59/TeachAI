"""Нет запускаемого кода — сообщение ученику, не текст исключения."""

from __future__ import annotations

from examples_html_utils import (
    executable_examples,
    interpret_examples_payload,
    is_examples_notice,
    validate_examples_payload,
)


def test_path_steps_do_not_drop_python_examples() -> None:
    payload = {
        "practice_possible": True,
        "examples": [
            {
                "title": "Установка Python в PATH",
                "description": "Галочка установщика.",
                "code": "1. Откройте установщик\n2. Add Python to PATH",
            },
            {
                "title": "Проверка версии",
                "description": "Показывает версию интерпретатора.",
                "code": "import sys\nprint(sys.version)",
            },
        ],
    }
    result = interpret_examples_payload(payload)
    assert isinstance(result, list)
    assert [item["title"] for item in result] == ["Проверка версии"]
    assert executable_examples(payload)[0]["title"] == "Проверка версии"
    validate_examples_payload(payload, min_examples=1)


def test_impossible_practice_is_a_notice() -> None:
    payload = {
        "practice_possible": False,
        "notice": "Урок про кнопки установщика, в редакторе это не запускается.",
        "examples": [
            {
                "title": "Установка Python в PATH",
                "description": "Шаги.",
                "code": "1. Откройте установщик\n2. Add Python to PATH",
            }
        ],
    }
    result = interpret_examples_payload(payload)
    assert is_examples_notice(result)
    assert "установщика" in result["notice"]
    assert "Ошибка" not in result["notice"]


def test_only_install_steps_become_notice() -> None:
    payload = {
        "examples": [
            {
                "title": "Установка Python в PATH",
                "description": "Шаги установщика.",
                "code": "1. Откройте установщик\n2. Add Python to PATH",
            }
        ]
    }
    result = interpret_examples_payload(payload)
    assert is_examples_notice(result)
    assert "Ошибка при генерации" not in result["notice"]
    try:
        validate_examples_payload(payload, min_examples=1)
    except ValueError as exc:
        assert "терминала" in str(exc)
    else:
        raise AssertionError("ожидался ValueError")


def main() -> None:
    test_path_steps_do_not_drop_python_examples()
    print("OK test_path_steps_do_not_drop_python_examples")
    test_impossible_practice_is_a_notice()
    print("OK test_impossible_practice_is_a_notice")
    test_only_install_steps_become_notice()
    print("OK test_only_install_steps_become_notice")


if __name__ == "__main__":
    main()
