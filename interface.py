"""
Модуль для создания интерактивного интерфейса с использованием ipywidgets.
Отвечает за взаимодействие с пользователем через Jupyter Notebook.

НОВАЯ АРХИТЕКТУРА: Этот модуль теперь служит фасадом для специализированных интерфейсов.
Обеспечивает полную обратную совместимость со старым интерфейсом.
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
from datetime import datetime
import re
import traceback

# Импортируем все специализированные интерфейсы
from interface_utils import InterfaceState, InterfaceUtils
from setup_interface import SetupInterface
from lesson_interface import LessonInterface
from assessment_interface import AssessmentInterface
from completion_interface import CompletionInterface


class UserInterface:
    """
    Фасад для создания интерактивного пользовательского интерфейса.

    ВАЖНО: Обеспечивает полную обратную совместимость с предыдущей версией.
    Все методы работают точно так же, как раньше!
    """

    def __init__(self, state_manager, content_generator, assessment, system_logger):
        """
        Инициализация интерфейса.

        Args:
            state_manager (StateManager): Объект менеджера состояния
            content_generator (ContentGenerator): Объект генератора контента
            assessment (Assessment): Объект модуля оценивания
            system_logger (Logger): Объект логгера
        """
        self.state_manager = state_manager
        self.content_generator = content_generator
        self.assessment = assessment
        self.system_logger = system_logger
        self.logger = logging.getLogger(__name__)

        # Текущее состояние интерфейса
        self.current_state = InterfaceState.INITIAL_SETUP

        # Данные текущего урока для совместимости
        self.current_course = None
        self.current_section = None
        self.current_topic = None
        self.current_lesson = None
        self.current_lesson_content = None
        self.current_questions = None
        self.current_answers = []

        # Инициализируем специализированные интерфейсы
        try:
            print(f"🔍 ОТЛАДКА UserInterface.__init__:")
            print(f"🔍 assessment = {assessment}")
            print(f"🔍 type(assessment) = {type(assessment)}")

            self.setup_interface = SetupInterface(
                state_manager, content_generator, system_logger, assessment
            )
            self.lesson_interface = LessonInterface(
                state_manager, content_generator, system_logger, assessment
            )
            self.assessment_interface = AssessmentInterface(
                state_manager, assessment, system_logger, None
            )
            self.completion_interface = CompletionInterface(
                state_manager, system_logger, content_generator, assessment
            )

            self.logger.info("UserInterface (фасад) успешно инициализирован")

        except Exception as e:
            self.logger.error(f"Ошибка при инициализации UserInterface: {str(e)}")
            raise

        # Утилиты интерфейса
        self.utils = InterfaceUtils()

        # Сохраняем старые стили для совместимости
        self.styles = {
            "correct": "background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin: 5px 0;",
            "incorrect": "background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 5px 0;",
            "info": "background-color: #d1ecf1; color: #0c5460; padding: 10px; border-radius: 5px; margin: 5px 0;",
            "warning": "background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; margin: 5px 0;",
            "header": "font-size: 24px; font-weight: bold; color: #495057; margin: 20px 0 10px 0;",
            "subheader": "font-size: 18px; font-weight: bold; color: #6c757d; margin: 15px 0 10px 0;",
            "button": "font-weight: bold;",
        }

    # ========================================
    # ПУБЛИЧНЫЕ МЕТОДЫ - ОБРАТНАЯ СОВМЕСТИМОСТЬ
    # ========================================

    def show_initial_setup(self):
        """
        Отображает форму первоначальной настройки.

        Returns:
            widgets.VBox: Виджет с формой настройки
        """
        self.current_state = InterfaceState.INITIAL_SETUP
        return self.setup_interface.show_initial_setup()

    def show_course_selection(self):
        """
        Отображает интерфейс выбора курса.

        Returns:
            widgets.VBox: Виджет с интерфейсом выбора курса
        """
        self.current_state = InterfaceState.COURSE_SELECTION
        return self.setup_interface.show_course_selection()

    def show_lesson(self, section_id, topic_id, lesson_id):
        """
        Отображает урок пользователю.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            widgets.VBox: Виджет с уроком
        """
        # Обновляем текущие данные для совместимости
        self.current_section = section_id
        self.current_topic = topic_id
        self.current_lesson = lesson_id
        self.current_state = InterfaceState.LESSON_VIEW

        # Создаем улучшенную версию show_lesson с обработчиками кнопок
        lesson_interface = self._create_enhanced_lesson_interface(
            section_id, topic_id, lesson_id
        )
        return lesson_interface

    def show_assessment(self):
        """
        Отображает тест для проверки знаний.

        Returns:
            widgets.VBox: Виджет с тестом
        """
        self.current_state = InterfaceState.ASSESSMENT

        # Получаем содержание урока для генерации вопросов
        if not self.current_lesson_content:
            # Пытаемся получить содержание из последнего урока
            lesson_data = self.state_manager.get_lesson_data(
                self.current_section, self.current_topic, self.current_lesson
            )
            if lesson_data:
                # Генерируем содержание урока для тестирования
                user_profile = self.state_manager.get_user_profile()
                course_plan = self.state_manager.get_course_plan()

                # Получаем названия
                course_title = self._get_safe_course_title(course_plan)
                (
                    section_title,
                    topic_title,
                    lesson_title,
                ) = self._get_element_titles_from_plan(
                    course_plan,
                    self.current_section,
                    self.current_topic,
                    self.current_lesson,
                )

                try:
                    lesson_content_data = self.content_generator.generate_lesson(
                        course=course_title,
                        section=section_title,
                        topic=topic_title,
                        lesson=lesson_title,
                        user_name=user_profile["name"],
                        communication_style=user_profile["communication_style"],
                    )
                    self.current_lesson_content = lesson_content_data["content"]
                except Exception as e:
                    self.logger.error(
                        f"Ошибка генерации содержания для теста: {str(e)}"
                    )
                    self.current_lesson_content = "Тестовое содержание урока"

        return self.assessment_interface.show_assessment(
            self.current_course,
            self.current_section,
            self.current_topic,
            self.current_lesson,
            self.current_lesson_content,
        )

    def show_course_completion(self):
        """
        Отображает экран завершения курса.

        Returns:
            widgets.VBox: Виджет с экраном завершения курса
        """
        self.current_state = InterfaceState.COURSE_COMPLETION
        return self.completion_interface.show_course_completion()

    # ========================================
    # ВНУТРЕННИЕ МЕТОДЫ - ИНТЕГРАЦИЯ ИНТЕРФЕЙСОВ
    # ========================================

    def _create_enhanced_lesson_interface(self, section_id, topic_id, lesson_id):
        """
        Создает улучшенный интерфейс урока с правильными обработчиками кнопок.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            widgets.VBox: Интерфейс урока с рабочими кнопками
        """
        try:
            # Получаем базовый интерфейс урока
            lesson_widget = self.lesson_interface.show_lesson(
                section_id, topic_id, lesson_id
            )

            # Ищем кнопки навигации в виджете и добавляем обработчики
            self._attach_lesson_button_handlers(
                lesson_widget, section_id, topic_id, lesson_id
            )

            return lesson_widget

        except Exception as e:
            self.logger.error(f"Ошибка при создании интерфейса урока: {str(e)}")

            # Возвращаем интерфейс ошибки
            error_header = self.utils.create_header("Ошибка при загрузке урока")
            error_message = self.utils.create_styled_message(
                f"Произошла ошибка при загрузке урока: {str(e)}", "incorrect"
            )

            back_button = widgets.Button(
                description="Вернуться к выбору курса",
                button_style="primary",
                icon="arrow-left",
            )

            def go_back_to_courses(b):
                # ИСПРАВЛЕНО: Используем правильную логику возврата к выбору курса
                from IPython.display import clear_output, display
                clear_output(wait=True)
                course_selection_widget = self.show_course_selection()
                display(course_selection_widget)

            back_button.on_click(go_back_to_courses)

            return widgets.VBox([error_header, error_message, back_button])

    def _attach_lesson_button_handlers(
        self, lesson_widget, section_id, topic_id, lesson_id
    ):
        """
        Присоединяет обработчики к кнопкам в интерфейсе урока.

        Args:
            lesson_widget (widgets.VBox): Виджет урока
            section_id, topic_id, lesson_id (str): ID элементов
        """

        def find_buttons_in_widget(widget):
            """Рекурсивно ищет кнопки в виджете."""
            buttons = []
            if hasattr(widget, "children"):
                for child in widget.children:
                    if isinstance(child, widgets.Button):
                        buttons.append(child)
                    else:
                        buttons.extend(find_buttons_in_widget(child))
            return buttons

        # Находим все кнопки в интерфейсе
        buttons = find_buttons_in_widget(lesson_widget)

        for button in buttons:
            description = button.description

            # Добавляем обработчики в зависимости от описания кнопки
            if description == "Назад":
                button.on_click(lambda b: self._handle_back_button())
            elif description == "Пройти тест":
                button.on_click(lambda b: self._handle_test_button())
            elif description == "Задать вопрос":
                button.on_click(lambda b: self._handle_ask_button())
            elif description == "Объясни подробнее":
                button.on_click(lambda b: self._handle_explain_button())
            elif description == "Приведи примеры":
                button.on_click(lambda b: self._handle_examples_button())

    def _handle_back_button(self):
        """Обработчик кнопки 'Назад'."""
        # ИСПРАВЛЕНО: Используем правильную логику возврата к выбору курса
        from IPython.display import clear_output, display
        clear_output(wait=True)
        course_selection_widget = self.show_course_selection()
        display(course_selection_widget)

    def _handle_test_button(self):
        """Обработчик кнопки 'Пройти тест'."""
        clear_output(wait=True)
        display(self.show_assessment())

    def _handle_ask_button(self):
        """Обработчик кнопки 'Задать вопрос' - показываем форму вопроса."""
        # Логика уже реализована в lesson_interface
        pass

    def _handle_explain_button(self):
        """Обработчик кнопки 'Объясни подробнее'."""
        # Логика уже реализована в lesson_interface
        pass

    def _handle_examples_button(self):
        """Обработчик кнопки 'Приведи примеры'."""
        # Логика уже реализована в lesson_interface
        pass

    # ========================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ
    # ========================================

    def _get_safe_course_title(self, course_plan):
        """
        Безопасно получает название курса.

        Args:
            course_plan (dict): План курса

        Returns:
            str: Название курса
        """
        course_title = course_plan.get("title", "Курс")
        if not course_title or course_title == "Курс":
            learning_progress = self.state_manager.get_learning_progress()
            course_title = learning_progress.get("current_course", "Курс Python")
        return course_title

    def _get_element_titles_from_plan(
        self, course_plan, section_id, topic_id, lesson_id
    ):
        """
        Получает названия элементов из плана курса.

        Returns:
            tuple: (section_title, topic_title, lesson_title)
        """
        section_title = "Раздел"
        topic_title = "Тема"
        lesson_title = "Урок"

        for section in course_plan.get("sections", []):
            if section.get("id") == section_id:
                section_title = (
                    section.get("title")
                    or section.get("name")
                    or section.get("id")
                    or "Раздел"
                )
                for topic in section.get("topics", []):
                    if topic.get("id") == topic_id:
                        topic_title = (
                            topic.get("title")
                            or topic.get("name")
                            or topic.get("id")
                            or "Тема"
                        )
                        for lesson in topic.get("lessons", []):
                            if lesson.get("id") == lesson_id:
                                lesson_title = (
                                    lesson.get("title")
                                    or lesson.get("name")
                                    or lesson.get("id")
                                    or "Урок"
                                )
                                break
                        break
                break

        return section_title, topic_title, lesson_title

    # ========================================
    # МЕТОДЫ ДЛЯ ПОЛНОЙ СОВМЕСТИМОСТИ СО СТАРЫМ КОДОМ
    # ========================================

    # Все старые методы, которые могли использоваться в других модулях
    def create_styled_message(self, message, style_type="info"):
        """СОВМЕСТИМОСТЬ: Создает стилизованное сообщение."""
        return self.utils.create_styled_message(message, style_type)

    def create_header(self, title, level="header"):
        """СОВМЕСТИМОСТЬ: Создает заголовок."""
        return self.utils.create_header(title, level)

    def create_navigation_info(
        self, course_title, section_title, topic_title, lesson_title, additional=""
    ):
        """СОВМЕСТИМОСТЬ: Создает навигационную информацию."""
        return self.utils.create_navigation_info(
            course_title, section_title, topic_title, lesson_title, additional
        )

    def get_safe_title(self, data, fallback="Элемент"):
        """СОВМЕСТИМОСТЬ: Безопасно получает название."""
        return self.utils.get_safe_title(data, fallback)

    def log_interface_action(self, action_type, details=None):
        """СОВМЕСТИМОСТЬ: Логирует действие интерфейса."""
        return self.utils.log_interface_action(action_type, details)
