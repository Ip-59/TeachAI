"""Рендеринг markdown-таблиц и LaTeX для widgets.HTML в Jupyter.

LLM часто возвращает сырые `| таблицы |` и `\\( ... \\)` / `\\[ ... \\]`.
В ipywidgets.HTML MathJax обычно не работает — конвертируем LaTeX в MathML.
"""

from __future__ import annotations

import html as html_module
import logging
import re
from typing import List, Tuple

import markdown

logger = logging.getLogger(__name__)

try:
    from latex2mathml.converter import convert as _latex_to_mathml

    _LATEX_AVAILABLE = True
except ImportError:
    _LATEX_AVAILABLE = False

_TABLE_PATTERN = re.compile(
    r"(?:^|\n)\s*(\|.+\|\s*\n\s*\|[-:\s|]+\|\s*\n(?:\s*\|.+\|\s*\n?)*)",
    re.MULTILINE,
)
_P_WRAPPED_TABLE_BLOCK = re.compile(
    r"((?:<p>\s*\|[^<]+\|\s*</p>\s*){2,})",
    re.IGNORECASE,
)
_P_MULTILINE_TABLE = re.compile(
    r"<p>\s*((?:\s*\|[^\n<]+\|\s*\n?)+)\s*</p>",
    re.IGNORECASE,
)

_DISPLAY_CSS = """
.lesson-math-display {
    display: block;
    text-align: left;
    margin: 0.75em 0;
    padding-left: 1em;
    overflow-x: auto;
}
.lesson-math-display math {
    display: inline;
    margin: 0;
    text-align: left;
}
.lesson-math-inline {
    display: inline;
    vertical-align: middle;
}
.lesson-math-fallback {
    font-family: 'Courier New', monospace;
    background: #f4f4f4;
    padding: 2px 6px;
    border-radius: 4px;
}
.lesson-table-wrap {
    display: inline-block !important;
    width: max-content !important;
    max-width: 100% !important;
    overflow-x: auto;
    margin: 12px 0;
    vertical-align: top;
}
.lesson-data-table {
    border-collapse: collapse !important;
    width: max-content !important;
    max-width: 100% !important;
    table-layout: auto !important;
    margin: 0 !important;
    font-size: 15px;
    line-height: 1.35;
}
.lesson-content table.lesson-data-table,
.explanation-compact table.lesson-data-table,
.concept-explanation table.lesson-data-table {
    border-collapse: collapse !important;
    width: max-content !important;
    max-width: 100% !important;
}
.lesson-data-table th,
.lesson-data-table td,
.lesson-content table.lesson-data-table th,
.lesson-content table.lesson-data-table td,
.explanation-compact table.lesson-data-table th,
.explanation-compact table.lesson-data-table td,
.concept-explanation table.lesson-data-table th,
.concept-explanation table.lesson-data-table td {
    border: 1px solid #bdc3c7;
    padding: 8px 16px !important;
    vertical-align: middle;
    white-space: nowrap;
    width: auto !important;
    max-width: none;
}
.lesson-data-table th,
.lesson-content table.lesson-data-table th,
.explanation-compact table.lesson-data-table th,
.concept-explanation table.lesson-data-table th {
    background-color: #3498db !important;
    color: #ffffff !important;
    font-weight: 600;
    text-align: left;
}
.lesson-data-table td,
.lesson-content table.lesson-data-table td,
.explanation-compact table.lesson-data-table td,
.concept-explanation table.lesson-data-table td {
    color: #1a365d !important;
    text-align: center;
    font-variant-numeric: tabular-nums;
}
.lesson-data-table td:first-child,
.lesson-data-table th:first-child,
.lesson-content table.lesson-data-table td:first-child,
.lesson-content table.lesson-data-table th:first-child,
.explanation-compact table.lesson-data-table td:first-child,
.explanation-compact table.lesson-data-table th:first-child,
.concept-explanation table.lesson-data-table td:first-child,
.concept-explanation table.lesson-data-table th:first-child {
    text-align: left;
}
.lesson-data-table tr:nth-child(even) td,
.lesson-content table.lesson-data-table tr:nth-child(even) td,
.explanation-compact table.lesson-data-table tr:nth-child(even) td,
.concept-explanation table.lesson-data-table tr:nth-child(even) td {
    background-color: #f8f9fa;
}
.lesson-data-table tr:hover td,
.lesson-content table.lesson-data-table tr:hover td,
.explanation-compact table.lesson-data-table tr:hover td,
.concept-explanation table.lesson-data-table tr:hover td {
    background-color: #eef6ff;
}
/* Старые таблицы без lesson-data-table — не растягивать на 100% */
.lesson-content table:not(.lesson-data-table),
.explanation-compact table:not(.lesson-data-table),
.concept-explanation table:not(.lesson-data-table) {
    width: max-content !important;
    max-width: 100% !important;
}

/* Типографика урока — обычный текст, светлые блоки кода */
.lesson-content {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #1a365d;
    font-weight: 400;
    max-width: 100%;
    padding: 4px 0;
}
.lesson-content h1, .lesson-content h2, .lesson-content h3, .lesson-content h4 {
    color: #1a365d;
    font-weight: 600;
    margin-top: 1.25em;
    margin-bottom: 0.5em;
    border-bottom: 1px solid #ddd;
    padding-bottom: 0.25em;
}
.lesson-content h1 { font-size: 1.75em; }
.lesson-content h2 { font-size: 1.4em; }
.lesson-content h3 { font-size: 1.2em; }
.lesson-content h4 { font-size: 1.05em; }
.lesson-content p, .lesson-content li {
    color: #1a365d;
    font-weight: 400;
    margin-bottom: 0.75em;
}
.lesson-content ul, .lesson-content ol {
    padding-left: 1.5em;
    margin-bottom: 0.75em;
}
.lesson-content strong, .lesson-content b {
    font-weight: 600;
    color: #1a365d;
}
.lesson-content em, .lesson-content i {
    font-style: italic;
    font-weight: 400;
}
.lesson-content pre {
    background-color: #f6f8fa;
    color: #1e293b;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 14px 16px;
    overflow-x: auto;
    margin: 12px 0;
    font-size: 0.92em;
    line-height: 1.5;
}
.lesson-content pre code {
    background: transparent;
    color: inherit;
    padding: 0;
    border: none;
    font-size: inherit;
    font-weight: 400;
    text-shadow: none;
}
.lesson-content code {
    background-color: #f0f0f0;
    color: #1a365d;
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid #ddd;
    font-family: 'Courier New', Consolas, monospace;
    font-size: 0.9em;
    font-weight: 400;
}
.lesson-content pre code .comment,
.lesson-content pre code .hljs-comment {
    color: #6b7280;
    font-style: italic;
    font-weight: 400;
}
.lesson-content blockquote {
    border-left: 3px solid #cbd5e1;
    background-color: #f9fafb;
    color: #1a365d;
    padding: 10px 16px;
    margin: 12px 0;
    font-style: italic;
}
"""


_TABLE_WRAP_STYLE = (
    "display:inline-block;width:max-content;max-width:100%;"
    "overflow-x:auto;margin:12px 0;vertical-align:top;"
)
_TABLE_STYLE = "width:max-content;max-width:100%;border-collapse:collapse;"


def get_display_css() -> str:
    """CSS для урока (типографика, таблицы, формулы) — вставлять в widgets.HTML."""
    return f"<style>{_DISPLAY_CSS}</style>"


def strip_embedded_styles(html: str) -> str:
    """Убирает встроенные <style> из HTML урока (устаревший кэш с тяжёлым CSS)."""
    if not html:
        return html
    return re.sub(r"<style[^>]*>[\s\S]*?</style>", "", html, flags=re.IGNORECASE)


def _latex_to_html(latex: str, display: bool = False) -> str:
    """Конвертирует фрагмент LaTeX в HTML (MathML или fallback)."""
    latex = latex.strip()
    if not latex:
        return ""

    if _LATEX_AVAILABLE:
        try:
            mathml = _latex_to_mathml(
                latex, display="block" if display else "inline"
            )
            css_class = "lesson-math-display" if display else "lesson-math-inline"
            tag = "div" if display else "span"
            return f'<{tag} class="{css_class}">{mathml}</{tag}>'
        except Exception as exc:
            logger.debug("LaTeX → MathML не удался: %s", exc)

    escaped = html_module.escape(latex)
    tag = "div" if display else "span"
    return f'<{tag} class="lesson-math-fallback">{escaped}</{tag}>'


def convert_latex(text: str) -> str:
    """Заменяет \\[...\\], \\(...\\) и $$...$$ на HTML."""
    if not text:
        return text

    patterns: List[Tuple[str, bool]] = [
        (r"\\\[([\s\S]*?)\\\]", True),
        (r"\\\(([\s\S]*?)\\\)", False),
        (r"\$\$([\s\S]*?)\$\$", True),
    ]
    for pattern, display in patterns:
        text = re.sub(
            pattern,
            lambda match, is_display=display: _latex_to_html(match.group(1), is_display),
            text,
        )
    return text


def _protect_blocks(text: str) -> Tuple[str, List[str]]:
    """Временно убирает pre/code-блоки, чтобы не трогать их при конвертации."""
    blocks: List[str] = []

    def _stash(match: re.Match) -> str:
        blocks.append(match.group(0))
        return f"__PROTECTED_BLOCK_{len(blocks) - 1}__"

    for pattern in (r"<pre[\s\S]*?</pre>", r"```[\s\S]*?```"):
        text = re.sub(pattern, _stash, text, flags=re.IGNORECASE)
    return text, blocks


def _restore_blocks(text: str, blocks: List[str]) -> str:
    for index, block in enumerate(blocks):
        text = text.replace(f"__PROTECTED_BLOCK_{index}__", block)
    return text


def _count_pipe_columns(row: str) -> int:
    return len([cell for cell in row.strip().strip("|").split("|") if cell is not None])


def _is_separator_row(row: str) -> bool:
    inner = row.strip().strip("|")
    if not inner:
        return False
    return all(re.fullmatch(r"[-:\s]+", cell.strip()) for cell in inner.split("|"))


def _pipe_rows_to_html(rows: List[str]) -> str:
    """Собирает markdown-таблицу из строк вида | a | b | и конвертирует в HTML."""
    cleaned = [row.strip() for row in rows if row.strip().startswith("|")]
    if len(cleaned) < 2:
        return ""

    if not _is_separator_row(cleaned[1]):
        columns = _count_pipe_columns(cleaned[0])
        separator = "|" + "|".join([" --- "] * columns) + "|"
        cleaned = [cleaned[0], separator, *cleaned[1:]]

    markdown_table = "\n".join(cleaned)
    try:
        return markdown.markdown(markdown_table, extensions=["tables"])
    except Exception as exc:
        logger.debug("pipe_rows_to_html: %s", exc)
        return ""


def _beautify_tables(html: str) -> str:
    """Оборачивает <table> и задаёт inline-стили (Jupyter часто игнорирует CSS)."""
    if not html or "<table" not in html.lower():
        return html

    # Снимаем старые обёртки — идempotent повторный вызов
    html = re.sub(
        r'<div class="lesson-table-wrap"[^>]*>\s*(<table[\s\S]*?</table>)\s*</div>',
        r"\1",
        html,
        flags=re.IGNORECASE,
    )

    def _wrap_table(match: re.Match) -> str:
        attrs = (match.group(1) or "").strip()
        body = match.group(2)

        if "lesson-data-table" not in attrs:
            if 'class="' in attrs:
                attrs = attrs.replace('class="', 'class="lesson-data-table ', 1)
            elif attrs:
                attrs = f'{attrs} class="lesson-data-table"'
            else:
                attrs = 'class="lesson-data-table"'

        if "width:max-content" not in attrs:
            if 'style="' in attrs:
                attrs = re.sub(
                    r'style="([^"]*)"',
                    lambda m: f'style="{m.group(1)};{_TABLE_STYLE}"',
                    attrs,
                    count=1,
                )
            else:
                attrs = f'{attrs} style="{_TABLE_STYLE}"'.strip()

        attrs_str = f" {attrs}" if attrs else ""
        return (
            f'<div class="lesson-table-wrap" style="{_TABLE_WRAP_STYLE}">'
            f"<table{attrs_str}>{body}</table></div>"
        )

    return re.sub(
        r"<table([^>]*)>([\s\S]*?)</table>",
        _wrap_table,
        html,
        flags=re.IGNORECASE,
    )


def _convert_p_wrapped_tables(text: str) -> str:
    """Таблицы, где каждая строка обёрнута в <p>| ... |</p> (типичный вывод LLM)."""

    def _replace_multiline(block_match: re.Match) -> str:
        rows = [
            line.strip()
            for line in block_match.group(1).splitlines()
            if line.strip().startswith("|")
        ]
        html = _pipe_rows_to_html(rows)
        return html or block_match.group(0)

    text = _P_MULTILINE_TABLE.sub(_replace_multiline, text)

    def _replace(block_match: re.Match) -> str:
        rows = re.findall(r"<p>\s*(\|[^<]+\|)\s*</p>", block_match.group(1), re.I)
        html = _pipe_rows_to_html(rows)
        return html or block_match.group(0)

    return _P_WRAPPED_TABLE_BLOCK.sub(_replace, text)


def _normalize_br_separated_tables(text: str) -> str:
    """Заменяет |...|<br> на переносы строк для последующего разбора таблицы."""
    text = re.sub(r"\|\s*<br\s*/?>", "|\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>\s*(?=\|)", "\n", text, flags=re.IGNORECASE)
    return text


def convert_markdown_tables(text: str) -> str:
    """Конвертирует markdown pipe-таблицы в HTML <table>."""
    text = _convert_p_wrapped_tables(text)
    text = _normalize_br_separated_tables(text)

    def _replace(match: re.Match) -> str:
        block = match.group(1).strip()
        rows = [line for line in block.splitlines() if line.strip().startswith("|")]
        html = _pipe_rows_to_html(rows)
        return html or match.group(0)

    return _TABLE_PATTERN.sub(_replace, text)


def enhance_content(content: str) -> str:
    """Чинит LaTeX и markdown-таблицы внутри HTML или plain text."""
    if not content:
        return content

    protected, blocks = _protect_blocks(content)
    protected = convert_latex(protected)
    protected = convert_markdown_tables(protected)
    protected = _beautify_tables(protected)
    return _restore_blocks(protected, blocks)


def render_markdown_to_html(content: str) -> str:
    """Полная конвертация markdown → HTML (заголовки, списки, таблицы, LaTeX)."""
    if not content:
        return content

    protected, blocks = _protect_blocks(content)
    protected = convert_latex(protected)
    try:
        html_out = markdown.markdown(
            protected,
            extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
        )
    except Exception as exc:
        logger.warning("markdown.markdown не удался: %s", exc)
        html_out = protected.replace("\n", "<br>\n")
    html_out = _beautify_tables(html_out)
    return _restore_blocks(html_out, blocks)
