"""Разбор ответа модели при проверке темы (без реального API)."""

from __future__ import annotations

from course_domain import classify_course_topic


class _FakeGenerator:
    def __init__(self, payload: str, fail_schema: bool = False) -> None:
        self.payload = payload
        self.fail_schema = fail_schema

    def make_api_request(self, **kwargs):
        if self.fail_schema and kwargs.get("response_format"):
            raise RuntimeError("schema not supported")
        return self.payload


def test_in_domain() -> None:
    gen = _FakeGenerator('{"in_domain": true, "reason": "это pandas"}')
    v = classify_course_topic("Основы pandas", "", gen)
    assert v.status == "in", v


def test_out_domain() -> None:
    gen = _FakeGenerator('{"in_domain": false, "reason": "бытовая тема"}')
    v = classify_course_topic("Кройка и шитьё", "", gen)
    assert v.status == "out", v


def test_json_in_fence() -> None:
    gen = _FakeGenerator('```json\n{"in_domain": false, "reason": "нет"}\n```')
    v = classify_course_topic("История Рима", "", gen)
    assert v.status == "out", v


def test_no_generator() -> None:
    v = classify_course_topic("Python", "")
    assert v.status == "error", v


def test_schema_fallback() -> None:
    gen = _FakeGenerator('{"in_domain": true, "reason": "ok"}', fail_schema=True)
    v = classify_course_topic("Нейросети", "", gen)
    assert v.status == "in", v


def test_facade_resolves_child() -> None:
    from course_domain import resolve_api_generator

    class _Facade:
        def __init__(self) -> None:
            self.lesson_gen = _FakeGenerator('{"in_domain": true, "reason": "x"}')

    facade = _Facade()
    assert resolve_api_generator(facade) is facade.lesson_gen
    v = classify_course_topic("Python", "", facade)
    assert v.status == "in", v


def main() -> None:
    for fn in (
        test_in_domain,
        test_out_domain,
        test_json_in_fence,
        test_no_generator,
        test_schema_fallback,
        test_facade_resolves_child,
    ):
        fn()
        print(f"OK {fn.__name__}")
    print("Разбор ответа классификатора прошёл.")


if __name__ == "__main__":
    main()
