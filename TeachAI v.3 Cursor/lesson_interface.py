"""
Интерфейс для отображения уроков и интерактивных функций.
Отвечает за показ содержания урока, примеров, объяснений и обработку вопросов пользователя.
ИСПРАВЛЕНО: Проблема #89 - добавлено кэширование содержания урока
ИСПРАВЛЕНО: Проблема #90 - убран course_context из generate_examples()
РЕФАКТОРИНГ: Разделен на модули для улучшения модульности.
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
import traceback
from interface_utils import InterfaceUtils, InterfaceState
from lesson_display import LessonDisplay
from lesson_navigation import LessonNavigation
from lesson_interaction import LessonInteraction
from lesson_utils import LessonUtils
from assessment_interface import AssessmentInterface
from control_tasks_interface import ControlTasksInterface


class LessonInterface:
    """Интерфейс для отображения уроков и интерактивных функций."""

    def __init__(
        self, state_manager, content_generator, system_logger, assessment=None
    ):
        """
        Инициализация интерфейса уроков.

        Args:
            state_manager: Менеджер состояния
            content_generator: Генератор контента
            system_logger: Системный логгер
            assessment: Модуль оценивания (опционально)
        """
        self.state_manager = state_manager
        self.content_generator = content_generator
        self.system_logger = system_logger
        self.assessment = assessment
        self.logger = logging.getLogger(__name__)

        # Утилиты интерфейса
        self.utils = InterfaceUtils()

        # Добавляем хранилище данных для интерактивных функций
        self.current_lesson_data = None
        self.current_lesson_content = None
        self.current_course_info = None
        self.current_lesson_id = None  # Для счетчика вопросов

        # ИСПРАВЛЕНО: Добавлено кэширование содержания урока (проблема #89)
        self.cached_lesson_content = None
        self.cached_lesson_title = None
        self.current_lesson_cache_key = None  # Для идентификации текущего урока

        # ИСПРАВЛЕНО: Ссылки на контейнеры для правильного закрытия
        self.explain_container = None
        self.examples_container = None
        self.qa_container = None
        self.control_tasks_container = None

        # Инициализируем модули
        self.display = LessonDisplay(self)
        self.navigation = LessonNavigation(self)
        self.interaction = LessonInteraction(self)
        self.lesson_utils = LessonUtils()
        self.control_tasks_interface = ControlTasksInterface(content_generator, self)

        # Инициализируем интерфейс тестирования
        try:
            self.assessment_interface = AssessmentInterface(
                state_manager, assessment, system_logger, self
            )
            self.logger.info("AssessmentInterface успешно инициализирован")
        except Exception as e:
            self.logger.error(f"Ошибка при инициализации AssessmentInterface: {str(e)}")
            self.assessment_interface = None

    def show_lesson(self, section_id, topic_id, lesson_id):
        """
        Отображает урок пользователю с кэшированием содержания.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            widgets.VBox: Виджет с уроком
        """
        return self.display.show_lesson(section_id, topic_id, lesson_id)

    def _create_enhanced_navigation_buttons(self, section_id, topic_id, lesson_id):
        """
        Создает улучшенные кнопки навигации для урока.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            widgets.HBox: Контейнер с кнопками навигации
        """
        return self.navigation.create_enhanced_navigation_buttons(
            section_id, topic_id, lesson_id
        )

    def _show_explanation_choice(self):
        """
        Показывает выбор типа объяснения.
        """
        self.interaction.show_explanation_choice()

    def _show_concept_explanation(self, concept):
        """
        Показывает объяснение конкретного понятия.

        Args:
            concept (dict): Данные о понятии
        """
        self.interaction.show_concept_explanation(concept)

    def _clear_lesson_cache(self):
        """
        Очищает кэш урока.
        """
        self.lesson_utils.clear_lesson_cache(self)

    def _setup_enhanced_qa_container(self, qa_container):
        """
        Настраивает улучшенный контейнер для вопросов и ответов.

        Args:
            qa_container: Контейнер для вопросов и ответов
        """
        self.interaction.setup_enhanced_qa_container(qa_container)

    def _get_element_titles(self, course_plan, section_id, topic_id, lesson_id):
        """
        Получает названия элементов курса.

        Args:
            course_plan (dict): План курса
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            tuple: (course_title, section_title, topic_title, lesson_title)
        """
        return self.lesson_utils.get_element_titles(
            course_plan, section_id, topic_id, lesson_id
        )

    def _get_course_id(self, course_plan):
        """
        Получает ID курса из плана курса.

        Args:
            course_plan (dict): План курса

        Returns:
            str: ID курса или "default"
        """
        return self.lesson_utils.get_course_id(course_plan)

    def _create_lesson_error_interface(self, title, message):
        """
        Создает интерфейс ошибки для урока.

        Args:
            title (str): Заголовок ошибки
            message (str): Сообщение об ошибке

        Returns:
            widgets.VBox: Виджет с сообщением об ошибке
        """
        return self.lesson_utils.create_lesson_error_interface(title, message, self)

    def _hide_other_containers(self):
        """
        Скрывает все контейнеры интерактивных функций.
        """
        try:
            if self.explain_container:
                self.explain_container.layout.display = "none"
            if self.examples_container:
                self.examples_container.layout.display = "none"
            if self.qa_container:
                self.qa_container.layout.display = "none"
            if self.control_tasks_container:
                self.control_tasks_container.layout.display = "none"
        except Exception as e:
            self.logger.error(f"Ошибка при скрытии контейнеров: {str(e)}")
