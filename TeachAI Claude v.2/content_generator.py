"""
Модуль для генерации учебного контента через OpenAI API.
Отвечает за создание уроков, вопросов и обработку ответов пользователя.

НОВАЯ АРХИТЕКТУРА: Этот модуль теперь служит фасадом для специализированных генераторов.
Обеспечивает полную обратную совместимость со старым интерфейсом.
ЗАВЕРШЕНО: Интеграция новых генераторов для логической модернизации.
ИСПРАВЛЕНО: Передача course_context в generate_examples (проблема #91)
ИСПРАВЛЕНО ЭТАП 30: Универсальный API для generate_course_plan (проблема #126)

РЕФАКТОРИНГ ЭТАП 27: Разделен на компоненты для соблюдения лимитов размера модулей.
"""

import logging
from content_generator_facade import ContentGeneratorFacade
from content_generator_compatibility import ContentGeneratorCompatibility


class ContentGenerator:
    """
    Основной класс для генерации учебного контента с использованием OpenAI API.

    ВАЖНО: Обеспечивает полную обратную совместимость с предыдущей версией.
    Все методы работают точно так же, как раньше!
    ЗАВЕРШЕНО: Добавлены новые методы для логической модернизации.
    ИСПРАВЛЕНО ЭТАП 30: Универсальный API для совместимости разных вызовов.
    """

    def __init__(self, api_key):
        """
        Инициализация генератора контента.

        Args:
            api_key (str): API ключ OpenAI
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key

        try:
            # Инициализируем основной фасад
            self.facade = ContentGeneratorFacade(api_key)

            # Инициализируем модуль обратной совместимости
            self.compatibility = ContentGeneratorCompatibility(self.facade)

            self.logger.info("ContentGenerator (объединенный) успешно инициализирован")

        except Exception as e:
            self.logger.error(f"Ошибка при инициализации ContentGenerator: {str(e)}")
            raise

        # Прямой доступ к атрибутам для совместимости
        self.communication_styles = self.compatibility.communication_styles

    # ========================================
    # ДЕЛЕГИРОВАНИЕ К FACADE (новые методы)
    # ========================================

    def generate_course_plan(
        self,
        course_name=None,
        course_description=None,
        user_data=None,
        course_data=None,
        total_study_hours=None,
        lesson_duration_minutes=None,
        **kwargs,
    ):
        """
        Универсальный метод генерации плана курса.
        Поддерживает два API:
        1. Персонализация: generate_course_plan(course_name, course_description, user_data)
        2. Временное планирование: generate_course_plan(course_data=..., total_study_hours=..., lesson_duration_minutes=...)

        Args:
            course_name (str, optional): Название курса
            course_description (str, optional): Описание курса
            user_data (dict, optional): Данные пользователя
            course_data (dict, optional): Данные о курсе (id, title, description)
            total_study_hours (int, optional): Общее время обучения в часах
            lesson_duration_minutes (int, optional): Длительность одного занятия в минутах
            **kwargs: Дополнительные параметры для обратной совместимости

        Returns:
            dict: План курса
        """
        try:
            # Извлекаем параметры из kwargs для полной совместимости
            if "course_data" in kwargs:
                course_data = kwargs["course_data"]
            if "total_study_hours" in kwargs:
                total_study_hours = kwargs["total_study_hours"]
            if "lesson_duration_minutes" in kwargs:
                lesson_duration_minutes = kwargs["lesson_duration_minutes"]

            # Делегируем универсальный вызов в фасад
            return self.facade.generate_course_plan(
                course_name=course_name,
                course_description=course_description,
                user_data=user_data,
                course_data=course_data,
                total_study_hours=total_study_hours,
                lesson_duration_minutes=lesson_duration_minutes,
            )
        except Exception as e:
            self.logger.error(f"Ошибка генерации плана курса: {str(e)}")
            raise

    def generate_lesson_content(self, lesson_data, user_data, course_context=None):
        """Генерирует содержание урока."""
        return self.facade.generate_lesson_content(
            lesson_data, user_data, course_context
        )

    def generate_examples(
        self,
        lesson_data,
        lesson_content,
        communication_style="friendly",
        course_context=None,
    ):
        """Генерирует практические примеры для урока."""
        return self.facade.generate_examples(
            lesson_data, lesson_content, communication_style, course_context
        )

    def get_detailed_explanation(
        self, lesson_data, lesson_content, communication_style="friendly"
    ):
        """Генерирует подробное объяснение материала урока."""
        return self.facade.get_detailed_explanation(
            lesson_data, lesson_content, communication_style
        )

    def answer_question(
        self, question, lesson_data, lesson_content, communication_style="friendly"
    ):
        """Отвечает на вопрос пользователя по материалу урока."""
        return self.facade.answer_question(
            question, lesson_data, lesson_content, communication_style
        )

    def generate_assessment(self, lesson_data, lesson_content, questions_count=5):
        """Генерирует тест для оценки знаний."""
        return self.facade.generate_assessment(
            lesson_data, lesson_content, questions_count
        )

    def extract_key_concepts(self, lesson_content, lesson_data):
        """Извлекает ключевые понятия из урока."""
        return self.facade.extract_key_concepts(lesson_content, lesson_data)

    def check_content_relevance(self, content, course_context):
        """Проверяет релевантность контента курсу."""
        return self.facade.check_content_relevance(content, course_context)

    # ========================================
    # ДЕЛЕГИРОВАНИЕ К COMPATIBILITY (старые методы)
    # ========================================

    def create_course_plan(self, course_name, course_description, user_data):
        """УСТАРЕЛО: Используйте generate_course_plan()."""
        return self.compatibility.create_course_plan(
            course_name, course_description, user_data
        )

    def create_lesson_content(self, lesson_data, user_data, course_context=None):
        """УСТАРЕЛО: Используйте generate_lesson_content()."""
        return self.compatibility.create_lesson_content(
            lesson_data, user_data, course_context
        )

    def create_examples(
        self,
        lesson_data,
        lesson_content,
        communication_style="friendly",
        course_context=None,
    ):
        """УСТАРЕЛО: Используйте generate_examples()."""
        return self.compatibility.create_examples(
            lesson_data, lesson_content, communication_style, course_context
        )

    def create_detailed_explanation(
        self, lesson_data, lesson_content, communication_style="friendly"
    ):
        """УСТАРЕЛО: Используйте get_detailed_explanation()."""
        return self.compatibility.create_detailed_explanation(
            lesson_data, lesson_content, communication_style
        )

    def create_question_answer(
        self, question, lesson_data, lesson_content, communication_style="friendly"
    ):
        """УСТАРЕЛО: Используйте answer_question()."""
        return self.compatibility.create_question_answer(
            question, lesson_data, lesson_content, communication_style
        )

    def create_assessment(self, lesson_data, lesson_content, questions_count=5):
        """УСТАРЕЛО: Используйте generate_assessment()."""
        return self.compatibility.create_assessment(
            lesson_data, lesson_content, questions_count
        )

    # ========================================
    # ДОПОЛНИТЕЛЬНЫЕ УДОБНЫЕ МЕТОДЫ
    # ========================================

    def get_generator_info(self):
        """Возвращает информацию о всех доступных генераторах."""
        return self.facade.get_generator_info()

    def validate_lesson_data(self, lesson_data):
        """Валидирует данные урока."""
        return self.facade.validate_lesson_data(lesson_data)

    def get_api_status(self):
        """Проверяет статус API подключения."""
        return self.facade.get_api_status()

    def get_communication_style_description(self, style):
        """Возвращает описание стиля общения."""
        return self.compatibility.get_communication_style_description(style)

    def validate_communication_style(self, style):
        """Проверяет валидность стиля общения."""
        return self.compatibility.validate_communication_style(style)

    def migrate_old_course_data(self, old_data):
        """Мигрирует данные курса из старого формата."""
        return self.compatibility.migrate_old_course_data(old_data)

    def get_migration_status(self, data):
        """Проверяет статус миграции данных."""
        return self.compatibility.get_migration_status(data)

    def get_compatibility_info(self):
        """Возвращает информацию о совместимости."""
        return self.compatibility.get_compatibility_info()

    # ========================================
    # МЕТОДЫ ДЛЯ ОТЛАДКИ И МОНИТОРИНГА
    # ========================================

    def get_system_status(self):
        """
        Возвращает полный статус системы генерации контента.

        Returns:
            dict: Статус всех компонентов системы
        """
        try:
            return {
                "facade_status": self.facade.get_api_status(),
                "generator_info": self.facade.get_generator_info(),
                "compatibility_info": self.compatibility.get_compatibility_info(),
                "api_key_set": bool(self.api_key),
                "initialization_successful": True,
            }
        except Exception as e:
            return {"error": str(e), "initialization_successful": False}

    def test_api_connection(self):
        """
        Тестирует подключение к API.

        Returns:
            dict: Результат тестирования
        """
        try:
            # Простой тест через генерацию короткого плана
            test_result = self.generate_course_plan(
                course_name="Тест",
                course_description="Тестовый курс для проверки API",
                user_data={"name": "Test", "level": "beginner"},
            )

            return {
                "api_connection": "success",
                "test_completed": True,
                "response_received": bool(test_result),
            }
        except Exception as e:
            return {
                "api_connection": "failed",
                "test_completed": False,
                "error": str(e),
            }
