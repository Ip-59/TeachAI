"""
Обработчик результатов тестирования знаний.
Отвечает за обработку отправки теста, отображение результатов и логику перехода к следующему уроку.
РЕФАКТОРИНГ: Выделен из assessment_interface.py для лучшей модульности (часть 1/2)
ИСПРАВЛЕНО ЭТАП 38: Исправлен метод сохранения результатов тестов во ВСЕХ местах (проблема #158, #161)
ИСПРАВЛЕНО ЭТАП 38: Исправлена распаковка результата calculate_score (проблема #163)
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
                # ИСПРАВЛЕНО ЭТАП 38: Правильная распаковка результата calculate_score (проблема #163)
                # calculate_score возвращает: (score_percentage, correct_answers_list, score_count)
                score, correct_answers, score_count = self.assessment.calculate_score(
                    current_questions, current_answers
                )

                # Добавляем отладочное логирование
                self.logger.info(f"Результаты теста:")
                self.logger.info(f"  • Оценка: {score:.1f}%")
                self.logger.info(f"  • Правильных ответов: {score_count}")
                self.logger.info(f"  • Список правильных ответов: {correct_answers}")
                self.logger.info(f"  • Тип correct_answers: {type(correct_answers)}")

                # Правильная логика сохранения результата
                lesson_id = f"{current_section}:{current_topic}:{current_lesson}"
                is_passed = score > 40  # Считаем пройденным при >40%

                # ИСПРАВЛЕНО ЭТАП 38: Используем правильный метод mark_lesson_completed (проблема #158, #161)
                if is_passed:
                    self.state_manager.mark_lesson_completed(lesson_id)
                    self.logger.info(
                        f"Урок {lesson_id} отмечен как завершенный с оценкой {score:.1f}%"
                    )
                else:
                    self.logger.info(
                        f"Урок {lesson_id} не пройден (оценка {score:.1f}%)"
                    )

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
                self.logger.error(f"Ошибка при обработке результатов теста: {str(e)}")
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
        try:
            course_stats = self.state_manager.get_detailed_course_statistics()
        except:
            # Если метод не существует, используем базовую статистику
            completed_lessons = self.state_manager.get_completed_lessons()
            course_stats = {
                "completed_lessons_count": len(completed_lessons),
                "total_lessons_count": 10,  # Заглушка
                "average_score": score,  # Заглушка
            }

        display(
            widgets.HTML(
                value=f"""
            <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; border: 1px solid #dee2e6;'>
                <h3 style='margin: 0 0 10px 0; color: #495057;'>📊 Общий прогресс по курсу</h3>
                <p style='margin: 3px 0;'><strong>Завершено уроков:</strong> {course_stats.get('completed_lessons_count', 0)}</p>
                <p style='margin: 3px 0;'><strong>Всего уроков:</strong> {course_stats.get('total_lessons_count', 'Неизвестно')}</p>
                <p style='margin: 3px 0;'><strong>Средний балл:</strong> {course_stats.get('average_score', 'Неизвестно')}</p>
            </div>
            """
            )
        )

        # Детальные результаты по вопросам
        display(
            widgets.HTML(
                value="<h3 style='margin: 15px 0 5px 0; font-size: 16px;'>Детальные результаты:</h3>"
            )
        )

        for i, (question, user_answer, correct_answer) in enumerate(
            zip(current_questions, current_answers, correct_answers)
        ):
            is_correct = user_answer == correct_answer
            result_color = "#28a745" if is_correct else "#dc3545"
            result_icon = "✅" if is_correct else "❌"

            # Безопасное получение текста вопроса
            question_text = question.get(
                "text", question.get("question", "Вопрос не загружен")
            )

            display(
                widgets.HTML(
                    value=f"""
                <div style='margin: 8px 0; padding: 10px; border-radius: 5px; border-left: 4px solid {result_color}; background-color: #f8f9fa;'>
                    <div style='font-weight: bold; margin-bottom: 5px;'>{result_icon} Вопрос {i+1}: {question_text}</div>
                    <div style='margin: 3px 0;'><strong>Ваш ответ:</strong> {user_answer or "Не отвечено"}</div>
                    <div style='margin: 3px 0;'><strong>Правильный ответ:</strong> {correct_answer}</div>
                </div>
                """
                )
            )

        # Навигационные кнопки в зависимости от результата
        self._create_navigation_buttons_by_score(
            score, is_passed, lesson_id, current_section, current_topic, current_lesson
        )

    def _create_navigation_buttons_by_score(
        self,
        score,
        is_passed,
        lesson_id,
        current_section,
        current_topic,
        current_lesson,
    ):
        """
        Создает навигационные кнопки в зависимости от оценки.

        Args:
            score (float): Оценка за тест
            is_passed (bool): Прошел ли тест
            lesson_id (str): ID урока
            current_section, current_topic, current_lesson (str): ID элементов
        """
        if is_passed:  # Оценка > 40%
            display(
                widgets.HTML(
                    value="<h3 style='margin: 15px 0 10px 0; font-size: 18px; color: #28a745;'>🎉 Урок успешно пройден!</h3>"
                )
            )

            # Проверяем, есть ли следующий урок
            try:
                next_lesson_data = self.state_manager.get_next_lesson()
                if next_lesson_data and len(next_lesson_data) >= 3:
                    next_section_id, next_topic_id, next_lesson_id = next_lesson_data[
                        :3
                    ]
                    has_next_lesson = True
                else:
                    has_next_lesson = False
            except:
                has_next_lesson = False

            if has_next_lesson:
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
                    layout=widgets.Layout(
                        width="200px", height="40px", margin="10px 5px"
                    ),
                )

                def on_next_lesson_clicked(b):
                    try:
                        clear_output(wait=True)
                        display(
                            widgets.HTML(
                                value="<p>Переход к следующему уроку...</p>",
                                layout=widgets.Layout(margin="20px 0"),
                            )
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Ошибка при переходе к следующему уроку: {str(e)}"
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
                    layout=widgets.Layout(
                        width="200px", height="40px", margin="10px 5px"
                    ),
                )

                def on_complete_course_clicked(b):
                    try:
                        clear_output(wait=True)
                        display(
                            widgets.HTML(
                                value="<p>Переход к завершению курса...</p>",
                                layout=widgets.Layout(margin="20px 0"),
                            )
                        )
                    except Exception as e:
                        self.logger.error(f"Ошибка при завершении курса: {str(e)}")

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
                layout=widgets.Layout(width="200px", height="40px", margin="10px 5px"),
            )

            # Кнопка продолжения с текущей оценкой
            continue_anyway_button = widgets.Button(
                description="Продолжить с текущей оценкой",
                button_style="info",
                tooltip="Продолжить обучение с текущим результатом",
                icon="arrow-right",
                layout=widgets.Layout(width="250px", height="40px", margin="10px 5px"),
            )

            def on_repeat_lesson_clicked(b):
                try:
                    clear_output(wait=True)
                    display(
                        widgets.HTML(
                            value="<p>Возвращение к уроку для повторного изучения...</p>",
                            layout=widgets.Layout(margin="20px 0"),
                        )
                    )
                except Exception as e:
                    self.logger.error(f"Ошибка при возврате к уроку: {str(e)}")

            def on_continue_anyway_clicked(b):
                # ИСПРАВЛЕНО ЭТАП 38: Используем mark_lesson_completed вместо save_lesson_assessment (проблема #161)
                try:
                    # Принудительно отмечаем урок как завершенный
                    self.state_manager.mark_lesson_completed(lesson_id)
                    self.logger.info(
                        f"Урок {lesson_id} принудительно отмечен как завершенный"
                    )

                    clear_output(wait=True)
                    display(
                        widgets.HTML(
                            value="<p>Переход к следующему уроку с текущей оценкой...</p>",
                            layout=widgets.Layout(margin="20px 0"),
                        )
                    )
                except Exception as e:
                    self.logger.error(
                        f"Ошибка при принудительном завершении урока: {str(e)}"
                    )

            repeat_lesson_button.on_click(on_repeat_lesson_clicked)
            continue_anyway_button.on_click(on_continue_anyway_clicked)

            display(
                widgets.HBox(
                    [repeat_lesson_button, continue_anyway_button],
                    layout=widgets.Layout(justify_content="center", margin="10px 0"),
                )
            )

        # Кнопка возврата к уроку (всегда доступна)
        back_to_lesson_button = widgets.Button(
            description="Вернуться к уроку",
            button_style="",
            tooltip="Вернуться к содержанию урока",
            icon="book",
            layout=widgets.Layout(width="200px", height="40px", margin="10px 5px"),
        )

        def on_back_to_lesson_clicked(b):
            try:
                clear_output(wait=True)
                display(
                    widgets.HTML(
                        value="<p>Возвращение к уроку...</p>",
                        layout=widgets.Layout(margin="20px 0"),
                    )
                )
            except Exception as e:
                self.logger.error(f"Ошибка при возврате к уроку: {str(e)}")

        back_to_lesson_button.on_click(on_back_to_lesson_clicked)
        display(back_to_lesson_button)

    def show_results(self, assessment_results=None):
        """
        Отображает результаты тестирования.

        Args:
            assessment_results (dict): Результаты тестирования
        """
        if assessment_results is None:
            # Показываем заглушку если результатов нет
            return widgets.HTML(
                value="<p>Результаты теста будут отображены здесь после завершения</p>",
                layout=widgets.Layout(margin="10px 0"),
            )

        # Создаем интерфейс результатов
        results_html = self.format_results(assessment_results)
        return widgets.HTML(value=results_html, layout=widgets.Layout(margin="10px 0"))

    def format_results(self, assessment_results):
        """
        Форматирует результаты тестирования в HTML.

        Args:
            assessment_results (dict): Результаты тестирования

        Returns:
            str: HTML с форматированными результатами
        """
        if not assessment_results:
            return "<p>Нет результатов для отображения</p>"

        score = assessment_results.get("score", 0)
        total_questions = assessment_results.get("total_questions", 0)
        correct_answers = assessment_results.get("correct_answers", 0)

        return f"""
        <div style='padding: 15px; border-radius: 8px; background-color: #f8f9fa; border: 1px solid #dee2e6;'>
            <h3 style='margin: 0 0 15px 0; color: #495057;'>Результаты тестирования</h3>
            <p><strong>Оценка:</strong> {score:.1f}%</p>
            <p><strong>Правильных ответов:</strong> {correct_answers} из {total_questions}</p>
            <p><strong>Статус:</strong> {'✅ Тест пройден' if score >= 40 else '❌ Тест не пройден'}</p>
        </div>
        """
