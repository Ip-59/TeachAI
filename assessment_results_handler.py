"""
Обработчик результатов тестирования знаний.
Отвечает за обработку отправки теста, отображение результатов и логику перехода к следующему уроку.
РЕФАКТОРИНГ: Выделен из assessment_interface.py для лучшей модульности (часть 1/2)
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging


class AssessmentResultsHandler:
    """Обработчик результатов тестирования."""

    def __init__(
        self,
        state_manager,
        assessment,
        system_logger,
        content_generator=None,
        lesson_interface=None,
    ):
        """
        Инициализация обработчика результатов.

        Args:
            state_manager: Менеджер состояния
            assessment: Модуль оценивания
            system_logger: Системный логгер
            content_generator: Генератор контента (для навигации)
            lesson_interface: Интерфейс урока (для активации кнопок)
        """
        self.state_manager = state_manager
        self.assessment = assessment
        self.system_logger = system_logger
        self.lesson_interface = lesson_interface
        self.logger = logging.getLogger(__name__)

        # Создаем content_generator если не передан (для навигации)
        if content_generator is None:
            try:
                from content_generator import ContentGenerator
                from config import ConfigManager

                config_manager = ConfigManager()
                config_manager.load_config()
                api_key = config_manager.get_api_key()
                self.content_generator = ContentGenerator(api_key)
            except Exception as e:
                self.logger.error(f"ОШИБКА при создании ContentGenerator: {str(e)}")
                self.content_generator = None
        else:
            self.content_generator = content_generator

    def handle_test_submission(
        self,
        results_output,
        current_questions,
        current_answers,
        course_plan,
        course_title,
        section_title,
        topic_title,
        lesson_title,
        current_course,
        current_section,
        current_topic,
        current_lesson,
    ):
        """
        Обрабатывает отправку результатов теста.
        """
        with results_output:
            # ЕДИНСТВЕННАЯ ОЧИСТКА ВЫВОДА В НАЧАЛЕ
            clear_output(wait=True)
            
            # Проверяем, что на все вопросы даны ответы
            unanswered_questions = [
                i + 1 for i, answer in enumerate(current_answers) if answer is None
            ]
            if unanswered_questions:
                display(
                    widgets.HTML(
                        value=f"<p style='color: #856404; background-color: #fff3cd; padding: 10px; border-radius: 5px; margin: 3px 0;'>Пожалуйста, ответьте на вопросы: {', '.join(map(str, unanswered_questions))} перед завершением теста.</p>"
                    )
                )
                return

            try:
                # Расчет результатов
                score, results, correct_answers = self.assessment.calculate_score(
                    current_questions, current_answers
                )

                # ИСПРАВЛЕНО: Урок НЕ завершается только на основе теста
                # Тест только сохраняется как пройденный/не пройденный
                lesson_id = f"{current_section}:{current_topic}:{current_lesson}"
                is_test_passed = score > 40  # Тест считается пройденным при >40%

                # ИСПРАВЛЕНО: Сохраняем результат теста с правильным статусом прохождения
                self.state_manager.save_lesson_assessment(lesson_id, score, is_test_passed)

                # Получаем ID курса
                course_id = course_plan.get("id", current_course)

                # Логируем результаты
                self.assessment.log_assessment_results(
                    course=course_id,
                    section=current_section,
                    topic=current_topic,
                    lesson=current_lesson,
                    questions=current_questions,
                    user_answers=current_answers,
                    correct_answers=correct_answers,
                    score=score,
                )

                # ИСПРАВЛЕНО: Отображаем результаты БЕЗ дополнительных очисток
                self.display_enhanced_test_results(
                    score,
                    correct_answers,
                    current_questions,
                    current_answers,
                    current_section,
                    current_topic,
                    current_lesson,
                    is_test_passed,
                    lesson_id,
                )

            except Exception as e:
                # В случае ошибки показываем сообщение об ошибке
                display(
                    widgets.HTML(
                        value=f"<p style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px; margin: 3px 0;'>Ошибка при обработке результатов теста: {str(e)}</p>"
                    )
                )

    def display_enhanced_test_results(
        self,
        score,
        correct_answers,
        current_questions,
        current_answers,
        current_section,
        current_topic,
        current_lesson,
        is_passed,
        lesson_id,
    ):
        """
        Отображает результаты тестирования с правильной логикой завершенности уроков.

        Args:
            score (float): Оценка за тест
            correct_answers (list): Список правильных ответов
            current_questions (list): Список вопросов
            current_answers (list): Список ответов пользователя
            current_section, current_topic, current_lesson (str): ID элементов
            is_passed (bool): Завершен ли урок
            lesson_id (str): Полный ID урока
        """
        # Создаем список всех виджетов результатов
        result_widgets = []
        
        # Заголовок результатов
        result_widgets.append(widgets.HTML(
            value="<h2 style='margin: 5px 0; font-size: 20px;'>Результаты теста</h2>"
        ))

        # Показываем оценку за тест
        if score >= 80:
            score_style = (
                "background-color: #d4edda; color: #155724; border: 2px solid #c3e6cb;"
            )
        elif score >= 60:
            score_style = (
                "background-color: #fff3cd; color: #856404; border: 2px solid #ffeaa7;"
            )
        else:
            score_style = (
                "background-color: #f8d7da; color: #721c24; border: 2px solid #f5c6cb;"
            )

        result_widgets.append(widgets.HTML(
            value=f"<div style='text-align: center; padding: 12px; margin: 5px 0; border-radius: 8px; font-size: 24px; font-weight: bold; {score_style}'>Ваш результат: {score:.1f}%</div>"
        ))

        # Получаем и показываем общий прогресс по курсу
        course_stats = self.state_manager.get_detailed_course_statistics()

        result_widgets.append(widgets.HTML(
            value=f"""
            <div style='background-color: #e9ecef; padding: 15px; margin: 10px 0; border-radius: 8px; border: 1px solid #adb5bd;'>
                <h3 style='margin: 0 0 10px 0; color: #495057; font-size: 18px;'>📊 Общий прогресс по курсу</h3>
                <p style='margin: 5px 0; font-size: 16px;'><strong>Средний балл по курсу:</strong> {course_stats['average_score']:.1f}%</p>
                <p style='margin: 5px 0; font-size: 16px;'><strong>Пройдено тестов:</strong> {course_stats['total_assessments']}</p>
                <p style='margin: 5px 0; font-size: 16px;'><strong>Прогресс курса:</strong> {course_stats['course_progress_percent']:.1f}% ({course_stats['completed_lessons']} из {course_stats['total_lessons']} уроков)</p>
            </div>
            """
        ))

        # Детальные результаты по вопросам (сокращенно)
        result_widgets.append(widgets.HTML(
            value="<h3 style='margin: 10px 0 5px 0; font-size: 18px;'>Детальные результаты:</h3>"
        ))

        # Создаем виджеты для каждого вопроса
        for i, (question, user_answer, correct_answer) in enumerate(
            zip(current_questions, current_answers, correct_answers)
        ):
            options = question.get("options", ["Нет вариантов"])

            # ИСПРАВЛЕНО: Правильно обрабатываем правильный ответ как номер варианта
            correct_answer_num = correct_answer if isinstance(correct_answer, int) else int(correct_answer)

            result_html = f"""
            <div style="margin: 5px 0; padding: 8px; border: 1px solid #dee2e6; border-radius: 6px; background-color: #ffffff;">
                <div style="font-weight: bold; margin-bottom: 4px; font-size: 16px; color: #212529; line-height: 1.3;">Вопрос {i+1}: {question['text']}</div>
                <div style="margin-top: 8px; padding: 8px; background-color: #f8f9fa; border-radius: 4px; border-left: 3px solid #007bff;">
                    <strong style="color: #495057;">Правильный ответ:</strong>
                    <div style="margin-top: 4px; color: #212529; line-height: 1.4;">{options[correct_answer_num - 1]}</div>
                </div>
            """

            for j, option in enumerate(options):
                option_num = j + 1
                if option_num == user_answer and option_num == correct_answer_num:
                    result_html += f'<div style="margin: 2px 0; padding: 4px 6px; border-radius: 4px; font-size: 15px; line-height: 1.3; background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;">{option} ✓ (Ваш ответ, правильно)</div>'
                elif option_num == user_answer:
                    result_html += f'<div style="margin: 2px 0; padding: 4px 6px; border-radius: 4px; font-size: 15px; line-height: 1.3; background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;">{option} ✗ (Ваш ответ, неправильно)</div>'
                elif option_num == correct_answer_num:
                    result_html += f'<div style="margin: 2px 0; padding: 4px 6px; border-radius: 4px; font-size: 15px; line-height: 1.3; background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;">{option} ✓ (Правильный ответ)</div>'
                else:
                    result_html += f'<div style="margin: 2px 0; padding: 4px 6px; border-radius: 4px; font-size: 15px; line-height: 1.3; background-color: #f8f9fa; color: #495057; border: 1px solid #dee2e6;">{option}</div>'

            result_html += "</div>"
            result_widgets.append(widgets.HTML(value=result_html))

        # Кнопки в зависимости от результата с правильной логикой завершенности
        if is_passed:  # Оценка > 40%
            result_widgets.append(widgets.HTML(
                value="<h3 style='margin: 15px 0 10px 0; font-size: 18px; color: #28a745;'>🎉 Поздравляем! Урок успешно пройден!</h3>"
            ))

            # Если тест пройден успешно
            if is_passed:
                # Активируем кнопку "Контрольные задания"
                self._activate_control_tasks_button()

                # Показываем сообщение об успешном прохождении
                result_widgets.append(widgets.HTML(
                    value=f"<p style='color: green; font-weight: bold;'>🎉 Тест пройден успешно! Доступны контрольные задания. Перейдите к выполнению контрольных заданий для завершения урока.</p>"
                ))

                # Добавляем кнопку для перехода к контрольным заданиям
                control_tasks_button = widgets.Button(
                    description="🛠️ Перейти к контрольным заданиям",
                    button_style="success",
                    layout=widgets.Layout(width="300px", margin="10px 0"),
                    tooltip="Нажмите, чтобы выполнить контрольные задания",
                )

                def on_control_tasks_clicked(b):
                    # Скрываем результаты теста
                    clear_output(wait=True)
                    self._show_control_tasks()

                control_tasks_button.on_click(on_control_tasks_clicked)
                result_widgets.append(control_tasks_button)

        else:
            # Тест не пройден - предлагаем повторить
            result_widgets.append(widgets.HTML(
                value="<h3 style='margin: 15px 0 10px 0; font-size: 18px; color: #dc3545;'>😔 Тест не пройден</h3>"
            ))

            result_widgets.append(widgets.HTML(
                value="<p style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0;'>Для прохождения урока необходимо набрать более 40%. Попробуйте еще раз или продолжите с текущей оценкой.</p>"
            ))

            # Кнопка повторения урока
            repeat_lesson_button = widgets.Button(
                description="Повторить урок",
                button_style="warning",
                tooltip="Вернуться к изучению материала урока",
                icon="refresh",
                layout=widgets.Layout(margin="5px 5px 5px 0px"),
            )

            # Кнопка продолжения с текущей оценкой
            continue_anyway_button = widgets.Button(
                description="Продолжить с текущей оценкой",
                button_style="info",
                tooltip="Продолжить обучение с текущим результатом",
                icon="arrow-right",
                layout=widgets.Layout(margin="5px 0px 5px 5px"),
            )

            def on_repeat_lesson_clicked(b):
                # Правильно отмечаем урок как незавершенный
                self.state_manager.mark_lesson_incomplete(lesson_id)

                # ИСПРАВЛЕНО: Убираем прямой вызов display() для избежания дублирования
                clear_output(wait=True)
                from lesson_interface import LessonInterface

                lesson_ui = LessonInterface(
                    self.state_manager,
                    self.content_generator,
                    self.system_logger,
                    self.assessment,
                )
                
                # Создаем виджет урока
                lesson_widget = lesson_ui.show_lesson(
                        current_section, current_topic, current_lesson
                )
                
                # Отображаем только один раз
                display(lesson_widget)

            def on_continue_anyway_clicked(b):
                # ИСПРАВЛЕНО: Принудительно отмечаем урок как завершенный
                self.state_manager.mark_lesson_complete_manually(lesson_id)

                # Активируем кнопку "Контрольные задания"
                self._activate_control_tasks_button()

                # Переходим к следующему уроку
                (
                    next_section_id,
                    next_topic_id,
                    next_lesson_id,
                    next_lesson_data,
                ) = self.state_manager.get_next_lesson()

                clear_output(wait=True)
                if next_section_id and next_topic_id and next_lesson_id:
                    # ИСПРАВЛЕНО: Убираем прямой вызов display() для избежания дублирования
                    from lesson_interface import LessonInterface

                    lesson_ui = LessonInterface(
                        self.state_manager,
                        self.content_generator,
                        self.system_logger,
                        self.assessment,
                    )
                    
                    # Создаем виджет урока
                    lesson_widget = lesson_ui.show_lesson(
                            next_section_id, next_topic_id, next_lesson_id
                    )
                    
                    # Отображаем только один раз
                    display(lesson_widget)
                else:
                    # Курс завершен
                    from completion_interface import CompletionInterface

                    completion_ui = CompletionInterface(
                        self.state_manager,
                        self.system_logger,
                        self.content_generator,
                        self.assessment,
                    )
                    display(completion_ui.show_course_completion())

            repeat_lesson_button.on_click(on_repeat_lesson_clicked)
            continue_anyway_button.on_click(on_continue_anyway_clicked)

            # Добавляем кнопки
            buttons_container = widgets.HBox([repeat_lesson_button, continue_anyway_button])
            result_widgets.append(buttons_container)

        # ИСПРАВЛЕНО: Отображаем все результаты ОДНИМ вызовом display()
        # Создаем единый контейнер со всеми результатами
        results_container = widgets.VBox(result_widgets)
        display(results_container)

    def _activate_control_tasks_button(self):
        """
        Активирует кнопку "Контрольные задания" в интерфейсе урока.
        """
        try:
            if self.lesson_interface and hasattr(self.lesson_interface, "navigation"):
                # Получаем ссылку на кнопку через navigation
                navigation = self.lesson_interface.navigation
                if (
                    hasattr(navigation, "control_tasks_button")
                    and navigation.control_tasks_button
                ):
                    navigation.control_tasks_button.disabled = False
                    navigation.control_tasks_button.tooltip = "Доступно для выполнения"
                    self.logger.info("Кнопка 'Контрольные задания' активирована")
                else:
                    self.logger.warning(
                        "Кнопка 'Контрольные задания' не найдена в navigation"
                    )
                    # Дополнительная диагностика
                    if hasattr(navigation, "__dict__"):
                        self.logger.debug(
                            f"Доступные атрибуты navigation: {list(navigation.__dict__.keys())}"
                        )
            else:
                self.logger.warning("lesson_interface или navigation недоступны")
                if self.lesson_interface:
                    self.logger.debug(
                        f"Доступные атрибуты lesson_interface: {list(self.lesson_interface.__dict__.keys())}"
                    )
        except Exception as e:
            self.logger.error(
                f"Ошибка при активации кнопки контрольных заданий: {str(e)}"
            )
            import traceback

            self.logger.error(f"Полный traceback: {traceback.format_exc()}")

    def _show_control_tasks(self):
        """
        Показывает контрольные задания пользователю.
        """
        try:
            if self.lesson_interface and hasattr(
                self.lesson_interface, "control_tasks_interface"
            ):
                # Показываем контрольные задания
                task_interface = (
                    self.lesson_interface.control_tasks_interface.show_control_task(
                        lesson_data=self.lesson_interface.current_lesson_data,
                        lesson_content=(
                            self.lesson_interface.current_lesson_raw_content
                            or self.lesson_interface.current_lesson_content
                        ),
                    )
                )
                display(task_interface)
            else:
                display(
                    widgets.HTML(
                        value="<p style='color: red;'>Ошибка: интерфейс контрольных заданий недоступен</p>"
                    )
                )
        except Exception as e:
            self.logger.error(f"Ошибка при показе контрольных заданий: {str(e)}")
            display(
                widgets.HTML(
                    value=f"<p style='color: red;'>Ошибка при загрузке контрольных заданий: {str(e)}</p>"
                )
            )
