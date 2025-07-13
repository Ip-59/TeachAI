"""
Менеджер содержания уроков.
Отвечает за генерацию, кэширование и управление содержанием уроков.

ИСПРАВЛЕНО: УБРАН ДЕМО-РЕЖИМ - теперь показываем реальные ошибки API для диагностики
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
            lesson_data = self._build_lesson_data(section_id, topic_id, lesson_id)
            user_data = self._get_user_data()
            course_context = self._get_course_context()

            self.logger.info(
                f"Вызов content_generator.generate_lesson_content для {lesson_cache_key}"
            )
            self.logger.debug(f"lesson_data: {lesson_data}")
            self.logger.debug(f"user_data: {user_data}")
            self.logger.debug(f"course_context: {course_context}")

            lesson_content_data = content_generator.generate_lesson_content(
                lesson_data=lesson_data,
                user_data=user_data,
                course_context=course_context,
            )

            if not lesson_content_data:
                error_msg = f"content_generator.generate_lesson_content вернул пустой результат для {lesson_cache_key}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            # Кэшируем результат
            self.cached_lesson_content = lesson_content_data
            self.current_lesson_cache_key = lesson_cache_key

            self.logger.info(
                f"Содержание урока {lesson_cache_key} успешно сгенерировано и закэшировано"
            )
            return lesson_content_data

        except Exception as e:
            # ИСПРАВЛЕНО: Убираем демо-режим - передаем ошибку выше для диагностики
            error_msg = (
                f"Ошибка генерации содержания урока {lesson_cache_key}: {str(e)}"
            )
            self.logger.error(error_msg)
            self.logger.error(f"Тип ошибки: {type(e).__name__}")

            # Логируем детали для диагностики
            if "Connection error" in str(e) or "connection" in str(e).lower():
                self.logger.error(
                    "ДИАГНОСТИКА: Обнаружена ошибка подключения к OpenAI API"
                )
                self.logger.error(
                    "ПРОВЕРЬТЕ: 1) API ключ в .env файле, 2) Интернет соединение, 3) Статус OpenAI API"
                )
            elif "timeout" in str(e).lower():
                self.logger.error("ДИАГНОСТИКА: Превышено время ожидания ответа от API")
            elif "rate limit" in str(e).lower():
                self.logger.error("ДИАГНОСТИКА: Превышен лимит запросов к API")
            elif "api key" in str(e).lower():
                self.logger.error("ДИАГНОСТИКА: Проблема с API ключом")
            else:
                self.logger.error(f"ДИАГНОСТИКА: Неизвестная ошибка API: {str(e)}")

            # Передаем ошибку выше вместо скрытия демо-режимом
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
            # Получаем данные урока из state_manager
            if hasattr(self.state_manager, "get_lesson_data"):
                lesson_data = self.state_manager.get_lesson_data(lesson_id)
                if lesson_data:
                    self.logger.debug(
                        f"Получены данные урока из state_manager: {lesson_data}"
                    )
                    return lesson_data

            # Fallback: создаем базовые данные
            fallback_data = {
                "id": lesson_id,
                "title": f"Урок {lesson_id}",
                "section_id": section_id,
                "topic_id": topic_id,
                "description": f"Урок в разделе {section_id}, тема {topic_id}",
            }
            self.logger.warning(f"Используем fallback данные урока: {fallback_data}")
            return fallback_data

        except Exception as e:
            self.logger.error(f"Ошибка получения данных урока: {str(e)}")
            # Возвращаем минимальные данные вместо падения
            return {
                "id": lesson_id,
                "title": f"Урок {lesson_id}",
                "section_id": section_id,
                "topic_id": topic_id,
            }

    def _get_user_data(self):
        """
        Получает данные пользователя.

        Returns:
            dict: Данные пользователя
        """
        try:
            if hasattr(self.state_manager, "get_user_profile"):
                user_data = self.state_manager.get_user_profile()
                self.logger.debug(f"Получены данные пользователя: {user_data}")
                return user_data or {}
            self.logger.warning("Метод get_user_profile недоступен в state_manager")
            return {}
        except Exception as e:
            self.logger.error(f"Ошибка получения данных пользователя: {str(e)}")
            return {}

    def _get_course_context(self):
        """
        Получает контекст курса.

        Returns:
            dict: Контекст курса
        """
        try:
            if hasattr(self.state_manager, "get_course_plan"):
                course_plan = self.state_manager.get_course_plan()
                context = {
                    "course_name": course_plan.get("course_name", "Курс Python")
                    if course_plan
                    else "Курс Python",
                    "course_plan": course_plan,
                }
                self.logger.debug(f"Получен контекст курса: {context}")
                return context
            self.logger.warning("Метод get_course_plan недоступен в state_manager")
            return {"course_name": "Курс Python"}
        except Exception as e:
            self.logger.error(f"Ошибка получения контекста курса: {str(e)}")
            return {"course_name": "Курс Python"}

    def get_control_tasks_interface(self, lesson_id, course_info):
        """
        Получает интерфейс контрольных заданий.

        Args:
            lesson_id (str): ID урока
            course_info (dict): Информация о курсе

        Returns:
            widgets.Widget or None: Интерфейс контрольных заданий или None
        """
        try:
            # Пока возвращаем None, так как контрольные задания не реализованы
            self.logger.debug(
                f"Контрольные задания для урока {lesson_id} не реализованы"
            )
            return None

        except Exception as e:
            self.logger.warning(
                f"Ошибка создания контрольных заданий для урока {lesson_id}: {str(e)}"
            )
            return None

    def clear_cache(self):
        """Очищает кэш содержания урока."""
        self.cached_lesson_content = None
        self.current_lesson_cache_key = None
        self.logger.info("Кэш содержания урока очищен")

    def get_cache_info(self):
        """
        Возвращает информацию о кэше.

        Returns:
            dict: Информация о кэше
        """
        return {
            "cache_active": self.cached_lesson_content is not None,
            "cached_lesson": self.current_lesson_cache_key,
            "cache_size": len(str(self.cached_lesson_content))
            if self.cached_lesson_content
            else 0,
        }
