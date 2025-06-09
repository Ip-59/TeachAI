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
        self, state_manager, assessment, system_logger, content_generator=None
    ):
        """
        Инициализация обработчика результатов.

        Args:
            state_manager: Менеджер состояния
            assessment: Модуль оценивания
            system_logger: Системный логгер
            content_generator: Генератор контента (для навигации)
        """
        self.state_manager = state_manager
        self.assessment = assessment
        self.system_logger = system_logger
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
        Обрабатывает отправку теста с правильной логикой завершенности уроков.

        Args:
            results_output: Контейнер для отображения результатов
            current_questions: Список вопросов теста
            current_answers: Список ответов пользователя
            course_plan: План курса
            course_title, section_title, topic_title, lesson_title: Названия элементов
            current_course, current_section, current_topic, current_lesson: ID элементов
        """
        with results_output:
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

                # Правильная логика сохранения результата
                lesson_id = f"{current_section}:{current_topic}:{current_lesson}"
                is_passed = score > 40  # Считаем пройденным при >40%

                # Сохраняем результат теста (с правильным флагом завершенности)
                self.state_manager.save_lesson_assessment(lesson_id, score, is_passed)

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

                # Отображаем результаты с правильной логикой завершенности
                self.display_enhanced_test_results(
                    score,
                    correct_answers,
                    current_questions,
                    current_answers,
                    current_section,
                    current_topic,
                    current_lesson,
                    is_passed,
                    lesson_id,
                )

            except Exception as e:
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
        # Заголовок результатов
        display(
            widgets.HTML(
                value="<h2 style='margin: 5px 0; font-size: 20px;'>Результаты теста</h2>"
            )
        )

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

        display(
            widgets.HTML(
                value=f"<div style='text-align: center; padding: 12px; margin: 5px 0; border-radius: 8px; font-size: 24px; font-weight: bold; {score_style}'>Ваш результат: {score:.1f}%</div>"
            )
        )

        # Получаем и показываем общий прогресс по курсу
        course_stats = self.state_manager.get_detailed_course_statistics()

        display(
            widgets.HTML(
                value=f"""
            <div style='background-color: #e9ecef; padding: 15px; margin: 10px 0; border-radius: 8px; border: 1px solid #adb5bd;'>
                <h3 style='margin: 0 0 10px 0; color: #495057; font-size: 18px;'>📊 Общий прогресс по курсу</h3>
                <p style='margin: 5px 0; font-size: 16px;'><strong>Средний балл по курсу:</strong> {course_stats['average_score']:.1f}%</p>
                <p style='margin: 5px 0; font-size: 16px;'><strong>Пройдено тестов:</strong> {course_stats['total_assessments']}</p>
                <p style='margin: 5px 0; font-size: 16px;'><strong>Прогресс курса:</strong> {course_stats['course_progress_percent']:.1f}% ({course_stats['completed_lessons']} из {course_stats['total_lessons']} уроков)</p>
            </div>
            """
            )
        )

        # Детальные результаты по вопросам (сокращенно)
        display(
            widgets.HTML(
                value="<h3 style='margin: 10px 0 5px 0; font-size: 18px;'>Детальные результаты:</h3>"
            )
        )

        for i, (question, user_answer, correct_answer) in enumerate(
            zip(current_questions, current_answers, correct_answers)
        ):
            options = question.get("options", ["Нет вариантов"])

            result_html = f"""
            <div style="margin: 5px 0; padding: 8px; border: 1px solid #dee2e6; border-radius: 6px; background-color: #ffffff;">
                <div style="font-weight: bold; margin-bottom: 4px; font-size: 16px; color: #212529; line-height: 1.3;">Вопрос {i+1}: {question['text']}</div>
            """

            for j, option in enumerate(options):
                option_num = j + 1
                if option_num == user_answer and option_num == correct_answer:
                    result_html += f'<div style="margin: 2px 0; padding: 4px 6px; border-radius: 4px; font-size: 15px; line-height: 1.3; background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;">{option} ✓ (Ваш ответ, правильно)</div>'
                elif option_num == user_answer:
                    result_html += f'<div style="margin: 2px 0; padding: 4px 6px; border-radius: 4px; font-size: 15px; line-height: 1.3; background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;">{option} ✗ (Ваш ответ, неправильно)</div>'
                elif option_num == correct_answer:
                    result_html += f'<div style="margin: 2px 0; padding: 4px 6px; border-radius: 4px; font-size: 15px; line-height: 1.3; background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;">{option} ✓ (Правильный ответ)</div>'
                else:
                    result_html += f'<div style="margin: 2px 0; padding: 4px 6px; border-radius: 4px; font-size: 15px; line-height: 1.3; background-color: #f8f9fa; color: #495057; border: 1px solid #dee2e6;">{option}</div>'

            result_html += "</div>"
            display(widgets.HTML(value=result_html))

        # Кнопки в зависимости от результата с правильной логикой завершенности
        if is_passed:  # Оценка > 40%
            display(
                widgets.HTML(
                    value="<h3 style='margin: 15px 0 10px 0; font-size: 18px; color: #28a745;'>🎉 Поздравляем! Урок успешно пройден!</h3>"
                )
            )

            # Автоматический переход к следующему уроку
            (
                next_section_id,
                next_topic_id,
                next_lesson_id,
                next_lesson_data,
            ) = self.state_manager.get_next_lesson()

            if next_section_id and next_topic_id and next_lesson_id:
                # Есть следующий урок
                display(
                    widgets.HTML(
                        value="<p style='margin: 5px 0; font-size: 16px;'>Готовы к переходу к следующему уроку.</p>"
                    )
                )

                # Кнопка перехода к следующему уроку
                next_lesson_button = widgets.Button(
                    description="Следующий урок",
                    button_style="success",
                    tooltip="Перейти к следующему уроку",
                    icon="arrow-right",
                    layout=widgets.Layout(margin="5px 5px 5px 0px"),
                )

                def on_next_lesson_clicked(b):
                    clear_output(wait=True)
                    from lesson_interface import LessonInterface

                    lesson_ui = LessonInterface(
                        self.state_manager,
                        self.content_generator,
                        self.system_logger,
                        self.assessment,
                    )
                    display(
                        lesson_ui.show_lesson(
                            next_section_id, next_topic_id, next_lesson_id
                        )
                    )

                next_lesson_button.on_click(on_next_lesson_clicked)
                display(next_lesson_button)
            else:
                # Курс завершен
                display(
                    widgets.HTML(
                        value="<p style='margin: 5px 0; font-size: 16px; color: #28a745;'><strong>🏆 Поздравляем! Вы завершили весь курс!</strong></p>"
                    )
                )

                # Кнопка завершения курса
                complete_course_button = widgets.Button(
                    description="Завершить курс",
                    button_style="success",
                    tooltip="Перейти к экрану завершения курса",
                    icon="trophy",
                    layout=widgets.Layout(margin="5px 0"),
                )

                def on_complete_course_clicked(b):
                    clear_output(wait=True)
                    from completion_interface import CompletionInterface

                    completion_ui = CompletionInterface(
                        self.state_manager,
                        self.system_logger,
                        self.content_generator,
                        self.assessment,
                    )
                    display(completion_ui.show_course_completion())

                complete_course_button.on_click(on_complete_course_clicked)
                display(complete_course_button)

        else:  # Оценка ≤ 40%
            display(
                widgets.HTML(
                    value="<h3 style='margin: 15px 0 10px 0; font-size: 18px; color: #dc3545;'>📚 Рекомендуем повторить материал</h3>"
                )
            )
            display(
                widgets.HTML(
                    value=f"<p style='margin: 5px 0; font-size: 16px;'>Ваш результат ({score:.1f}%) ниже порогового значения (40%). Выберите дальнейшие действия:</p>"
                )
            )

            # Кнопка повторения урока
            repeat_lesson_button = widgets.Button(
                description="Изучить урок снова",
                button_style="warning",
                tooltip="Вернуться к изучению урока",
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

                clear_output(wait=True)
                from lesson_interface import LessonInterface

                lesson_ui = LessonInterface(
                    self.state_manager,
                    self.content_generator,
                    self.system_logger,
                    self.assessment,
                )
                display(
                    lesson_ui.show_lesson(
                        current_section, current_topic, current_lesson
                    )
                )

            def on_continue_anyway_clicked(b):
                # Принудительно отмечаем урок как завершенный
                self.state_manager.save_lesson_assessment(
                    lesson_id, score, True
                )  # is_passed=True принудительно

                # Переходим к следующему уроку
                (
                    next_section_id,
                    next_topic_id,
                    next_lesson_id,
                    next_lesson_data,
                ) = self.state_manager.get_next_lesson()

                clear_output(wait=True)
                if next_section_id and next_topic_id and next_lesson_id:
                    from lesson_interface import LessonInterface

                    lesson_ui = LessonInterface(
                        self.state_manager,
                        self.content_generator,
                        self.system_logger,
                        self.assessment,
                    )
                    display(
                        lesson_ui.show_lesson(
                            next_section_id, next_topic_id, next_lesson_id
                        )
                    )
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

            display(
                widgets.HBox(
                    [repeat_lesson_button, continue_anyway_button],
                    layout=widgets.Layout(margin="2px 0"),
                )
            )
