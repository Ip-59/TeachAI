"""
Интерфейс тестирования знаний для TeachAI.
Отвечает за создание интерфейсов тестирования, отображение вопросов и обработку результатов.

ИСПРАВЛЕНО ЭТАП 52: Упрощенная версия без сложного HTML для стабильной работы
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
import traceback
import html


class AssessmentInterface:
    """Интерфейс для тестирования знаний по урокам."""

    def __init__(self, state_manager, content_generator, assessment, system_logger):
        """
        Инициализация интерфейса тестирования.

        Args:
            state_manager: Менеджер состояния
            content_generator: Генератор контента
            assessment: Модуль оценивания
            system_logger: Системный логгер
        """
        self.state_manager = state_manager
        self.content_generator = content_generator
        self.assessment = assessment
        self.system_logger = system_logger
        self.logger = logging.getLogger(__name__)

        # Текущие данные тестирования
        self.current_questions = []
        self.current_answers = []
        self.current_lesson_data = None

        self.logger.info("AssessmentInterface инициализирован")

    def show_assessment(
        self,
        current_lesson_content=None,
        current_course_info=None,
        current_lesson_id=None,
        current_course=None,
        current_section=None,
        current_topic=None,
        current_lesson=None,
        **kwargs,
    ):
        """
        Отображает интерфейс тестирования урока.

        Args:
            current_lesson_content: Содержание урока
            current_course_info: Информация о курсе
            current_lesson_id: ID урока
            current_course: Название курса
            current_section: Название раздела
            current_topic: Название темы
            current_lesson: Название урока

        Returns:
            widgets.VBox: Интерфейс тестирования
        """
        try:
            self.logger.info(f"🎯 Запуск тестирования для урока: {current_lesson_id}")

            # Извлекаем правильные названия
            if current_course_info and isinstance(current_course_info, dict):
                course_title = (
                    current_course_info.get("course_title")
                    or current_course
                    or "Python"
                )
                section_title = (
                    current_course_info.get("section_title")
                    or current_section
                    or "Основы"
                )
                topic_title = (
                    current_course_info.get("topic_title")
                    or current_topic
                    or "Программирование"
                )
                lesson_title = (
                    current_course_info.get("lesson_title")
                    or current_lesson
                    or "Условные операторы"
                )
            else:
                course_title = current_course or "Python"
                section_title = current_section or "Основы"
                topic_title = current_topic or "Программирование"
                lesson_title = current_lesson or "Условные операторы"

            self.logger.info(
                f"📚 Курс: {course_title}, Раздел: {section_title}, Тема: {topic_title}, Урок: {lesson_title}"
            )

            # Проверяем наличие содержания урока
            if not current_lesson_content:
                return self._create_error_interface(
                    "Содержание урока недоступно",
                    "Для генерации вопросов необходимо содержание урока.",
                )

            # Проверяем наличие модуля оценивания
            if not self.assessment:
                return self._create_error_interface(
                    "Модуль оценивания недоступен",
                    "Assessment модуль не инициализирован.",
                )

            # Сохраняем данные для использования
            self.current_lesson_data = {
                "lesson_content": current_lesson_content,
                "course_info": current_course_info,
                "lesson_id": current_lesson_id,
                "course": course_title,
                "section": section_title,
                "topic": topic_title,
                "lesson": lesson_title,
                "course_title": course_title,
                "section_title": section_title,
                "topic_title": topic_title,
                "lesson_title": lesson_title,
                "title": lesson_title,
            }

            # Генерируем вопросы для тестирования
            questions = self._generate_questions(current_lesson_content)
            if not questions:
                return self._create_error_interface(
                    "Не удалось сгенерировать вопросы",
                    "Ошибка при генерации тестовых вопросов.",
                )

            self.current_questions = questions
            self.current_answers = [None] * len(questions)

            # Создаем интерфейс тестирования
            return self._create_assessment_interface()

        except Exception as e:
            self.logger.error(f"Ошибка в show_assessment: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return self._create_error_interface(
                "Критическая ошибка тестирования",
                f"Произошла непредвиденная ошибка: {str(e)}",
            )

    def _generate_questions(self, lesson_content):
        """Генерирует вопросы для тестирования."""
        try:
            self.logger.info("🎯 Генерация вопросов для тестирования")

            # Используем генератор контента для создания вопросов
            questions = self.content_generator.generate_assessment(
                lesson_data=self.current_lesson_data,
                lesson_content=lesson_content,
                questions_count=5,
            )

            self.logger.info(
                f"✅ Сгенерировано {len(questions) if questions else 0} вопросов"
            )
            return questions

        except Exception as e:
            self.logger.error(f"Ошибка генерации вопросов: {str(e)}")
            return []

    def _create_assessment_interface(self):
        """Создает упрощенный интерфейс тестирования."""
        try:
            # Заголовок
            header = widgets.HTML(
                value=f"""
                <div style="background: linear-gradient(135deg, #10b981, #059669);
                           padding: 20px; border-radius: 12px; margin-bottom: 25px;
                           color: white; text-align: center;">
                    <h2 style="margin: 0; font-size: 24px;">🎯 Тестирование знаний</h2>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">
                        Урок: {self.current_lesson_data.get('lesson', 'Урок')}
                    </p>
                </div>
            """
            )

            # Создаем вопросы как обычные виджеты (без HTML)
            questions_widgets = []

            for i, question in enumerate(self.current_questions):
                question_widget = self._create_simple_question_widget(question, i)
                questions_widgets.append(question_widget)

            # Кнопка отправки
            submit_button = widgets.Button(
                description="📝 Отправить тест",
                button_style="success",
                layout=widgets.Layout(width="200px", height="45px"),
            )

            submit_button.on_click(self._handle_test_submission)

            # Контейнер для результатов
            self.results_container = widgets.Output()

            return widgets.VBox(
                [
                    header,
                    *questions_widgets,
                    widgets.HBox(
                        [submit_button], layout=widgets.Layout(justify_content="center")
                    ),
                    self.results_container,
                ],
                layout=widgets.Layout(margin="0 auto", max_width="800px"),
            )

        except Exception as e:
            self.logger.error(f"Ошибка создания интерфейса: {str(e)}")
            return self._create_error_interface(
                "Ошибка создания интерфейса",
                f"Не удалось создать интерфейс тестирования: {str(e)}",
            )

    def _create_simple_question_widget(self, question, index):
        """Создает простой виджет для одного вопроса."""
        # Извлекаем данные вопроса
        question_text = question.get(
            "text", question.get("question", f"Вопрос {index + 1}")
        )
        options = question.get("options", ["Вариант 1", "Вариант 2", "Вариант 3"])

        # Заголовок вопроса
        question_header = widgets.HTML(
            value=f"""
            <div style="background: #f8fafc; border-left: 4px solid #10b981;
                       padding: 15px; margin: 20px 0 10px 0; border-radius: 8px;">
                <h4 style="margin: 0; color: #1f2937;">Вопрос {index + 1}</h4>
                <p style="margin: 10px 0 0 0; color: #374151; font-size: 16px;">
                    {html.escape(question_text)}
                </p>
            </div>
        """
        )

        # Простые радиокнопки
        radio_group = widgets.RadioButtons(
            options=options,
            layout=widgets.Layout(margin="0 0 20px 20px"),
            style={"description_width": "initial"},
        )

        # Обработчик изменения ответа
        def on_answer_change(change, question_index=index):
            if change["type"] == "change" and change["name"] == "value":
                self.current_answers[question_index] = change["new"]
                self.logger.debug(
                    f"Ответ на вопрос {question_index + 1}: {change['new']}"
                )

        radio_group.observe(on_answer_change)

        return widgets.VBox([question_header, radio_group])

    def _handle_test_submission(self, button):
        """Обрабатывает отправку теста."""
        try:
            with self.results_container:
                clear_output(wait=True)

                # Проверяем что все вопросы отвечены
                unanswered = [
                    i + 1
                    for i, answer in enumerate(self.current_answers)
                    if answer is None
                ]
                if unanswered:
                    display(
                        widgets.HTML(
                            value=f"""
                        <div style="color: #dc3545; background: #f8d7da; border: 1px solid #f5c6cb;
                                   padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <strong>⚠️ Тест не завершен</strong><br>
                            Пожалуйста, ответьте на все вопросы. Не отвечены: {', '.join(map(str, unanswered))}
                        </div>
                    """
                        )
                    )
                    return

                # Подсчитываем результаты
                correct_answers = 0
                total_questions = len(self.current_questions)

                for i, (question, user_answer) in enumerate(
                    zip(self.current_questions, self.current_answers)
                ):
                    correct_answer = question.get(
                        "correct_answer", question.get("answer")
                    )
                    if user_answer == correct_answer:
                        correct_answers += 1

                # Вычисляем процент и оценку
                score_percent = (correct_answers / total_questions) * 100
                is_passed = score_percent >= 70

                # Отображаем результаты
                self._show_results(
                    correct_answers, total_questions, score_percent, is_passed
                )

                # Сохраняем результат
                self._save_assessment_result(score_percent, is_passed)

        except Exception as e:
            self.logger.error(f"Ошибка обработки теста: {str(e)}")
            with self.results_container:
                display(
                    widgets.HTML(
                        value=f"""
                    <div style="color: #dc3545; background: #f8d7da; border: 1px solid #f5c6cb;
                               padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <strong>❌ Ошибка обработки теста</strong><br>
                        {html.escape(str(e))}
                    </div>
                """
                    )
                )

    def _show_results(self, correct_answers, total_questions, score_percent, is_passed):
        """Отображает результаты тестирования."""
        grade = (
            "Отлично"
            if score_percent >= 90
            else "Хорошо"
            if score_percent >= 80
            else "Удовлетворительно"
            if is_passed
            else "Неудовлетворительно"
        )

        results_html = f"""
            <div style="background: linear-gradient(135deg, {'#10b981' if is_passed else '#dc2626'}, {'#059669' if is_passed else '#b91c1c'});
                       padding: 20px; border-radius: 12px; margin: 20px 0;
                       color: white; text-align: center;">
                <h2 style="margin: 0 0 15px 0; font-size: 24px;">
                    {'🎉' if is_passed else '😞'} Результаты тестирования
                </h2>
                <div style="font-size: 18px; margin-bottom: 15px;">
                    <strong>Правильных ответов: {correct_answers} из {total_questions}</strong>
                </div>
                <div style="font-size: 20px; margin-bottom: 15px;">
                    <strong>Оценка: {score_percent:.1f}% - {grade}</strong>
                </div>
                <p style="margin: 0; font-size: 16px;">
                    {f"Поздравляем! Тест пройден успешно." if is_passed
                     else "Рекомендуем повторить материал и пройти тест заново."}
                </p>
            </div>
        """

        display(widgets.HTML(value=results_html))

        # Кнопки для дальнейших действий
        self._show_action_buttons(is_passed)

    def _show_action_buttons(self, is_passed):
        """Показывает кнопки действий после теста."""
        buttons = []

        if is_passed:
            next_button = widgets.Button(
                description="➡️ Следующий урок",
                button_style="success",
                layout=widgets.Layout(width="180px", margin="5px"),
            )
            buttons.append(next_button)

        retry_button = widgets.Button(
            description="🔄 Пройти еще раз",
            button_style="warning",
            layout=widgets.Layout(width="180px", margin="5px"),
        )

        lesson_button = widgets.Button(
            description="📚 К уроку",
            button_style="info",
            layout=widgets.Layout(width="180px", margin="5px"),
        )

        buttons.extend([retry_button, lesson_button])

        def on_retry_click(b):
            # Сбрасываем ответы и показываем тест заново
            self.current_answers = [None] * len(self.current_questions)
            with self.results_container:
                clear_output(wait=True)
                display(widgets.HTML(value="<p>Перезапуск теста...</p>"))

        def on_lesson_click(b):
            with self.results_container:
                clear_output(wait=True)
                display(widgets.HTML(value="<p>Возврат к уроку...</p>"))

        retry_button.on_click(on_retry_click)
        lesson_button.on_click(on_lesson_click)

        display(widgets.HBox(buttons, layout=widgets.Layout(justify_content="center")))

    def _save_assessment_result(self, score, is_passed):
        """Сохраняет результат тестирования."""
        try:
            if self.current_lesson_data and self.state_manager:
                lesson_id = self.current_lesson_data.get("lesson_id")
                self.state_manager.save_assessment_result(lesson_id, score, is_passed)
                self.logger.info(
                    f"Результат тестирования сохранен: {score}% ({'пройден' if is_passed else 'не пройден'})"
                )
        except Exception as e:
            self.logger.error(f"Ошибка сохранения результата: {str(e)}")

    def _create_error_interface(self, title, message):
        """Создает интерфейс с сообщением об ошибке."""
        return widgets.VBox(
            [
                widgets.HTML(
                    value=f"""
                <div style="color: #dc3545; background: #f8d7da; border: 1px solid #f5c6cb;
                           padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                    <h3 style="margin: 0 0 15px 0;">⚠️ {html.escape(title)}</h3>
                    <p style="margin: 0; font-size: 16px;">
                        {html.escape(message)}
                    </p>
                </div>
            """
                )
            ],
            layout=widgets.Layout(margin="0 auto", max_width="600px"),
        )
