"""
Интерактивные функции для уроков.
Вынесены из lesson_interface.py для улучшения модульности.
"""

import ipywidgets as widgets
import logging
from lesson_utils import LessonUtils


class LessonInteraction:
    """Интерактивные функции для уроков."""

    def __init__(self, lesson_interface):
        """
        Инициализация интерактивных функций.

        Args:
            lesson_interface: Экземпляр LessonInterface
        """
        self.lesson_interface = lesson_interface
        self.logger = logging.getLogger(__name__)
        self.utils = LessonUtils()

    def show_explanation_choice(self):
        """
        Показывает выбор типа объяснения.
        """
        try:
            # Создаем заголовок
            title_html = widgets.HTML(value="<h3>📚 Выберите тип объяснения:</h3>")

            # Кнопка "Полное объяснение"
            full_explanation_button = widgets.Button(
                description="📖 Полное объяснение урока",
                button_style="primary",
                layout=widgets.Layout(width="auto", margin="5px"),
            )

            # Кнопка "Ключевые понятия"
            concepts_button = widgets.Button(
                description="🔑 Ключевые понятия",
                button_style="info",
                layout=widgets.Layout(width="auto", margin="5px"),
            )

            # Кнопка "Назад"
            back_button = widgets.Button(
                description="← Назад",
                button_style="warning",
                layout=widgets.Layout(width="auto", margin="5px"),
            )

            # Привязываем обработчики
            def on_full_explanation_clicked(b):
                try:
                    # Получаем информацию о курсе
                    course_info = self.lesson_interface.current_course_info
                    course_title = course_info.get("course_title", "Курс")
                    section_title = course_info.get("section_title", "Раздел")
                    topic_title = course_info.get("topic_title", "Тема")
                    lesson_title = course_info.get("lesson_title", "Урок")

                    # Генерируем полное объяснение
                    explanation = self.lesson_interface.content_generator.get_detailed_explanation(
                        course=course_title,
                        section=section_title,
                        topic=topic_title,
                        lesson=lesson_title,
                        lesson_content=self.lesson_interface.current_lesson_content,
                        communication_style=self.lesson_interface.current_course_info[
                            "user_profile"
                        ]["communication_style"],
                    )

                    # Создаем виджет с объяснением
                    explanation_html = widgets.HTML(value=explanation)

                    # Кнопка закрытия
                    close_button = widgets.Button(
                        description="✕ Закрыть",
                        button_style="danger",
                        layout=widgets.Layout(width="auto", margin="10px 0"),
                    )

                    def on_close_clicked(b):
                        self.lesson_interface.explain_container.layout.display = "none"

                    close_button.on_click(on_close_clicked)

                    # Обновляем контейнер
                    self.lesson_interface.explain_container.children = [
                        explanation_html,
                        close_button,
                    ]

                except Exception as e:
                    self.logger.error(
                        f"Ошибка при генерации полного объяснения: {str(e)}"
                    )
                    error_html = widgets.HTML(
                        value=f"<p style='color: red;'>Ошибка при генерации объяснения: {str(e)}</p>"
                    )
                    self.lesson_interface.explain_container.children = [error_html]

            def on_concepts_explanation_clicked(b):
                try:
                    # Генерируем ключевые понятия
                    concepts = self.lesson_interface.content_generator.generate_concepts(
                        lesson_content=self.lesson_interface.current_lesson_content,
                        communication_style=self.lesson_interface.current_course_info[
                            "user_profile"
                        ]["communication_style"],
                    )

                    # Создаем список понятий
                    concepts_list = []
                    for concept_data in concepts:
                        concept_button = widgets.Button(
                            description=f"🔑 {concept_data['title']}",
                            button_style="info",
                            layout=widgets.Layout(width="auto", margin="2px"),
                        )

                        def create_concept_handler(concept_data):
                            def handle_concept_click(b):
                                self.show_concept_explanation(concept_data)

                            return handle_concept_click

                        concept_button.on_click(create_concept_handler(concept_data))
                        concepts_list.append(concept_button)

                    # Кнопка "Назад"
                    back_to_choice_button = widgets.Button(
                        description="← Назад к выбору",
                        button_style="warning",
                        layout=widgets.Layout(width="auto", margin="10px 0"),
                    )

                    def on_back_clicked(b):
                        self.show_explanation_choice()

                    back_to_choice_button.on_click(on_back_clicked)

                    # Обновляем контейнер
                    self.lesson_interface.explain_container.children = [
                        widgets.HTML(value="<h3>🔑 Ключевые понятия:</h3>"),
                        widgets.VBox(concepts_list),
                        back_to_choice_button,
                    ]

                except Exception as e:
                    self.logger.error(f"Ошибка при генерации понятий: {str(e)}")
                    error_html = widgets.HTML(
                        value=f"<p style='color: red;'>Ошибка при генерации понятий: {str(e)}</p>"
                    )
                    self.lesson_interface.explain_container.children = [error_html]

            def on_back_clicked(b):
                self.lesson_interface.explain_container.layout.display = "none"

            # Привязываем обработчики
            full_explanation_button.on_click(on_full_explanation_clicked)
            concepts_button.on_click(on_concepts_explanation_clicked)
            back_button.on_click(on_back_clicked)

            # Создаем контейнер
            choice_container = widgets.VBox(
                [title_html, full_explanation_button, concepts_button, back_button],
                layout=widgets.Layout(
                    width="100%",
                    padding="20px",
                    border="1px solid #ddd",
                    border_radius="10px",
                ),
            )

            # Показываем контейнер
            self.lesson_interface.explain_container.children = [choice_container]
            self.lesson_interface.explain_container.layout.display = "block"

        except Exception as e:
            self.logger.error(f"Ошибка при показе выбора объяснения: {str(e)}")

    def show_concept_explanation(self, concept):
        """
        Показывает объяснение конкретного понятия.

        Args:
            concept (dict): Данные о понятии
        """
        try:
            # Создаем заголовок
            title_html = widgets.HTML(value=f"<h3>🔑 {concept['title']}</h3>")

            # Создаем описание понятия
            description_html = widgets.HTML(value=f"<p>{concept['description']}</p>")

            # Кнопка "Назад к понятиям"
            back_button = widgets.Button(
                description="← Назад к понятиям",
                button_style="warning",
                layout=widgets.Layout(width="auto", margin="10px 0"),
            )

            def on_back_clicked(b):
                # Возвращаемся к списку понятий
                try:
                    concepts = self.lesson_interface.content_generator.generate_concepts(
                        lesson_content=self.lesson_interface.current_lesson_content,
                        communication_style=self.lesson_interface.current_course_info[
                            "user_profile"
                        ]["communication_style"],
                    )

                    concepts_list = []
                    for concept_data in concepts:
                        concept_button = widgets.Button(
                            description=f"🔑 {concept_data['title']}",
                            button_style="info",
                            layout=widgets.Layout(width="auto", margin="2px"),
                        )

                        def create_concept_handler(concept_data):
                            def handle_concept_click(b):
                                self.show_concept_explanation(concept_data)

                            return handle_concept_click

                        concept_button.on_click(create_concept_handler(concept_data))
                        concepts_list.append(concept_button)

                    # Кнопка "Назад к выбору"
                    back_to_choice_button = widgets.Button(
                        description="← Назад к выбору",
                        button_style="warning",
                        layout=widgets.Layout(width="auto", margin="10px 0"),
                    )

                    def on_back_to_choice_clicked(b):
                        self.show_explanation_choice()

                    back_to_choice_button.on_click(on_back_to_choice_clicked)

                    # Обновляем контейнер
                    self.lesson_interface.explain_container.children = [
                        widgets.HTML(value="<h3>🔑 Ключевые понятия:</h3>"),
                        widgets.VBox(concepts_list),
                        back_to_choice_button,
                    ]

                except Exception as e:
                    self.logger.error(f"Ошибка при возврате к понятиям: {str(e)}")

            back_button.on_click(on_back_clicked)

            # Кнопка "Закрыть"
            close_button = widgets.Button(
                description="✕ Закрыть",
                button_style="danger",
                layout=widgets.Layout(width="auto", margin="10px 0"),
            )

            def on_close_clicked(b):
                self.lesson_interface.explain_container.layout.display = "none"

            close_button.on_click(on_close_clicked)

            # Создаем контейнер
            concept_container = widgets.VBox(
                [title_html, description_html, back_button, close_button],
                layout=widgets.Layout(
                    width="100%",
                    padding="20px",
                    border="1px solid #ddd",
                    border_radius="10px",
                ),
            )

            # Обновляем контейнер
            self.lesson_interface.explain_container.children = [concept_container]

        except Exception as e:
            self.logger.error(f"Ошибка при показе объяснения понятия: {str(e)}")

    def setup_enhanced_qa_container(self, qa_container):
        """
        Настраивает улучшенный контейнер для вопросов и ответов.

        Args:
            qa_container: Контейнер для вопросов и ответов
        """
        try:
            # Создаем заголовок
            title_html = widgets.HTML(value="<h3>❓ Задайте вопрос по уроку:</h3>")

            # Поле ввода вопроса
            question_input = widgets.Textarea(
                placeholder="Введите ваш вопрос здесь...",
                layout=widgets.Layout(width="100%", height="100px"),
            )

            # Кнопка отправки вопроса
            send_button = widgets.Button(
                description="📤 Отправить вопрос",
                button_style="success",
                layout=widgets.Layout(width="auto", margin="10px 0"),
            )

            # Область для ответа
            answer_area = widgets.HTML(
                value="<p>Ответ появится здесь после отправки вопроса.</p>",
                layout=widgets.Layout(
                    width="100%", padding="10px", border="1px solid #ddd"
                ),
            )

            # Кнопка закрытия
            close_button = widgets.Button(
                description="✕ Закрыть",
                button_style="danger",
                layout=widgets.Layout(width="auto", margin="10px 0"),
            )

            def on_send_question_button_clicked(b):
                try:
                    question = question_input.value.strip()
                    if not question:
                        answer_area.value = (
                            "<p style='color: orange;'>Пожалуйста, введите вопрос.</p>"
                        )
                        return

                    # Показываем загрузку
                    answer_area.value = (
                        "<p><strong>Анализ вопроса и подготовка ответа...</strong></p>"
                    )

                    # Увеличиваем счетчик вопросов
                    questions_count = (
                        self.lesson_interface.state_manager.increment_questions_count(
                            self.lesson_interface.current_lesson_id
                        )
                    )

                    # Проверяем релевантность вопроса
                    relevance_result = self.lesson_interface.content_generator.check_question_relevance(
                        question,
                        self.lesson_interface.current_lesson_content,
                        self.lesson_interface.current_lesson_data,
                    )

                    # Если вопрос нерелевантен
                    if not relevance_result["is_relevant"]:
                        non_relevant_response = self.lesson_interface.content_generator.generate_non_relevant_response(
                            question, relevance_result["suggestions"]
                        )
                        # Добавляем напоминание, если нужно
                        if questions_count >= 3:
                            warning = self.lesson_interface.content_generator.generate_multiple_questions_warning(
                                questions_count
                            )
                            non_relevant_response += warning
                        answer_area.value = non_relevant_response
                    else:
                        # Вопрос релевантен - генерируем ответ
                        answer_area.value = (
                            "<p><strong>Генерация ответа...</strong></p>"
                        )

                        answer = self.lesson_interface.content_generator.answer_question(
                            course=self.lesson_interface.current_course_info[
                                "course_title"
                            ],
                            section=self.lesson_interface.current_course_info[
                                "section_title"
                            ],
                            topic=self.lesson_interface.current_course_info[
                                "topic_title"
                            ],
                            lesson=self.lesson_interface.current_course_info[
                                "lesson_title"
                            ],
                            user_question=question,
                            lesson_content=self.lesson_interface.current_lesson_content,
                            user_name=self.lesson_interface.current_course_info[
                                "user_profile"
                            ]["name"],
                            communication_style=self.lesson_interface.current_course_info[
                                "user_profile"
                            ][
                                "communication_style"
                            ],
                        )

                        # Логируем вопрос и ответ
                        self.lesson_interface.system_logger.log_question(
                            question, answer
                        )

                        # Добавляем напоминание, если нужно
                        if questions_count >= 3:
                            warning = self.lesson_interface.content_generator.generate_multiple_questions_warning(
                                questions_count
                            )
                            answer += warning

                        answer_area.value = answer

                    # Очищаем поле ввода
                    question_input.value = ""

                except Exception as e:
                    self.logger.error(f"Ошибка при генерации ответа: {str(e)}")
                    answer_area.value = f"<p style='color: red;'>Ошибка при генерации ответа: {str(e)}</p>"

            def on_close_button_clicked(b):
                qa_container.layout.display = "none"

            # Привязываем обработчики
            send_button.on_click(on_send_question_button_clicked)
            close_button.on_click(on_close_button_clicked)

            # Создаем контейнер
            qa_container.children = [
                title_html,
                question_input,
                send_button,
                answer_area,
                close_button,
            ]

        except Exception as e:
            self.logger.error(f"Ошибка при настройке QA контейнера: {str(e)}")

    def hide_other_containers(self):
        """
        Скрывает другие контейнеры при показе интерактивных функций.
        """
        try:
            if self.lesson_interface.explain_container:
                self.lesson_interface.explain_container.layout.display = "none"
            if self.lesson_interface.examples_container:
                self.lesson_interface.examples_container.layout.display = "none"
            if self.lesson_interface.qa_container:
                self.lesson_interface.qa_container.layout.display = "none"
        except Exception as e:
            self.logger.error(f"Ошибка при скрытии контейнеров: {str(e)}")
