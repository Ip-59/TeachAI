"""Единый пайплайн учебного текста: Markdown/HTML → HTML для ipywidgets."""

from __future__ import annotations

import logging
import re

from content_renderer import (
    enhance_content,
    get_display_css,
    strip_embedded_styles,
)

logger = logging.getLogger(__name__)

_OUTER_FENCE = re.compile(
    r"^\s*(`{3}|~{3})([A-Za-z0-9_+\-]*)[ \t]*\r?\n([\s\S]*?)\r?\n[ \t]*\1[ \t]*\s*$"
)
_HTML_START = re.compile(
    r"<(div|p|h[1-6]|ul|ol|pre|style|section|article|table|blockquote)\b",
    re.IGNORECASE,
)
_CODE_LANGS = frozenset(
    {
        "python",
        "py",
        "javascript",
        "js",
        "typescript",
        "ts",
        "sql",
        "bash",
        "sh",
        "json",
        "yaml",
        "html",
        "css",
        "r",
        "java",
        "c",
        "cpp",
    }
)

_WRAPPER_CSS = """
.qa-answer, .explanation-compact, .concept-explanation {
    padding: 16px 20px;
    border-radius: 10px;
    margin: 12px 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}
.qa-answer, .explanation-compact {
    background: linear-gradient(135deg, #e7f3ff 0%, #cce7ff 100%);
    border-left: 4px solid #007bff;
}
.concept-explanation {
    background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
    border-left: 4px solid #ff9800;
}
"""


def unwrap_outer_fence(text: str) -> str:
    """
    Снимает одну внешнюю обёртку ```markdown / ```html вокруг всего ответа.

    Внутренние блоки кода не трогает. Цельный ответ-пример на python/js
    оставляет как есть.
    """
    if not text:
        return text
    match = _OUTER_FENCE.match(text.strip())
    if not match:
        return text
    lang = (match.group(2) or "").strip().lower()
    body = match.group(3)
    if lang in _CODE_LANGS and lang not in {"html", "markdown", "md", "text"}:
        return text
    logger.debug("Снята внешняя обёртка fence lang=%s", lang or "(пусто)")
    return body


def looks_like_html(text: str) -> bool:
    """True, если текст уже HTML, а не Markdown."""
    stripped = (text or "").lstrip()
    if not stripped.startswith("<"):
        return False
    return bool(_HTML_START.match(stripped))


def _ensure_lesson_wrapper(html: str) -> str:
    stripped = html.lstrip()
    if stripped.startswith('<div class="lesson-content"'):
        return html
    return f'<div class="lesson-content">\n{html}\n</div>'


def _to_lesson_html(text: str) -> str:
    text = unwrap_outer_fence(text or "")
    if not text.strip():
        return '<div class="lesson-content"></div>'

    if looks_like_html(text):
        html = enhance_content(text)
        html = strip_embedded_styles(html)
        return _ensure_lesson_wrapper(html)

    from content_formatter_final import ContentFormatterFinal

    html = ContentFormatterFinal().format_lesson_content(text)
    html = strip_embedded_styles(html)
    return _ensure_lesson_wrapper(html)


def render_student_content(
    text: str,
    *,
    css: bool = True,
    wrapper: str = "lesson-content",
    lead_html: str = "",
) -> str:
    """
    Канон показа учебного текста в Jupyter.

    Args:
        text: Markdown или HTML от LLM / из кэша.
        css: Вставлять ли ``get_display_css()``.
        wrapper: Внешний класс (``lesson-content``, ``qa-answer``,
            ``explanation-compact``, ``concept-explanation``).
        lead_html: Уже готовый HTML-префикс (стиль общения), не markdown.
    """
    body = _to_lesson_html(text)
    if lead_html:
        body = body.replace(
            '<div class="lesson-content">',
            f'<div class="lesson-content">{lead_html}',
            1,
        )
    if wrapper and wrapper != "lesson-content":
        html = f'<div class="{wrapper}">{body}</div>'
    else:
        html = body
    if not css:
        return html
    extra = f"<style>{_WRAPPER_CSS}</style>" if wrapper != "lesson-content" else ""
    return f"{extra}{get_display_css()}{html}"
