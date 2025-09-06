"""
Интерфейс для отображения уроков и интерактивных функций.
Отвечает за показ содержания урока, примеров, объяснений и обработку вопросов пользователя.

ИСПРАВЛЕНО ЭТАП 52: КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ - правильная передача данных урока в кнопку тестирования
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
            parent_facade: Ссылка на родительский фасад (опционально)
        """
        self.state_manager = state_manager
        self.content_generator = content_generator
        self.system_logger = system_logger
        self.assessment = assessment
        self.parent_facade = parent_facade
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
            self.logger.info(f"🚀 НАЧАЛО: Отображение урока {lesson_id}")

            # ШАГ 1: Получение плана курса
            self.logger.info("📋 ШАГ 1: Получение плана курса...")
            course_plan = self.state_manager.get_course_plan()
            if not course_plan:
                self.logger.error("❌ План курса недоступен")
                return self._create_error_interface("Ошибка", "План курса недоступен")

            # ШАГ 2: Получение профиля пользователя
            self.logger.info("👤 ШАГ 2: Получение профиля пользователя...")
            user_profile = self.state_manager.get_user_profile()

            # ШАГ 3: Извлечение названий элементов
            self.logger.info("🏷️ ШАГ 3: Извлечение названий элементов...")
            (
                course_title,
                section_title,
                topic_title,
                lesson_title,
            ) = self.lesson_utils.get_element_titles_from_plan(
                course_plan, section_id, topic_id, lesson_id
            )

            self.logger.info(
                f"📝 Названия: {course_title} → {section_title} → {topic_title} → {lesson_title}"
            )

            # ШАГ 4: Формирование данных урока для генерации
            self.logger.info("📊 ШАГ 4: Формирование данных урока...")
            lesson_data = {
                "course": course_title,
                "section": section_title,
                "topic": topic_title,
                "lesson": lesson_title,
                "section_id": section_id,
                "topic_id": topic_id,
                "lesson_id": lesson_id,
            }

            # ШАГ 5: Генерация содержания урока
            self.logger.info("🎯 ШАГ 5: Генерация содержания урока...")
            lesson_content_data = self.content_manager.get_lesson_content(
                course_title,
                section_title,
                topic_title,
                lesson_title,
                lesson_data,
                user_profile,
            )

            if not lesson_content_data:
                self.logger.error("❌ Не удалось сгенерировать содержание урока")
                return self._create_error_interface(
                    "Ошибка генерации", "Не удалось сгенерировать содержание урока"
                )

            # ШАГ 6: Интеграция демо-ячеек (если нужно)
            self.logger.info("🔧 ШАГ 6: Интеграция демо-ячеек...")
            try:
                lesson_content_data = self.content_manager.integrate_demo_cells(
                    lesson_content_data, lesson_id
                )
                self.logger.info("✅ Демо-ячейки интегрированы")
            except Exception as e:
                self.logger.warning(
                    f"⚠️ Ошибка интеграции демо-ячеек (не критично): {str(e)}"
                )

            # ШАГ 7: Обновление прогресса урока
            self.logger.info("📈 ШАГ 7: Обновление прогресса урока...")
            try:
                self.content_manager.update_lesson_progress(
                    course_title, section_id, topic_id, lesson_id
                )
                self.logger.info("✅ Прогресс урока обновлен")
            except Exception as e:
                self.logger.warning(
                    f"⚠️ Ошибка обновления прогресса (не критично): {str(e)}"
                )

            # ШАГ 8: Сохранение данных урока
            self.logger.info("💾 ШАГ 8: Сохранение данных урока...")
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

            # ШАГ 9: Логирование урока
            self.logger.info("📄 ШАГ 9: Логирование урока...")
            try:
                self._log_lesson(
                    course_title, section_title, topic_title, lesson_content_data
                )
                self.logger.info("✅ Урок залогирован")
            except Exception as e:
                self.logger.warning(f"⚠️ Ошибка логирования (не критично): {str(e)}")

            # ШАГ 10: Создание интерфейса урока
            self.logger.info("🎨 ШАГ 10: Создание интерфейса урока...")
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

            self.logger.info("🎉 УРОК ГОТОВ ДЛЯ ОТОБРАЖЕНИЯ!")
            return lesson_interface

        except Exception as e:
            self.logger.error(f"💥 КРИТИЧЕСКАЯ ОШИБКА в show_lesson: {str(e)}")
            self.logger.error(f"📋 Traceback: {traceback.format_exc()}")
            return self._create_error_interface("Критическая ошибка", str(e))

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
        Сохраняет данные урока в объекте.

        ИСПРАВЛЕНО ЭТАП 49: Безопасная обработка lesson_content_data с проверкой на None
        """
        try:
            self.logger.info("💾 Начало сохранения данных урока...")

            # ИСПРАВЛЕНО: Проверяем lesson_content_data перед использованием
            if not lesson_content_data:
                self.logger.error("❌ lesson_content_data пуст или None")
                # Устанавливаем безопасные значения по умолчанию
                self.current_lesson_content = None
                self.current_lesson_data = None
            elif isinstance(lesson_content_data, dict):
                # Безопасно извлекаем содержание урока
                content = lesson_content_data.get("content")
                if content:
                    self.current_lesson_content = content
                    self.logger.info("✅ Содержание урока извлечено из 'content'")
                else:
                    # Пробуем альтернативные ключи
                    alt_content = (
                        lesson_content_data.get("lesson_content")
                        or lesson_content_data.get("text")
                        or lesson_content_data.get("html")
                        or str(lesson_content_data)
                    )
                    self.current_lesson_content = alt_content
                    self.logger.warning(
                        f"⚠️ Ключ 'content' не найден, используем альтернативу: {type(alt_content)}"
                    )

                self.current_lesson_data = lesson_content_data
            else:
                # lesson_content_data не словарь - используем как есть
                self.current_lesson_content = str(lesson_content_data)
                self.current_lesson_data = {"content": str(lesson_content_data)}
                self.logger.warning(
                    f"⚠️ lesson_content_data не dict, преобразуем: {type(lesson_content_data)}"
                )

            # Формируем ID урока
            self.current_lesson_id = f"{section_id}:{topic_id}:{lesson_id}"

            # Формируем информацию о курсе
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
                "facade": self.parent_facade,
            }

            # КРИТИЧЕСКИ ВАЖНО: Передаем данные в обработчики интерактивных действий
            self.logger.info("🔗 Передача данных в interactive_handlers...")

            # Проверяем что у нас есть для передачи
            if self.current_lesson_content is None:
                self.logger.error(
                    "❌ current_lesson_content = None! Данные урока не будут переданы!"
                )
            else:
                self.logger.info(
                    f"✅ current_lesson_content готов: {type(self.current_lesson_content)}"
                )

            if self.current_course_info is None:
                self.logger.error(
                    "❌ current_course_info = None! Информация о курсе не будет передана!"
                )
            else:
                self.logger.info(
                    f"✅ current_course_info готов: {len(self.current_course_info)} полей"
                )

            # Передаем данные в interactive_handlers
            self.interactive_handlers.set_lesson_data(
                self.current_lesson_content,
                self.current_course_info,
                self.current_lesson_id,
            )

            self.logger.info("✅ Данные урока успешно сохранены и переданы")

        except Exception as e:
            self.logger.error(f"💥 Ошибка при сохранении данных урока: {str(e)}")
            self.logger.error(f"📋 Traceback: {traceback.format_exc()}")
            # Устанавливаем безопасные значения по умолчанию
            self.current_lesson_content = None
            self.current_lesson_data = None
            self.current_course_info = None
            self.current_lesson_id = None

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

        ИСПРАВЛЕНО ЭТАП 52: Правильная передача данных урока в кнопку тестирования

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

            # Контрольные задания (если есть)
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

            # ИСПРАВЛЕНО ЭТАП 52: Кнопка тестирования с правильными данными урока
            self.logger.info("🎨 Создание кнопки тестирования...")

            # Создаем правильный объект lesson_data_for_button для кнопки тестирования
            lesson_data_for_button = {
                "id": lesson_id,
                "lesson_id": lesson_id,
                "section_id": section_id,
                "topic_id": topic_id,
                "course": course_title,
                "section": section_title,
                "topic": topic_title,
                "lesson": lesson_title,
                "lesson_title": lesson_title,
            }

            self.logger.info(
                f"📊 Данные для кнопки тестирования: {list(lesson_data_for_button.keys())}"
            )

            assessment_button = self.lesson_utils.create_assessment_button(
                self.assessment, lesson_data_for_button, self.current_course_info
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

    def get_current_lesson_data(self):
        """
        ИСПРАВЛЕНО ЭТАП 49: Возвращает данные текущего урока для interface_facade.

        Returns:
            dict: Данные текущего урока
        """
        try:
            if not self.current_lesson_content and not self.current_course_info:
                self.logger.warning("⚠️ Нет данных текущего урока для возврата")
                return None

            lesson_data = {
                "lesson_content": self.current_lesson_content,
                "course_info": self.current_course_info,
                "lesson_id": self.current_lesson_id,
                "lesson_data": self.current_lesson_data,
            }

            self.logger.info(f"📊 Возвращаем данные урока: {list(lesson_data.keys())}")
            return lesson_data

        except Exception as e:
            self.logger.error(f"Ошибка получения данных урока: {str(e)}")
            return None

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
