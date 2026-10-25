"""
Карта уроков курса и переход между ними.

Политика доступа: завершённые + текущий + первый незавершённый (следующий).
"""

from __future__ import annotations

import html
import logging
from typing import Any, Iterator

import ipywidgets as widgets

logger = logging.getLogger(__name__)


def iter_plan_lessons(course_plan: dict) -> Iterator[dict[str, Any]]:
    """Плоский список уроков в порядке плана."""
    for section in course_plan.get("sections") or []:
        section_id = section.get("id") or ""
        section_title = section.get("title") or "Раздел"
        for topic in section.get("topics") or []:
            topic_id = topic.get("id") or ""
            topic_title = topic.get("title") or "Тема"
            for lesson in topic.get("lessons") or []:
                lesson_id = lesson.get("id") or ""
                if not (section_id and topic_id and lesson_id):
                    continue
                yield {
                    "section_id": section_id,
                    "section_title": section_title,
                    "topic_id": topic_id,
                    "topic_title": topic_title,
                    "lesson_id": lesson_id,
                    "lesson_title": lesson.get("title") or "Урок",
                    "description": lesson.get("description") or "",
                    "keywords": list(lesson.get("keywords") or []),
                    "full_id": f"{section_id}:{topic_id}:{lesson_id}",
                }


def _current_full_id(state_manager) -> str:
    learning = state_manager.state.get("learning") or {}
    return (
        f"{learning.get('current_section', '')}:"
        f"{learning.get('current_topic', '')}:"
        f"{learning.get('current_lesson', '')}"
    )


def first_incomplete_id(state_manager, course_plan: dict) -> str | None:
    """Первый незавершённый урок по плану (следующий доступный)."""
    for item in iter_plan_lessons(course_plan):
        if not state_manager.is_lesson_completed(item["full_id"]):
            return item["full_id"]
    return None


def lesson_access_status(
    state_manager, item: dict[str, Any], current_id: str, next_id: str | None
) -> str:
    """
    Returns:
        ``completed`` | ``current`` | ``next`` | ``locked``.
    """
    full_id = item["full_id"]
    if state_manager.is_lesson_completed(full_id):
        return "completed"
    if full_id == current_id:
        return "current"
    if next_id and full_id == next_id:
        return "next"
    return "locked"


def is_lesson_accessible(
    state_manager, section_id: str, topic_id: str, lesson_id: str
) -> bool:
    """Можно ли открыть урок при политике completed ∪ current ∪ next."""
    course_plan = state_manager.get_course_plan()
    full_id = f"{section_id}:{topic_id}:{lesson_id}"
    current_id = _current_full_id(state_manager)
    next_id = first_incomplete_id(state_manager, course_plan)
    for item in iter_plan_lessons(course_plan):
        if item["full_id"] == full_id:
            return lesson_access_status(state_manager, item, current_id, next_id) != "locked"
    return False


def build_outline_widget(
    lesson_interface, section_id: str, topic_id: str, lesson_id: str
) -> widgets.Widget:
    """Accordion содержания курса + Вперёд/Назад по доступным урокам."""
    sm = lesson_interface.state_manager
    course_plan = sm.get_course_plan()
    items = list(iter_plan_lessons(course_plan))
    current_id = f"{section_id}:{topic_id}:{lesson_id}"
    next_id = first_incomplete_id(sm, course_plan)

    if not items:
        return widgets.HTML(value="<p>План курса пуст.</p>")

    sections_order: list[str] = []
    by_section: dict[str, list[dict]] = {}
    titles: dict[str, str] = {}
    for item in items:
        sid = item["section_id"]
        if sid not in by_section:
            sections_order.append(sid)
            titles[sid] = item["section_title"]
            by_section[sid] = []
        by_section[sid].append(item)

    accordion_children = []
    selected_index = 0
    for idx, sid in enumerate(sections_order):
        rows = []
        last_topic = None
        for item in by_section[sid]:
            if item["topic_id"] != last_topic:
                last_topic = item["topic_id"]
                rows.append(
                    widgets.HTML(
                        value=(
                            "<div style='font-weight:600;margin:8px 0 4px 0;color:#495057;'>"
                            f"{html.escape(item['topic_title'])}</div>"
                        )
                    )
                )
            status = lesson_access_status(sm, item, current_id, next_id)
            rows.append(_lesson_row(lesson_interface, item, status))
            if item["full_id"] == current_id:
                selected_index = idx
        accordion_children.append(
            widgets.VBox(rows, layout=widgets.Layout(padding="4px 8px"))
        )

    accordion = widgets.Accordion(children=accordion_children)
    for i, sid in enumerate(sections_order):
        accordion.set_title(i, titles[sid])
    accordion.selected_index = selected_index

    nav = _prev_next_bar(lesson_interface, items, current_id, sm, next_id)
    hint = widgets.HTML(
        value=(
            "<div style='color:#6c757d;font-size:13px;margin:4px 0 8px 0;'>"
            "Открыты завершённые уроки, текущий и следующий незавершённый."
            "</div>"
        )
    )
    return widgets.VBox(
        [
            widgets.HTML(value="<h3 style='margin:8px 0 4px 0;'>Содержание курса</h3>"),
            hint,
            nav,
            accordion,
        ],
        layout=widgets.Layout(
            width="100%",
            border="1px solid #dee2e6",
            border_radius="6px",
            padding="8px 12px",
            margin="8px 0 16px 0",
        ),
    )


def open_lesson(lesson_interface, section_id: str, topic_id: str, lesson_id: str) -> None:
    """Переход к уроку, если политика доступа позволяет."""
    if not is_lesson_accessible(lesson_interface.state_manager, section_id, topic_id, lesson_id):
        logger.warning(
            "Отказ в переходе к %s:%s:%s — урок закрыт политикой доступа",
            section_id,
            topic_id,
            lesson_id,
        )
        return

    lesson_interface.state_manager.update_learning_progress(
        section=section_id, topic=topic_id, lesson=lesson_id
    )
    try:
        lesson_interface.system_logger.log_activity(
            action_type="lesson_jump",
            details={
                "section_id": section_id,
                "topic_id": topic_id,
                "lesson_id": lesson_id,
            },
        )
    except Exception as exc:
        logger.debug("Не удалось записать lesson_jump: %s", exc)

    from IPython.display import clear_output, display

    clear_output(wait=True)
    display(lesson_interface.show_lesson(section_id, topic_id, lesson_id))


def _lesson_row(lesson_interface, item: dict, status: str) -> widgets.Widget:
    marks = {
        "completed": "✅",
        "current": "▶",
        "next": "📘",
        "locked": "🔒",
    }
    labels = {
        "completed": "завершён",
        "current": "текущий",
        "next": "следующий",
        "locked": "закрыт",
    }
    button = widgets.Button(
        description=f"{marks[status]} {item['lesson_title']}",
        tooltip=labels[status],
        disabled=status == "locked",
        button_style="success"
        if status == "completed"
        else ("info" if status == "current" else ("warning" if status == "next" else "")),
        layout=widgets.Layout(width="100%", margin="2px 0"),
    )
    if status != "locked":
        sid, tid, lid = item["section_id"], item["topic_id"], item["lesson_id"]

        def _on_click(_b, s=sid, t=tid, l=lid):
            open_lesson(lesson_interface, s, t, l)

        button.on_click(_on_click)

    return button


def _prev_next_bar(lesson_interface, items, current_id, sm, next_id) -> widgets.HBox:
    statuses = [
        lesson_access_status(sm, item, current_id, next_id) for item in items
    ]
    index = next((i for i, it in enumerate(items) if it["full_id"] == current_id), 0)

    prev_item = None
    for i in range(index - 1, -1, -1):
        if statuses[i] != "locked":
            prev_item = items[i]
            break
    next_item = None
    for i in range(index + 1, len(items)):
        if statuses[i] != "locked":
            next_item = items[i]
            break

    prev_btn = widgets.Button(
        description="← Предыдущий урок",
        disabled=prev_item is None,
        layout=widgets.Layout(width="auto", margin="4px"),
    )
    next_btn = widgets.Button(
        description="Следующий урок →",
        disabled=next_item is None,
        layout=widgets.Layout(width="auto", margin="4px"),
    )
    if prev_item:
        p = prev_item
        prev_btn.on_click(
            lambda _b, s=p["section_id"], t=p["topic_id"], l=p["lesson_id"]: open_lesson(
                lesson_interface, s, t, l
            )
        )
    if next_item:
        n = next_item
        next_btn.on_click(
            lambda _b, s=n["section_id"], t=n["topic_id"], l=n["lesson_id"]: open_lesson(
                lesson_interface, s, t, l
            )
        )
    return widgets.HBox([prev_btn, next_btn])
