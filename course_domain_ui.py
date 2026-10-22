"""Предупреждение, если своя тема вне Python / AI/ML."""

from __future__ import annotations

import html
import logging
from typing import Any, Callable

import ipywidgets as widgets
from IPython.display import clear_output, display

from course_domain import DomainVerdict, classify_course_topic
from loading_indicators import make_wait_banner
from project_identity import PROJECT_FULL_TITLE, limitations_html_list

logger = logging.getLogger(__name__)


def _resolve_content_generator(setup: Any) -> Any | None:
    """ContentGenerator с setup или с engine после ленивой инициализации."""
    generator = getattr(setup, "content_generator", None)
    if generator is not None:
        return generator
    engine = getattr(setup, "engine", None)
    if engine is None:
        return None
    if not getattr(engine, "is_ready", False):
        try:
            if not engine.initialize():
                return None
        except Exception as exc:
            logger.warning("Не удалось инициализировать engine для проверки темы: %s", exc)
            return None
    generator = getattr(engine, "content_generator", None)
    if generator is not None:
        setup.content_generator = generator
        if getattr(engine, "interface", None) and getattr(
            engine.interface, "setup_interface", None
        ):
            engine.interface.setup_interface.content_generator = generator
    return generator


def _warning_html(title: str, verdict: DomainVerdict) -> str:
    safe_title = html.escape(title)
    safe_reason = html.escape(verdict.reason)
    return (
        "<div style='background:#fff3cd;border:1px solid #ffeaa7;border-radius:8px;"
        "padding:16px;margin:8px 0;'>"
        "<h3 style='margin:0 0 8px 0;color:#856404;'>Тема вне области TeachAI</h3>"
        f"<p style='margin:0 0 8px 0;'><strong>«{safe_title}»</strong> не относится "
        "к Python, анализу данных и машинному обучению.</p>"
        f"<p style='margin:0 0 8px 0;color:#856404;'>{safe_reason}</p>"
        "<p style='margin:0 0 4px 0;'>Можно выбрать другой курс из списка. "
        "Если всё же начать эту тему, <strong>не гарантируется</strong> корректность "
        "учебного материала в части:</p>"
        f"{limitations_html_list()}"
        f"<p style='margin:12px 0 0 0;font-size:13px;color:#6c757d;'>"
        f"{html.escape(PROJECT_FULL_TITLE)}</p>"
        "</div>"
    )


def _set_status(status_box: widgets.Box | None, widget: Any | None) -> None:
    """Один слот под формой: без Output/display — нет задвоений в Jupyter."""
    if status_box is None:
        if widget is not None:
            display(widget)
        return
    status_box.children = () if widget is None else (widget,)


def gate_custom_course(
    setup: Any,
    course: dict,
    user_profile: dict,
    start_course: Callable,
    switch_to_catalog: Callable[[], None],
    status_box: widgets.Box | None = None,
    output: widgets.Output | None = None,
) -> None:
    """
    Если тема в области — сразу старт. Иначе предупреждение и две кнопки.

    Args:
        setup: SetupInterface.
        course: объект своего курса.
        user_profile: профиль ученика.
        start_course: ``_start_course(setup, course, profile)``.
        switch_to_catalog: переключить UI на каталог.
        status_box: ``VBox`` под формой выбора (предпочтительно).
        output: устаревший параметр; если передан без status_box — игнор
            (задвоения из Output больше не используем).
    """
    del output  # совместимость вызовов; слот — только status_box

    def show(widget: Any | None) -> None:
        _set_status(status_box, widget)

    show(make_wait_banner("Проверяем, относится ли тема к Python и AI/ML…"))
    generator = _resolve_content_generator(setup)
    if generator is None:
        show(
            setup.utils.create_styled_message(
                "Система ещё не готова к запросам к модели. "
                "Вернитесь на дашборд, нажмите «Продолжить обучение» "
                "(или «Начать ещё один курс») и повторите ввод темы.",
                "incorrect",
            )
        )
        return
    verdict = classify_course_topic(
        course.get("title") or "",
        course.get("description") or "",
        generator=generator,
    )
    course["domain_status"] = verdict.status
    course["domain_reason"] = verdict.reason
    logger.info(
        "Проверка темы «%s»: %s (%s)",
        course.get("title"),
        verdict.status,
        verdict.source,
    )
    if verdict.status == "error":
        show(setup.utils.create_styled_message(verdict.reason, "incorrect"))
        return
    if verdict.status == "in":
        show(None)
        clear_output(wait=True)
        start_course(setup, course, user_profile)
        return

    force_btn = widgets.Button(
        description="Всё равно начать этот курс",
        button_style="warning",
        layout=widgets.Layout(width="auto", margin="4px 8px 4px 0"),
    )
    other_btn = widgets.Button(
        description="Выбрать другой курс",
        button_style="primary",
        layout=widgets.Layout(width="auto", margin="4px 0"),
    )

    def on_force(_b) -> None:
        course["domain_override"] = True
        show(None)
        clear_output(wait=True)
        display(
            setup.utils.create_styled_message(
                "Запускаем курс вне области Python / AI/ML. "
                "Практика кодом и качество материала не гарантируются.",
                "warning",
            )
        )
        start_course(setup, course, user_profile)

    def on_other(_b) -> None:
        switch_to_catalog()
        show(
            setup.utils.create_styled_message(
                "Выберите курс из списка или другую тему внутри Python / AI/ML.",
                "info",
            )
        )

    force_btn.on_click(on_force)
    other_btn.on_click(on_other)
    show(
        widgets.VBox(
            [
                widgets.HTML(value=_warning_html(course.get("title") or "", verdict)),
                widgets.HBox([force_btn, other_btn]),
            ]
        )
    )
