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
            widgets.VBox: Виджет с заданием
        """
        import pprint
        print("\n[DEBUG] Контрольное задание, которое будет показано студенту:\n")
        pprint.pprint(task_data)
        print("\n[DEBUG] КОНЕЦ task_data\n")
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

        # ИСПРАВЛЕНО: Контейнер для результатов как VBox вместо Output
        results_output = widgets.VBox(layout=widgets.Layout(margin="10px 0"))

        # Обработчики кнопок
        def on_execute_button_clicked(b):
            # ИСПРАВЛЕНО: Очищаем контейнер результатов
            results_output.children = []
            
            try:
                # Создаем пространство имен для выполнения
                namespace = {}
                
                # Создаем буферы для захвата вывода
                import io
                import sys
                from contextlib import redirect_stdout
                
                output_buffer = io.StringIO()
                
                # Выполняем код с перехватом вывода
                with redirect_stdout(output_buffer):
                    exec(code_input.value, namespace)
                
                # Получаем результат
                output = output_buffer.getvalue()
                
                # Создаем виджет для отображения результата
                if output.strip():
                    result_html = widgets.HTML(
                        value=f"<p style='color: green;'>✅ Код выполнен успешно!</p><pre style='background: #f8f9fa; padding: 10px; border-radius: 4px;'>{output}</pre>"
                    )
                else:
                    result_html = widgets.HTML(
                        value="<p style='color: green;'>✅ Код выполнен успешно! (без вывода)</p>"
                        )
                
                # Добавляем результат в контейнер
                results_output.children = [result_html]
                
            except Exception as e:
                error_html = widgets.HTML(
                    value=f"<p style='color: red;'>❌ Ошибка выполнения: {str(e)}</p>"
                )
                # Добавляем ошибку в контейнер
                results_output.children = [error_html]

        def on_check_button_clicked(b):
            # ИСПРАВЛЕНО: Защита от множественных нажатий
            check_button.disabled = True
            check_button.description = "Проверяется..."
            try:
                self._check_solution(code_input.value, task_data, results_output)
            finally:
                # Восстанавливаем кнопку
                check_button.disabled = False
                check_button.description = "Проверить решение"

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
        # ИСПРАВЛЕНО: Защита от множественных вызовов
        if self.is_checking:
            self.logger.warning("Попытка множественного вызова _check_solution - игнорируем")
            return
        self.is_checking = True
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
            print(f"user_code: {user_code[:200]}...")

            # Проверяем выполнение
            validation_result = self.tasks_generator.validate_task_execution(
                user_code,
                task_data.get("expected_output", ""),
                check_variable=check_variable,
                expected_variable_value=expected_variable_value,
            )

            print(f"Результат валидации: {validation_result}")
            
            # Дополнительная диагностика
            if check_variable:
                print(f"🔍 [DIAGNOSTIC] Проверка переменной '{check_variable}':")
                print(f"   Ожидаемое значение: {expected_variable_value}")
                print(f"   Фактическое значение: {validation_result.get('actual_variable')}")
                print(f"   Совпадение: {validation_result.get('actual_variable') == expected_variable_value}")
            else:
                print(f"🔍 [DIAGNOSTIC] Проверка вывода:")
                print(f"   Ожидаемый вывод: '{task_data.get('expected_output', '')}'")
                print(f"   Фактический вывод: '{validation_result.get('actual_output', '')}'")
                print(f"   Совпадение: {validation_result.get('actual_output') == task_data.get('expected_output', '').strip()}")

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
                error_message = validation_result.get("error_message", "")
                error_details = ""
                if error_message:
                    error_details = f"<p style='color: #721c24; margin: 10px 0;'><strong>Ошибка исполнения:</strong><br><pre style='background-color: #f8f9fa; padding: 10px; border-radius: 3px; margin: 5px 0; font-size: 12px;'>{error_message}</pre></p>"
                
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
                    f"{error_details}"
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
        finally:
            # ИСПРАВЛЕНО: Сбрасываем флаг проверки
            self.is_checking = False

    def _save_task_result(self, task_data: Dict[str, Any], is_correct: bool):
        """
        Сохраняет результат выполнения задания.
        ИСПРАВЛЕНО: Урок отмечается как завершенный только при успешном выполнении контрольного задания

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
                
                # ИСПРАВЛЕНО: Если контрольное задание выполнено правильно И тест пройден - урок завершен
                if is_correct:
                    # Проверяем, пройден ли тест
                    if self.lesson_interface.state_manager.is_test_passed(lesson_id):
                        # Урок полностью завершен: тест пройден + контрольное задание выполнено
                        self.lesson_interface.state_manager.save_lesson_assessment(
                            lesson_id, 
                            self.lesson_interface.state_manager.get_lesson_score(lesson_id), 
                            True  # Теперь урок действительно завершен
                        )
                        # ДОБАВЛЕНО: всегда выставляем флаг завершённости
                        self.lesson_interface.state_manager.mark_lesson_complete_manually(lesson_id)
                        self.logger.info(f"Урок {lesson_id} полностью завершен: тест пройден + контрольное задание выполнено")
                    else:
                        self.logger.info(f"Контрольное задание выполнено, но тест не пройден для урока {lesson_id}")
                else:
                    self.logger.info(f"Контрольное задание НЕ выполнено для урока {lesson_id}")
                    
                self.logger.info(
                    f"Результат контрольного задания сохранен: {is_correct}"
                )
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении результата: {str(e)}")

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

    # Оставляю _show_success_buttons для обратной совместимости
    def _show_success_buttons(self):
        buttons = self._create_success_buttons()
        for button in buttons:
            display(button)

    def _create_retry_buttons(self):
        """
        Создает кнопки после неудачного выполнения задания.
        
        Returns:
            List[widgets.Widget]: Список виджетов кнопок
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
        return [buttons_container]
    
    def _show_retry_buttons(self):
        """
        Показывает кнопки после неудачного выполнения задания.
        """
        buttons = self._create_retry_buttons()
        for button in buttons:
            display(button)

    def _navigate_to_next_lesson(self):
        """
        Переходит к следующему уроку.
        """
        try:
            # ИСПРАВЛЕНО: Показываем сообщение о загрузке только если вывод не очищен
            display(widgets.HTML(value="<p>🔄 Переход к следующему уроку...</p>"))

            # Получаем следующий урок
            next_lesson = self.lesson_interface.state_manager.get_next_lesson()
            self.logger.info(f"get_next_lesson() вернул: {next_lesson}")

            if next_lesson and len(next_lesson) >= 3:
                section_id, topic_id, lesson_id = next_lesson[:3]
                current_lesson_id = self.lesson_interface.current_lesson_id
                next_lesson_id = f"{section_id}:{topic_id}:{lesson_id}"
                
                self.logger.info(f"Текущий урок: {current_lesson_id}")
                self.logger.info(f"Следующий урок: {next_lesson_id}")
                
                if current_lesson_id == next_lesson_id:
                    self.logger.warning("ВНИМАНИЕ: Следующий урок совпадает с текущим!")
                
                self.logger.info(
                    f"Переход к уроку: {section_id}:{topic_id}:{lesson_id}"
                )

                # ИСПРАВЛЕНО: Очищаем текущий вывод перед показом нового урока
                clear_output(wait=True)
                
                # Показываем следующий урок через правильную логику
                lesson_widget = self.lesson_interface.show_lesson(
                    section_id, topic_id, lesson_id
                )
                if lesson_widget:
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
            clear_output(wait=True)
            display(
                widgets.HTML(
                    value=f"<p style='color: red;'>❌ Ошибка при переходе к следующему уроку: {str(e)}</p>"
                )
            )

    def _return_to_lesson(self):
        """
        Возвращается к текущему уроку.
        """
        try:
            # ИСПРАВЛЕНО: Очищаем вывод и правильно возвращаемся к уроку
            clear_output(wait=True)
            
            # Показываем текущий урок
            current_info = self.lesson_interface.current_course_info
            lesson_widget = self.lesson_interface.show_lesson(
                current_info["section_id"],
                current_info["topic_id"],
                current_info["lesson_id"],
            )
            
            if lesson_widget:
                display(lesson_widget)
            else:
                display(
                    widgets.HTML(
                        value="<p style='color: red;'>❌ Ошибка при загрузке урока</p>"
                    )
            )
        except Exception as e:
            self.logger.error(f"Ошибка при возврате к уроку: {str(e)}")
            clear_output(wait=True)
            display(
                widgets.HTML(
                    value=f"<p style='color: red;'>❌ Ошибка при возврате к уроку: {str(e)}</p>"
                )
            )

    def _force_next_lesson(self):
        """
        Принудительно переходит к следующему уроку.
        """
        try:
            # ИСПРАВЛЕНО: Принудительно отмечаем урок как завершенный
            lesson_id = self.lesson_interface.current_lesson_id
            if lesson_id:
                # Отмечаем урок как завершенный вручную
                self.lesson_interface.state_manager.mark_lesson_complete_manually(lesson_id)
                self.logger.info(f"Урок {lesson_id} принудительно отмечен как завершенный")
                
                # Принудительно сохраняем состояние
                self.lesson_interface.state_manager.save_state()

            # ИСПРАВЛЕНО: Очищаем вывод перед переходом
            clear_output(wait=True)

            # Переходим к следующему уроку
            self._navigate_to_next_lesson()
        except Exception as e:
            self.logger.error(f"Ошибка при принудительном переходе: {str(e)}")
            clear_output(wait=True)
            display(
                widgets.HTML(
                    value=f"<p style='color: red;'>❌ Ошибка при принудительном переходе: {str(e)}</p>"
                )
            )

    def _create_skip_task_interface(self, task_data: Dict[str, Any]) -> widgets.VBox:
        """
        Создает интерфейс для уроков, где контрольное задание не нужно.

        Args:
            task_data (Dict[str, Any]): Данные задания с причиной пропуска

        Returns:
            widgets.VBox: Виджет с сообщением и кнопкой перехода
        """
        # Причина пропуска задания
        skip_reason = task_data.get("skip_reason", "Контрольное задание не требуется для данного урока")
        
        # Сообщение о пропуске
        skip_message = widgets.HTML(
            value=f"<div style='background-color: #e7f3ff; border: 1px solid #b8daff; border-radius: 5px; padding: 20px; margin: 10px 0;'>"
            f"<h3 style='color: #004085; margin: 0 0 10px 0;'>ℹ️ Контрольное задание не требуется</h3>"
            f"<p style='color: #004085; margin: 0;'>{skip_reason}</p>"
            f"<p style='color: #004085; margin: 10px 0 0 0;'>Урок можно считать пройденным. Переходите к следующему уроку.</p>"
            f"</div>"
        )
        
        # Кнопка перехода к следующему уроку
        next_lesson_button = widgets.Button(
            description="➡️ Перейти к следующему уроку",
            button_style="success",
            layout=widgets.Layout(width="300px", margin="20px 0"),
        )
        
        def on_next_lesson_clicked(b):
            # Отмечаем урок как пройденный (так как контрольное задание не нужно)
            lesson_id = self.lesson_interface.current_lesson_id
            if lesson_id:
                # ИСПРАВЛЕНО: Урок считается пройденным при пропуске контрольного задания 
                # независимо от результата теста
                self.lesson_interface.state_manager.mark_lesson_complete_manually(lesson_id)
                self.logger.info(f"Урок {lesson_id} отмечен как пройденный (контрольное задание не требуется)")
                
                # Принудительно сохраняем состояние
                self.lesson_interface.state_manager.save_state()
                
                # Проверяем, что урок действительно отмечен как завершенный
                is_completed = self.lesson_interface.state_manager.is_lesson_completed(lesson_id)
                self.logger.info(f"Проверка завершенности урока {lesson_id}: {is_completed}")
            
            # Состояние уже сохранено выше, дополнительная перезагрузка не требуется
            
            # Переходим к следующему уроку
            self._navigate_to_next_lesson()
        
        next_lesson_button.on_click(on_next_lesson_clicked)
        
        # Собираем интерфейс
        return widgets.VBox([
            skip_message,
            next_lesson_button
        ])

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
