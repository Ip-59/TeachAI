"""
Виджет интерактивной ячейки для контрольных заданий.
Позволяет студенту редактировать код, выполнять его и получать проверку результата.
"""

import ipywidgets as widgets
import time
from cell_widget_base import CellWidgetBase
from interactive_cell_ui import (
    create_task_widget,
    create_code_editor,
    create_run_button,
    create_clear_button,
    create_reset_button,
    create_solution_button,
    create_status_widget,
    create_result_widget,
    create_stats_widget,
    create_button_row,
    update_task_widget,
    update_status_widget,
    update_result_widget,
    update_stats_widget,
)
from interactive_cell_logic import (
    execute_student_code,
    find_result_in_namespace,
    check_execution_result,
    log_execution_attempt,
    get_cell_attempt_count,
    check_attempt_limit,
    is_cell_task_completed,
    get_cell_statistics,
)
from result_checker import CheckResult, check_result
from control_tasks_logger import log_attempt, get_cell_stats, is_cell_completed
from typing import Optional, Any, Dict, List, Tuple


class InteractiveCellWidget(CellWidgetBase):
    """
    Интерактивная ячейка с редактором кода для контрольных заданий.
    Позволяет студенту писать, выполнять и проверять код.
    """

    def __init__(
        self,
        task_description: str,
        expected_result: Any,
        check_type: str = "exact",
        initial_code: str = "",
        cell_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        check_kwargs: Optional[Dict[str, Any]] = None,
        max_attempts: Optional[int] = None,
        show_solution: bool = False,
        solution_code: str = "",
        **kwargs,
    ):
        """
        Инициализация интерактивной ячейки.

        Args:
            task_description: Описание задания для студента
            expected_result: Ожидаемый результат выполнения
            check_type: Тип проверки ('exact', 'numeric', 'list', 'function', 'output')
            initial_code: Начальный код в редакторе
            cell_id: Уникальный идентификатор ячейки
            title: Заголовок ячейки
            description: Дополнительное описание
            check_kwargs: Дополнительные параметры для проверки
            max_attempts: Максимальное количество попыток (None = без ограничений)
            show_solution: Показывать ли кнопку с решением
            solution_code: Код решения задачи
        """
        self.task_description = task_description
        self.expected_result = expected_result
        self.check_type = check_type
        self.initial_code = initial_code
        self.check_kwargs = check_kwargs or {}
        self.max_attempts = max_attempts
        self.show_solution = show_solution
        self.solution_code = solution_code

        # Создаем виджеты до вызова родительского конструктора
        self._create_widgets()

        # Подготавливаем параметры для родительского конструктора
        parent_kwargs = kwargs.copy()
        if cell_id is not None:
            parent_kwargs["cell_id"] = cell_id
        if title is not None:
            parent_kwargs["title"] = title
        if description is not None:
            parent_kwargs["description"] = description

        super().__init__(**parent_kwargs)

        # Загружаем статистику и последнюю попытку
        self._load_previous_state()

    def _create_widgets(self):
        """Создание специфичных для интерактивной ячейки виджетов."""

        # Создаем виджеты через UI модуль
        self.task_widget = create_task_widget(self.task_description)
        self.code_editor = create_code_editor(self.initial_code)
        self.run_button = create_run_button()
        self.clear_button = create_clear_button()
        self.reset_button = create_reset_button()

        # Кнопка с решением (если разрешено)
        if self.show_solution:
            self.solution_button = create_solution_button()
            self.solution_button.on_click(self._show_solution)

        # Статус и результат проверки
        self.status_widget = create_status_widget()
        self.result_widget = create_result_widget()
        self.stats_widget = create_stats_widget()

        # Привязка событий
        self.run_button.on_click(self._execute_and_check)
        self.clear_button.on_click(self._clear_code)
        self.reset_button.on_click(self._reset_code)

    def _get_specific_widgets(self) -> List[widgets.Widget]:
        """Возвращает виджеты специфичные для интерактивной ячейки."""
        widgets_list = [
            self.task_widget,
            self.code_editor,
            self._create_button_row(),
            self.status_widget,
            self.result_widget,
            self.stats_widget,
        ]

        return widgets_list

    def _create_button_row(self) -> widgets.HBox:
        """Создает строку с кнопками управления."""
        buttons = [self.run_button, self.clear_button, self.reset_button]

        if self.show_solution:
            buttons.append(self.solution_button)

        return create_button_row(
            self.run_button,
            self.clear_button,
            self.reset_button,
            self.solution_button if self.show_solution else None,
        )

    def _execute_and_check(self, button):
        """Выполняет код студента и проверяет результат."""
        start_time = time.time()

        # Проверяем ограничения по попыткам
        if not check_attempt_limit(self.cell_id, self.max_attempts):
            self._update_status("❌ Превышено максимальное количество попыток", "error")
            return

        # Проверяем, что есть код для выполнения
        student_code = self.code_editor.value.strip()
        if not student_code:
            self._update_status("❌ Введите код для выполнения", "error")
            return

        self._update_status("⏳ Выполняется...", "running")

        try:
            # Выполняем код студента через логику модуль
            result, output, success, images = execute_student_code(
                student_code, self.execution_namespace
            )
            self._last_sandbox_images = images
            execution_time_ms = (time.time() - start_time) * 1000

            if success:
                # Если результат None, пытаемся найти переменную в пространстве имен
                if (
                    result is None
                    and hasattr(self, "execution_namespace")
                    and self.execution_namespace
                ):
                    result = find_result_in_namespace(
                        self.execution_namespace, self.expected_result
                    )

                # Проверяем результат через логику модуль
                check_result_obj = check_execution_result(
                    result, self.expected_result, self.check_type, self.check_kwargs
                )

                # Логируем попытку через логику модуль
                log_execution_attempt(
                    cell_id=self.cell_id,
                    student_code=student_code,
                    execution_result=result,
                    execution_output=output,
                    execution_success=success,
                    check_result=check_result_obj,
                    execution_time_ms=execution_time_ms,
                )

                # Обновляем интерфейс через UI модуль
                update_result_widget(
                    self.result_widget, check_result_obj, execution_time_ms
                )
                update_status_widget(
                    self.status_widget,
                    f"{'✅ ЗАЧЁТ' if check_result_obj.passed else '❌ НЕ ЗАЧЁТ'}: {check_result_obj.message}",
                    "success" if check_result_obj.passed else "error",
                )
                self._update_stats_display()

            else:
                # Ошибка выполнения
                failed_check = CheckResult(
                    passed=False, message="Ошибка выполнения кода", score=0.0
                )

                # Логируем неуспешную попытку
                log_execution_attempt(
                    cell_id=self.cell_id,
                    student_code=student_code,
                    execution_result=None,
                    execution_output=output,
                    execution_success=success,
                    check_result=failed_check,
                    execution_time_ms=execution_time_ms,
                )

                update_status_widget(
                    self.status_widget, "❌ Ошибка выполнения (см. вывод ниже)", "error"
                )
                self._update_stats_display()

            try:
                from code_sandbox import display_images

                display_images(getattr(self, "_last_sandbox_images", None))
            except Exception:
                pass

        except Exception as e:
            update_status_widget(
                self.status_widget, f"❌ Неожиданная ошибка: {e}", "error"
            )

    def _update_result_display(
        self, check_result_obj: CheckResult, execution_time_ms: float
    ):
        """Обновляет отображение результата проверки."""
        if check_result_obj.passed:
            status_color = "#28a745"  # Зеленый
            status_icon = "✅"
            status_text = "ЗАЧЁТ"
        else:
            status_color = "#dc3545"  # Красный
            status_icon = "❌"
            status_text = "НЕ ЗАЧЁТ"

        result_html = f"""
        <div style='border: 2px solid {status_color}; border-radius: 8px; padding: 12px; margin: 8px 0; background: {"#d4edda" if check_result_obj.passed else "#f8d7da"}'>
            <div style='font-weight: bold; font-size: 16px; color: {status_color}; margin-bottom: 8px;'>
                {status_icon} {status_text}
            </div>
            <div style='margin-bottom: 6px;'>
                <strong>Результат:</strong> {check_result_obj.message}
            </div>
            <div style='font-size: 12px; color: #666;'>
                Оценка: {check_result_obj.score:.1%} | Время выполнения: {execution_time_ms:.1f} мс
            </div>
        </div>
        """

        self.result_widget.value = result_html
        self._update_status(
            f"{status_icon} {status_text}: {check_result_obj.message}",
            "success" if check_result_obj.passed else "error",
        )

    def _update_status(self, message: str, status_type: str = "info"):
        """Обновляет статус ячейки."""
        color_map = {
            "info": "#17a2b8",
            "success": "#28a745",
            "error": "#dc3545",
            "warning": "#ffc107",
            "running": "#6f42c1",
        }

        color = color_map.get(status_type, "#666")
        self.status_widget.value = (
            f"<div style='color: {color}; font-weight: bold;'>{message}</div>"
        )

    def _update_stats_display(self):
        """Обновляет отображение статистики."""
        stats = get_cell_stats(self.cell_id)

        if stats:
            completed_icon = "✅" if stats["successful_attempts"] > 0 else "⏳"
            stats_html = f"""
            <div style='background: #f8f9fa; padding: 8px; border-radius: 4px; font-size: 12px; color: #666;'>
                {completed_icon} Попыток: {stats['total_attempts']} |
                Успешных: {stats['successful_attempts']} |
                Лучший результат: {stats['best_score']:.1%} |
                Средний результат: {stats['average_score']:.1%}
            </div>
            """
            self.stats_widget.value = stats_html

    def _get_attempt_count(self) -> int:
        """Возвращает количество попыток для данной ячейки."""
        stats = get_cell_stats(self.cell_id)
        return stats["total_attempts"] if stats else 0

    def _clear_code(self, button):
        """Очищает редактор кода."""
        self.code_editor.value = ""
        self._update_status("🗑 Код очищен", "info")
        self.result_widget.value = ""

    def _reset_code(self, button):
        """Возвращает начальный код."""
        self.code_editor.value = self.initial_code
        self._update_status("🔄 Код сброшен к начальному", "info")
        self.result_widget.value = ""

    def _show_solution(self, button):
        """Показывает решение задачи."""
        if self.solution_code:
            self.code_editor.value = self.solution_code
            self._update_status("💡 Показано решение", "warning")
        else:
            self._update_status("❌ Решение не предоставлено", "error")

    def _load_previous_state(self):
        """Загружает предыдущее состояние ячейки."""
        # Обновляем статистику
        self._update_stats_display()

        # Проверяем, выполнена ли ячейка
        if is_cell_completed(self.cell_id):
            self._update_status("✅ Задание уже выполнено!", "success")

    def set_expected_result(self, expected_result: Any, check_type: str = None):
        """
        Устанавливает новый ожидаемый результат.

        Args:
            expected_result: Новый ожидаемый результат
            check_type: Новый тип проверки (опционально)
        """
        self.expected_result = expected_result
        if check_type:
            self.check_type = check_type

        self._update_status("🔄 Ожидаемый результат обновлен", "info")
        self.result_widget.value = ""

    def set_task_description(self, task_description: str):
        """
        Устанавливает новое описание задания.

        Args:
            task_description: Новое описание задания
        """
        self.task_description = task_description
        self.task_widget.value = (
            f"<div style='background: #f8f9fa; padding: 10px; border-left: 4px solid #007bff; margin: 5px 0;'>"
            f"<strong>📝 Задание:</strong><br>{self.task_description}</div>"
        )

    def get_student_code(self) -> str:
        """Возвращает текущий код студента."""
        return self.code_editor.value

    def set_code(self, code: str):
        """Устанавливает код в редактор."""
        self.code_editor.value = code

    def is_completed(self) -> bool:
        """Проверяет, выполнена ли ячейка."""
        return is_cell_completed(self.cell_id)

    def get_cell_info(self) -> Dict[str, Any]:
        """Возвращает расширенную информацию об интерактивной ячейке."""
        info = super().get_cell_info()
        stats = get_cell_stats(self.cell_id)

        info.update(
            {
                "task_description": self.task_description,
                "check_type": self.check_type,
                "max_attempts": self.max_attempts,
                "has_solution": bool(self.solution_code),
                "is_completed": self.is_completed(),
                "current_code": self.get_student_code(),
                "stats": stats,
            }
        )

        return info


def create_interactive_cell(
    task_description: str,
    expected_result: Any,
    check_type: str = "exact",
    initial_code: str = "",
    title: str = None,
    description: str = None,
    cell_id: str = None,
    check_kwargs: Dict[str, Any] = None,
    max_attempts: int = None,
    show_solution: bool = False,
    solution_code: str = "",
) -> InteractiveCellWidget:
    """
    Функция-помощник для быстрого создания интерактивной ячейки.

    Args:
        task_description: Описание задания
        expected_result: Ожидаемый результат
        check_type: Тип проверки
        initial_code: Начальный код
        title: Заголовок ячейки
        description: Описание ячейки
        cell_id: Уникальный идентификатор ячейки
        check_kwargs: Параметры проверки
        max_attempts: Максимум попыток
        show_solution: Показывать кнопку решения
        solution_code: Код решения

    Returns:
        Экземпляр InteractiveCellWidget
    """
    return InteractiveCellWidget(
        task_description=task_description,
        expected_result=expected_result,
        check_type=check_type,
        initial_code=initial_code,
        title=title,
        description=description,
        cell_id=cell_id,
        check_kwargs=check_kwargs,
        max_attempts=max_attempts,
        show_solution=show_solution,
        solution_code=solution_code,
    )
