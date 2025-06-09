"""
Интерфейс для отображения уроков и интерактивных функций.
Отвечает за показ содержания урока, примеров, объяснений и обработку вопросов пользователя.
РЕФАКТОРИНГ: Разделен на модули для соответствия лимиту размера.
ИСПРАВЛЕНО ЭТАП 34: Добавлена ссылка на parent_facade для кнопки тестирования (проблема #145)
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
import traceback
from interface_utils import InterfaceUtils, InterfaceState
from lesson_interactive_handlers import LessonInteractiveHandlers
from lesson_content_manager import LessonContentManager
from lesson_utils import LessonUtils


class LessonInterface:
    """Интерфейс для отображения уроков и интерактивных функций."""

    def __init__(
        self,
        state_manager,
        content_generator,
        system_logger,
        assessment=None,
        parent_facade=None,
    ):
        """
        Инициализация интерфейса уроков.

        Args:
            state_manager: Менеджер состояния
            content_generator: Генератор контента
            system_logger: Системный логгер
            assessment: Модуль оценивания (опционально)
            parent_facade: Ссылка на родительский фасад (опционально) - ДОБАВЛЕНО ЭТАП 34
        """
        self.state_manager = state_manager
        self.content_generator = content_generator
        self.system_logger = system_logger
        self.assessment = assessment
        self.parent_facade = (
            parent_facade  # ИСПРАВЛЕНО ЭТАП 34: Сохраняем ссылку на facade
        )
        self.logger = logging.getLogger(__name__)

        # Утилиты интерфейса
        self.utils = InterfaceUtils()

        # Инициализация подмодулей
        self.interactive_handlers = LessonInteractiveHandlers(
            content_generator=content_generator,
            state_manager=state_manager,
            utils=self.utils,
            logger=self.logger,
        )

        self.content_manager = LessonContentManager(
            state_manager=state_manager, logger=self.logger
        )

        self.lesson_utils = LessonUtils(interface_utils=self.utils, logger=self.logger)

        # Данные текущего урока
        self.current_lesson_data = None
        self.current_lesson_content = None
        self.current_course_info = None
        self.current_lesson_id = None

        self.logger.info("LessonInterface инициализирован с подмодулями")

    def show_lesson(self, section_id, topic_id, lesson_id):
        """
        Отображает урок пользователю.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            widgets.VBox: Интерфейс урока
        """
        try:
            self.logger.info(f"Показ урока: {section_id}:{topic_id}:{lesson_id}")

            # Получаем план курса
            course_plan = self._get_course_plan()
            if not course_plan:
                return self._create_error_interface(
                    "Ошибка курса", "План курса недоступен"
                )

            # Извлекаем названия элементов
            (
                course_title,
                section_title,
                topic_title,
                lesson_title,
            ) = self.lesson_utils.get_element_titles_from_plan(
                course_plan, section_id, topic_id, lesson_id
            )

            # Получаем данные урока из плана
            lesson_data = self.lesson_utils.get_lesson_from_plan(
                course_plan, section_id, topic_id, lesson_id
            )

            # Получаем профиль пользователя
            user_profile = self._get_user_profile()

            # Получаем содержание урока (с кэшированием)
            lesson_content_data = self.content_manager.get_lesson_content(
                section_id, topic_id, lesson_id, self.content_generator
            )

            # Валидация данных урока
            is_valid, error_msg = self.lesson_utils.validate_lesson_data(
                lesson_content_data, lesson_data
            )
            if not is_valid:
                return self._create_error_interface("Ошибка данных урока", error_msg)

            # Интеграция демо-ячеек
            lesson_content_data = self.content_manager.integrate_demo_cells(
                lesson_content_data, lesson_id
            )

            # Сохраняем данные урока
            self._store_lesson_data(
                lesson_content_data,
                course_title,
                section_title,
                topic_title,
                lesson_title,
                section_id,
                topic_id,
                lesson_id,
                user_profile,
                course_plan,
            )

            # Обновляем прогресс обучения
            course_id = self.lesson_utils.get_course_id(course_plan)
            self.content_manager.update_lesson_progress(
                course_id, section_id, topic_id, lesson_id
            )

            # Логируем урок
            self._log_lesson(
                course_title, section_title, topic_title, lesson_content_data
            )

            # Создаем интерфейс урока
            return self._create_lesson_interface(
                lesson_content_data,
                lesson_data,
                course_title,
                section_title,
                topic_title,
                lesson_title,
                section_id,
                topic_id,
                lesson_id,
                user_profile,
            )

        except Exception as e:
            self.logger.error(f"Критическая ошибка при отображении урока: {str(e)}")
            self.logger.error(traceback.format_exc())
            return self._create_error_interface(
                "Критическая ошибка", f"Произошла критическая ошибка: {str(e)}"
            )

    def _get_course_plan(self):
        """
        Получает план курса из StateManager.

        Returns:
            dict: План курса или None
        """
        try:
            # Попробуем несколько способов получения плана курса
            if hasattr(self.state_manager, "get_course_plan"):
                return self.state_manager.get_course_plan()
            elif hasattr(self.state_manager, "course_data_manager"):
                return self.state_manager.course_data_manager.get_course_plan()
            elif (
                hasattr(self.state_manager, "state")
                and "course_plan" in self.state_manager.state
            ):
                return self.state_manager.state["course_plan"]
            else:
                self.logger.error("Не удалось найти метод получения плана курса")
                return None

        except Exception as e:
            self.logger.error(f"Ошибка получения плана курса: {str(e)}")
            return None

    def _get_user_profile(self):
        """
        Получает профиль пользователя.

        Returns:
            dict: Профиль пользователя
        """
        try:
            if hasattr(self.state_manager, "get_user_profile"):
                return self.state_manager.get_user_profile()
            elif hasattr(self.state_manager, "get_user_data"):
                return self.state_manager.get_user_data()
            else:
                return {}
        except Exception as e:
            self.logger.warning(f"Ошибка получения профиля пользователя: {str(e)}")
            return {}

    def _store_lesson_data(
        self,
        lesson_content_data,
        course_title,
        section_title,
        topic_title,
        lesson_title,
        section_id,
        topic_id,
        lesson_id,
        user_profile,
        course_plan,
    ):
        """
        Сохраняет данные текущего урока.
        """
        # Сохраняем данные урока
        self.current_lesson_data = lesson_content_data
        self.current_lesson_content = lesson_content_data["content"]
        self.current_lesson_id = f"{section_id}:{topic_id}:{lesson_id}"
        self.current_course_info = {
            "course_title": course_title,
            "section_title": section_title,
            "topic_title": topic_title,
            "lesson_title": lesson_title,
            "section_id": section_id,
            "topic_id": topic_id,
            "lesson_id": lesson_id,
            "user_profile": user_profile,
            "course_plan": course_plan,
            "facade": self.parent_facade,  # ИСПРАВЛЕНО ЭТАП 34: Добавлена ссылка на facade для кнопки тестирования
        }

        # Передаем данные в обработчики интерактивных действий
        self.interactive_handlers.set_lesson_data(
            self.current_lesson_content,
            self.current_course_info,
            self.current_lesson_id,
        )

    def _log_lesson(
        self, course_title, section_title, topic_title, lesson_content_data
    ):
        """
        Логирует урок в системном логгере.
        """
        try:
            self.system_logger.log_lesson(
                course=course_title,
                section=section_title,
                topic=topic_title,
                lesson_title=lesson_content_data["title"],
                lesson_content=lesson_content_data["content"],
            )
        except Exception as e:
            self.logger.warning(f"Ошибка логирования урока: {str(e)}")

    def _create_lesson_interface(
        self,
        lesson_content_data,
        lesson_data,
        course_title,
        section_title,
        topic_title,
        lesson_title,
        section_id,
        topic_id,
        lesson_id,
        user_profile,
    ):
        """
        Создает полный интерфейс урока.

        Returns:
            widgets.VBox: Интерфейс урока
        """
        # Заголовок урока
        lesson_header = self.lesson_utils.create_lesson_header(lesson_title)

        # Навигационная информация
        estimated_time = f"⏱️ {lesson_content_data.get('estimated_time', 30)} мин."
        nav_info = self.lesson_utils.create_navigation_info(
            course_title, section_title, topic_title, lesson_title, estimated_time
        )

        # Содержание урока
        lesson_content = self.lesson_utils.create_lesson_content(lesson_content_data)

        # Интерактивные кнопки
        interactive_buttons = self.lesson_utils.create_interactive_buttons(
            self.interactive_handlers
        )

        # Контрольные задания (если есть)
        control_tasks_interface = self.content_manager.get_control_tasks_interface(
            lesson_id, self.current_course_info
        )

        # Кнопка тестирования
        assessment_button = self.lesson_utils.create_assessment_button(
            self.assessment, lesson_data, self.current_course_info
        )

        # Собираем интерфейс
        interface_components = [
            lesson_header,
            nav_info,
            lesson_content,
            interactive_buttons,
        ]

        # Добавляем контрольные задания если есть
        if control_tasks_interface:
            interface_components.append(control_tasks_interface)

        # Добавляем кнопку тестирования
        interface_components.append(assessment_button)

        return widgets.VBox(
            interface_components,
            layout=widgets.Layout(margin="0 auto", max_width="900px"),
        )

    def _create_error_interface(self, error_title, error_message):
        """
        Создает интерфейс ошибки.

        Args:
            error_title (str): Заголовок ошибки
            error_message (str): Сообщение об ошибке

        Returns:
            widgets.VBox: Интерфейс ошибки
        """
        return self.lesson_utils.create_lesson_error_interface(
            error_title, error_message
        )

    def get_current_lesson_info(self):
        """
        Возвращает информацию о текущем уроке.

        Returns:
            dict: Информация о текущем уроке
        """
        return {
            "lesson_id": self.current_lesson_id,
            "course_info": self.current_course_info,
            "has_content": self.current_lesson_content is not None,
            "cache_info": self.content_manager.get_cache_info(),
        }

    def clear_lesson_cache(self):
        """Очищает кэш урока."""
        self.content_manager.clear_cache()
        self.current_lesson_data = None
        self.current_lesson_content = None
        self.current_course_info = None
        self.current_lesson_id = None
        self.logger.info("Кэш урока очищен")
