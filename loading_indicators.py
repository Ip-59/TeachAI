"""
Индикаторы ожидания ответа LLM (ipywidgets).

Важно: после ``display(widget)`` нельзя «прятать» через ``clear_output`` —
виджеты Jupyter часто остаются на экране, а ячейка при этом ломается.
Скрытие — через очистку/``close()`` самого виджета.
"""

from __future__ import annotations

import html
import logging
from contextlib import contextmanager
from typing import Any, Generator, Optional

import ipywidgets as widgets
from IPython.display import display

logger = logging.getLogger(__name__)

_SPIN_CSS = """
@keyframes teachai-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
"""


def make_wait_banner(message: str, *, variant: str = "default") -> widgets.HTML:
    """Простой баннер ожидания (спиннер + текст)."""
    safe = html.escape(message or "Загрузка...")
    if variant == "lesson":
        return widgets.HTML(
            value=(
                "<div style='background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);"
                "color:white;padding:20px;border-radius:10px;margin:10px 0;text-align:center;'>"
                "<div style='display:inline-block;width:44px;height:44px;"
                "border:4px solid rgba(255,255,255,0.3);border-top:4px solid white;"
                "border-radius:50%;animation:teachai-spin 1s linear infinite;'></div>"
                f"<h3 style='margin:14px 0 0 0;color:white;'>{safe}</h3>"
                "<p style='margin:8px 0 0 0;opacity:0.9;font-size:0.9em;'>"
                "Это может занять несколько секунд…</p>"
                f"<style>{_SPIN_CSS}</style></div>"
            )
        )
    return widgets.HTML(
        value=(
            "<div style='background:#f8f9fa;padding:18px;border-radius:10px;margin:10px 0;"
            "text-align:center;border:2px solid #ecf0f1;'>"
            "<div style='display:inline-block;width:36px;height:36px;"
            "border:4px solid #ecf0f1;border-top:4px solid #3498db;"
            "border-radius:50%;animation:teachai-spin 1s linear infinite;'></div>"
            f"<p style='margin:12px 0 0 0;color:#2c3e50;font-size:1em;font-weight:500;'>"
            f"{safe}</p>"
            "<p style='margin:6px 0 0 0;color:#7f8c8d;font-size:0.85em;'>"
            "Пожалуйста, подождите…</p>"
            f"<style>{_SPIN_CSS}</style></div>"
        )
    )


def dismiss_widget(widget: Any) -> None:
    """Убирает ранее отображённый виджет ожидания без clear_output ячейки."""
    if widget is None:
        return
    try:
        if hasattr(widget, "value"):
            widget.value = ""
        if hasattr(widget, "layout") and widget.layout is not None:
            widget.layout.display = "none"
            widget.layout.height = "0px"
            widget.layout.margin = "0"
            widget.layout.padding = "0"
            widget.layout.border = "0"
        if hasattr(widget, "close"):
            widget.close()
    except Exception as exc:
        logger.debug("Не удалось скрыть виджет ожидания: %s", exc)


class LoadingIndicator:
    """Базовый индикатор ожидания."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.is_active = False
        self.widget: Optional[widgets.Widget] = None

    def show(self, message: str = "Загрузка...") -> widgets.Widget:
        self.is_active = True
        self.widget = make_wait_banner(message, variant="default")
        self.logger.info("Индикатор показан: %s", message)
        return self.widget

    def hide(self) -> None:
        self.is_active = False
        dismiss_widget(self.widget)
        self.widget = None
        self.logger.info("Индикатор скрыт")


class OpenAIAPILoadingIndicator(LoadingIndicator):
    """Сообщения для операций с моделью."""

    def __init__(self) -> None:
        super().__init__()
        self.operation_messages = {
            "generate_course_plan": "📋 Составляю персонализированный учебный план…",
            "generate_lesson": "🎓 Генерирую урок…",
            "generate_examples": "📝 Создаю примеры…",
            "generate_test": "📋 Формирую тест…",
            "generate_explanation": "💡 Генерирую объяснение…",
            "generate_control_task": "💻 Создаю контрольное задание…",
            "check_relevance": "🔍 Проверяю релевантность вопроса…",
            "generate_qa": "❓ Готовлю ответ на вопрос…",
            "generate_concepts": "🔑 Выделяю ключевые понятия…",
            "explain_concept": "💡 Объясняю понятие…",
            "classify_topic": "🔎 Проверяю тему курса…",
            "default": "🤖 Обрабатываю запрос к модели…",
        }

    def show_for_operation(
        self, operation: str, custom_message: Optional[str] = None
    ) -> widgets.Widget:
        message = custom_message or self.operation_messages.get(
            operation, self.operation_messages["default"]
        )
        return self.show(f"{message}\n\n⏱️ Это может занять несколько секунд…")


class LessonLoadingIndicator(OpenAIAPILoadingIndicator):
    """Индикатор загрузки урока."""

    def show_lesson_loading(self, lesson_title: str = "") -> widgets.Widget:
        title_text = f" «{lesson_title}»" if lesson_title else ""
        message = f"📖 Загружаю урок{title_text}…"
        self.is_active = True
        self.widget = make_wait_banner(message, variant="lesson")
        self.logger.info("Индикатор урока показан: %s", lesson_title)
        return self.widget


class LoadingManager:
    """Один активный индикатор на экран."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.current_indicator: Optional[widgets.Widget] = None
        self.indicators = {
            "default": LoadingIndicator(),
            "openai": OpenAIAPILoadingIndicator(),
            "lesson": LessonLoadingIndicator(),
        }

    def show_loading(self, indicator_type: str = "default", **kwargs) -> widgets.Widget:
        self.hide_loading()
        indicator = self.indicators.get(indicator_type, self.indicators["default"])
        if indicator_type == "openai" and "operation" in kwargs:
            self.current_indicator = indicator.show_for_operation(
                kwargs["operation"], kwargs.get("custom_message")
            )
        elif indicator_type == "lesson":
            self.current_indicator = indicator.show_lesson_loading(
                kwargs.get("lesson_title", "")
            )
        else:
            self.current_indicator = indicator.show(
                kwargs.get("message", "Загрузка...")
            )
        self.logger.info("Индикатор показан: %s", indicator_type)
        return self.current_indicator

    def hide_loading(self) -> None:
        widget = self.current_indicator
        self.current_indicator = None
        for indicator in self.indicators.values():
            indicator.is_active = False
            if indicator.widget is widget:
                indicator.widget = None
        dismiss_widget(widget)
        self.logger.info("Индикатор скрыт")


@contextmanager
def displayed_loading(
    manager: Optional[LoadingManager],
    indicator_type: str = "openai",
    **kwargs: Any,
) -> Generator[Optional[widgets.Widget], None, None]:
    """
    Показать индикатор на время блока; всегда скрыть в ``finally``.

    Args:
        manager: LoadingManager или None (тогда no-op).
        indicator_type: ``openai`` / ``lesson`` / ``default``.
        **kwargs: ``operation``, ``lesson_title``, ``message``, …
    """
    if manager is None:
        yield None
        return
    widget = manager.show_loading(indicator_type, **kwargs)
    display(widget)
    try:
        yield widget
    finally:
        manager.hide_loading()
