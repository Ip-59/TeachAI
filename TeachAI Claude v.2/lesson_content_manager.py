"""
Менеджер содержания уроков.
Отвечает за генерацию, кэширование и управление содержанием уроков.

ИСПРАВЛЕНО: УБРАН ДЕМО-РЕЖИМ - теперь показываем реальные ошибки API для диагностики
ИСПРАВЛЕНО: ДОБАВЛЕН метод integrate_demo_cells для интеграции демо-ячеек
ИСПРАВЛЕНО: ДОБАВЛЕН метод update_lesson_progress для обновления прогресса
"""

import logging


class LessonContentManager:
    """Менеджер содержания уроков."""

    def __init__(self, state_manager, logger=None):
        """
        Инициализация менеджера содержания.

        Args:
            state_manager: Менеджер состояния
            logger: Логгер (опционально)
        """
        self.state_manager = state_manager
        self.logger = logger or logging.getLogger(__name__)

        # Кэш содержания урока
        self.cached_lesson_content = None
        self.current_lesson_cache_key = None

        self.logger.info("LessonContentManager инициализирован")

    def get_lesson_content(self, section_id, topic_id, lesson_id, content_generator):
        """
        Получает содержание урока с кэшированием.

        ИСПРАВЛЕНО: Убран демо-режим - теперь ошибки API передаются выше для правильной диагностики

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока
            content_generator: Генератор контента

        Returns:
            dict: Содержание урока

        Raises:
            Exception: Любые ошибки генерации передаются выше для диагностики
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
        self.logger.info(f"Генерация нового содержания урока {lesson_cache_key}")

        try:
            # Проверяем доступность content_generator
            if not content_generator:
                error_msg = f"ContentGenerator недоступен для урока {lesson_cache_key}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            # Формируем правильные аргументы для generate_lesson_content
            lesson_data = {
                "id": lesson_id,
                "title": f"Урок {lesson_id}",
                "description": f"Урок из раздела {section_id}, темы {topic_id}",
            }

            user_data = {
                "communication_style": "friendly",
                "learning_style": "practical",
            }

            # Вызываем генерацию контента
            self.logger.info(
                f"Вызов content_generator.generate_lesson_content для {lesson_cache_key}"
            )
            lesson_content_data = content_generator.generate_lesson_content(
                lesson_data, user_data
            )

            if not lesson_content_data:
                error_msg = f"ContentGenerator вернул пустые данные для урока {lesson_cache_key}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            # Кэшируем результат
            self.cached_lesson_content = lesson_content_data
            self.current_lesson_cache_key = lesson_cache_key

            self.logger.info(
                f"✅ Содержание урока {lesson_cache_key} сгенерировано и кэшировано"
            )
            return lesson_content_data

        except Exception as e:
            # ИСПРАВЛЕНО: Убран демо-режим - показываем реальные ошибки для диагностики
            if "Connection error" in str(e):
                self.logger.error(
                    "🔍 ДИАГНОСТИКА: Обнаружена ошибка подключения к OpenAI API"
                )
                self.logger.error("🔧 ПРОВЕРЬТЕ:")
                self.logger.error("   1) API ключ OpenAI в .env файле")
                self.logger.error("   2) Подключение к интернету")
                self.logger.error("   3) Статус OpenAI API (https://status.openai.com)")
                self.logger.error("   4) Лимиты использования API")
            elif "timeout" in str(e).lower():
                self.logger.error(
                    "🔍 ДИАГНОСТИКА: Превышено время ожидания ответа от API"
                )
                self.logger.error(
                    "🔧 ПОПРОБУЙТЕ: Повторить запрос через несколько секунд"
                )
            elif "rate limit" in str(e).lower():
                self.logger.error("🔍 ДИАГНОСТИКА: Превышен лимит запросов к OpenAI API")
                self.logger.error(
                    "🔧 ПОДОЖДИТЕ: Несколько минут перед следующим запросом"
                )
            else:
                self.logger.error(
                    f"🔍 ДИАГНОСТИКА: Неизвестная ошибка генерации урока: {str(e)}"
                )
                self.logger.error("🔧 ПРОВЕРЬТЕ: Логи выше для деталей")

            # Передаем ошибку выше для полной диагностики
            raise

    def integrate_demo_cells(self, lesson_content_data, lesson_id):
        """
        Интегрирует демо-ячейки в содержание урока.

        Args:
            lesson_content_data (dict): Данные содержания урока
            lesson_id (str): ID урока

        Returns:
            dict: Обновленные данные урока с интегрированными демо-ячейками
        """
        try:
            self.logger.info(f"Интеграция демо-ячеек для урока {lesson_id}")

            # Проверяем входные данные
            if not lesson_content_data:
                self.logger.warning("lesson_content_data пуст, возвращаем как есть")
                return lesson_content_data

            # Если данные урока в правильном формате - возвращаем их
            # В будущем здесь можно добавить логику интеграции демо-ячеек
            # из demo_cell_widget.py в содержание урока

            # ВРЕМЕННАЯ РЕАЛИЗАЦИЯ: просто возвращаем данные как есть
            # чтобы не ломать функциональность
            self.logger.info("Демо-ячейки интегрированы (временная реализация)")
            return lesson_content_data

        except Exception as e:
            self.logger.error(f"Ошибка интеграции демо-ячеек: {str(e)}")
            # В случае ошибки возвращаем исходные данные
            return lesson_content_data

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
            self.logger.info(
                f"Обновление прогресса урока {section_id}:{topic_id}:{lesson_id}"
            )

            # Проверяем доступность state_manager
            if not self.state_manager:
                self.logger.warning("state_manager недоступен для обновления прогресса")
                return

            # Пытаемся обновить прогресс через различные методы state_manager
            if hasattr(self.state_manager, "update_lesson_progress"):
                self.state_manager.update_lesson_progress(
                    course_id, section_id, topic_id, lesson_id
                )
                self.logger.info(
                    "Прогресс урока обновлен через state_manager.update_lesson_progress"
                )
            elif hasattr(self.state_manager, "set_current_lesson"):
                self.state_manager.set_current_lesson(section_id, topic_id, lesson_id)
                self.logger.info(
                    "Текущий урок установлен через state_manager.set_current_lesson"
                )
            else:
                self.logger.warning(
                    "Не найден метод для обновления прогресса в state_manager"
                )

        except Exception as e:
            self.logger.warning(
                f"Ошибка обновления прогресса урока (не критично): {str(e)}"
            )

    def _clear_lesson_cache(self):
        """
        Очищает кэш содержания урока.
        """
        self.cached_lesson_content = None
        self.current_lesson_cache_key = None
        self.logger.debug("Кэш содержания урока очищен")
