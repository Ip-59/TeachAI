"""
Модуль для генерации подробных объяснений материалов уроков.
Отвечает за создание расширенных теоретических разборов и детальных пояснений концепций.
ИСПРАВЛЕНО: компактные интервалы и контрастный код
"""

from content_utils import BaseContentGenerator, ContentUtils


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

            # Сохраняем отладочную информацию
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

            # ИСПРАВЛЕНО: Применяем улучшенные CSS стили с компактными интервалами
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
        """
        ИСПРАВЛЕНО: Применяет компактные CSS стили к объяснению.

        Args:
            explanation (str): Исходное объяснение
            communication_style (str): Стиль общения

        Returns:
            str: Стилизованное объяснение
        """
        # Получаем префикс в зависимости от стиля общения
        utils = ContentUtils()
        prefix = utils.get_style_prefix(communication_style, "explanation")

        # ИСПРАВЛЕНО: Компактные CSS стили с контрастным кодом
        compact_css = """
        <style>
        .explanation-compact {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 16px;
            line-height: 1.4;
            padding: 20px;
            background: linear-gradient(135deg, #e7f3ff 0%, #cce7ff 100%);
            border-radius: 10px;
            margin: 15px 0;
            border-left: 4px solid #007bff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .explanation-compact h1, .explanation-compact h2, .explanation-compact h3, .explanation-compact h4 {
            color: #495057;
            margin-top: 15px;
            margin-bottom: 8px;
            line-height: 1.2;
            border-bottom: 2px solid #007bff;
            padding-bottom: 4px;
        }
        .explanation-compact h1 { font-size: 20px; }
        .explanation-compact h2 { font-size: 18px; }
        .explanation-compact h3 { font-size: 17px; }
        .explanation-compact h4 { font-size: 16px; }
        .explanation-compact p {
            margin-bottom: 8px;
            line-height: 1.3;
            text-align: justify;
        }
        .explanation-compact ul, .explanation-compact ol {
            margin-bottom: 10px;
            padding-left: 25px;
            line-height: 1.3;
        }
        .explanation-compact li {
            margin-bottom: 4px;
        }
        .explanation-compact code {
            background-color: #1a1a1a;
            color: #00ff41;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            font-weight: 600;
            border: 1px solid #333;
        }
        .explanation-compact pre {
            background-color: #1a1a1a;
            color: #00ff41;
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.05;
            border: 2px solid #333;
        }
        .explanation-compact pre code {
            background: none;
            color: inherit;
            padding: 0;
            font-size: inherit;
        }
        .explanation-compact .concept-block {
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 12px;
            margin: 10px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .explanation-compact .highlight {
            background-color: #fff3cd;
            padding: 8px;
            border-radius: 6px;
            border-left: 3px solid #ffc107;
            margin: 8px 0;
        }
        .explanation-compact strong {
            color: #495057;
            font-weight: 600;
        }
        .explanation-compact em {
            color: #6c757d;
            font-style: italic;
        }
        </style>
        <div class="explanation-compact">
        """

        return f"{compact_css}{prefix}{explanation}</div>"

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

        Базовое содержание урока:
        {lesson_content[:2000]}  # Ограничиваем длину для запроса

        Используй следующий стиль общения: {style_description}

        Предоставь расширенное объяснение, включающее:
        1. Глубокий разбор основных концепций
        2. Больше примеров и иллюстраций
        3. Практические сценарии применения
        4. Дополнительную информацию по теме
        5. Ссылки на связанные концепции

        Используй HTML-форматирование для структурирования ответа с компактной структурой.

        Структурируй ответ следующим образом:
        - Используй <h3> для основных разделов объяснения
        - Код помещай в <pre><code> блоки
        - Важные концепции оборачивай в <div class="concept-block">
        - Ключевые моменты выделяй в <div class="highlight">
        - Используй <strong> для акцентов и <em> для пояснений
        """
