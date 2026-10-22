"""Разбор JSON-ответов классификатора КЗ (без живого API)."""

from __future__ import annotations

from control_task_llm_judge import _bool_field, _parse_json_object


def test_parse_subject_json() -> None:
    data = _parse_json_object(
        '{"subject": "анализ данных с Python", "reason": "pandas в тексте"}'
    )
    assert data["subject"].startswith("анализ")


def test_parse_matches_in_fence() -> None:
    raw = '```json\n{"matches": false, "reason": "другая тема"}\n```'
    data = _parse_json_object(raw)
    assert _bool_field(data, "matches") is False


def test_bool_string_da() -> None:
    assert _bool_field({"matches": "да"}, "matches") is True


def main() -> None:
    for fn in (
        test_parse_subject_json,
        test_parse_matches_in_fence,
        test_bool_string_da,
    ):
        fn()
        print(f"OK {fn.__name__}")
    print("LLM-judge КЗ: разбор JSON OK.")


if __name__ == "__main__":
    main()
