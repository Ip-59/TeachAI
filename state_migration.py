"""Миграция state.json к схеме D1–D8.

Вызывается при загрузке состояния. Идемпотентна: повторный вызов безвреден.
Старые файлы без visited_lessons / lesson_pass_mode / offtopic_count приводятся
к новой схеме, прогресс ученика не обнуляется.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 2  # 1 = до пакета 3; 2 = D1–D8


def ensure_learning_fields(state: dict) -> bool:
    """Гарантирует наличие новых ключей. Не трогает смысл completed_lessons."""
    changed = False
    learning = state.setdefault("learning", {})
    for key, blank in (
        ("visited_lessons", list),
        ("lesson_pass_mode", dict),
        ("offtopic_count", dict),
        ("completed_lessons", list),
        ("lesson_completion_status", dict),
    ):
        if key not in learning:
            learning[key] = blank()
            changed = True
    return changed


def migrate_control_task_attempts(state: dict) -> bool:
    changed = False
    for lid, rec in list((state.get("control_tasks") or {}).items()):
        if not isinstance(rec, dict):
            continue
        if "attempts" not in rec:
            attempt = {
                "is_correct": bool(rec.get("is_correct")),
                "timestamp": rec.get("completed_at") or "",
                "with_hint": bool(rec.get("with_hint", False)),
            }
            rec["attempts"] = [attempt]
            rec.setdefault("best_is_correct", bool(rec.get("is_correct")))
            changed = True
        else:
            if "best_is_correct" not in rec:
                rec["best_is_correct"] = bool(rec.get("is_correct"))
                changed = True
    return changed


def migrate_visited_and_completed(state: dict, is_lesson_completed) -> bool:
    """Разделяет старый completed_lessons (открытые) на visited + реально пройденные."""
    learning = state.setdefault("learning", {})
    if learning.get("_schema_version", 1) >= SCHEMA_VERSION:
        return False

    visited = learning.setdefault("visited_lessons", [])
    completed = list(learning.get("completed_lessons") or [])
    for lid in completed:
        if lid not in visited:
            visited.append(lid)

    kept = [lid for lid in completed if is_lesson_completed(lid)]
    learning["completed_lessons"] = kept

    modes = learning.setdefault("lesson_pass_mode", {})
    status = learning.get("lesson_completion_status") or {}
    for lid, done in status.items():
        if not done or lid in modes:
            continue
        ct = (state.get("control_tasks") or {}).get(lid) or {}
        if ct.get("is_correct") or ct.get("best_is_correct"):
            modes[lid] = "normal"
        else:
            modes[lid] = "forced"

    learning["_schema_version"] = SCHEMA_VERSION
    logger.info(
        "Миграция state schema=%s: visited=%d, completed=%d (было %d)",
        SCHEMA_VERSION,
        len(visited),
        len(kept),
        len(completed),
    )
    return True


def migrate_learning_state(state: dict, *, is_lesson_completed=None) -> bool:
    changed = ensure_learning_fields(state)
    changed = migrate_control_task_attempts(state) or changed
    if is_lesson_completed is not None:
        changed = migrate_visited_and_completed(state, is_lesson_completed) or changed
    return changed
