"""
Модуль для генерации подробных объяснений материалов уроков.
Отвечает за создание расширенных теоретических разборов и детальных пояснений концепций.
"""

from content_utils import BaseContentGenerator, ContentUtils
from student_content import render_student_content


class ExplanationGenerator(BaseContentGenerator):
    """Генератор подробных объяснений для уроков."""

    def __init__(self, api_key):
        """
        Инициализация генератора объяснений.

        Args:
            api_key (str): API ключ OpenAI
        """
        super().__init__(api_key)
        self.logger.info("ExplanationGenerator инициализирован")

    def get_detailed_explanation(
        self,
        course,
        section,
        topic,
        lesson,
        lesson_content,
        communication_style="friendly",
    ):
        """
        Генерирует подробное объяснение материала урока.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson (str): Название урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения

        Returns:
            str: Подробное объяснение

        Raises:
            Exception: Если не удалось сгенерировать объяснение
        """
        try:
            lesson_title = str(lesson) if lesson is not None else "Урок"

            prompt = self._build_explanation_prompt(
                course,
                section,
                topic,
                lesson_title,
                lesson_content,
                communication_style,
            )

            messages = [
                {
                    "role": "system",
                    "content": "Ты - опытный преподаватель и эксперт в данной области.",
                },
                {"role": "user", "content": prompt},
            ]

            explanation = self.make_api_request(
                messages=messages, temperature=0.7, max_tokens=3500
            )

            self.save_debug_response(
                "detailed_explanation",
                prompt,
                explanation,
                {
                    "course": course,
                    "section": section,
                    "topic": topic,
                    "lesson": lesson_title,
                    "communication_style": communication_style,
                },
            )

            styled_explanation = self._apply_compact_styles(
                explanation, communication_style
            )

            self.logger.info("Подробное объяснение успешно сгенерировано")
            return styled_explanation

        except Exception as e:
            self.logger.error(
                f"Критическая ошибка при генерации подробного объяснения: {str(e)}"
            )
            raise Exception(f"Не удалось сгенерировать подробное объяснение: {str(e)}")

    def _apply_compact_styles(self, explanation, communication_style):
        """Оборачивает объяснение в канон рендера (``.explanation-compact``)."""
        utils = ContentUtils()
        prefix = utils.get_style_prefix(communication_style, "explanation")
        return render_student_content(
            explanation,
            wrapper="explanation-compact",
            lead_html=prefix,
        )

    def _build_explanation_prompt(
        self, course, section, topic, lesson_title, lesson_content, communication_style
    ):
        """
        Создает промпт для генерации подробного объяснения.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson_title (str): Название урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения

        Returns:
            str: Промпт для API
        """
        style_description = ContentUtils.COMMUNICATION_STYLES.get(
            communication_style, ContentUtils.COMMUNICATION_STYLES["friendly"]
        )

        return f"""
        Предоставь подробное объяснение материала по следующему уроку:

        Курс: {course}
        Раздел: {section}
        Тема: {topic}
        Урок: {lesson_title}

        СОДЕРЖАНИЕ УРОКА (ОСНОВА ДЛЯ ОБЪЯСНЕНИЯ):
        {lesson_content[:2000]}

        Используй следующий стиль общения: {style_description}

        Требования:
        1. Анализируй только содержание урока выше.
        2. Не придумывай факты, которых нет в уроке.
        3. Все примеры связаны с содержанием урока.

        Структура:
        1. Глубокий разбор основных концепций из урока
        2. Примеры и иллюстрации на основе урока
        3. Практические сценарии из урока
        4. Связанные концепции из урока

        Формат: Markdown (заголовки ## / ###, списки, **жирный**).
        Код только внутри блоков ``` с языком темы. Не оборачивай весь ответ
        в один fence. Не используй HTML.
        """
