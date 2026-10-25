"""
Доступ к контрольному заданию: обычный путь после теста и педагогический bypass.

Вынесено из lesson_navigation.py, чтобы не раздувать навигацию.
"""

from __future__ import annotations

import logging

import ipywidgets as widgets

logger = logging.getLogger(__name__)


def can_open_control_tasks(state_manager, lesson_id: str) -> bool:
    """True, если тест пройден или ученик уже подтвердил переход без теста."""
    if state_manager.is_test_passed(lesson_id):
        return True
    return state_manager.is_test_bypassed(lesson_id)


class ControlTaskAccess:
    """Открывает КЗ или показывает подтверждение принудительного входа."""

    def __init__(self, lesson_interface) -> None:
        self.lesson_interface = lesson_interface
        self.logger = logging.getLogger(__name__)

    def handle_open_clicked(self) -> None:
        """Обработчик кнопки «Контрольные задания»."""
        lesson_id = self._current_lesson_id()
        sm = self.lesson_interface.state_manager

        if can_open_control_tasks(sm, lesson_id):
            self.open_control_task()
            return

        self._show_bypass_confirmation(lesson_id)

    def confirm_bypass_and_open(self, lesson_id: str) -> None:
        """Фиксирует bypass и открывает КЗ."""
        sm = self.lesson_interface.state_manager
        if not sm.mark_test_bypassed(lesson_id):
            self._show_error("Не удалось сохранить переход к практике без теста.")
            return

        self.logger.info(
            "Педагогический bypass входа в КЗ для урока %s", lesson_id
        )
        try:
            system_logger = getattr(self.lesson_interface, "system_logger", None)
            if system_logger:
                system_logger.log_activity(
                    action_type="control_task_test_bypassed",
                    details={"lesson_id": lesson_id},
                )
        except Exception as exc:
            self.logger.warning("Не удалось записать лог bypass: %s", exc)

        self.open_control_task()

    def open_control_task(self) -> None:
        """Генерирует и показывает контрольное задание в контейнере урока."""
        from loading_indicators import make_wait_banner

        li = self.lesson_interface
        li._hide_other_containers()
        container = li.control_tasks_container
        if not container:
            self.logger.error("control_tasks_container не найден")
            return

        lesson_data, lesson_content = self._resolve_current_lesson_payload()
        lesson_title = (lesson_data or {}).get("title") or (
            (li.current_course_info or {}).get("lesson_title") or "?"
        )
        self.logger.info(
            "Открытие КЗ для урока «%s» (id=%s)",
            lesson_title,
            getattr(li, "current_lesson_id", None),
        )

        container.layout.display = "block"
        container.children = [
            make_wait_banner(
                f"💻 Создаю контрольное задание по уроку «{lesson_title}»…"
            )
        ]

        close_button = self._close_button()
        try:
            if not lesson_data or not (lesson_content or "").strip():
                raise ValueError(
                    "Нет данных текущего урока для генерации КЗ. "
                    "Откройте урок заново с оглавления."
                )
            task_interface = li.control_tasks_interface.show_control_task(
                lesson_data=lesson_data,
                lesson_content=lesson_content,
            )
            children = [task_interface] if task_interface else []
            children.append(close_button)
            container.children = children
        except Exception as exc:
            self.logger.error("Ошибка при генерации контрольного задания: %s", exc)
            container.children = [
                widgets.HTML(
                    value=(
                        "<div style='background:#e7f3ff;border:1px solid #b8daff;"
                        "border-radius:8px;padding:16px;margin:8px 0;'>"
                        "<p style='color:#004085;margin:0;line-height:1.5;'>"
                        "Не получилось открыть контрольное задание. "
                        "Повторите попытку."
                        "</p></div>"
                    )
                ),
                close_button,
            ]

    def _resolve_current_lesson_payload(self) -> tuple[dict | None, str]:
        """Актуальные lesson_data + текст урока (не чужой урок из stale state)."""
        li = self.lesson_interface
        info = getattr(li, "current_course_info", None) or {}
        section_id = info.get("section_id")
        topic_id = info.get("topic_id")
        lesson_id = info.get("lesson_id")

        lesson_data = None
        if section_id and topic_id and lesson_id:
            try:
                lesson_data = li.state_manager.get_lesson_data(
                    section_id, topic_id, lesson_id
                )
            except Exception as exc:
                self.logger.warning("get_lesson_data не удался: %s", exc)

        if not lesson_data:
            lesson_data = getattr(li, "current_lesson_data", None)

        # Всегда предпочитаем текст, привязанный к текущему экрану урока.
        lesson_content = (
            info.get("lesson_raw_content")
            or getattr(li, "current_lesson_raw_content", None)
            or info.get("lesson_content")
            or getattr(li, "current_lesson_content", None)
            or ""
        )
        if isinstance(lesson_data, dict) and lesson_data.get("title"):
            # Синхронизируем title с планом, если в памяти устарел другой урок
            expected = str(info.get("lesson_title") or "").strip()
            actual = str(lesson_data.get("title") or "").strip()
            if expected and actual and expected.lower() != actual.lower():
                self.logger.warning(
                    "Расхождение названий урока: info=%r data=%r — берём план",
                    expected,
                    actual,
                )
                lesson_data = dict(lesson_data)
                lesson_data["title"] = expected
        return lesson_data, str(lesson_content)

    def _show_bypass_confirmation(self, lesson_id: str) -> None:
        li = self.lesson_interface
        li._hide_other_containers()
        container = li.control_tasks_container
        if not container:
            self.logger.error("control_tasks_container не найден")
            return

        notice = widgets.HTML(
            value=(
                "<div style='background:#fff3cd;color:#856404;padding:12px;"
                "border-radius:8px;border:1px solid #ffeeba;margin:8px 0;'>"
                "<strong>Тест ещё не пройден.</strong> "
                "Можно перейти к практике без теста: это педагогический обход "
                "входного порога, оценка теста при этом не ставится."
                "</div>"
            )
        )
        go_button = widgets.Button(
            description="Перейти к практике без теста",
            button_style="warning",
            icon="forward",
            layout=widgets.Layout(width="auto", margin="5px"),
        )
        cancel_button = widgets.Button(
            description="Отмена",
            button_style="",
            layout=widgets.Layout(width="auto", margin="5px"),
        )

        def on_go(_b):
            self.confirm_bypass_and_open(lesson_id)

        def on_cancel(_b):
            container.layout.display = "none"
            container.children = []

        go_button.on_click(on_go)
        cancel_button.on_click(on_cancel)

        container.layout.display = "block"
        container.children = [
            notice,
            widgets.HBox([go_button, cancel_button]),
        ]

    def _show_error(self, message: str) -> None:
        container = self.lesson_interface.control_tasks_container
        if not container:
            return
        container.layout.display = "block"
        container.children = [
            widgets.HTML(value=f"<p style='color: red;'>{message}</p>"),
            self._close_button(),
        ]

    def _close_button(self) -> widgets.Button:
        button = widgets.Button(
            description="✕ Закрыть",
            button_style="danger",
            layout=widgets.Layout(width="auto", margin="10px 0"),
        )

        def on_close(_b):
            if self.lesson_interface.control_tasks_container:
                self.lesson_interface.control_tasks_container.layout.display = "none"

        button.on_click(on_close)
        return button

    def _current_lesson_id(self) -> str:
        info = getattr(self.lesson_interface, "current_course_info", {}) or {}
        explicit = getattr(self.lesson_interface, "current_lesson_id", None)
        if explicit:
            return explicit
        return (
            f"{info.get('section_id', '')}:"
            f"{info.get('topic_id', '')}:"
            f"{info.get('lesson_id', '')}"
        )
