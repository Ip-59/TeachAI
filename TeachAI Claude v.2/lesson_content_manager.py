"""
Менеджер контента уроков и интеграций.
Отвечает за работу с демо-ячейками, контрольными заданиями и кэшированием.

ИСПРАВЛЕНО ЭТАП 29: Устранена ошибка вызова generate_lesson_content с неправильными аргументами
"""

import logging
import traceback

# Импорт demo_cells_integration с обработкой ошибок
try:
    from demo_cells_integration import DemoCellsIntegration

    DEMO_CELLS_AVAILABLE = True
except ImportError:
    logging.warning("Модуль demo_cells_integration недоступен")
    DEMO_CELLS_AVAILABLE = False

# Импорт control_tasks_generator с обработкой ошибок
try:
    from control_tasks_generator import ControlTasksGenerator

    CONTROL_TASKS_AVAILABLE = True
except ImportError:
    logging.warning("Модуль control_tasks_generator недоступен")
    CONTROL_TASKS_AVAILABLE = False


class LessonContentManager:
    """Менеджер контента уроков и интеграций."""

    def __init__(self, state_manager, logger):
        """
        Инициализация менеджера контента.

        Args:
            state_manager: Менеджер состояния
            logger: Логгер
        """
        self.state_manager = state_manager
        self.logger = logger

        # Кэширование содержания урока для экономии API запросов
        self.cached_lesson_content = None
        self.cached_lesson_title = None
        self.current_lesson_cache_key = None

        # Интеграция демо-ячеек
        self.demo_cells_integration = None
        if DEMO_CELLS_AVAILABLE:
            try:
                self.demo_cells_integration = DemoCellsIntegration()
                self.logger.info("Demo cells integration инициализирован")
            except Exception as e:
                self.logger.error(f"Ошибка инициализации demo cells: {str(e)}")
                self.demo_cells_integration = None

        # Интеграция контрольных заданий
        self.control_tasks_generator = None
        self.current_control_tasks = None
        if CONTROL_TASKS_AVAILABLE:
            try:
                # Получаем API ключ из StateManager
                api_key = None
                if hasattr(state_manager, "state") and "api_key" in state_manager.state:
                    api_key = state_manager.state["api_key"]

                self.control_tasks_generator = ControlTasksGenerator(api_key)
                self.logger.info("Control tasks generator инициализирован")
            except Exception as e:
                self.logger.error(
                    f"Ошибка инициализации control tasks generator: {str(e)}"
                )
                self.control_tasks_generator = None

    def get_lesson_content(self, section_id, topic_id, lesson_id, content_generator):
        """
        Получает содержание урока с кэшированием.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока
            content_generator: Генератор контента

        Returns:
            dict: Содержание урока
        """
        lesson_cache_key = f"{section_id}:{topic_id}:{lesson_id}"

        # Проверяем кэш
        if (
            self.current_lesson_cache_key == lesson_cache_key
            and self.cached_lesson_content
        ):
            self.logger.debug(
                f"Используем кэшированное содержание урока {lesson_cache_key}"
            )
            return self.cached_lesson_content

        # Генерируем новое содержание
        try:
            # ИСПРАВЛЕНО: Формируем правильные аргументы для generate_lesson_content
            lesson_data = self._build_lesson_data(section_id, topic_id, lesson_id)
            user_data = self._get_user_data()
            course_context = self._get_course_context()

            lesson_content_data = content_generator.generate_lesson_content(
                lesson_data=lesson_data,
                user_data=user_data,
                course_context=course_context,
            )

            # Кэшируем результат
            self.cached_lesson_content = lesson_content_data
            self.current_lesson_cache_key = lesson_cache_key

            self.logger.info(
                f"Сгенерировано и закэшировано содержание урока {lesson_cache_key}"
            )
            return lesson_content_data

        except Exception as e:
            self.logger.error(f"Ошибка генерации содержания урока: {str(e)}")
            raise

    def _build_lesson_data(self, section_id, topic_id, lesson_id):
        """
        Формирует данные урока из ID компонентов.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            dict: Данные урока
        """
        try:
            # Получаем план курса
            course_plan = self._get_course_plan()
            if not course_plan:
                # Fallback - базовые данные урока
                return {
                    "id": lesson_id,
                    "title": f"Урок {lesson_id}",
                    "section_id": section_id,
                    "topic_id": topic_id,
                    "description": "",
                }

            # Ищем урок в плане курса
            for section in course_plan.get("sections", []):
                if section.get("id") == section_id:
                    for topic in section.get("topics", []):
                        if topic.get("id") == topic_id:
                            for lesson in topic.get("lessons", []):
                                if lesson.get("id") == lesson_id:
                                    # Нашли урок - возвращаем его данные
                                    return {
                                        "id": lesson_id,
                                        "title": lesson.get(
                                            "title", f"Урок {lesson_id}"
                                        ),
                                        "description": lesson.get("description", ""),
                                        "section_id": section_id,
                                        "topic_id": topic_id,
                                        "section_title": section.get("title", ""),
                                        "topic_title": topic.get("title", ""),
                                        "estimated_time": lesson.get(
                                            "estimated_time", 30
                                        ),
                                        "objectives": lesson.get("objectives", []),
                                    }

            # Урок не найден - возвращаем базовые данные
            self.logger.warning(
                f"Урок {section_id}:{topic_id}:{lesson_id} не найден в плане курса"
            )
            return {
                "id": lesson_id,
                "title": f"Урок {lesson_id}",
                "section_id": section_id,
                "topic_id": topic_id,
                "description": "",
            }

        except Exception as e:
            self.logger.error(f"Ошибка формирования данных урока: {str(e)}")
            # Fallback - базовые данные
            return {
                "id": lesson_id,
                "title": f"Урок {lesson_id}",
                "section_id": section_id,
                "topic_id": topic_id,
                "description": "",
            }

    def _get_user_data(self):
        """
        Получает данные пользователя из state_manager.

        Returns:
            dict: Данные пользователя
        """
        try:
            if hasattr(self.state_manager, "get_user_profile"):
                return self.state_manager.get_user_profile()
            elif hasattr(self.state_manager, "get_user_data"):
                return self.state_manager.get_user_data()
            elif (
                hasattr(self.state_manager, "state")
                and "user" in self.state_manager.state
            ):
                return self.state_manager.state["user"]
            else:
                # Fallback - базовые данные пользователя
                return {
                    "name": "Пользователь",
                    "communication_style": "friendly",
                    "lesson_duration_minutes": 30,
                }
        except Exception as e:
            self.logger.warning(f"Ошибка получения данных пользователя: {str(e)}")
            return {
                "name": "Пользователь",
                "communication_style": "friendly",
                "lesson_duration_minutes": 30,
            }

    def _get_course_context(self):
        """
        Получает контекст курса из state_manager.

        Returns:
            dict: Контекст курса
        """
        try:
            course_plan = self._get_course_plan()
            if course_plan:
                return {
                    "course_title": course_plan.get("title", "Курс"),
                    "course_description": course_plan.get("description", ""),
                    "course_plan": course_plan,
                }
            else:
                return {}
        except Exception as e:
            self.logger.warning(f"Ошибка получения контекста курса: {str(e)}")
            return {}

    def _get_course_plan(self):
        """
        Получает план курса из state_manager.

        Returns:
            dict: План курса или None
        """
        try:
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
                return None
        except Exception as e:
            self.logger.error(f"Ошибка получения плана курса: {str(e)}")
            return None

    def integrate_demo_cells(self, lesson_content_data, lesson_id):
        """
        Интегрирует демо-ячейки в содержание урока.

        Args:
            lesson_content_data (dict): Данные урока
            lesson_id (str): ID урока

        Returns:
            dict: Урок с интегрированными демо-ячейками
        """
        try:
            if self.demo_cells_integration:
                lesson_content_data[
                    "content"
                ] = self.demo_cells_integration.integrate_demo_cells_in_lesson(
                    lesson_content_data["content"], lesson_id
                )
                self.logger.debug(
                    f"Демо-ячейки успешно интегрированы в урок {lesson_id}"
                )
            else:
                self.logger.debug("Demo cells integration недоступен")

            return lesson_content_data

        except Exception as e:
            self.logger.warning(f"Ошибка интеграции демо-ячеек: {str(e)}")
            return lesson_content_data

    def generate_control_tasks(self, lesson_data, course_info):
        """
        Генерирует контрольные задания для урока.

        Args:
            lesson_data (dict): Данные урока
            course_info (dict): Информация о курсе

        Returns:
            list: Список контрольных заданий или None
        """
        try:
            if not self.control_tasks_generator:
                self.logger.debug("Control tasks generator недоступен")
                return None

            # Генерируем контрольные задания
            tasks = self.control_tasks_generator.generate_tasks(
                lesson_content=lesson_data.get("content", ""),
                lesson_title=lesson_data.get("title", ""),
                course_context=course_info,
            )

            if tasks:
                self.current_control_tasks = tasks
                self.logger.info(f"Сгенерировано {len(tasks)} контрольных заданий")
                return tasks
            else:
                self.logger.debug("Контрольные задания не сгенерированы")
                return None

        except Exception as e:
            self.logger.error(f"Ошибка генерации контрольных заданий: {str(e)}")
            return None

    def get_control_tasks_interface(self, lesson_id, course_info):
        """
        Создает интерфейс контрольных заданий.

        Args:
            lesson_id (str): ID урока
            course_info (dict): Информация о курсе

        Returns:
            widgets.Widget: Интерфейс контрольных заданий или None
        """
        try:
            if not self.current_control_tasks:
                # Пытаемся сгенерировать задания
                lesson_data = {"id": lesson_id, "title": f"Урок {lesson_id}"}
                self.generate_control_tasks(lesson_data, course_info)

            if self.current_control_tasks and self.control_tasks_generator:
                return self.control_tasks_generator.create_tasks_interface(
                    self.current_control_tasks, lesson_id
                )
            else:
                return None

        except Exception as e:
            self.logger.error(
                f"Ошибка создания интерфейса контрольных заданий: {str(e)}"
            )
            return None

    def update_lesson_progress(self, course_id, section_id, topic_id, lesson_id):
        """
        Обновляет прогресс изучения урока.

        Args:
            course_id (str): ID курса
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока
        """
        try:
            if hasattr(self.state_manager, "update_lesson_progress"):
                self.state_manager.update_lesson_progress(
                    course_id, section_id, topic_id, lesson_id
                )
            elif hasattr(self.state_manager, "log_lesson_view"):
                self.state_manager.log_lesson_view(lesson_id)

            self.logger.debug(f"Прогресс урока {lesson_id} обновлен")

        except Exception as e:
            self.logger.warning(f"Ошибка обновления прогресса урока: {str(e)}")

    def clear_cache(self):
        """Очищает кэш содержания урока."""
        self.cached_lesson_content = None
        self.cached_lesson_title = None
        self.current_lesson_cache_key = None
        self.current_control_tasks = None
        self.logger.debug("Кэш содержания урока очищен")

    def get_cache_status(self):
        """
        Возвращает статус кэша.

        Returns:
            dict: Информация о кэше
        """
        return {
            "has_cached_content": self.cached_lesson_content is not None,
            "cache_key": self.current_lesson_cache_key,
            "has_control_tasks": self.current_control_tasks is not None,
            "demo_cells_available": self.demo_cells_integration is not None,
            "control_tasks_available": self.control_tasks_generator is not None,
        }
