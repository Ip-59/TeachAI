"""Проверки скрытия индикаторов без clear_output ячейки."""

from __future__ import annotations

from loading_indicators import (
    LoadingManager,
    dismiss_widget,
    displayed_loading,
    make_wait_banner,
)


def test_dismiss_clears_html() -> None:
    w = make_wait_banner("тест")
    assert "спин" in w.value.lower() or "spin" in w.value.lower() or "teachai-spin" in w.value
    dismiss_widget(w)
    assert w.value == ""
    assert w.layout.display == "none"


def test_hide_after_lesson_show() -> None:
    mgr = LoadingManager()
    widget = mgr.show_loading("lesson", lesson_title="CV")
    assert widget is not None
    assert "Загружаю" in widget.value
    mgr.hide_loading()
    assert mgr.current_indicator is None
    assert widget.value == ""
    assert widget.layout.display == "none"


def test_openai_course_plan_message() -> None:
    mgr = LoadingManager()
    w = mgr.show_loading("openai", operation="generate_course_plan")
    assert "план" in w.value.lower()
    mgr.hide_loading()


def test_context_manager_hides_on_error() -> None:
    mgr = LoadingManager()
    try:
        with displayed_loading(mgr, "openai", operation="generate_test"):
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert mgr.current_indicator is None


def main() -> None:
    for fn in (
        test_dismiss_clears_html,
        test_hide_after_lesson_show,
        test_openai_course_plan_message,
        test_context_manager_hides_on_error,
    ):
        fn()
        print(f"OK {fn.__name__}")
    print("Индикаторы ожидания: скрытие работает.")


if __name__ == "__main__":
    main()
