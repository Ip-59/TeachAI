#!/usr/bin/env python3
"""
Исправленный интерфейс для отображения и обработки контрольных заданий.
Исправления:
1. Улучшенная проверка переменных без print()
2. Показ дашборда после успешного выполнения задания
3. Улучшенная диагностика и логирование
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
from typing import Dict, Any, Optional
from control_tasks_generator import ControlTasksGenerator


class ControlTasksInterfaceFixed:
    """Исправленный интерфейс для контрольных заданий."""

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
        # ИСПРАВЛЕНО: Флаг для предотвращения множественных вызовов
        self.is_checking = False

    def show_control_task(self, lesson_data: Dict[str, Any], lesson_content: str):
        """
        Показывает контрольное задание пользователю.

        Args:
            lesson_data (Dict[str, Any]): Данные урока
            lesson_content (str): Содержание урока

        Returns:
            widgets.VBox: Виджет с контрольным заданием
        """
        from IPython.display import clear_output
        try:
            print("\n" + "="*80)
            print("🔍 [DIAGNOSTIC] show_control_task ВЫЗВАН")
            print("="*80)
            
            # Очищаем вывод перед показом нового задания
            clear_output(wait=True)
            
            # Генерируем задание
            communication_style = self.lesson_interface.current_course_info.get(
                "user_profile", {}
            ).get("communication_style", "friendly")

            course_context = self.lesson_interface.current_course_info

            print(f"\n📤 [DIAGNOSTIC] Вызываем generate_control_task...")
            self.current_task = self.tasks_generator.generate_control_task(
                lesson_data=lesson_data,
                lesson_content=lesson_content,
                communication_style=communication_style,
                course_context=course_context,
            )

            print(f"\n📥 [DIAGNOSTIC] Результат generate_control_task:")
            print(f"title: {self.current_task.get('title', 'НЕТ')}")
            print(f"description: {self.current_task.get('description', 'НЕТ')[:100]}...")
            print(f"task_code: {self.current_task.get('task_code', 'НЕТ')[:100]}...")
            print(f"expected_output: {self.current_task.get('expected_output', 'НЕТ')}")
            print(f"check_variable: {self.current_task.get('check_variable', 'НЕТ')}")
            print(f"expected_variable_value: {self.current_task.get('expected_variable_value', 'НЕТ')}")
            print("="*80 + "\n")

            # Проверяем, нужно ли задание
            if not self.current_task.get("is_needed", True):
                # Задание не нужно, показываем сообщение и переходим к следующему уроку
                return self._create_skip_task_interface(self.current_task)

            # Создаем интерфейс задания
            return self._create_task_interface(self.current_task)

        except Exception as e:
            print(f"\n❌ [DIAGNOSTIC] ОШИБКА в show_control_task: {str(e)}")
            print("="*80 + "\n")
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
            widgets.VBox: Виджет с интерфейсом задания
        """
        # Заголовок задания
        title_html = widgets.HTML(
            value=f"<h2 style='color: #2c3e50; margin: 10px 0;'>{task_data.get('title', 'Контрольное задание')}</h2>"
        )

        # Описание задания
        description_html = widgets.HTML(
            value=f"<div style='background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 10px 0;'>"
            f"<p style='margin: 0; color: #495057;'>{task_data.get('description', 'Описание задания')}</p>"
            f"</div>"
        )

        # Поле для ввода кода
        code_input = widgets.Textarea(
            value=task_data.get("task_code", ""),
            placeholder="Введите ваш код здесь...",
            description="Код:",
            layout=widgets.Layout(width="100%", height="200px"),
            style={"font-family": "monospace"}
        )

        # Контейнер для результатов
        results_output = widgets.VBox([])

        # Кнопки
        execute_button = widgets.Button(
            description="▶️ Выполнить код",
            button_style="primary",
            layout=widgets.Layout(width="200px", margin="10px")
        )

        check_button = widgets.Button(
            description="✅ Проверить решение",
            button_style="success",
            layout=widgets.Layout(width="200px", margin="10px")
        )

        # Обработчики кнопок
        def on_execute_button_clicked(b):
            # ИСПРАВЛЕНО: Очищаем контейнер результатов
            results_output.children = []
            
            try:
                user_code = code_input.value
                
                # Выполняем код
                import io
                from contextlib import redirect_stdout
                output_buffer = io.StringIO()
                local_vars = {}
                
                with redirect_stdout(output_buffer):
                    exec(user_code, {}, local_vars)
                
                actual_output = output_buffer.getvalue()
                
                # Показываем результат выполнения
                result_html = widgets.HTML(
                    value=f"<div style='background-color: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 5px; padding: 15px; margin: 10px 0;'>"
                    f"<h4 style='color: #0056b3; margin: 0;'>Результат выполнения:</h4>"
                    f"<pre style='background-color: #f8f9fa; padding: 10px; border-radius: 3px; margin: 10px 0;'>{actual_output or 'Нет вывода'}</pre>"
                    f"<p style='color: #0056b3; margin: 10px 0;'><strong>Переменные:</strong> {list(local_vars.keys())}</p>"
                    f"</div>"
                )
                
                results_output.children = [result_html]
                
            except Exception as e:
                error_html = widgets.HTML(
                    value=f"<div style='background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px; margin: 10px 0;'>"
                    f"<h4 style='color: #721c24; margin: 0;'>Ошибка выполнения:</h4>"
                    f"<p style='color: #721c24; margin: 10px 0;'>{str(e)}</p>"
                    f"</div>"
                )
                results_output.children = [error_html]

        def on_check_button_clicked(b):
            # ИСПРАВЛЕНО: Защита от множественных нажатий
            if self.is_checking:
                self.logger.warning("Попытка множественного вызова проверки - игнорируем")
                return
            self.is_checking = True
            
            try:
                user_code = code_input.value
                self._check_solution(user_code, task_data, results_output)
            finally:
                self.is_checking = False

        execute_button.on_click(on_execute_button_clicked)
        check_button.on_click(on_check_button_clicked)

        # Создаем интерфейс
        interface = widgets.VBox([
            title_html,
            description_html,
            code_input,
            widgets.HBox([execute_button, check_button]),
            results_output
        ])

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
        try:
            # ИСПРАВЛЕНО: Очищаем контейнер результатов
            results_output.children = []

            # Получаем параметры проверки переменной
            check_variable = task_data.get("check_variable")
            expected_variable_value = task_data.get("expected_variable_value")

            print(f"\n🔍 [DIAGNOSTIC] Проверка решения:")
            print(f"check_variable: {check_variable}")
            print(f"expected_variable_value: {expected_variable_value}")
            print(f"expected_output: {task_data.get('expected_output', 'НЕТ')}")

            # Проверяем выполнение
            validation_result = self.tasks_generator.validate_task_execution(
                user_code,
                task_data.get("expected_output", ""),
                check_variable=check_variable,
                expected_variable_value=expected_variable_value,
            )

            print(f"Результат валидации: {validation_result}")

            # Создаем все виджеты для отображения
            result_widgets = []

            if validation_result["is_correct"]:
                # Успех
                success_html = widgets.HTML(
                    value="<div style='background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 10px 0;'>"
                    "<h3 style='color: #155724; margin: 0;'>🎉 Задание выполнено правильно!</h3>"
                    "<p style='color: #155724; margin: 10px 0;'>Отличная работа! Вы успешно справились с заданием.</p>"
                    f"<p style='color: #155724; margin: 10px 0;'><strong>Ваш результат:</strong> {validation_result.get('actual_output', 'Нет вывода')}" +
                    (f"; <strong>Значение переменной:</strong> {validation_result.get('actual_variable')}" if check_variable else "") +
                    "</p>"
                    "</div>"
                )
                result_widgets.append(success_html)

                # Сохраняем результат
                self._save_task_result(task_data, True)

                # Добавляем кнопки для перехода
                success_buttons = self._create_success_buttons()
                result_widgets.extend(success_buttons)

            else:
                # Ошибка
                error_html = widgets.HTML(
                        value="<div style='background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px; margin: 10px 0;'>"
                        "<h3 style='color: #721c24; margin: 0;'>❌ Задание выполнено неправильно</h3>"
                        "<p style='color: #721c24; margin: 10px 0;'>Попробуйте еще раз или посмотрите эталонное решение.</p>"
                    f"<p style='color: #721c24; margin: 10px 0;'><strong>Ваш результат:</strong> {validation_result.get('actual_output', 'Нет вывода')}" +
                    (f"; <strong>Значение переменной:</strong> {validation_result.get('actual_variable')}" if check_variable else "") +
                    "</p>"
                    f"<p style='color: #721c24; margin: 10px 0;'><strong>Ожидаемый результат:</strong> {task_data.get('expected_output', 'Не указан')}" +
                    (f"; <strong>Ожидалось значение переменной:</strong> {expected_variable_value}" if check_variable else "") +
                    "</p>"
                        "</div>"
                    )
                result_widgets.append(error_html)

                # Эталонное решение
                solution_html = widgets.HTML(
                    value=f"<div style='background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 10px 0;'>"
                    f"<h4 style='color: #856404; margin: 0;'>Эталонное решение:</h4>"
                    f"<pre style='background-color: #f8f9fa; padding: 10px; border-radius: 3px; margin: 10px 0;'>{task_data.get('solution_code', '')}</pre>"
                    f"</div>"
                )
                result_widgets.append(solution_html)

                # Сохраняем результат
                self._save_task_result(task_data, False)

                # Добавляем кнопки для повторной попытки
                retry_buttons = self._create_retry_buttons()
                result_widgets.extend(retry_buttons)

            # ИСПРАВЛЕНО: Добавляем все виджеты в контейнер результатов
            results_output.children = result_widgets

        except Exception as e:
            error_html = widgets.HTML(
                value=f"<div style='background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px; margin: 10px 0;'>"
                f"<h3 style='color: #721c24; margin: 0;'>❌ Ошибка при проверке</h3>"
                f"<p style='color: #721c24; margin: 10px 0;'>{str(e)}</p>"
                f"</div>"
            )
            # ИСПРАВЛЕНО: Добавляем ошибку в контейнер результатов
            results_output.children = [error_html]

    def _save_task_result(self, task_data: Dict[str, Any], is_correct: bool):
        """
        Сохраняет результат выполнения задания.

        Args:
            task_data (Dict[str, Any]): Данные задания
            is_correct (bool): Правильно ли выполнено задание
        """
        try:
            # Получаем информацию о текущем уроке
            current_lesson_id = getattr(self.lesson_interface, 'current_lesson_id', None)
            current_course_info = getattr(self.lesson_interface, 'current_course_info', {})
            
            # Сохраняем результат в состояние
            if hasattr(self.lesson_interface, 'state_manager') and self.lesson_interface.state_manager:
                state_manager = self.lesson_interface.state_manager
                
                # Обновляем прогресс урока
                if current_lesson_id:
                    lesson_progress = state_manager.get_lesson_progress(current_lesson_id)
                    if lesson_progress:
                        lesson_progress["control_task_completed"] = True
                        lesson_progress["control_task_correct"] = is_correct
                        state_manager.save_lesson_progress(current_lesson_id, lesson_progress)
                
                # Обновляем общий прогресс курса
                if current_course_info:
                    course_id = current_course_info.get("course_id")
                    if course_id:
                        course_progress = state_manager.get_course_progress(course_id)
                        if course_progress:
                            completed_lessons = course_progress.get("completed_lessons", 0)
                            if is_correct:
                                course_progress["completed_lessons"] = completed_lessons + 1
                            state_manager.save_course_progress(course_id, course_progress)
            
            self.logger.info(f"Результат задания сохранен: {'правильно' if is_correct else 'неправильно'}")
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении результата задания: {str(e)}")

    def _create_success_buttons(self):
        """
        Создает кнопки после успешного выполнения задания.
        Теперь сначала показывается дашборд, а переход к следующему уроку — только после нажатия на кнопку на дашборде.
        Returns:
            List[widgets.Widget]: Список виджетов кнопок
        """
        # Кнопка показать дашборд
        dashboard_button = widgets.Button(
            description="📊 Показать дашборд обучения",
            button_style="info",
            layout=widgets.Layout(width="300px", margin="10px"),
        )

        def on_dashboard_clicked(b):
            from IPython.display import clear_output, display
            clear_output(wait=True)
            # Получаем ссылку на startup_dashboard через lesson_interface
            startup_dashboard = None
            engine = getattr(self.lesson_interface, "engine", None)
            if engine and hasattr(engine, "startup_dashboard") and engine.startup_dashboard:
                startup_dashboard = engine.startup_dashboard
            elif hasattr(self.lesson_interface, "startup_dashboard"):
                startup_dashboard = self.lesson_interface.startup_dashboard
            if startup_dashboard:
                dashboard_widget = startup_dashboard.show_dashboard()
                display(dashboard_widget)
                # Настроить обработчик кнопки 'Продолжить обучение'
                def after_dashboard(_):
                    clear_output(wait=True)
                    self._navigate_to_next_lesson()
                if hasattr(startup_dashboard, "continue_button") and startup_dashboard.continue_button:
                    startup_dashboard.continue_button.on_click(after_dashboard)
            else:
                # Если не удалось получить дашборд — fallback: сразу переход
                self._navigate_to_next_lesson()

        dashboard_button.on_click(on_dashboard_clicked)
        return [dashboard_button]

    def _create_retry_buttons(self):
        """
        Создает кнопки для повторной попытки.

        Returns:
            List[widgets.Widget]: Список виджетов кнопок
        """
        retry_button = widgets.Button(
            description="🔄 Попробовать снова",
            button_style="warning",
            layout=widgets.Layout(width="200px", margin="10px"),
        )

        continue_button = widgets.Button(
            description="⏭️ Пропустить задание",
            button_style="danger",
            layout=widgets.Layout(width="200px", margin="10px"),
        )

        def on_retry_clicked(b):
            # Логика возврата к уроку
            self._return_to_lesson()

        def on_continue_clicked(b):
            # Логика принудительного перехода
            self._force_next_lesson()

        retry_button.on_click(on_retry_clicked)
        continue_button.on_click(on_continue_clicked)

        return [retry_button, continue_button]

    def _navigate_to_next_lesson(self):
        """Переходит к следующему уроку."""
        try:
            if hasattr(self.lesson_interface, "_navigate_to_next_lesson"):
                self.lesson_interface._navigate_to_next_lesson()
            else:
                print("Метод _navigate_to_next_lesson не найден в lesson_interface")
        except Exception as e:
            self.logger.error(f"Ошибка при переходе к следующему уроку: {str(e)}")

    def _return_to_lesson(self):
        """Возвращается к уроку."""
        try:
            if hasattr(self.lesson_interface, "_return_to_lesson"):
                self.lesson_interface._return_to_lesson()
            else:
                print("Метод _return_to_lesson не найден в lesson_interface")
        except Exception as e:
            self.logger.error(f"Ошибка при возврате к уроку: {str(e)}")

    def _force_next_lesson(self):
        """Принудительно переходит к следующему уроку."""
        try:
            if hasattr(self.lesson_interface, "_force_next_lesson"):
                self.lesson_interface._force_next_lesson()
            else:
                print("Метод _force_next_lesson не найден в lesson_interface")
        except Exception as e:
            self.logger.error(f"Ошибка при принудительном переходе: {str(e)}")

    def _create_skip_task_interface(self, task_data: Dict[str, Any]) -> widgets.VBox:
        """
        Создает интерфейс для пропуска задания.

        Args:
            task_data (Dict[str, Any]): Данные задания

        Returns:
            widgets.VBox: Виджет с интерфейсом пропуска
        """
        skip_reason = task_data.get("skip_reason", "Задание не требуется для данного урока")

        skip_html = widgets.HTML(
            value=f"<div style='background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 20px; margin: 10px 0;'>"
            f"<h3 style='color: #856404; margin: 0;'>⏭️ Контрольное задание пропущено</h3>"
            f"<p style='color: #856404; margin: 10px 0;'>{skip_reason}</p>"
            f"<p style='color: #856404; margin: 10px 0;'>Урок будет отмечен как завершенный.</p>"
            f"</div>"
        )

        next_lesson_button = widgets.Button(
            description="➡️ Перейти к следующему уроку",
            button_style="success",
            layout=widgets.Layout(width="300px", margin="10px"),
        )

        def on_next_lesson_clicked(b):
            # Отмечаем урок как пройденный (так как контрольное задание не нужно)
            try:
                if hasattr(self.lesson_interface, "state_manager") and self.lesson_interface.state_manager:
                    current_lesson_id = getattr(self.lesson_interface, 'current_lesson_id', None)
                    if current_lesson_id:
                        lesson_progress = self.lesson_interface.state_manager.get_lesson_progress(current_lesson_id)
                        if lesson_progress:
                            lesson_progress["control_task_completed"] = True
                            lesson_progress["control_task_correct"] = True  # Пропуск считается успешным
                            self.lesson_interface.state_manager.save_lesson_progress(current_lesson_id, lesson_progress)
            except Exception as e:
                self.logger.error(f"Ошибка при сохранении прогресса: {str(e)}")
            
            # Переходим к следующему уроку
            self._navigate_to_next_lesson()

        next_lesson_button.on_click(on_next_lesson_clicked)

        interface = widgets.VBox([skip_html, next_lesson_button])
        return interface

    def _create_error_interface(self, error_message: str) -> widgets.VBox:
        """
        Создает интерфейс для отображения ошибки.

        Args:
            error_message (str): Сообщение об ошибке

        Returns:
            widgets.VBox: Виджет с интерфейсом ошибки
        """
        error_html = widgets.HTML(
            value=f"<div style='background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 20px; margin: 10px 0;'>"
            f"<h3 style='color: #721c24; margin: 0;'>❌ Ошибка загрузки задания</h3>"
            f"<p style='color: #721c24; margin: 10px 0;'>{error_message}</p>"
            f"</div>"
        )

        close_button = widgets.Button(
            description="❌ Закрыть",
            button_style="danger",
            layout=widgets.Layout(width="200px", margin="10px"),
        )

        def on_close_clicked(b):
            # Скрываем контейнер контрольных заданий
            try:
                if hasattr(self.lesson_interface, "_hide_control_tasks"):
                    self.lesson_interface._hide_control_tasks()
                else:
                    print("Метод _hide_control_tasks не найден в lesson_interface")
            except Exception as e:
                self.logger.error(f"Ошибка при закрытии: {str(e)}")

        close_button.on_click(on_close_clicked)

        interface = widgets.VBox([error_html, close_button])
        return interface 