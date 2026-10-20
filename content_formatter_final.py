"""Форматирование markdown-урока: код-блоки + канон content_renderer."""

from __future__ import annotations

import html as html_module
import logging
import re
from typing import List, Tuple

from content_renderer import enhance_content, render_markdown_to_html

_CODE_PLACEHOLDER_TAG = "TEACHAI_CODE_BLOCK"
_CODE_FENCE = re.compile(
    r"```([A-Za-z0-9_+\-]*)[ \t]*\r?\n(.*?)```",
    re.DOTALL,
)


def code_block_placeholder(index: int) -> str:
    """HTML-комментарий — markdown его не ломает (в отличие от __PLACEHOLDER__)."""
    return f"<!--{_CODE_PLACEHOLDER_TAG}_{index}-->"


def content_has_unresolved_code_placeholders(content: str) -> bool:
    """True, если в HTML остались заглушки вместо блоков кода."""
    if not content:
        return False
    if "<pre>" in content and "CODE_BLOCK_" not in content:
        return False
    return bool(
        re.search(
            rf"(?:<!--{_CODE_PLACEHOLDER_TAG}_\d+-->|<strong>CODE_BLOCK_\d+</strong>|__CODE_BLOCK_\d+__)",
            content,
            re.IGNORECASE,
        )
    )


class ContentFormatterFinal:
    """Собирает HTML урока: fences → pre/code, остальное через канон markdown."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.base_css = ""

    def format_lesson_content(self, raw_content: str, lesson_title: str = "") -> str:
        """
        Форматирует контент урока для показа в Jupyter.

        Args:
            raw_content: Сырой markdown от LLM.
            lesson_title: Название урока (для логов).
        """
        try:
            self.logger.info("Форматирование контента урока: %s", lesson_title)
            cleaned = self._clean_content(raw_content)
            with_placeholders, code_blocks = self._extract_code_blocks(cleaned)
            processed = render_markdown_to_html(with_placeholders)
            restored = self._restore_code_blocks(processed, code_blocks)
            enhanced = enhance_content(restored)
            enhanced = self._clean_final_content(enhanced)
            return self._create_final_html(enhanced, lesson_title)
        except Exception as exc:
            self.logger.error("Ошибка при форматировании контента: %s", exc)
            return self._create_error_html(raw_content, str(exc))

    def _clean_content(self, content: str) -> str:
        """Сжимает лишние пустые строки. HTML-теги не вырезает."""
        content = content or ""
        content = re.sub(r"\n{3,}", "\n\n", content)
        return content.strip()

    def _extract_code_blocks(self, content: str) -> Tuple[str, List[str]]:
        code_blocks: List[str] = []

        def save_code_block(match: re.Match) -> str:
            language = (match.group(1) or "").strip() or "text"
            formatted_code = self._format_code(match.group(2), language)
            html_block = (
                f'<pre><code class="language-{html_module.escape(language)}">'
                f"{formatted_code}</code></pre>"
            )
            code_blocks.append(html_block)
            return code_block_placeholder(len(code_blocks) - 1)

        replaced = _CODE_FENCE.sub(save_code_block, content)
        return replaced, code_blocks

    def _format_code(self, code: str, language: str = "text") -> str:
        """Экранирует HTML, сохраняет пустые строки и отступы."""
        del language
        lines = code.replace("\r\n", "\n").split("\n")
        # Снимаем только общий хвостовой пустой ряд от fence, не внутренние пустые
        while lines and lines[-1] == "":
            lines.pop()
        formatted: List[str] = []
        for line in lines:
            cleaned = line.rstrip()
            escaped = html_module.escape(cleaned, quote=False)
            if cleaned.strip().startswith("#"):
                formatted.append(f'<span class="comment">{escaped}</span>')
            else:
                formatted.append(escaped)
        return "\n".join(formatted)

    def _restore_code_blocks(self, content: str, code_blocks: List[str]) -> str:
        for index, code_block in enumerate(code_blocks):
            for placeholder in (
                code_block_placeholder(index),
                f"__CODE_BLOCK_{index}__",
            ):
                content = content.replace(placeholder, code_block)
            content = re.sub(
                rf"<p>\s*<strong>CODE_BLOCK_{index}</strong>\s*</p>",
                code_block,
                content,
                flags=re.IGNORECASE,
            )
            content = re.sub(
                rf"<strong>CODE_BLOCK_{index}</strong>",
                code_block,
                content,
                flags=re.IGNORECASE,
            )
        return content

    def _clean_final_content(self, content: str) -> str:
        content = re.sub(
            r"<p>\s*(<pre><code[\s\S]*?</code></pre>)\s*</p>",
            r"\1",
            content,
            flags=re.IGNORECASE,
        )
        return re.sub(r"<p>\s*</p>", "", content)

    def _create_final_html(self, content: str, lesson_title: str) -> str:
        del lesson_title
        return f'<div class="lesson-content">\n{self.base_css}\n{content}\n</div>'

    def _create_error_html(self, original_content: str, error_message: str) -> str:
        safe_error = html_module.escape(error_message)
        safe_original = html_module.escape(original_content or "")
        return (
            '<div class="lesson-content">'
            "<div class='warning'><h3>Ошибка форматирования</h3>"
            f"<p>Произошла ошибка при форматировании контента: {safe_error}</p>"
            f"<p>Оригинальный контент:</p><pre>{safe_original}</pre></div></div>"
        )
