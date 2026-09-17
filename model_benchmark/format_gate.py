"""Автопроверка формы ответа (format gate) для уроков."""

from __future__ import annotations

import re
from typing import Any


def check_lesson_format(text: str, rubric_gate: dict[str, Any]) -> dict[str, Any]:
    """
    Проверяет формальные признаки текста урока.

    Args:
        text: Сырой ответ модели.
        rubric_gate: Секция format_gate из rubric.json.

    Returns:
        Словарь с passed, reasons и флагами проверок.
    """
    reasons: list[str] = []
    content = text or ""
    min_chars = int(rubric_gate.get("min_chars", 800))

    checks = {
        "min_chars": len(content.strip()) >= min_chars,
        "markdown_heading": bool(re.search(r"(?m)^#{1,3}\s+\S", content)),
        "python_code_block": bool(
            re.search(r"```python\s*\n[\s\S]+?```", content, re.IGNORECASE)
        ),
    }

    if not checks["min_chars"]:
        reasons.append(f"текст короче {min_chars} символов")
    if rubric_gate.get("require_markdown_headings", True) and not checks[
        "markdown_heading"
    ]:
        reasons.append("нет markdown-заголовков")
    if rubric_gate.get("require_python_code_block", True) and not checks[
        "python_code_block"
    ]:
        reasons.append("нет блока ```python```")

    passed = len(reasons) == 0
    return {
        "passed": passed,
        "status": "ok" if passed else rubric_gate.get("on_fail", "format_fail"),
        "checks": checks,
        "reasons": reasons,
        "char_count": len(content.strip()),
    }
