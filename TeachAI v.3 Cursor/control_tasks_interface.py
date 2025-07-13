#!/usr/bin/env python3
"""
Интерфейс для отображения и обработки контрольных заданий.
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
from typing import Dict, Any, Optional
from control_tasks_generator import ControlTasksGenerator


class ControlTasksInterface:
    """Интерфейс для контрольных заданий."""

    def __init__(self, content_generator, lesson_interface):
        """
        Инициализация интерфейса контрольных заданий.

        Args:
            content_generator: Генератор контента
            lesson_interface: Интерфейс урока
        """
        self.content_generator = content_generator
        self.lesson_interface = lesson_interface
        self.logger = logging.getLogger(__name__)

        # Создаем генератор контрольных заданий
        self.tasks_generator = ControlTasksGenerator(content_generator.api_key)

        # Текущее задание
        self.current_task = None
        self.task_result = None

    def show_control_task(self, lesson_data: Dict[str, Any], lesson_content: str):
        """
        Показывает контрольное задание пользователю.

        Args:
            lesson_data (Dict[str, Any]): Данные урока
            lesson_content (str): Содержание урока

        Returns:
            widgets.VBox: Виджет с контрольным заданием
        """
        try:
            # Генерируем задание
            communication_style = self.lesson_interface.current_course_info.get(
                "user_profile", {}
            ).get("communication_style", "friendly")

            course_context = self.lesson_interface.current_course_info

            self.current_task = self.tasks_generator.generate_control_task(
                lesson_data=lesson_data,
                lesson_content=lesson_content,
                communication_style=communication_style,
                course_context=course_context,
            )

            # Создаем интерфейс задания
            return self._create_task_interface(self.current_task)

        except Exception as e:
            self.logger.error(f"Ошибка при показе контрольного задания: {str(e)}")
            return self._create_error_interface(
                f"Ошибка при загрузке задания: {str(e)}"
            )

    def _create_task_interface(self, task_data: Dict[str, Any]) -> widgets.VBox:
        """
        Создает интерфейс для отображения задания.

        Args:
            task_data (Dict[str, Any]): Данные задания

        Returns:
            widgets.VBox: Виджет с заданием
        """
        # Заголовок задания
        title_html = widgets.HTML(
            value=f"<h2 style='color: #2c3e50; margin: 10px 0;'>{task_data.get('title', 'Контрольное задание')}</h2>",
            layout=widgets.Layout(margin="10px 0"),
        )

        # Описание задания
        description_html = widgets.HTML(
            value=f"<p style='margin: 10px 0; line-height: 1.5;'>{task_data.get('description', '')}</p>",
            layout=widgets.Layout(margin="10px 0"),
        )

        # Поле для ввода кода (ИСПРАВЛЕНО: не показываем готовое решение)
        code_input = widgets.Textarea(
            value="",  # Пустое поле для ввода кода студентом
            placeholder="Введите ваш код здесь...",
            description="Код:",
            layout=widgets.Layout(width="100%", height="200px"),
            style={"description_width": "initial"},
        )

        # Кнопка выполнения
        execute_button = widgets.Button(
            description="▶ Выполнить код",
            button_style="success",
            layout=widgets.Layout(width="200px", margin="10px 0"),
        )

        # Кнопка проверки
        check_button = widgets.Button(
            description="✓ Проверить решение",
            button_style="primary",
            layout=widgets.Layout(width="200px", margin="10px 0"),
        )

        # Контейнер для результатов
        results_output = widgets.Output(layout=widgets.Layout(margin="10px 0"))

        # Обработчики кнопок
        def on_execute_button_clicked(b):
            with results_output:
                clear_output()
                try:
                    # Выполняем код
                    exec(code_input.value)
                    display(
                        widgets.HTML(
                            value="<p style='color: green;'>✅ Код выполнен успешно!</p>"
                        )
                    )
                except Exception as e:
                    display(
                        widgets.HTML(
                            value=f"<p style='color: red;'>❌ Ошибка выполнения: {str(e)}</p>"
                        )
                    )

        def on_check_button_clicked(b):
            self._check_solution(code_input.value, task_data, results_output)

        execute_button.on_click(on_execute_button_clicked)
        check_button.on_click(on_check_button_clicked)

        # Создаем контейнер с кнопками
        buttons_container = widgets.HBox(
            [execute_button, check_button],
            layout=widgets.Layout(justify_content="space-around", margin="10px 0"),
        )

        # Собираем интерфейс
        interface = widgets.VBox(
            [
                title_html,
                description_html,
                code_input,
                buttons_container,
                results_output,
            ],
            layout=widgets.Layout(width="100%"),
        )

        return interface

    def _check_solution(
        self, user_code: str, task_data: Dict[str, Any], results_output
    ):
        """
        Проверяет решение пользователя.

        Args:
            user_code (str): Код пользователя
            task_data (Dict[str, Any]): Данные задания
            results_output: Контейнер для вывода результатов
        """
        with results_output:
            clear_output()

            try:
                # Проверяем выполнение
                validation_result = self.tasks_generator.validate_task_execution(
                    user_code, task_data.get("expected_output", "")
                )

                if validation_result["is_correct"]:
                    # Показываем успех
                    success_html = widgets.HTML(
                        value="<div style='background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 10px 0;'>"
                        "<h3 style='color: #155724; margin: 0;'>🎉 Задание выполнено правильно!</h3>"
                        "<p style='color: #155724; margin: 10px 0;'>Отличная работа! Вы успешно справились с заданием.</p>"
                        "</div>"
                    )
                    display(success_html)

                    # Сохраняем результат
                    self._save_task_result(task_data, True)

                    # Показываем кнопки для перехода
                    self._show_success_buttons()

                else:
                    # Показываем ошибку и эталонное решение
                    error_html = widgets.HTML(
                        value="<div style='background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px; margin: 10px 0;'>"
                        "<h3 style='color: #721c24; margin: 0;'>❌ Задание выполнено неправильно</h3>"
                        "<p style='color: #721c24; margin: 10px 0;'>Попробуйте еще раз или посмотрите эталонное решение.</p>"
                        "</div>"
                    )
                    display(error_html)

                    # Показываем эталонное решение
                    solution_html = widgets.HTML(
                        value=f"<div style='background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 10px 0;'>"
                        f"<h4 style='color: #856404; margin: 0;'>Эталонное решение:</h4>"
                        f"<pre style='background-color: #f8f9fa; padding: 10px; border-radius: 3px; margin: 10px 0;'>{task_data.get('solution_code', '')}</pre>"
                        f"</div>"
                    )
                    display(solution_html)

                    # Сохраняем результат
                    self._save_task_result(task_data, False)

                    # Показываем кнопки для повторной попытки
                    self._show_retry_buttons()

            except Exception as e:
                error_html = widgets.HTML(
                    value=f"<div style='background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px; margin: 10px 0;'>"
                    f"<h3 style='color: #721c24; margin: 0;'>❌ Ошибка при проверке</h3>"
                    f"<p style='color: #721c24; margin: 10px 0;'>{str(e)}</p>"
                    f"</div>"
                )
                display(error_html)

    def _save_task_result(self, task_data: Dict[str, Any], is_correct: bool):
        """
        Сохраняет результат выполнения задания.

        Args:
            task_data (Dict[str, Any]): Данные задания
            is_correct (bool): Правильно ли выполнено задание
        """
        try:
            # Сохраняем в state.json
            lesson_id = self.lesson_interface.current_lesson_id
            if lesson_id:
                self.lesson_interface.state_manager.save_control_task_result(
                    lesson_id, task_data.get("title", "Задание"), is_correct
                )
                self.logger.info(
                    f"Результат контрольного задания сохранен: {is_correct}"
                )
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении результата: {str(e)}")

    def _show_success_buttons(self):
        """
        Показывает кнопки после успешного выполнения задания.
        """
        # Кнопка перехода к следующему уроку
        next_lesson_button = widgets.Button(
            description="➡ Перейти к следующему уроку",
            button_style="success",
            layout=widgets.Layout(width="250px", margin="10px"),
        )

        def on_next_lesson_clicked(b):
            # Логика перехода к следующему уроку
            self._navigate_to_next_lesson()

        next_lesson_button.on_click(on_next_lesson_clicked)
        display(next_lesson_button)

    def _show_retry_buttons(self):
        """
        Показывает кнопки после неудачного выполнения задания.
        """
        # Кнопка повторить урок
        retry_button = widgets.Button(
            description="🔄 Пройти урок ещё раз",
            button_style="warning",
            layout=widgets.Layout(width="200px", margin="10px"),
        )

        # Кнопка продолжить с текущим результатом
        continue_button = widgets.Button(
            description="➡ Продолжить с текущим результатом",
            button_style="info",
            layout=widgets.Layout(width="250px", margin="10px"),
        )

        def on_retry_clicked(b):
            # Логика возврата к уроку
            self._return_to_lesson()

        def on_continue_clicked(b):
            # Логика принудительного перехода
            self._force_next_lesson()

        retry_button.on_click(on_retry_clicked)
        continue_button.on_click(on_continue_clicked)

        buttons_container = widgets.HBox([retry_button, continue_button])
        display(buttons_container)

    def _navigate_to_next_lesson(self):
        """
        Переходит к следующему уроку.
        """
        try:
            # Показываем сообщение о загрузке
            display(widgets.HTML(value="<p>🔄 Переход к следующему уроку...</p>"))

            # Получаем следующий урок
            next_lesson = self.lesson_interface.state_manager.get_next_lesson()

            if next_lesson and len(next_lesson) >= 3:
                section_id, topic_id, lesson_id = next_lesson[:3]
                self.logger.info(
                    f"Переход к уроку: {section_id}:{topic_id}:{lesson_id}"
                )

                # Показываем следующий урок
                lesson_widget = self.lesson_interface.show_lesson(
                    section_id, topic_id, lesson_id
                )
                if lesson_widget:
                    # Очищаем текущий вывод и показываем новый урок
                    clear_output(wait=True)
                    display(lesson_widget)
                else:
                    display(
                        widgets.HTML(
                            value="<p style='color: red;'>❌ Ошибка при загрузке следующего урока</p>"
                        )
                    )
            else:
                # Курс завершен
                clear_output(wait=True)
                display(widgets.HTML(value="<p>🎉 Поздравляем! Вы завершили курс!</p>"))

        except Exception as e:
            self.logger.error(f"Ошибка при переходе к следующему уроку: {str(e)}")
            import traceback

            self.logger.error(f"Полный traceback: {traceback.format_exc()}")
            display(
                widgets.HTML(
                    value=f"<p style='color: red;'>❌ Ошибка при переходе: {str(e)}</p>"
                )
            )

    def _return_to_lesson(self):
        """
        Возвращается к текущему уроку.
        """
        try:
            # Показываем текущий урок
            current_info = self.lesson_interface.current_course_info
            self.lesson_interface.show_lesson(
                current_info["section_id"],
                current_info["topic_id"],
                current_info["lesson_id"],
            )
        except Exception as e:
            self.logger.error(f"Ошибка при возврате к уроку: {str(e)}")

    def _force_next_lesson(self):
        """
        Принудительно переходит к следующему уроку.
        """
        try:
            # Принудительно отмечаем урок как завершенный
            lesson_id = self.lesson_interface.current_lesson_id
            if lesson_id:
                self.lesson_interface.state_manager.save_lesson_assessment(
                    lesson_id, 0, True
                )

            # Переходим к следующему уроку
            self._navigate_to_next_lesson()
        except Exception as e:
            self.logger.error(f"Ошибка при принудительном переходе: {str(e)}")

    def _create_error_interface(self, error_message: str) -> widgets.VBox:
        """
        Создает интерфейс ошибки.

        Args:
            error_message (str): Сообщение об ошибке

        Returns:
            widgets.VBox: Виджет с ошибкой
        """
        error_html = widgets.HTML(
            value=f"<div style='background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px; margin: 10px 0;'>"
            f"<h3 style='color: #721c24; margin: 0;'>❌ Ошибка</h3>"
            f"<p style='color: #721c24; margin: 10px 0;'>{error_message}</p>"
            f"</div>"
        )

        close_button = widgets.Button(
            description="✕ Закрыть",
            button_style="danger",
            layout=widgets.Layout(width="auto", margin="10px 0"),
        )

        def on_close_clicked(b):
            # Скрываем контейнер контрольных заданий
            if self.lesson_interface.control_tasks_container:
                self.lesson_interface.control_tasks_container.layout.display = "none"

        close_button.on_click(on_close_clicked)

        return widgets.VBox([error_html, close_button])
