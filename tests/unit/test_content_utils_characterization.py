"""Характеризация публичного API content_utils до/после сплита (пакет 6)."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_parse_llm_json_plain_object():
    from content_utils import parse_llm_json

    assert parse_llm_json('{"a": 1, "b": [2]}') == {"a": 1, "b": [2]}


def test_parse_llm_json_fenced_and_surrounding_text():
    from content_utils import parse_llm_json

    fenced = """```json
{"ok": true, "n": 3}
```"""
    assert parse_llm_json(fenced) == {"ok": True, "n": 3}
    wrapped = 'Преамбула\n{"x": 7}\nхвост'
    assert parse_llm_json(wrapped) == {"x": 7}


def test_parse_llm_json_rejects_garbage():
    from content_utils import parse_llm_json

    with pytest.raises(ValueError):
        parse_llm_json("это не json")


def test_communication_styles_and_get_style_prefix():
    from content_utils import ContentUtils

    styles = ContentUtils.COMMUNICATION_STYLES
    assert set(styles) >= {"formal", "friendly", "casual", "brief"}
    utils = ContentUtils()
    examples = utils.get_style_prefix("friendly", "examples")
    assert "пример" in examples.lower() or "Примеры" in examples or "примеров" in examples.lower()
    qa = utils.get_style_prefix("brief", "qa")
    assert "Краткий" in qa or "кратк" in qa.lower()
    assert utils.get_style_prefix("friendly", "unknown_type") == ""


def test_append_question_reminder_threshold():
    from content_utils import append_question_reminder

    base = "<p>ответ</p>"
    assert append_question_reminder(base, 3) == base
    with_note = append_question_reminder(base, 4)
    assert with_note.startswith(base)
    assert "продолжим обучение" in with_note


def test_non_retryable_api_error_by_status_and_quota():
    from content_utils import non_retryable_api_error

    class Exc(Exception):
        def __init__(self, code=None, msg="err"):
            super().__init__(msg)
            if code is not None:
                self.status_code = code

    assert "401" in non_retryable_api_error(Exc(401))
    assert "400" in non_retryable_api_error(Exc(400))
    assert non_retryable_api_error(Exc(msg="Error code: 403 boom"))
    assert "квот" in non_retryable_api_error(Exc(msg="insufficient_quota")).lower()
    assert non_retryable_api_error(Exc(429)) == ""
    assert non_retryable_api_error(Exc(500)) == ""


def test_extract_lesson_headers_order_and_strip_tags():
    from content_utils import BaseContentGenerator

    gen = BaseContentGenerator.__new__(BaseContentGenerator)
    html = "<h2>A</h2><p>x</p><h3><b>B</b></h3><h2>A</h2>"
    assert gen.extract_lesson_headers(html) == ["A", "B"]
    assert gen.extract_lesson_headers("") == []


def test_prepare_lesson_text_for_analysis_strips_breadcrumb():
    from content_utils import BaseContentGenerator

    gen = BaseContentGenerator.__new__(BaseContentGenerator)
    html = (
        "<style>.x{color:red}</style>"
        "<h1>Курс Python</h1>"
        "<h2>Раздел 1</h2>"
        "<h3>Тема A</h3>"
        "<h2>Тело урока</h2>"
        "<p>Важный текст про списки.</p>"
        "<script>alert(1)</script>"
    )
    ctx = {
        "course_title": "Курс Python",
        "section_title": "Раздел 1",
        "topic_title": "Тема A",
    }
    text = gen.prepare_lesson_text_for_analysis(
        html, course_context=ctx, lesson_title="Урок 1", max_chars=6000
    )
    assert "Важный текст про списки" in text
    assert "Тело урока" in text
    assert "alert" not in text
    assert "color:red" not in text
    assert not text.lower().startswith("курс python")
