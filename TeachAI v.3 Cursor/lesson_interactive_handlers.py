"""
Обработчики интерактивных функций урока.
Отвечает за форму вопросов, примеры, проверку релевантности и счетчики вопросов.
РЕФАКТОРИНГ: Выделен из lesson_interface.py для лучшей модульности (часть 2/3)
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
from content_utils import append_question_reminder


class LessonInteractiveHandlers:
    """Обработчики интерактивных функций урока."""

    def __init__(
        self, state_manager, content_generator, system_logger, current_course_info
    ):
        """
        Инициализация обработчиков интерактивных функций.

        Args:
            state_manager: Менеджер состояния
            content_generator: Генератор контента
            system_logger: Системный логгер
            current_course_info: Информация о текущем курсе и уроке
        """
        self.state_manager = state_manager
        self.content_generator = content_generator
        self.system_logger = system_logger
        self.logger = logging.getLogger(__name__)

        # Данные текущего урока
        self.current_course_info = current_course_info
        self.current_lesson_data = None
        self.current_lesson_content = None
        self.current_lesson_id = None

        # Устанавливаем данные урока из course_info если доступны
        if hasattr(current_course_info, "get"):
            self.current_lesson_data = current_course_info.get("lesson_data")
            self.current_lesson_content = current_course_info.get("lesson_content")
            self.current_lesson_id = current_course_info.get("lesson_id")

    def update_lesson_data(self, lesson_data, lesson_content, lesson_id):
        """
        Обновляет данные урока для интерактивных функций.

        Args:
            lesson_data (dict): Метаданные урока
            lesson_content (str): Содержание урока
            lesson_id (str): ID урока для счетчика вопросов
        """
        self.current_lesson_data = lesson_data
        self.current_lesson_content = lesson_content
        self.current_lesson_id = lesson_id

    def setup_enhanced_qa_container(self, qa_container):
        """
        Настраивает улучшенный контейнер для вопросов и ответов с проверкой релевантности.

        Args:
            qa_container (widgets.VBox): Контейнер для Q&A
        """
        # Текстовое поле для вопроса
        question_input = widgets.Text(
            placeholder="Введите ваш вопрос здесь", layout=widgets.Layout(width="80%")
        )

        # Кнопка отправки вопроса
        send_question_button = widgets.Button(
            description="Отправить",
            button_style="primary",
            tooltip="Отправить вопрос",
            icon="paper-plane",
        )

        # Контейнер для вопроса
        question_container = widgets.HBox([question_input, send_question_button])

        # Контейнер для ответа
        answer_output = widgets.Output()

        # Улучшенный обработчик отправки вопроса с проверкой релевантности
        def on_send_question_button_clicked(b):
            question = question_input.value.strip()
            if not question:
                return

            with answer_output:
                clear_output(wait=True)
                display(
                    widgets.HTML(
                        value=f"<p><strong>Ваш вопрос:</strong> {question}</p>"
                    )
                )
                display(
                    widgets.HTML(
                        value=f"<p><strong>Анализ вопроса и подготовка ответа...</strong></p>"
                    )
                )

            try:
                # Увеличиваем счетчик вопросов
                questions_count = self.state_manager.increment_questions_count(
                    self.current_lesson_id
                )

                # Проверяем релевантность вопроса
                relevance_result = self.content_generator.check_question_relevance(
                    question, self.current_lesson_content, self.current_lesson_data
                )

                with answer_output:
                    clear_output(wait=True)
                    display(
                        widgets.HTML(
                            value=f"<p><strong>Ваш вопрос:</strong> {question}</p>"
                        )
                    )

                    # Если вопрос нерелевантен
                    if not relevance_result["is_relevant"]:
                        non_relevant_response = (
                            self.content_generator.generate_non_relevant_response(
                                question, relevance_result["suggestions"]
                            )
                        )
                        # Добавляем напоминание, если нужно
                        non_relevant_response = append_question_reminder(
                            non_relevant_response, questions_count
                        )
                        display(widgets.HTML(value=non_relevant_response))
                    else:
                        # Вопрос релевантен - генерируем ответ
                        display(
                            widgets.HTML(
                                value=f"<p><strong>Генерация ответа...</strong></p>"
                            )
                        )

                        answer = self.content_generator.answer_question(
                            course=self.current_course_info["course_title"],
                            section=self.current_course_info["section_title"],
                            topic=self.current_course_info["topic_title"],
                            lesson=self.current_course_info["lesson_title"],
                            user_question=question,
                            lesson_content=self.current_lesson_content,
                            user_name=self.current_course_info["user_profile"]["name"],
                            communication_style=self.current_course_info[
                                "user_profile"
                            ]["communication_style"],
                        )

                        # Логируем вопрос и ответ
                        self.system_logger.log_question(question, answer)

                        clear_output(wait=True)
                        display(
                            widgets.HTML(
                                value=f"<p><strong>Ваш вопрос:</strong> {question}</p>"
                            )
                        )
                        # Добавляем напоминание, если нужно
                        answer = append_question_reminder(answer, questions_count)
                        display(widgets.HTML(value=answer))

                # Очищаем поле ввода
                question_input.value = ""

            except Exception as e:
                with answer_output:
                    clear_output(wait=True)
                    display(
                        widgets.HTML(
                            value=f"<p><strong>Ваш вопрос:</strong> {question}</p>"
                        )
                    )
                    display(
                        widgets.HTML(
                            value=f"<p style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px;'>Не удалось обработать вопрос: {str(e)}</p>"
                        )
                    )

        # Привязываем обработчик к кнопке
        send_question_button.on_click(on_send_question_button_clicked)

        # Настройка qa_container
        qa_container.children = [question_container, answer_output]

    def handle_examples_button_click(self, examples_container):
        """
        Обработчик кнопки "Приведи примеры".

        Args:
            examples_container: Контейнер для отображения примеров
        """
        with examples_container:
            clear_output(wait=True)
            display(widgets.HTML(value="<h3>Практические примеры</h3>"))
            display(
                widgets.HTML(
                    value="<p><strong>Загрузка практических примеров...</strong></p>"
                )
            )

            try:
                # Передаем контекст курса для обеспечения релевантности примеров
                course_context = {
                    "course_title": self.current_course_info["course_title"],
                    "course_plan": self.current_course_info.get("course_plan"),
                    "section_title": self.current_course_info["section_title"],
                    "topic_title": self.current_course_info["topic_title"],
                }

                examples = self.content_generator.generate_examples(
                    lesson_data=self.current_lesson_data,
                    lesson_content=self.current_lesson_content,
                    communication_style=self.current_course_info["user_profile"][
                        "communication_style"
                    ],
                    course_context=course_context,
                )

                clear_output(wait=True)
                display(widgets.HTML(value="<h3>Практические примеры</h3>"))
                display(widgets.HTML(value=f"<div>{examples}</div>"))

                # Кнопка закрытия примеров
                close_button = widgets.Button(
                    description="Закрыть примеры", button_style="primary"
                )

                def on_close_button_clicked(b):
                    examples_container.layout.display = "none"
                    # Очищаем содержимое для освобождения памяти
                    with examples_container:
                        clear_output(wait=True)

                close_button.on_click(on_close_button_clicked)
                display(close_button)

            except Exception as e:
                clear_output(wait=True)
                display(widgets.HTML(value="<h3>Ошибка при загрузке примеров</h3>"))
                display(
                    widgets.HTML(
                        value=f"<p style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px;'>Не удалось сгенерировать примеры: {str(e)}</p>"
                    )
                )

                close_button = widgets.Button(
                    description="Закрыть", button_style="primary"
                )

                def on_close_button_clicked(b):
                    examples_container.layout.display = "none"
                    with examples_container:
                        clear_output(wait=True)

                close_button.on_click(on_close_button_clicked)
                display(close_button)

    def get_qa_button_handler(
        self, qa_container, explain_container, examples_container
    ):
        """
        Возвращает обработчик для кнопки "Задать вопрос".

        Args:
            qa_container: Контейнер для вопросов
            explain_container: Контейнер для объяснений (нужно скрыть)
            examples_container: Контейнер для примеров (нужно скрыть)

        Returns:
            function: Обработчик события клика
        """

        def on_ask_button_clicked(b):
            # Скрываем другие контейнеры
            explain_container.layout.display = "none"
            examples_container.layout.display = "none"
            # Показываем контейнер вопросов
            qa_container.layout.display = "flex"

        return on_ask_button_clicked

    def get_examples_button_handler(
        self, examples_container, qa_container, explain_container
    ):
        """
        Возвращает обработчик для кнопки "Приведи примеры".

        Args:
            examples_container: Контейнер для примеров
            qa_container: Контейнер для вопросов (нужно скрыть)
            explain_container: Контейнер для объяснений (нужно скрыть)

        Returns:
            function: Обработчик события клика
        """

        def on_examples_button_clicked(b):
            # Скрываем другие контейнеры
            qa_container.layout.display = "none"
            explain_container.layout.display = "none"

            # Показываем примеры
            examples_container.layout.display = "block"

            # Запускаем обработчик примеров
            self.handle_examples_button_click(examples_container)

        return on_examples_button_clicked
