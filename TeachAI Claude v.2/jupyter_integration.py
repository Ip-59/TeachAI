"""
Модуль интеграции с Jupiter Notebook ячейками.
Служит мостом между основной системой обучения TeachAI и модулями Jupiter Notebook.
НОВОЕ: Единая точка взаимодействия с демо-ячейками и интерактивными ячейками
НОВОЕ: Управление состоянием ячеек и синхронизация с системой прогресса
НОВОЕ: Обработка ошибок и fallback случаи для различных модулей
"""

import logging
import ipywidgets as widgets
from IPython.display import display, clear_output
from typing import List, Dict, Tuple, Optional, Any

# Импорты модулей Jupiter Notebook с обработкой ошибок
try:
    from demo_cell_widget import DemoCellWidget, create_demo_cell
    from demo_cells_integration import DemoCellsIntegration

    DEMO_CELLS_AVAILABLE = True
    logging.info("Модули демонстрационных ячеек загружены успешно")
except ImportError as e:
    logging.warning(f"Модули демонстрационных ячеек недоступны: {str(e)}")
    DEMO_CELLS_AVAILABLE = False

try:
    from interactive_cell_widget import InteractiveCellWidget, create_interactive_cell

    INTERACTIVE_CELLS_AVAILABLE = True
    logging.info("Модули интерактивных ячеек загружены успешно")
except ImportError as e:
    logging.warning(f"Модули интерактивных ячеек недоступны: {str(e)}")
    INTERACTIVE_CELLS_AVAILABLE = False

try:
    from control_tasks_logger import get_cell_stats, is_cell_completed, log_attempt

    CONTROL_TASKS_LOGGER_AVAILABLE = True
    logging.info("Модуль логирования контрольных заданий загружен успешно")
except ImportError as e:
    logging.warning(f"Модуль логирования контрольных заданий недоступен: {str(e)}")
    CONTROL_TASKS_LOGGER_AVAILABLE = False


class JupyterIntegration:
    """Интегратор Jupiter Notebook ячеек в систему обучения TeachAI."""

    def __init__(self, state_manager=None):
        """
        Инициализация интегратора Jupiter ячеек.

        Args:
            state_manager (optional): Менеджер состояния для синхронизации данных
        """
        self.state_manager = state_manager
        self.logger = logging.getLogger(__name__)

        # Инициализируем подмодули, если доступны
        self.demo_cells_integration = None
        if DEMO_CELLS_AVAILABLE:
            try:
                self.demo_cells_integration = DemoCellsIntegration()
                self.logger.info("DemoCellsIntegration инициализирован")
            except Exception as e:
                self.logger.error(
                    f"Ошибка инициализации DemoCellsIntegration: {str(e)}"
                )
                self.demo_cells_integration = None

        # Счетчики для уникальных ID
        self._demo_cell_counter = 0
        self._interactive_cell_counter = 0

        # Кэш созданных ячеек
        self._created_cells = {}

        self.logger.info("JupyterIntegration инициализирован")

    def get_capabilities(self):
        """
        Возвращает информацию о доступных возможностях интеграции.

        Returns:
            Dict: Словарь с информацией о доступных функциях
        """
        return {
            "demo_cells_available": DEMO_CELLS_AVAILABLE,
            "interactive_cells_available": INTERACTIVE_CELLS_AVAILABLE,
            "control_tasks_logger_available": CONTROL_TASKS_LOGGER_AVAILABLE,
            "demo_cells_integration_ready": self.demo_cells_integration is not None,
            "state_manager_connected": self.state_manager is not None,
        }

    def integrate_demo_cells_in_content(
        self, content: str, lesson_id: str = None
    ) -> str:
        """
        Интегрирует демонстрационные ячейки в HTML содержимое.

        Args:
            content (str): HTML содержимое с примерами кода
            lesson_id (str, optional): ID урока для уникальности ячеек

        Returns:
            str: Содержимое с интегрированными демо-ячейками
        """
        try:
            if not DEMO_CELLS_AVAILABLE or self.demo_cells_integration is None:
                self.logger.warning(
                    "Демо-ячейки недоступны, возвращаем оригинальное содержимое"
                )
                return content

            # Интегрируем демо-ячейки
            integrated_content = (
                self.demo_cells_integration.integrate_demo_cells_in_lesson(
                    content, lesson_id
                )
            )

            self.logger.info(
                f"Демо-ячейки интегрированы в содержимое урока {lesson_id}"
            )
            return integrated_content

        except Exception as e:
            self.logger.error(f"Ошибка интеграции демо-ячеек: {str(e)}")
            return content  # Возвращаем оригинальное содержимое при ошибке

    def create_demo_cell(
        self,
        code: str,
        title: str = None,
        description: str = None,
        lesson_id: str = None,
    ) -> widgets.Widget:
        """
        Создает демонстрационную ячейку с кодом.

        Args:
            code (str): Python код для демонстрации
            title (str, optional): Заголовок ячейки
            description (str, optional): Описание ячейки
            lesson_id (str, optional): ID урока для уникальности

        Returns:
            widgets.Widget: Демонстрационная ячейка или fallback виджет
        """
        try:
            if not DEMO_CELLS_AVAILABLE:
                return self._create_demo_fallback(code, title, description)

            # Генерируем уникальный ID
            self._demo_cell_counter += 1
            cell_id = f"demo_{lesson_id or 'cell'}_{self._demo_cell_counter}"

            # Создаем демо-ячейку
            demo_cell = create_demo_cell(
                code=code,
                title=title or f"Демонстрация #{self._demo_cell_counter}",
                description=description or "Интерактивный пример кода",
                cell_id=cell_id,
            )

            # Сохраняем в кэш
            self._created_cells[cell_id] = {
                "type": "demo",
                "widget": demo_cell,
                "lesson_id": lesson_id,
            }

            self.logger.debug(f"Создана демо-ячейка: {cell_id}")
            return demo_cell

        except Exception as e:
            self.logger.error(f"Ошибка создания демо-ячейки: {str(e)}")
            return self._create_demo_fallback(code, title, description)

    def create_control_task_cells(
        self, control_tasks: List[Dict], lesson_id: str
    ) -> List[widgets.Widget]:
        """
        Создает интерактивные ячейки для контрольных заданий.

        Args:
            control_tasks (List[Dict]): Список контрольных заданий
            lesson_id (str): ID урока

        Returns:
            List[widgets.Widget]: Список интерактивных ячеек
        """
        try:
            if not control_tasks:
                self.logger.info("Контрольные задания не предоставлены")
                return []

            if not INTERACTIVE_CELLS_AVAILABLE:
                self.logger.warning(
                    "Интерактивные ячейки недоступны, создаем fallback виджеты"
                )
                return [
                    self._create_interactive_fallback(task, i + 1)
                    for i, task in enumerate(control_tasks)
                ]

            interactive_cells = []

            for i, task in enumerate(control_tasks):
                try:
                    self._interactive_cell_counter += 1
                    cell_id = f"{lesson_id}_task_{i+1}"

                    # Создаем интерактивную ячейку
                    interactive_cell = create_interactive_cell(
                        task_description=task.get("description", "Выполните задание"),
                        expected_result=task.get("expected_result"),
                        check_type=task.get("check_type", "exact"),
                        initial_code=task.get("initial_code", "# Ваш код здесь\n"),
                        cell_id=cell_id,
                        title=task.get("title", f"Контрольное задание #{i+1}"),
                        description=f"Контрольное задание #{i+1} урока {lesson_id}",
                        max_attempts=task.get("max_attempts"),
                        show_solution=task.get("show_solution", False),
                        solution_code=task.get("solution_code", ""),
                    )

                    interactive_cells.append(interactive_cell)

                    # Сохраняем в кэш
                    self._created_cells[cell_id] = {
                        "type": "interactive",
                        "widget": interactive_cell,
                        "lesson_id": lesson_id,
                        "task_data": task,
                    }

                    self.logger.debug(f"Создана интерактивная ячейка: {cell_id}")

                except Exception as cell_error:
                    self.logger.error(
                        f"Ошибка создания ячейки для задания {i+1}: {str(cell_error)}"
                    )
                    # Добавляем fallback виджет для этого задания
                    interactive_cells.append(
                        self._create_interactive_fallback(task, i + 1)
                    )

            self.logger.info(
                f"Создано {len(interactive_cells)} интерактивных ячеек для урока {lesson_id}"
            )
            return interactive_cells

        except Exception as e:
            self.logger.error(f"Ошибка создания контрольных заданий: {str(e)}")
            return []

    def sync_control_tasks_progress(
        self, lesson_id: str, control_tasks: List[Dict]
    ) -> bool:
        """
        Синхронизирует прогресс контрольных заданий с системой состояния.

        Args:
            lesson_id (str): ID урока
            control_tasks (List[Dict]): Список контрольных заданий

        Returns:
            bool: True если синхронизация прошла успешно
        """
        try:
            if not self.state_manager:
                self.logger.warning(
                    "State manager не подключен, синхронизация невозможна"
                )
                return False

            if not CONTROL_TASKS_LOGGER_AVAILABLE:
                self.logger.warning(
                    "Control tasks logger недоступен, синхронизация невозможна"
                )
                return False

            updated = False

            for i, task in enumerate(control_tasks):
                task_cell_id = f"{lesson_id}_task_{i+1}"

                try:
                    # Получаем статистику из логгера Jupiter ячеек
                    cell_stats = get_cell_stats(task_cell_id)
                    is_completed = is_cell_completed(task_cell_id)

                    # Получаем текущий статус из системы состояния
                    current_status = (
                        self.state_manager.learning_progress.get_control_task_status(
                            lesson_id, task_cell_id
                        )
                    )

                    # Обновляем, если есть изменения
                    if (
                        cell_stats["total_attempts"] > 0
                        and current_status != is_completed
                    ):
                        success = self.state_manager.learning_progress.save_control_task_result(
                            lesson_id=lesson_id,
                            task_id=task_cell_id,
                            is_completed=is_completed,
                            attempts_count=cell_stats["total_attempts"],
                        )

                        if success:
                            updated = True
                            self.logger.debug(
                                f"Синхронизирован статус задания {task_cell_id}: {is_completed}"
                            )

                except Exception as task_error:
                    self.logger.error(
                        f"Ошибка синхронизации задания {task_cell_id}: {str(task_error)}"
                    )
                    continue

            if updated:
                self.logger.info(
                    f"Синхронизация контрольных заданий урока {lesson_id} завершена"
                )

            return True

        except Exception as e:
            self.logger.error(f"Ошибка синхронизации контрольных заданий: {str(e)}")
            return False

    def get_control_tasks_summary(self, lesson_id: str) -> Dict[str, Any]:
        """
        Получает сводку по выполнению контрольных заданий урока.

        Args:
            lesson_id (str): ID урока

        Returns:
            Dict: Сводка по контрольным заданиям
        """
        try:
            if not self.state_manager:
                return {"error": "State manager не подключен"}

            # Получаем прогресс из системы состояния
            progress = (
                self.state_manager.learning_progress.get_lesson_control_tasks_progress(
                    lesson_id
                )
            )

            # Добавляем информацию из логгера ячеек, если доступен
            if CONTROL_TASKS_LOGGER_AVAILABLE:
                cells_info = []

                # Ищем ячейки этого урока в кэше
                for cell_id, cell_data in self._created_cells.items():
                    if (
                        cell_data["type"] == "interactive"
                        and cell_data["lesson_id"] == lesson_id
                    ):
                        cell_stats = get_cell_stats(cell_id)
                        cells_info.append(
                            {
                                "cell_id": cell_id,
                                "is_completed": is_cell_completed(cell_id),
                                "total_attempts": cell_stats["total_attempts"],
                                "successful_attempts": cell_stats[
                                    "successful_attempts"
                                ],
                            }
                        )

                progress["cells_details"] = cells_info

            return progress

        except Exception as e:
            self.logger.error(f"Ошибка получения сводки контрольных заданий: {str(e)}")
            return {"error": str(e)}

    def create_progress_widget(self, lesson_id: str) -> widgets.Widget:
        """
        Создает виджет для отображения прогресса контрольных заданий.

        Args:
            lesson_id (str): ID урока

        Returns:
            widgets.Widget: Виджет прогресса
        """
        try:
            summary = self.get_control_tasks_summary(lesson_id)

            if "error" in summary:
                return widgets.HTML(
                    value=f"<p style='color: #721c24;'>Ошибка получения прогресса: {summary['error']}</p>"
                )

            # Создаем прогресс-бар
            total_tasks = summary.get("total_tasks", 0)
            completed_tasks = summary.get("completed_tasks", 0)
            completion_rate = summary.get("completion_rate", 0)

            if total_tasks == 0:
                return widgets.HTML(
                    value="<p style='color: #6c757d;'>Контрольные задания для этого урока отсутствуют</p>"
                )

            # Определяем цвет прогресс-бара
            if completion_rate == 100:
                progress_color = "#28a745"  # Зеленый
                status_text = "Все задания выполнены! ✅"
            elif completion_rate >= 50:
                progress_color = "#ffc107"  # Желтый
                status_text = f"Выполнено заданий: {completed_tasks} из {total_tasks}"
            else:
                progress_color = "#dc3545"  # Красный
                status_text = f"Выполнено заданий: {completed_tasks} из {total_tasks}"

            progress_html = f"""
            <div style="margin: 10px 0;">
                <h4>📝 Прогресс контрольных заданий</h4>
                <div style="background-color: #e9ecef; border-radius: 10px; padding: 3px; margin: 10px 0;">
                    <div style="background-color: {progress_color}; width: {completion_rate}%; height: 20px; border-radius: 8px; text-align: center; line-height: 20px; color: white; font-weight: bold;">
                        {completion_rate:.0f}%
                    </div>
                </div>
                <p style="color: #495057; margin: 5px 0;"><strong>{status_text}</strong></p>
            </div>
            """

            return widgets.HTML(value=progress_html)

        except Exception as e:
            self.logger.error(f"Ошибка создания виджета прогресса: {str(e)}")
            return widgets.HTML(
                value=f"<p style='color: #721c24;'>Ошибка создания виджета прогресса: {str(e)}</p>"
            )

    def cleanup_lesson_cells(self, lesson_id: str):
        """
        Очищает кэш ячеек для конкретного урока.

        Args:
            lesson_id (str): ID урока
        """
        try:
            cells_to_remove = []

            for cell_id, cell_data in self._created_cells.items():
                if cell_data.get("lesson_id") == lesson_id:
                    cells_to_remove.append(cell_id)

            for cell_id in cells_to_remove:
                del self._created_cells[cell_id]

            if cells_to_remove:
                self.logger.info(
                    f"Очищены ячейки урока {lesson_id}: {len(cells_to_remove)} ячеек"
                )

        except Exception as e:
            self.logger.error(f"Ошибка очистки ячеек урока: {str(e)}")

    def get_integration_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику работы интегратора.

        Returns:
            Dict: Статистика интеграции
        """
        try:
            capabilities = self.get_capabilities()

            demo_cells_count = sum(
                1 for cell in self._created_cells.values() if cell["type"] == "demo"
            )
            interactive_cells_count = sum(
                1
                for cell in self._created_cells.values()
                if cell["type"] == "interactive"
            )

            unique_lessons = set(
                cell["lesson_id"]
                for cell in self._created_cells.values()
                if cell.get("lesson_id")
            )

            return {
                "capabilities": capabilities,
                "total_cells_created": len(self._created_cells),
                "demo_cells_created": demo_cells_count,
                "interactive_cells_created": interactive_cells_count,
                "lessons_with_cells": len(unique_lessons),
                "demo_cell_counter": self._demo_cell_counter,
                "interactive_cell_counter": self._interactive_cell_counter,
            }

        except Exception as e:
            self.logger.error(f"Ошибка получения статистики интеграции: {str(e)}")
            return {"error": str(e)}

    # ========================================
    # FALLBACK МЕТОДЫ
    # ========================================

    def _create_demo_fallback(
        self, code: str, title: str = None, description: str = None
    ) -> widgets.Widget:
        """
        Создает fallback виджет для демонстрации кода, если модули недоступны.

        Args:
            code (str): Код для отображения
            title (str, optional): Заголовок
            description (str, optional): Описание

        Returns:
            widgets.Widget: Fallback виджет
        """
        import html

        fallback_html = f"""
        <div style="border: 2px solid #007bff; border-radius: 8px; margin: 15px 0; background-color: #f8f9ff;">
            <div style="background-color: #007bff; color: white; padding: 8px 12px; font-weight: bold;">
                🐍 {title or 'Демонстрация кода'} <span style="float: right;">⚠️ Демо-режим</span>
            </div>
            <div style="background-color: #f8f9fa; padding: 12px;">
                <pre style="margin: 0; font-family: 'Courier New', monospace; font-size: 13px; line-height: 1.4; color: #212529;">
                    <code>{html.escape(code)}</code>
                </pre>
            </div>
            <div style="padding: 8px 12px; background-color: #e7f3ff; font-size: 13px; color: #495057;">
                💡 {description or 'Интерактивные демо-ячейки недоступны. Скопируйте код в Jupyter Notebook для выполнения.'}
            </div>
        </div>
        """

        return widgets.HTML(value=fallback_html)

    def _create_interactive_fallback(
        self, task: Dict, task_number: int
    ) -> widgets.Widget:
        """
        Создает fallback виджет для интерактивного задания, если модули недоступны.

        Args:
            task (Dict): Данные задания
            task_number (int): Номер задания

        Returns:
            widgets.Widget: Fallback виджет
        """
        import html

        fallback_html = f"""
        <div style="border: 2px solid #dc3545; border-radius: 8px; margin: 15px 0; background-color: #fff5f5;">
            <div style="background-color: #dc3545; color: white; padding: 8px 12px; font-weight: bold;">
                📝 {task.get('title', f'Контрольное задание #{task_number}')} <span style="float: right;">⚠️ Статический режим</span>
            </div>
            <div style="padding: 15px;">
                <p><strong>Описание:</strong> {task.get('description', 'Выполните задание согласно инструкции')}</p>
                <div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0;">
                    <strong>Начальный код:</strong>
                    <pre style="margin: 5px 0; font-family: 'Courier New', monospace;">
                        <code>{html.escape(task.get('initial_code', '# Ваш код здесь'))}</code>
                    </pre>
                </div>
                <p style="color: #856404; background-color: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    <strong>⚠️ Интерактивные ячейки недоступны.</strong><br>
                    Скопируйте код в Jupyter Notebook для выполнения задания.
                </p>
            </div>
        </div>
        """

        return widgets.HTML(value=fallback_html)
