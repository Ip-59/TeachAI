"""
Интерфейс для тестирования знаний пользователя.
Отвечает за отображение тестов и координацию с обработчиком результатов.
РЕФАКТОРИНГ: Основной координирующий модуль (часть 2/2, размер: ~225 строк)
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
from interface_utils import InterfaceUtils, InterfaceStyles, InterfaceState

# Импортируем специализированный обработчик результатов
from assessment_results_handler import AssessmentResultsHandler


class AssessmentInterface:
    """Интерфейс для проведения тестирования знаний."""

    def __init__(self, state_manager, assessment, system_logger):
        """
        Инициализация интерфейса тестирования.

        Args:
            state_manager: Менеджер состояния
            assessment: Модуль оценивания (может быть None - создадим сами)
            system_logger: Системный логгер
        """
        self.state_manager = state_manager
        self.system_logger = system_logger
        self.logger = logging.getLogger(__name__)

        # Создаем assessment если он не передан
        if assessment is None:
            try:
                # Импортируем и создаем assessment и content_generator
                from content_generator import ContentGenerator
                from assessment import Assessment
                from config import ConfigManager

                # Получаем API ключ
                config_manager = ConfigManager()
                config_manager.load_config()
                api_key = config_manager.get_api_key()

                # Создаем content_generator и assessment
                self.content_generator = ContentGenerator(api_key)
                self.assessment = Assessment(self.content_generator, system_logger)

                self.logger.info("Assessment успешно создан")
            except Exception as e:
                self.logger.error(f"ОШИБКА при создании Assessment: {str(e)}")
                raise
        else:
            self.assessment = assessment
            # Создаем content_generator для навигации
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

        # Утилиты интерфейса
        self.utils = InterfaceUtils()

        # Данные текущего теста
        self.current_questions = None
        self.current_answers = []

        # Создаем словари для отслеживания RadioButtons
        self.question_widgets = {}

        # Создаем специализированный обработчик результатов
        self.results_handler = AssessmentResultsHandler(
            state_manager, self.assessment, system_logger, self.content_generator
        )

    def show_assessment(
        self,
        current_course,
        current_section,
        current_topic,
        current_lesson,
        current_lesson_content,
    ):
        """
        Отображает тест для проверки знаний.

        Args:
            current_course (str): ID текущего курса
            current_section (str): ID текущего раздела
            current_topic (str): ID текущей темы
            current_lesson (str): ID текущего урока
            current_lesson_content (str): Содержание урока

        Returns:
            widgets.VBox: Виджет с тестом
        """
        try:
            # Получаем данные о курсе и уроке
            course_plan = self.state_manager.get_course_plan()
            lesson_data = self.state_manager.get_lesson_data(
                current_section, current_topic, current_lesson
            )

            if not lesson_data:
                raise ValueError(f"Данные текущего урока не найдены")

            # Получаем названия элементов
            (
                course_title,
                section_title,
                topic_title,
                lesson_title,
            ) = self._get_element_titles(
                course_plan, current_section, current_topic, current_lesson
            )

            # Показываем сообщение о загрузке
            loading_display = widgets.HTML(
                value=f"<h1 style='margin: 2px 0; font-size: 24px;'>Тест по теме: {lesson_title}</h1><p style='margin: 3px 0;'><strong>Подготовка тестовых вопросов...</strong></p>",
                layout=widgets.Layout(margin="0px"),
            )
            display(loading_display)

            # Генерируем вопросы для теста
            try:
                if self.assessment is None:
                    raise Exception(
                        "self.assessment равен None - это основная проблема!"
                    )

                questions = self.assessment.generate_questions(
                    course=course_title,
                    section=section_title,
                    topic=topic_title,
                    lesson=lesson_title,
                    lesson_content=current_lesson_content,
                    num_questions=5,
                )
            except Exception as e:
                self.logger.error(f"ОШИБКА при генерации вопросов: {str(e)}")
                # Очищаем сообщение о загрузке и показываем ошибку
                clear_output(wait=True)
                return self._create_error_interface(
                    "Ошибка при генерации теста",
                    f"Не удалось сгенерировать вопросы для теста: {str(e)}",
                    current_section,
                    current_topic,
                    current_lesson,
                )

            # Очищаем сообщение о загрузке
            clear_output(wait=True)

            # Сохраняем вопросы
            self.current_questions = questions
            self.current_answers = [None] * len(questions)

            # Создаем интерфейс теста с МАКСИМАЛЬНО КОМПАКТНЫМИ отступами
            nav_info = widgets.HTML(
                value=self.utils.create_navigation_info(
                    course_title, section_title, topic_title, lesson_title, "Тест"
                ),
                layout=widgets.Layout(margin="0px"),
            )

            test_header = widgets.HTML(
                value="<h1 style='margin: 2px 0; font-size: 24px; font-weight: bold; color: #495057;'>Проверка знаний</h1>",
                layout=widgets.Layout(margin="0px"),
            )

            test_description = widgets.HTML(
                value=f"<p style='margin: 3px 0; line-height: 1.3;'>Ответьте на следующие вопросы по теме <strong>{lesson_title}</strong>, чтобы проверить свои знания.</p>",
                layout=widgets.Layout(margin="0px"),
            )

            # Создаем вопросы с минимальными отступами
            questions_container = self._create_compact_questions_interface(questions)

            # Кнопка завершения теста
            submit_button = widgets.Button(
                description="Завершить тест",
                button_style="success",
                tooltip="Проверить ответы",
                icon="check",
                layout=widgets.Layout(width="200px", height="40px", margin="5px 0"),
            )

            # Контейнер для результатов
            results_output = widgets.Output(layout=widgets.Layout(margin="0px"))

            # Обработчик кнопки завершения теста
            def on_submit_button_clicked(b):
                self.results_handler.handle_test_submission(
                    results_output,
                    self.current_questions,
                    self.current_answers,
                    course_plan,
                    course_title,
                    section_title,
                    topic_title,
                    lesson_title,
                    current_course,
                    current_section,
                    current_topic,
                    current_lesson,
                )

            submit_button.on_click(on_submit_button_clicked)

            # Собираем интерфейс с минимальными отступами
            form = widgets.VBox(
                [
                    nav_info,
                    test_header,
                    test_description,
                    questions_container,
                    submit_button,
                    results_output,
                ],
                layout=widgets.Layout(margin="0px", padding="0px"),
            )

            return form

        except Exception as e:
            self.logger.error(f"Ошибка при отображении теста: {str(e)}")
            self.system_logger.log_activity(
                action_type="assessment_display_error", status="error", error=str(e)
            )

            return self._create_error_interface(
                "Ошибка при загрузке теста",
                f"Произошла ошибка при загрузке теста: {str(e)}",
                current_section,
                current_topic,
                current_lesson,
            )

    def _create_compact_questions_interface(self, questions):
        """
        Создает КОМПАКТНЫЙ интерфейс для вопросов с минимальными отступами.

        Args:
            questions (list): Список вопросов

        Returns:
            widgets.VBox: Контейнер с вопросами
        """
        questions_widgets = []

        for i, question in enumerate(questions):
            # Компактный заголовок вопроса
            question_title_widget = widgets.HTML(
                value=f"<div style='font-size: 18px; font-weight: bold; color: #212529; margin-bottom: 4px; padding-bottom: 3px; border-bottom: 1px solid #dee2e6; line-height: 1.3;'>Вопрос {i+1}: {question['text']}</div>",
                layout=widgets.Layout(margin="0px"),
            )

            # Создаем RadioButtons с минимальными отступами
            options = question.get("options", ["Нет вариантов ответа"])
            radio_buttons = widgets.RadioButtons(
                options=[(option, j + 1) for j, option in enumerate(options)],
                description="",
                disabled=False,
                layout=widgets.Layout(
                    margin="4px 10px", width="100%"  # Еще более уменьшенные отступы
                ),
                style={"description_width": "0px"},
            )

            # Создаем обработчик для каждого вопроса
            def create_answer_handler(question_index):
                def handle_answer_change(change):
                    if change["type"] == "change" and change["name"] == "value":
                        if change["new"] is not None:
                            self.current_answers[question_index] = change["new"]

                return handle_answer_change

            # Привязываем обработчик
            radio_buttons.observe(create_answer_handler(i), names="value")

            # Сохраняем ссылку на RadioButtons для отладки
            self.question_widgets[i] = radio_buttons

            # Максимально компактная структура вопроса
            question_container = widgets.VBox(
                [question_title_widget, radio_buttons],
                layout=widgets.Layout(
                    border="2px solid #e9ecef",
                    border_radius="8px",
                    padding="8px",  # Уменьшенный padding
                    margin="4px 0",  # Уменьшенный margin
                    background_color="#ffffff",
                ),
            )

            questions_widgets.append(question_container)

        return widgets.VBox(
            questions_widgets, layout=widgets.Layout(margin="0px", gap="2px")
        )

    def _get_element_titles(
        self, course_plan, current_section, current_topic, current_lesson
    ):
        """
        Получает названия элементов курса.

        Args:
            course_plan (dict): План курса
            current_section (str): ID раздела
            current_topic (str): ID темы
            current_lesson (str): ID урока

        Returns:
            tuple: (course_title, section_title, topic_title, lesson_title)
        """
        # Получаем название курса
        course_title = self.utils.get_safe_title(course_plan, "Курс")
        if not course_title or course_title == "Курс":
            learning_progress = self.state_manager.get_learning_progress()
            course_title = learning_progress.get("current_course", "Курс Python")

        # Ищем названия раздела и темы
        section_title = "Раздел"
        topic_title = "Тема"
        lesson_title = "Урок"

        for section in course_plan.get("sections", []):
            if section.get("id") == current_section:
                section_title = self.utils.get_safe_title(section, "Раздел")
                for topic in section.get("topics", []):
                    if topic.get("id") == current_topic:
                        topic_title = self.utils.get_safe_title(topic, "Тема")
                        for lesson in topic.get("lessons", []):
                            if lesson.get("id") == current_lesson:
                                lesson_title = self.utils.get_safe_title(lesson, "Урок")
                                break
                        break
                break

        return course_title, section_title, topic_title, lesson_title

    def _create_error_interface(
        self, title, message, current_section, current_topic, current_lesson
    ):
        """Создает интерфейс ошибки с РАБОЧИМИ кнопками."""
        error_header = self.utils.create_header(title)
        error_message = self.utils.create_styled_message(message, "incorrect")

        back_button = widgets.Button(
            description="Вернуться к уроку", button_style="primary", icon="arrow-left"
        )

        def go_back_to_lesson(b):
            clear_output(wait=True)
            from lesson_interface import LessonInterface

            lesson_ui = LessonInterface(
                self.state_manager,
                self.content_generator,
                self.system_logger,
                self.assessment,
            )
            display(
                lesson_ui.show_lesson(current_section, current_topic, current_lesson)
            )

        back_button.on_click(go_back_to_lesson)

        return widgets.VBox([error_header, error_message, back_button])
