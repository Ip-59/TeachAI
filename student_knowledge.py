"""Что студент уже проходил — для заданий, а не для угадывания темы.

Перечень понятий строится вместе с уроком и лежит в кэше урока.
В профиль как пройденные он попадает только при переходе к следующему
уроку (верное КЗ, «не требуется», «Продолжить с текущей оценкой» и т.п.).
"""

from __future__ import annotations

import logging
from typing import Any

from lesson_outline import iter_plan_lessons

_STORE = "lesson_concepts"


def _clean_concepts(concepts: list) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for item in concepts or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("title") or item.get("name") or "").strip()
        brief = str(
            item.get("description") or item.get("brief_description") or ""
        ).strip()
        if name:
            short = brief[:240]
            cleaned.append(
                {
                    "title": name,
                    "name": name,
                    "description": short,
                    "brief": short,
                }
            )
    return cleaned


def _valid_lesson_id(lesson_full_id: str) -> bool:
    return bool(
        lesson_full_id and not lesson_full_id.endswith(":") and "::" not in lesson_full_id
    )


def concepts_from_cache(state_manager: Any, lesson_full_id: str) -> list[dict[str, str]]:
    """Понятия, сохранённые вместе с текстом урока."""
    cache = (state_manager.state.get("lesson_content_cache") or {}).get(lesson_full_id) or {}
    return _clean_concepts(cache.get("concepts") or [])


def attach_concepts_to_lesson(
    state_manager: Any, lesson_full_id: str, concepts: list
) -> list[dict[str, str]]:
    """Кладёт перечень в кэш урока. В профиль как пройденные не пишет."""
    cleaned = _clean_concepts(concepts)
    if not _valid_lesson_id(lesson_full_id):
        return cleaned
    cache = state_manager.state.setdefault("lesson_content_cache", {})
    entry = cache.setdefault(lesson_full_id, {})
    entry["concepts"] = cleaned
    state_manager.save_state()
    return cleaned


def lesson_counts_as_studied(state_manager: Any, lesson_full_id: str) -> bool:
    """Урок засчитан тестом (>40%) или принудительным переходом."""
    learning = state_manager.state.get("learning") or {}
    if (learning.get("lesson_completion_status") or {}).get(lesson_full_id):
        return True
    score = (learning.get("lesson_scores") or {}).get(lesson_full_id, 0)
    try:
        return float(score) > 40
    except (TypeError, ValueError):
        return False


def mark_lesson_concepts_passed(state_manager: Any, lesson_full_id: str) -> None:
    """Переносит понятия из кэша урока в профиль как пройденные."""
    concepts = concepts_from_cache(state_manager, lesson_full_id)
    if concepts:
        remember_lesson_concepts(state_manager, lesson_full_id, concepts)


def ensure_lesson_concepts(
    state_manager: Any,
    content_generator: Any,
    lesson_full_id: str,
    lesson_content: str,
    lesson_data: dict,
    communication_style: str,
    course_context: dict | None,
) -> list:
    """Возвращает понятия урока, один раз спросив модель, если в кэше их нет."""
    existing = concepts_from_cache(state_manager, lesson_full_id)
    if not existing and content_generator is not None:
        try:
            existing = content_generator.generate_concepts(
                lesson_content=lesson_content,
                communication_style=communication_style,
                lesson_data=lesson_data,
                course_context=course_context,
            )
        except Exception as exc:
            logging.getLogger(__name__).error(
                "Не удалось составить понятия урока %s: %s", lesson_full_id, exc
            )
            existing = []
        if existing:
            existing = attach_concepts_to_lesson(
                state_manager, lesson_full_id, existing
            )
    if existing and lesson_counts_as_studied(state_manager, lesson_full_id):
        remember_lesson_concepts(state_manager, lesson_full_id, existing)
    return existing


def remember_lesson_concepts(
    state_manager: Any, lesson_full_id: str, concepts: list
) -> None:
    """Сохраняет понятия урока в профиль."""
    if not _valid_lesson_id(lesson_full_id):
        return
    cleaned = _clean_concepts(concepts)
    learning = state_manager.state.setdefault("learning", {})
    store = learning.setdefault(_STORE, {})
    store[lesson_full_id] = cleaned
    state_manager.save_state()


def knowledge_brief_ru(state_manager: Any, current_full_id: str) -> str:
    """Текст для промпта: место в курсе и что было до этого урока."""
    plan = state_manager.get_course_plan() or {}
    lessons = list(iter_plan_lessons(plan))
    prior: list[dict[str, Any]] = []
    index = 0
    for number, item in enumerate(lessons, start=1):
        if item["full_id"] == current_full_id:
            index = number
            break
        prior.append(item)
    total = len(lessons)
    stored = (state_manager.state.get("learning") or {}).get(_STORE) or {}
    place = (
        f"Место в курсе: урок {index} из {total}."
        if index
        else "Место в курсе: текущий урок не найден в плане."
    )
    lines = [
        place,
        "Ниже только то, что студент уже проходил до этого урока. "
        "Этого и текста текущего урока достаточно, чтобы решить, "
        "какой приём можно требовать. Новый синтаксис из будущих уроков нельзя.",
    ]
    if not prior:
        lines.append(
            "Предыдущих уроков нет: студент ещё не изучал, как писать код."
        )
        return "\n".join(lines)
    for item in prior:
        concepts = stored.get(item["full_id"]) or []
        names = [
            str(c.get("name") or c.get("title") or "").strip()
            for c in concepts
            if isinstance(c, dict)
        ]
        names = [name for name in names if name]
        line = f"- «{item['lesson_title']}»"
        if names:
            line += ": пройденные понятия " + ", ".join(names)
        else:
            line += ": понятия ещё не засчитаны"
        lines.append(line)
    return "\n".join(lines)
