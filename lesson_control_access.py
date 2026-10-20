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
        li = self.lesson_interface
        li._hide_other_containers()
        container = li.control_tasks_container
        if not container:
            self.logger.error("control_tasks_container не найден")
            return

        container.layout.display = "block"
        container.children = [
            widgets.HTML(value="<p><strong>Генерация контрольного задания...</strong></p>")
        ]

        close_button = self._close_button()
        try:
            task_interface = li.control_tasks_interface.show_control_task(
                lesson_data=li.current_lesson_data,
                lesson_content=(
                    li.current_lesson_raw_content or li.current_lesson_content
                ),
            )
            children = [task_interface] if task_interface else []
            children.append(close_button)
            container.children = children
        except Exception as exc:
            self.logger.error("Ошибка при генерации контрольного задания: %s", exc)
            container.children = [
                widgets.HTML(
                    value=(
                        "<p style='color: red;'>Ошибка при генерации "
                        f"контрольного задания: {exc}</p>"
                    )
                ),
                close_button,
            ]

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
