"""
Координатор для генерации практических примеров по материалам уроков.
Координирует работу модулей генерации и валидации примеров.
ИСПРАВЛЕНО: Разделение на специализированные модули для улучшения архитектуры
"""

from examples_generation import ExamplesGeneration
from examples_validation import ExamplesValidation


class ExamplesGenerator:
    """Координатор генерации практических примеров для уроков."""

    def __init__(self, api_key):
        """
        Инициализация координатора примеров.

        Args:
            api_key (str): API ключ OpenAI
        """
        self.generation = ExamplesGeneration(api_key)
        self.validation = ExamplesValidation(api_key)
        self.logger = self.generation.logger
        self.logger.info("ExamplesGenerator (координатор) инициализирован")

    def generate_examples(
        self,
        lesson_data,
        lesson_content,
        communication_style="friendly",
        course_context=None,
    ):
        """
        Генерирует практические примеры с валидацией релевантности.

        Args:
            lesson_data (dict): Данные об уроке (название, описание, ключевые слова)
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения
            course_context (dict, optional): Контекст курса для обеспечения релевантности

        Returns:
            str: Строка с практическими примерами

        Raises:
            Exception: Если не удалось сгенерировать примеры
        """
        try:
            # Генерируем примеры
            examples = self.generation.generate_examples(
                lesson_data=lesson_data,
                lesson_content=lesson_content,
                communication_style=communication_style,
                course_context=course_context,
            )

            # Определяем предметную область для валидации
            course_subject = self.generation._determine_course_subject(
                course_context, lesson_content, lesson_data.get("keywords", [])
            )

            # Извлекаем данные для валидации
            lesson_title = lesson_data.get("title", "Урок")
            lesson_description = lesson_data.get("description", "Нет описания")
            lesson_keywords = lesson_data.get("keywords", [])
            keywords_str = (
                ", ".join(lesson_keywords)
                if isinstance(lesson_keywords, list)
                else str(lesson_keywords)
            )

            # Валидируем и при необходимости перегенерируем
            validated_examples = self.validation.validate_and_regenerate_if_needed(
                examples=examples,
                course_subject=course_subject,
                lesson_title=lesson_title,
                lesson_description=lesson_description,
                keywords_str=keywords_str,
                lesson_content=lesson_content,
                communication_style=communication_style,
            )

            # Применяем стили к валидированным примерам
            styled_examples = self.generation._apply_visible_styles(
                validated_examples, communication_style
            )

            self.logger.info(
                f"Примеры по теме '{course_subject}' успешно сгенерированы и валидированы"
            )
            return styled_examples

        except Exception as e:
            self.logger.error(f"Критическая ошибка при генерации примеров: {str(e)}")
            raise Exception(f"Не удалось сгенерировать примеры: {str(e)}")

    # Делегируем методы для обратной совместимости
    def _determine_course_subject(
        self, course_context, lesson_content, lesson_keywords
    ):
        """Делегирует определение предметной области."""
        return self.generation._determine_course_subject(
            course_context, lesson_content, lesson_keywords
        )

    def _validate_examples_relevance(self, examples, course_subject):
        """Делегирует валидацию релевантности."""
        return self.validation.validate_examples_relevance(examples, course_subject)

    def _regenerate_with_strict_prompt(
        self,
        lesson_title,
        lesson_description,
        keywords_str,
        lesson_content,
        communication_style,
        course_subject,
    ):
        """Делегирует повторную генерацию."""
        return self.validation.regenerate_with_strict_prompt(
            lesson_title,
            lesson_description,
            keywords_str,
            lesson_content,
            communication_style,
            course_subject,
        )

    def _create_fallback_python_example(self, lesson_title):
        """Делегирует создание fallback примера."""
        return self.validation._create_fallback_python_example(lesson_title)

    def _apply_visible_styles(self, examples, communication_style):
        """Делегирует применение стилей."""
        return self.generation._apply_visible_styles(examples, communication_style)

    def _build_enhanced_examples_prompt(
        self,
        lesson_title,
        lesson_description,
        keywords_str,
        lesson_content,
        communication_style,
        course_subject,
    ):
        """Делегирует создание промпта."""
        return self.generation._build_enhanced_examples_prompt(
            lesson_title,
            lesson_description,
            keywords_str,
            lesson_content,
            communication_style,
            course_subject,
        )
