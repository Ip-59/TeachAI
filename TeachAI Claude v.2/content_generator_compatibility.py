"""
Модуль обратной совместимости для ContentGenerator.
Обеспечивает полную совместимость со старым API.
"""

import logging
from datetime import datetime


class ContentGeneratorCompatibility:
    """
    Класс обеспечивающий обратную совместимость со старым API ContentGenerator.
    """

    def __init__(self, facade):
        """
        Инициализация модуля совместимости.

        Args:
            facade: Экземпляр ContentGeneratorFacade
        """
        self.facade = facade
        self.logger = logging.getLogger(__name__)

        # Сохраняем старые атрибуты для совместимости
        self.communication_styles = {
            "formal": "Формальный, академический стиль общения с использованием научной терминологии.",
            "friendly": "Дружелюбный стиль общения, использующий простые объяснения и аналогии.",
            "casual": "Непринужденный, разговорный стиль с элементами юмора.",
            "brief": "Краткий и четкий стиль, фокусирующийся только на ключевой информации.",
        }

        # API ключ для совместимости
        self.api_key = facade.api_key

        self.logger.info("ContentGeneratorCompatibility инициализирован")

    # ========================================
    # СТАРЫЕ МЕТОДЫ - ПОЛНАЯ СОВМЕСТИМОСТЬ
    # ========================================

    def create_course_plan(self, course_name, course_description, user_data):
        """
        УСТАРЕЛО: Используйте generate_course_plan().
        Обеспечивает совместимость со старым API.
        """
        self.logger.warning(
            "Используется устаревший метод create_course_plan, рекомендуется generate_course_plan"
        )
        return self.facade.generate_course_plan(
            course_name, course_description, user_data
        )

    def create_lesson_content(self, lesson_data, user_data, course_context=None):
        """
        УСТАРЕЛО: Используйте generate_lesson_content().
        Обеспечивает совместимость со старым API.
        """
        self.logger.warning(
            "Используется устаревший метод create_lesson_content, рекомендуется generate_lesson_content"
        )
        return self.facade.generate_lesson_content(
            lesson_data, user_data, course_context
        )

    def create_examples(
        self,
        lesson_data,
        lesson_content,
        communication_style="friendly",
        course_context=None,
    ):
        """
        УСТАРЕЛО: Используйте generate_examples().
        Обеспечивает совместимость со старым API.
        """
        self.logger.warning(
            "Используется устаревший метод create_examples, рекомендуется generate_examples"
        )
        return self.facade.generate_examples(
            lesson_data, lesson_content, communication_style, course_context
        )

    def create_detailed_explanation(
        self, lesson_data, lesson_content, communication_style="friendly"
    ):
        """
        УСТАРЕЛО: Используйте get_detailed_explanation().
        Обеспечивает совместимость со старым API.
        """
        self.logger.warning(
            "Используется устаревший метод create_detailed_explanation, рекомендуется get_detailed_explanation"
        )
        return self.facade.get_detailed_explanation(
            lesson_data, lesson_content, communication_style
        )

    def create_question_answer(
        self, question, lesson_data, lesson_content, communication_style="friendly"
    ):
        """
        УСТАРЕЛО: Используйте answer_question().
        Обеспечивает совместимость со старым API.
        """
        self.logger.warning(
            "Используется устаревший метод create_question_answer, рекомендуется answer_question"
        )
        return self.facade.answer_question(
            question, lesson_data, lesson_content, communication_style
        )

    def create_assessment(self, lesson_data, lesson_content, questions_count=5):
        """
        УСТАРЕЛО: Используйте generate_assessment().
        Обеспечивает совместимость со старым API.
        """
        self.logger.warning(
            "Используется устаревший метод create_assessment, рекомендуется generate_assessment"
        )
        return self.facade.generate_assessment(
            lesson_data, lesson_content, questions_count
        )

    # ========================================
    # МЕТОДЫ ОБРАБОТКИ УСТАРЕВШИХ ПАРАМЕТРОВ
    # ========================================

    def get_communication_style_description(self, style):
        """
        Возвращает описание стиля общения.
        Для обратной совместимости.

        Args:
            style (str): Стиль общения

        Returns:
            str: Описание стиля
        """
        return self.communication_styles.get(
            style, self.communication_styles["friendly"]
        )

    def validate_communication_style(self, style):
        """
        Проверяет валидность стиля общения.

        Args:
            style (str): Стиль общения

        Returns:
            bool: True если стиль валиден
        """
        return style in self.communication_styles

    def normalize_lesson_data(self, lesson_data):
        """
        Нормализует данные урока для обратной совместимости.

        Args:
            lesson_data (dict or str): Данные урока (может быть строкой в старом API)

        Returns:
            dict: Нормализованные данные урока
        """
        if isinstance(lesson_data, str):
            # Старый API передавал строку как название урока
            return {
                "title": lesson_data,
                "description": f"Урок: {lesson_data}",
                "keywords": [],
            }
        elif isinstance(lesson_data, dict):
            # Дополняем недостающие поля
            normalized = lesson_data.copy()
            if "title" not in normalized:
                normalized["title"] = "Урок"
            if "description" not in normalized:
                normalized["description"] = normalized["title"]
            if "keywords" not in normalized:
                normalized["keywords"] = []
            return normalized
        else:
            # Создаем минимальные данные
            return {"title": "Урок", "description": "Урок", "keywords": []}

    def normalize_user_data(self, user_data):
        """
        Нормализует данные пользователя для обратной совместимости.

        Args:
            user_data (dict): Данные пользователя

        Returns:
            dict: Нормализованные данные пользователя
        """
        if not isinstance(user_data, dict):
            return {}

        normalized = user_data.copy()

        # Добавляем значения по умолчанию для обязательных полей
        if "learning_style" not in normalized:
            normalized["learning_style"] = "friendly"
        if "session_duration" not in normalized:
            normalized["session_duration"] = "30 минут"
        if "name" not in normalized:
            normalized["name"] = "Студент"

        return normalized

    # ========================================
    # МЕТОДЫ МИГРАЦИИ
    # ========================================

    def migrate_old_course_data(self, old_data):
        """
        Мигрирует данные курса из старого формата.

        Args:
            old_data (dict): Данные в старом формате

        Returns:
            dict: Данные в новом формате
        """
        try:
            # Проверяем, нужна ли миграция
            if "version" in old_data and old_data["version"] >= "2.0":
                return old_data

            # Выполняем миграцию
            migrated = {
                "version": "2.0",
                "migrated_at": datetime.now().isoformat(),
                "title": old_data.get("name", old_data.get("title", "Курс")),
                "description": old_data.get("description", "Описание курса"),
                "sections": [],
            }

            # Мигрируем секции и уроки
            if "lessons" in old_data:
                # Старый формат: плоский список уроков
                section = {
                    "title": "Основной раздел",
                    "topics": [
                        {"title": "Основная тема", "lessons": old_data["lessons"]}
                    ],
                }
                migrated["sections"].append(section)
            elif "sections" in old_data:
                # Новый формат уже есть
                migrated["sections"] = old_data["sections"]

            self.logger.info("Выполнена миграция данных курса")
            return migrated

        except Exception as e:
            self.logger.error(f"Ошибка миграции данных курса: {str(e)}")
            # Возвращаем безопасный минимум
            return {
                "version": "2.0",
                "title": "Курс",
                "description": "Описание курса",
                "sections": [],
            }

    def get_migration_status(self, data):
        """
        Проверяет статус миграции данных.

        Args:
            data (dict): Данные для проверки

        Returns:
            dict: Статус миграции
        """
        try:
            version = data.get("version", "1.0")
            needs_migration = version < "2.0"

            return {
                "current_version": version,
                "target_version": "2.0",
                "needs_migration": needs_migration,
                "migration_available": True,
                "checked_at": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "error": str(e),
                "needs_migration": True,
                "migration_available": True,
            }

    # ========================================
    # СЛУЖЕБНЫЕ МЕТОДЫ
    # ========================================

    def log_deprecated_usage(self, method_name, recommended_method):
        """
        Логирует использование устаревших методов.

        Args:
            method_name (str): Название устаревшего метода
            recommended_method (str): Рекомендуемый метод
        """
        self.logger.warning(
            f"DEPRECATED: Метод '{method_name}' устарел. "
            f"Рекомендуется использовать '{recommended_method}'"
        )

    def get_compatibility_info(self):
        """
        Возвращает информацию о совместимости.

        Returns:
            dict: Информация о совместимости
        """
        return {
            "compatibility_version": "2.0",
            "supported_versions": ["1.0", "1.1", "1.2", "2.0"],
            "deprecated_methods": [
                "create_course_plan",
                "create_lesson_content",
                "create_examples",
                "create_detailed_explanation",
                "create_question_answer",
                "create_assessment",
            ],
            "migration_available": True,
            "backward_compatible": True,
        }
