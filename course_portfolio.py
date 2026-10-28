"""
Портфель курсов ученика: несколько слотов + зеркало активного в корне state.

Корень ``learning`` / ``course_plan`` / ``lesson_content_cache`` / ``control_tasks``
остаётся рабочим слотом. ``state['courses'][id]`` — сохранённые копии.
"""

from __future__ import annotations

import copy
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

_MIRROR_KEYS = (
    "learning",
    "course_plan",
    "lesson_content_cache",
    "control_tasks",
)


def empty_learning() -> dict[str, Any]:
    return {
        "current_course": "",
        "current_section": "",
        "current_topic": "",
        "current_lesson": "",
        "completed_lessons": [],
        "visited_lessons": [],
        "lesson_pass_mode": {},
        "offtopic_count": {},
        "lesson_scores": {},
        "lesson_attempts": {},
        "lesson_completion_status": {},
        "control_task_bypass": {},
        "questions_count": {},
        "average_score": 0,
        "total_assessments": 0,
        "total_score": 0,
        "course_progress_percent": 0,
    }


def empty_plan() -> dict[str, Any]:
    return {
        "id": "",
        "title": "",
        "description": "",
        "total_duration_minutes": 0,
        "sections": [],
    }


def _now() -> str:
    return datetime.now().isoformat()


def _slot_from_mirror(state: dict, course_id: str) -> dict[str, Any]:
    plan = state.get("course_plan") or {}
    learning = state.get("learning") or {}
    title = plan.get("title") or course_id or "Курс"
    source = plan.get("source") or "catalog"
    status = "completed" if _looks_completed(state) else "active"
    meta = {
            "course_id": course_id,
            "title": title,
            "source": source,
            "status": status,
            "updated_at": _now(),
        }
    if plan.get("domain_override"):
        meta["domain_override"] = True
    return {
        "meta": meta,
        "learning": copy.deepcopy(learning),
        "course_plan": copy.deepcopy(plan),
        "lesson_content_cache": copy.deepcopy(
            state.get("lesson_content_cache") or {}
        ),
        "control_tasks": copy.deepcopy(state.get("control_tasks") or {}),
    }


def _looks_completed(state: dict) -> bool:
    plan = state.get("course_plan") or {}
    if not (plan.get("sections") or []):
        return False
    learning = state.get("learning") or {}
    percent = learning.get("course_progress_percent") or 0
    return percent >= 99.9


def _clear_mirror(state: dict) -> None:
    state["learning"] = empty_learning()
    state["course_plan"] = empty_plan()
    state["lesson_content_cache"] = {}
    state["control_tasks"] = {}


def _apply_slot(state: dict, slot: dict) -> None:
    state["learning"] = copy.deepcopy(slot.get("learning") or empty_learning())
    state["course_plan"] = copy.deepcopy(slot.get("course_plan") or empty_plan())
    state["lesson_content_cache"] = copy.deepcopy(
        slot.get("lesson_content_cache") or {}
    )
    state["control_tasks"] = copy.deepcopy(slot.get("control_tasks") or {})


def migrate_state(state: dict) -> bool:
    """
    Приводит state к портфелю. Возвращает True, если что-то изменилось.
    """
    changed = False
    if "courses" not in state or not isinstance(state.get("courses"), dict):
        state["courses"] = {}
        changed = True
    if "active_course_id" not in state:
        state["active_course_id"] = ""
        changed = True
    if "control_tasks" not in state:
        state["control_tasks"] = {}
        changed = True
    if "lesson_content_cache" not in state:
        state["lesson_content_cache"] = {}
        changed = True

    plan = state.get("course_plan") or {}
    learning = state.get("learning") or {}
    cid = (
        (plan.get("id") or "").strip()
        or (learning.get("current_course") or "").strip()
    )
    if cid and cid not in state["courses"]:
        slot = _slot_from_mirror(state, cid)
        slot["meta"]["created_at"] = _now()
        state["courses"][cid] = slot
        state["active_course_id"] = cid
        changed = True
        logger.info("Миграция портфеля: слот %s из текущего курса", cid)
    elif cid and not state.get("active_course_id"):
        state["active_course_id"] = cid
        changed = True
    return changed


def snapshot_active(state: dict) -> None:
    """Пишет зеркало в ``courses[active_course_id]``."""
    cid = (state.get("active_course_id") or "").strip()
    plan = state.get("course_plan") or {}
    if not cid:
        cid = (plan.get("id") or "").strip()
        if cid:
            state["active_course_id"] = cid
    if not cid:
        return
    existing = state.setdefault("courses", {}).get(cid, {})
    slot = _slot_from_mirror(state, cid)
    created = (existing.get("meta") or {}).get("created_at")
    slot["meta"]["created_at"] = created or _now()
    # D7: не терять пометку «вне области» при каждом save_state
    if (existing.get("meta") or {}).get("domain_override"):
        slot["meta"]["domain_override"] = True
    if (existing.get("meta") or {}).get("status") == "completed":
        slot["meta"]["status"] = "completed"
    state["courses"][cid] = slot


def list_user_courses(state: dict) -> list[dict[str, Any]]:
    """Список слотов для UI (без тяжёлых планов)."""
    snapshot_active(state)
    active = state.get("active_course_id") or ""
    rows = []
    for cid, slot in (state.get("courses") or {}).items():
        meta = slot.get("meta") or {}
        learning = slot.get("learning") or {}
        rows.append(
            {
                "course_id": cid,
                "title": meta.get("title") or cid,
                "source": meta.get("source") or "catalog",
                "status": meta.get("status") or "active",
                "is_active": cid == active,
                "domain_override": bool(meta.get("domain_override")),
                "current_lesson": learning.get("current_lesson") or "",
                "current_section": learning.get("current_section") or "",
                "current_topic": learning.get("current_topic") or "",
                "progress_percent": learning.get("course_progress_percent") or 0,
            }
        )
    rows.sort(key=lambda r: (not r["is_active"], r["title"].lower()))
    return rows


def switch_course(state: dict, course_id: str) -> bool:
    """Снапшот текущего и загрузка другого слота в зеркало."""
    if course_id not in (state.get("courses") or {}):
        logger.warning("switch_course: нет слота %s", course_id)
        return False
    snapshot_active(state)
    _apply_slot(state, state["courses"][course_id])
    state["active_course_id"] = course_id
    learning = state.setdefault("learning", empty_learning())
    learning["current_course"] = course_id
    snapshot_active(state)
    logger.info("Переключение на курс %s", course_id)
    return True


def delete_course(state: dict, course_id: str) -> bool:
    """Удаляет слот. Если удалили активный — грузит другой или пустое зеркало."""
    courses = state.get("courses") or {}
    if course_id not in courses:
        return False
    was_active = state.get("active_course_id") == course_id
    if not was_active:
        snapshot_active(state)
    del courses[course_id]
    state["courses"] = courses
    if was_active:
        remaining = next(iter(courses), None)
        if remaining:
            _apply_slot(state, courses[remaining])
            state["active_course_id"] = remaining
            learning = state.setdefault("learning", empty_learning())
            learning["current_course"] = remaining
            snapshot_active(state)
        else:
            state["active_course_id"] = ""
            _clear_mirror(state)
    logger.info("Удалён курс %s", course_id)
    return True


def begin_new_course(state: dict) -> None:
    """Сохраняет текущий курс и очищает зеркало под новый план."""
    snapshot_active(state)
    state["active_course_id"] = ""
    _clear_mirror(state)


def bind_new_plan(state: dict, course_plan: dict, source: str = "catalog") -> None:
    """Привязывает только что сохранённый план к активному слоту."""
    cid = (course_plan.get("id") or "").strip()
    if not cid:
        return
    state["active_course_id"] = cid
    learning = state.setdefault("learning", empty_learning())
    learning["current_course"] = cid
    snapshot_active(state)
    meta = state["courses"][cid].setdefault("meta", {})
    meta["title"] = course_plan.get("title") or cid
    meta["source"] = course_plan.get("source") or source
    meta["status"] = "active"
    meta["updated_at"] = _now()
    if "created_at" not in meta:
        meta["created_at"] = _now()
    # D7: курс вне области
    if course_plan.get("domain_override"):
        meta["domain_override"] = True


def mark_active_completed(state: dict) -> None:
    snapshot_active(state)
    cid = state.get("active_course_id") or ""
    if cid and cid in (state.get("courses") or {}):
        state["courses"][cid].setdefault("meta", {})["status"] = "completed"


def has_course(state: dict, course_id: str) -> bool:
    return course_id in (state.get("courses") or {})
