"""
Интерфейс для отображения уроков и интерактивных функций.
Отвечает за показ содержания урока, примеров, объяснений и обработку вопросов пользователя.
РЕФАКТОРИНГ: Разделен на модули для соответствия лимиту размера.
ИСПРАВЛЕНО ЭТАП 34: Добавлена ссылка на parent_facade для кнопки тестирования (проблема #145)
ИСПРАВЛЕНО ЭТАП 43: Добавлена защита от ошибок контрольных заданий
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
            self.logger.info(
                f"🚀 НАЧАЛО: Показ урока {section_id}:{topic_id}:{lesson_id}"
            )

            # ШАГ 1: Получаем план курса
            self.logger.info("📋 ШАГ 1: Получение плана курса...")
            course_plan = self._get_course_plan()
            if not course_plan:
                self.logger.error("❌ ШАГ 1: План курса недоступен")
                return self._create_error_interface(
                    "Ошибка курса", "План курса недоступен"
                )
            self.logger.info("✅ ШАГ 1: План курса получен успешно")

            # ШАГ 2: Извлекаем названия элементов
            self.logger.info("📝 ШАГ 2: Извлечение названий элементов...")
            try:
                (
                    course_title,
                    section_title,
                    topic_title,
                    lesson_title,
                ) = self.lesson_utils.get_element_titles_from_plan(
                    course_plan, section_id, topic_id, lesson_id
                )
                self.logger.info(f"✅ ШАГ 2: Названия извлечены - {lesson_title}")
            except Exception as e:
                self.logger.error(f"❌ ШАГ 2: Ошибка извлечения названий: {str(e)}")
                raise

            # ШАГ 3: Получаем данные урока из плана
            self.logger.info("📊 ШАГ 3: Получение данных урока из плана...")
            try:
                lesson_data = self.lesson_utils.get_lesson_from_plan(
                    course_plan, section_id, topic_id, lesson_id
                )
                self.logger.info(f"✅ ШАГ 3: Данные урока получены: {type(lesson_data)}")
            except Exception as e:
                self.logger.error(f"❌ ШАГ 3: Ошибка получения данных урока: {str(e)}")
                raise

            # ШАГ 4: Получаем профиль пользователя
            self.logger.info("👤 ШАГ 4: Получение профиля пользователя...")
            try:
                user_profile = self._get_user_profile()
                self.logger.info(f"✅ ШАГ 4: Профиль получен: {type(user_profile)}")
            except Exception as e:
                self.logger.error(f"❌ ШАГ 4: Ошибка получения профиля: {str(e)}")
                raise

            # ШАГ 5: Получаем содержание урока (с кэшированием)
            self.logger.info("📖 ШАГ 5: Получение содержания урока...")
            try:
                lesson_content_data = self.content_manager.get_lesson_content(
                    section_id, topic_id, lesson_id, self.content_generator
                )
                self.logger.info(
                    f"✅ ШАГ 5: Содержание урока получено: {type(lesson_content_data)}"
                )
            except Exception as e:
                self.logger.error(f"❌ ШАГ 5: Ошибка получения содержания: {str(e)}")
                raise

            # ШАГ 6: Валидация данных урока
            self.logger.info("🔍 ШАГ 6: Валидация данных урока...")
            try:
                is_valid, error_msg = self.lesson_utils.validate_lesson_data(
                    lesson_content_data, lesson_data
                )
                if not is_valid:
                    self.logger.error(f"❌ ШАГ 6: Валидация не пройдена: {error_msg}")
                    return self._create_error_interface(
                        "Ошибка данных урока", error_msg
                    )
                self.logger.info("✅ ШАГ 6: Валидация пройдена успешно")
            except Exception as e:
                self.logger.error(f"❌ ШАГ 6: Ошибка валидации: {str(e)}")
                raise

            # ШАГ 7: Интеграция демо-ячеек
            self.logger.info("🔧 ШАГ 7: Интеграция демо-ячеек...")
            try:
                lesson_content_data = self.content_manager.integrate_demo_cells(
                    lesson_content_data, lesson_id
                )
                self.logger.info("✅ ШАГ 7: Демо-ячейки интегрированы")
            except Exception as e:
                self.logger.error(f"❌ ШАГ 7: Ошибка интеграции демо-ячеек: {str(e)}")
                raise

            # ШАГ 8: Сохраняем данные урока
            self.logger.info("💾 ШАГ 8: Сохранение данных урока...")
            try:
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
                self.logger.info("✅ ШАГ 8: Данные урока сохранены")
            except Exception as e:
                self.logger.error(f"❌ ШАГ 8: Ошибка сохранения данных: {str(e)}")
                raise

            # ШАГ 9: Обновляем прогресс обучения
            self.logger.info("📈 ШАГ 9: Обновление прогресса обучения...")
            try:
                if hasattr(self.content_manager, "update_lesson_progress"):
                    self.content_manager.update_lesson_progress(
                        "unknown", section_id, topic_id, lesson_id
                    )
                self.logger.info("✅ ШАГ 9: Прогресс обновлен")
            except Exception as e:
                self.logger.warning(
                    f"⚠️ ШАГ 9: Ошибка обновления прогресса (не критично): {str(e)}"
                )

            # ШАГ 10: Создаем интерфейс урока
            self.logger.info("🎨 ШАГ 10: Создание интерфейса урока...")
            try:
                lesson_interface = self._create_lesson_interface(
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
                self.logger.info("✅ ШАГ 10: Интерфейс урока создан успешно")
                self.logger.info("🎉 УРОК ГОТОВ К ОТОБРАЖЕНИЮ!")
                return lesson_interface
            except Exception as e:
                self.logger.error(f"❌ ШАГ 10: Ошибка создания интерфейса: {str(e)}")
                raise

        except Exception as e:
            error_msg = f"Критическая ошибка при отображении урока: {str(e)}"
            self.logger.error(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {error_msg}")
            self.logger.error(f"📋 Traceback: {traceback.format_exc()}")
            return self._create_error_interface("Критическая ошибка", error_msg)

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

        Args:
            lesson_content_data (dict): Данные содержания урока
            lesson_data (dict): Базовые данные урока
            course_title (str): Название курса
            section_title (str): Название раздела
            topic_title (str): Название темы
            lesson_title (str): Название урока
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока
            user_profile (dict): Профиль пользователя

        Returns:
            widgets.VBox: Интерфейс урока
        """
        try:
            self.logger.info("🎨 СОЗДАНИЕ ИНТЕРФЕЙСА: Начало создания компонентов...")

            # Заголовок урока
            self.logger.info("🎨 Создание заголовка урока...")
            lesson_header = self.lesson_utils.create_lesson_header(lesson_title)
            self.logger.info("✅ Заголовок урока создан")

            # Навигационная информация
            self.logger.info("🎨 Создание навигационной информации...")
            estimated_time = f"⏱️ {lesson_content_data.get('estimated_time', 30)} мин."
            nav_info = self.lesson_utils.create_navigation_info(
                course_title, section_title, topic_title, lesson_title, estimated_time
            )
            self.logger.info("✅ Навигационная информация создана")

            # Содержание урока
            self.logger.info("🎨 Создание содержания урока...")
            lesson_content = self.lesson_utils.create_lesson_content(
                lesson_content_data
            )
            self.logger.info("✅ Содержание урока создано")

            # Интерактивные кнопки
            self.logger.info("🎨 Создание интерактивных кнопок...")
            interactive_buttons = self.lesson_utils.create_interactive_buttons(
                self.interactive_handlers
            )
            self.logger.info("✅ Интерактивные кнопки созданы")

            # ИСПРАВЛЕНО ЭТАП 43: Контрольные задания (если есть) - с защитой от ошибок
            self.logger.info("🎨 Создание контрольных заданий...")
            control_tasks_interface = None
            try:
                control_tasks_interface = (
                    self.content_manager.get_control_tasks_interface(
                        lesson_id, self.current_course_info
                    )
                )
                if control_tasks_interface:
                    self.logger.info("✅ Контрольные задания успешно созданы")
                else:
                    self.logger.info("ℹ️ Контрольные задания не созданы или недоступны")
            except Exception as e:
                self.logger.warning(
                    f"⚠️ Ошибка создания контрольных заданий (не критично): {str(e)}"
                )
                control_tasks_interface = None

            # Кнопка тестирования
            self.logger.info("🎨 Создание кнопки тестирования...")
            assessment_button = self.lesson_utils.create_assessment_button(
                self.assessment, lesson_data, self.current_course_info
            )
            self.logger.info("✅ Кнопка тестирования создана")

            # Собираем интерфейс
            self.logger.info("🎨 Сборка компонентов интерфейса...")
            interface_components = [
                lesson_header,
                nav_info,
                lesson_content,
                interactive_buttons,
            ]

            # Добавляем контрольные задания если есть
            if control_tasks_interface:
                interface_components.append(control_tasks_interface)
                self.logger.info("✅ Контрольные задания добавлены в интерфейс")

            # Добавляем кнопку тестирования
            interface_components.append(assessment_button)
            self.logger.info("✅ Кнопка тестирования добавлена в интерфейс")

            # Создаем финальный VBox
            self.logger.info("🎨 Создание финального VBox...")
            final_interface = widgets.VBox(
                interface_components,
                layout=widgets.Layout(margin="0 auto", max_width="900px"),
            )
            self.logger.info("✅ Финальный VBox создан успешно")

            # Проверяем что получили
            self.logger.info(
                f"🔍 ПРОВЕРКА РЕЗУЛЬТАТА: Тип объекта: {type(final_interface)}"
            )
            self.logger.info(
                f"🔍 ПРОВЕРКА РЕЗУЛЬТАТА: Количество компонентов: {len(interface_components)}"
            )
            self.logger.info("🎉 ИНТЕРФЕЙС УРОКА ГОТОВ ДЛЯ ВОЗВРАТА!")

            return final_interface

        except Exception as e:
            self.logger.error(
                f"💥 КРИТИЧЕСКАЯ ОШИБКА в _create_lesson_interface: {str(e)}"
            )
            self.logger.error(f"📋 Traceback: {traceback.format_exc()}")
            # Возвращаем интерфейс ошибки вместо исключения
            return self._create_error_interface("Ошибка создания интерфейса", str(e))

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
                self.logger.warning("Методы получения профиля пользователя недоступны")
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
        """Сохраняет данные текущего урока."""
        self.current_lesson_data = {
            "lesson_content_data": lesson_content_data,
            "course_title": course_title,
            "section_title": section_title,
            "topic_title": topic_title,
            "lesson_title": lesson_title,
            "section_id": section_id,
            "topic_id": topic_id,
            "lesson_id": lesson_id,
            "user_profile": user_profile,
        }
        self.current_lesson_content = lesson_content_data
        self.current_course_info = {
            "course_title": course_title,
            "course_plan": course_plan,
            "current_lesson": lesson_title,
        }
        self.current_lesson_id = lesson_id
