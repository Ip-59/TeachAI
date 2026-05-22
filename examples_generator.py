"""
Координатор для генерации практических примеров по материалам уроков.

Основной формат данных внутри проекта — list[dict] с полями
{"title", "description", "code"}. HTML — только финальный артефакт
для обратной совместимости (legacy-консьюмеры через UI на HTML).
"""

from typing import Any, Dict, List, Optional

from examples_generation import ExamplesGeneration
from examples_html_utils import render_examples_json_to_html
from examples_validation import ExamplesValidation


class ExamplesGenerator:
    """Координатор генерации практических примеров для уроков."""

    def __init__(self, api_key: str) -> None:
        self.generation = ExamplesGeneration(api_key)
        self.validation = ExamplesValidation(api_key)
        self.logger = self.generation.logger
        self.logger.info("ExamplesGenerator (координатор) инициализирован")

    def generate_examples_data(
        self,
        lesson_data: Dict[str, Any],
        lesson_content: str,
        communication_style: str = "friendly",
        course_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, str]]:
        """Возвращает валидированный список примеров (без HTML).

        Это основной (чистый) путь. UI и виджеты Jupyter получают
        структурированные данные напрямую, без обратного парсинга HTML.
        """
        try:
            raw = self.generation.generate_examples_data(
                lesson_data=lesson_data,
                lesson_content=lesson_content,
                communication_style=communication_style,
                course_context=course_context,
            )

            course_subject = self.generation._determine_course_subject(
                course_context, lesson_content, lesson_data.get("keywords", [])
            )

            lesson_title = lesson_data.get("title", "Урок")
            lesson_description = lesson_data.get("description", "Нет описания")
            lesson_keywords = lesson_data.get("keywords", [])
            keywords_str = (
                ", ".join(lesson_keywords)
                if isinstance(lesson_keywords, list)
                else str(lesson_keywords)
            )

            validated = self.validation.validate_and_regenerate_if_needed(
                examples=raw,
                course_subject=course_subject,
                lesson_title=lesson_title,
                lesson_description=lesson_description,
                keywords_str=keywords_str,
                lesson_content=lesson_content,
                communication_style=communication_style,
            )

            self.logger.info(
                f"Примеры по теме '{course_subject}' сгенерированы и валидированы "
                f"({len(validated)} шт.)"
            )
            return validated

        except Exception as e:
            self.logger.error(f"Критическая ошибка при генерации примеров: {str(e)}")
            raise Exception(f"Не удалось сгенерировать примеры: {str(e)}")

    def generate_examples(
        self,
        lesson_data: Dict[str, Any],
        lesson_content: str,
        communication_style: str = "friendly",
        course_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Возвращает примеры в виде HTML — обратная совместимость.

        Получает list[dict] через generate_examples_data, затем рендерит
        финальный HTML и навешивает стили. Никакого обратного парсинга HTML.
        """
        examples_data = self.generate_examples_data(
            lesson_data=lesson_data,
            lesson_content=lesson_content,
            communication_style=communication_style,
            course_context=course_context,
        )
        body = render_examples_json_to_html({"examples": examples_data})
        return self.generation._apply_visible_styles(body, communication_style)

    def _determine_course_subject(
        self,
        course_context: Optional[Dict[str, Any]],
        lesson_content: str,
        lesson_keywords: Any,
    ) -> str:
        """Делегирует определение предметной области."""
        return self.generation._determine_course_subject(
            course_context, lesson_content, lesson_keywords
        )

    def _create_fallback_python_example(
        self, lesson_title: str, lesson_content: str = ""
    ) -> List[Dict[str, str]]:
        """Делегирует создание fallback примеров (list[dict])."""
        return self.validation._create_fallback_python_example(lesson_title, lesson_content)

    def _apply_visible_styles(self, examples: str, communication_style: str) -> str:
        """Делегирует применение HTML-стилей (используется только в HTML-пути)."""
        return self.generation._apply_visible_styles(examples, communication_style)

    def _build_enhanced_examples_prompt(
        self,
        lesson_title: str,
        lesson_description: str,
        keywords_str: str,
        lesson_content: str,
        communication_style: str,
        course_subject: str,
    ) -> str:
        """Делегирует создание промпта."""
        return self.generation._build_enhanced_examples_prompt(
            lesson_title,
            lesson_description,
            keywords_str,
            lesson_content,
            communication_style,
            course_subject,
        )
