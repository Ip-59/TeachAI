"""Локальные дата и время с часов компьютера.

Снятие делается штатным ``datetime.now().astimezone()`` в начале этапа.
Отладочные файлы для этого не используются.
"""

from __future__ import annotations

import logging
from datetime import datetime

_LOG = logging.getLogger("teachai.clock")

_WEEKDAYS = (
    "понедельник",
    "вторник",
    "среда",
    "четверг",
    "пятница",
    "суббота",
    "воскресенье",
)
_MONTHS = (
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)

_last_stage = ""
_last_moment: datetime | None = None


def read_clock() -> datetime:
    """Текущие локальные дата и время."""
    return datetime.now().astimezone()


def format_clock_ru(moment: datetime | None = None) -> str:
    """Человекочитаемая строка: день недели, дата, часы и минуты."""
    current = moment if moment is not None else read_clock()
    weekday = _WEEKDAYS[current.weekday()]
    month = _MONTHS[current.month - 1]
    return (
        f"{weekday}, {current.day} {month} {current.year}, "
        f"{current.strftime('%H:%M')}"
    )


def mark_stage(stage: str) -> str:
    """Снимает время в начале этапа и запоминает его.

    Args:
        stage: Имя этапа: старт, дашборд, урок, тест, вопрос, объяснение,
            примеры, контрольное.

    Returns:
        Строка времени для экрана и промпта.
    """
    global _last_stage, _last_moment
    _last_moment = read_clock()
    _last_stage = stage
    text = format_clock_ru(_last_moment)
    _LOG.info("Этап «%s»: %s", stage, text)
    return text


def latest_stage_clock() -> str:
    """Время последнего этапа. Если этап ещё не отмечался — новое чтение."""
    if _last_moment is None:
        return format_clock_ru(read_clock())
    return format_clock_ru(_last_moment)
