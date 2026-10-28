"""
Компактный UI вопросов теста (RadioButtons) и снимок ответов.

Вынесено из assessment_interface.py, чтобы не раздувать координатор.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

import ipywidgets as widgets

logger = logging.getLogger(__name__)


def collect_answers_from_widgets(
    question_widgets: Dict[int, widgets.RadioButtons],
    questions: Optional[List[Any]],
    fallback_answers: Optional[List[Any]] = None,
) -> List[Any]:
    """
    Снимает ответы с RadioButtons.

    ``observe`` ненадёжен для первого выбора; источник истины — ``.value``.

    Args:
        question_widgets: Индекс вопроса → RadioButtons.
        questions: Список вопросов (для длины).
        fallback_answers: Резерв, если виджет недоступен.

    Returns:
        Список значений вариантов или None для неотвеченных.
    """
    fallback = fallback_answers or []
    n = len(questions or [])
    answers: List[Any] = []
    for i in range(n):
        widget = question_widgets.get(i)
        if widget is not None and widget.value is not None:
            answers.append(widget.value)
        elif i < len(fallback) and fallback[i] is not None:
            answers.append(fallback[i])
        else:
            answers.append(None)
    logger.debug("Снимок ответов теста: %s", answers)
    return answers


def build_compact_questions_interface(
    questions: List[dict],
    on_answer_change: Optional[Callable[[int, Any], None]] = None,
) -> tuple[widgets.VBox, Dict[int, widgets.RadioButtons]]:
    """
    Строит компактный список вопросов с RadioButtons.

    Args:
        questions: Вопросы с полями ``text`` и ``options``.
        on_answer_change: Опционально ``(index, value)`` при смене выбора.

    Returns:
        (контейнер VBox, словарь виджетов по индексу).
    """
    questions_widgets: List[widgets.Widget] = []
    question_widgets: Dict[int, widgets.RadioButtons] = {}

    for i, question in enumerate(questions):
        if not isinstance(question, dict):
            logger.error("Вопрос %s не является словарем: %s", i + 1, question)
            continue

        if "text" not in question:
            logger.error("Вопрос %s не содержит поле 'text': %s", i + 1, question)
            continue

        question_title_widget = widgets.HTML(
            value=(
                f"<div style='font-size: 18px; font-weight: bold; color: #212529; "
                f"margin-bottom: 4px; padding-bottom: 3px; border-bottom: 1px solid #dee2e6; "
                f"line-height: 1.3;'>Вопрос {i + 1}: {question['text']}</div>"
            ),
            layout=widgets.Layout(margin="0px"),
        )

        if "options" not in question or not isinstance(question["options"], list):
            logger.error(
                "Вопрос %s не содержит корректные варианты ответов: %s",
                i + 1,
                question,
            )
            continue

        options = question["options"]
        radio_buttons = widgets.RadioButtons(
            options=[(option, j + 1) for j, option in enumerate(options)],
            value=None,  # без предвыбранного варианта: иначе неотвеченный вопрос засчитывается
            description="",
            disabled=False,
            layout=widgets.Layout(margin="4px 10px", width="100%"),
            style={"description_width": "0px"},
        )

        def create_answer_handler(question_index: int):
            def handle_answer_change(change):
                if change["type"] == "change" and change["name"] == "value":
                    if change["new"] is not None and on_answer_change is not None:
                        on_answer_change(question_index, change["new"])

            return handle_answer_change

        radio_buttons.observe(create_answer_handler(i), names="value")
        question_widgets[i] = radio_buttons

        question_container = widgets.VBox(
            [question_title_widget, radio_buttons],
            layout=widgets.Layout(
                border="2px solid #e9ecef",
                border_radius="8px",
                padding="8px",
                margin="4px 0",
                background_color="#ffffff",
            ),
        )
        questions_widgets.append(question_container)

    container = widgets.VBox(
        questions_widgets, layout=widgets.Layout(margin="0px", gap="2px")
    )
    return container, question_widgets
