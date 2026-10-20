"""Сборка курса по названию, которое ввёл ученик (не из каталога)."""

from __future__ import annotations

import re
import time
from typing import Any


_TITLE_MIN = 3
_TITLE_MAX = 120
_DESC_MAX = 2000


def slugify_course_title(title: str) -> str:
    """Короткий id-фрагмент из названия (латиница и кириллица)."""
    text = (title or "").strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^\w\-]+", "", text, flags=re.UNICODE)
    text = text.strip("-")[:40]
    return text or "course"


def validate_custom_course(title: str, description: str = "") -> str | None:
    """
    Проверяет поля своего курса.

    Returns:
        Текст ошибки или None, если поля корректны.
    """
    name = (title or "").strip()
    if len(name) < _TITLE_MIN:
        return f"Введите название курса (не короче {_TITLE_MIN} символов)."
    if len(name) > _TITLE_MAX:
        return f"Название слишком длинное (максимум {_TITLE_MAX} символов)."
    desc = (description or "").strip()
    if len(desc) > _DESC_MAX:
        return f"Описание слишком длинное (максимум {_DESC_MAX} символов)."
    return None


def build_custom_course(title: str, description: str = "") -> dict[str, Any]:
    """
    Синтетический объект курса для ``generate_course_plan``.

    Не пишется в ``courses.json``.
    """
    name = title.strip()
    desc = (description or "").strip()
    if not desc:
        desc = f"Персональный курс по теме «{name}», план строится под запрос ученика."
    suffix = hex(int(time.time()))[-6:]
    course_id = f"custom_{slugify_course_title(name)}_{suffix}"
    return {
        "id": course_id,
        "title": name,
        "description": desc,
        "prerequisites": "Не указаны",
        "difficulty": "По запросу ученика",
        "keywords": [],
        "source": "user",
    }
