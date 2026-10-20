"""Проверки канона рендера без Jupyter (python student_content_checks.py)."""

from __future__ import annotations

from content_formatter_final import ContentFormatterFinal
from student_content import (
    looks_like_html,
    render_student_content,
    unwrap_outer_fence,
)


def test_unwrap_keeps_inner_code() -> None:
    raw = "```markdown\n# Заголовок\n\n```python\nx = 1\n```\nещё текст\n```"
    out = unwrap_outer_fence(raw)
    assert "```python" in out
    assert out.strip().startswith("# Заголовок")


def test_unwrap_leaves_python_sample() -> None:
    raw = "```python\nprint(1)\n```"
    assert unwrap_outer_fence(raw) == raw


def test_looks_like_html() -> None:
    assert looks_like_html('<div class="lesson-content"><p>a</p></div>')
    assert not looks_like_html("# Заголовок\n\nтекст")


def test_code_blank_lines_and_indent() -> None:
    md = (
        "# Урок\n\n"
        "```python\n"
        "def f():\n"
        "    x = 1\n"
        "\n"
        "    return x\n"
        "```\n"
    )
    html = ContentFormatterFinal().format_lesson_content(md, "t")
    assert "<pre>" in html
    assert "    x = 1" in html
    assert "\n\n    return x" in html or "\n\n    return" in html
    assert "CODE_BLOCK" not in html


def test_unlabeled_fence_not_python_class() -> None:
    md = "```\nplain\n```"
    html = ContentFormatterFinal().format_lesson_content(md)
    assert 'class="language-text"' in html
    assert "language-python" not in html


def test_render_does_not_strip_fences() -> None:
    md = "## Тема\n\n```python\na = 1\nb = 2\n```\n"
    html = render_student_content(md)
    assert "<pre>" in html
    assert "a = 1" in html
    assert "```" not in html  # уже HTML, метки fences не торчат
    assert "lesson-content" in html
    assert "<style>" in html


def test_render_lead_html_does_not_eat_markdown() -> None:
    html = render_student_content(
        "## Раздел\n\nсписок:\n\n- один\n- два",
        wrapper="qa-answer",
        lead_html="<p>Префикс</p>",
    )
    assert "Префикс" in html
    assert "<h2>" in html
    assert "<li>" in html
    assert "qa-answer" in html


def main() -> None:
    tests = [
        test_unwrap_keeps_inner_code,
        test_unwrap_leaves_python_sample,
        test_looks_like_html,
        test_code_blank_lines_and_indent,
        test_unlabeled_fence_not_python_class,
        test_render_does_not_strip_fences,
        test_render_lead_html_does_not_eat_markdown,
    ]
    for fn in tests:
        fn()
        print(f"OK {fn.__name__}")
    print("Все проверки рендера прошли.")


if __name__ == "__main__":
    main()
