"""Страховка: outside с причиной про урок → course."""

from relevance_checker import RelevanceChecker


def test_outside_reason_about_lesson_promoted_to_course():
    raw = {
        "scope": "outside",
        "is_relevant": False,
        "on_lesson": False,
        "confidence": 90,
        "reason": (
            "Ваш вопрос о PyTorch не относится к предмету курса, "
            "который фокусируется на операторах и выражениях в Python."
        ),
        "suggestions": [],
    }
    fixed = RelevanceChecker._promote_outside_confused_with_lesson(
        raw, "Операторы и выражения"
    )
    assert fixed["scope"] == "course"
    assert fixed["is_relevant"] is True
    assert fixed["on_lesson"] is False


def test_outside_reason_without_lesson_markers_stays_outside():
    raw = {
        "scope": "outside",
        "is_relevant": False,
        "on_lesson": False,
        "confidence": 90,
        "reason": "Вопрос про готовку каши вне предмета этого курса.",
        "suggestions": [],
    }
    fixed = RelevanceChecker._promote_outside_confused_with_lesson(
        raw, "Операторы и выражения"
    )
    assert fixed["scope"] == "outside"
    assert fixed["is_relevant"] is False


def test_course_untouched():
    raw = {
        "scope": "course",
        "is_relevant": True,
        "on_lesson": False,
        "confidence": 80,
        "reason": "Это не тема текущего урока.",
        "suggestions": [],
    }
    fixed = RelevanceChecker._promote_outside_confused_with_lesson(
        raw, "Операторы и выражения"
    )
    assert fixed is raw
