"""
Модуль для генерации подробных объяснений материалов уроков.
Отвечает за создание расширенных теоретических разборов и детальных пояснений концепций.

ИСПРАВЛЕНО ЭТАП 50: ДОБАВЛЕН недостающий метод generate_explanation для исправления AttributeError
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

    def generate_explanation(
        self, lesson_data, lesson_content, communication_style="friendly"
    ):
        """
        ДОБАВЛЕНО ЭТАП 50: Генерация подробного объяснения урока

        Исправляет ошибку: 'ExplanationGenerator' object has no attribute 'generate_explanation'
        Делегирует вызов к существующему методу get_detailed_explanation()

        Args:
            lesson_data (dict): Данные урока с ключами для извлечения информации
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения

        Returns:
            str: Подробное объяснение урока

        Raises:
            Exception: Если не удалось сгенерировать объяснение
        """
        try:
            # Извлекаем данные из lesson_data с поддержкой различных ключей
            course = lesson_data.get(
                "course_title", lesson_data.get("course_name", "Курс")
            )
            section = lesson_data.get(
                "section_title",
                lesson_data.get(
                    "section_name", lesson_data.get("section_id", "Раздел")
                ),
            )
            topic = lesson_data.get(
                "topic_title",
                lesson_data.get("topic_name", lesson_data.get("topic_id", "Тема")),
            )
            lesson = lesson_data.get(
                "title", lesson_data.get("lesson_title", lesson_data.get("id", "Урок"))
            )

            # Детальное логирование для отладки
            self.logger.info(
                f"🔧 Генерация объяснения для: {course} → {section} → {topic} → {lesson}"
            )
            self.logger.debug(f"Стиль общения: {communication_style}")
            self.logger.debug(
                f"Доступные ключи в lesson_data: {list(lesson_data.keys())}"
            )

            # Делегируем к существующему методу get_detailed_explanation
            result = self.get_detailed_explanation(
                course=course,
                section=section,
                topic=topic,
                lesson=lesson,
                lesson_content=lesson_content,
                communication_style=communication_style,
            )

            self.logger.info("✅ Объяснение успешно сгенерировано")
            return result

        except Exception as e:
            error_msg = f"Ошибка генерации объяснения: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            self.logger.error(f"lesson_data: {lesson_data}")
            return f"⚠️ {error_msg}\n\nПожалуйста, попробуйте позже или обратитесь к администратору."

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
                    "content": "Ты - опытный преподаватель и эксперт в данной области. "
                    "Твоя задача - дать подробное, понятное объяснение материала урока. "
                    "Используй ясный язык, приводи примеры и аналогии там, где это уместно.",
                },
                {"role": "user", "content": prompt},
            ]

            explanation = self.make_api_request(
                messages=messages, temperature=0.7, max_tokens=3000
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

            # Применяем стилизацию к объяснению
            styled_explanation = self._style_explanation(
                explanation, lesson_title, communication_style
            )

            self.logger.info(
                f"Успешно сгенерировано объяснение для урока '{lesson_title}'"
            )
            return styled_explanation

        except Exception as e:
            self.logger.error(f"Критическая ошибка при генерации объяснения: {str(e)}")
            raise Exception(f"Не удалось сгенерировать объяснение: {str(e)}")

    def _build_explanation_prompt(
        self, course, section, topic, lesson, lesson_content, communication_style
    ):
        """
        Создает промпт для генерации подробного объяснения.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson (str): Название урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения

        Returns:
            str: Промпт для API
        """
        style_instructions = self._get_style_instructions(communication_style)

        return f"""
        Создай подробное объяснение урока, которое поможет студенту глубже понять материал.

        Контекст:
        - Курс: {course}
        - Раздел: {section}
        - Тема: {topic}
        - Урок: {lesson}

        Содержание урока:
        {lesson_content}

        {style_instructions}

        ТРЕБОВАНИЯ К ОБЪЯСНЕНИЮ:
        1. Начни с краткого резюме основных идей урока
        2. Разбери каждый важный концепт детально
        3. Объясни связи между различными понятиями
        4. Приведи дополнительные примеры и аналогии
        5. Укажи на практическое применение материала
        6. Выдели ключевые моменты, которые важно запомнить
        7. Предложи способы лучше понять и запомнить материал

        СТРУКТУРА ОТВЕТА:
        **Краткое резюме:**
        (2-3 предложения с основными идеями урока)

        **Детальный разбор концептов:**
        1. **Первый концепт:** Объяснение с примерами
        2. **Второй концепт:** Объяснение с примерами
        (и так далее для каждого важного концепта)

        **Практические примеры:**
        - Конкретные примеры применения
        - Демонстрация концептов в действии

        **Ключевые выводы:**
        - Главные идеи, которые важно запомнить
        - Связи между концептами

        **Советы по изучению:**
        - Рекомендации по лучшему усвоению материала
        - Способы практического применения знаний

        ФОРМАТИРОВАНИЕ:
        - Используй **жирный текст** для важных терминов и заголовков разделов
        - Для примеров кода используй формат: ```python код здесь ```
        - Создавай нумерованные списки для пошаговых объяснений
        - Используй маркированные списки для перечислений

        Объяснение должно быть информативным, хорошо структурированным и доступным для понимания.
        """

    def _get_style_instructions(self, communication_style):
        """
        Возвращает инструкции по стилю общения.

        Args:
            communication_style (str): Стиль общения

        Returns:
            str: Инструкции для промпта
        """
        styles = {
            "formal": "Используй формальный, академический стиль. Применяй точную терминологию и структурированное изложение.",
            "friendly": "Используй дружелюбный, понятный стиль. Объясняй сложные концепты простыми словами.",
            "casual": "Используй непринужденный стиль общения. Можешь использовать разговорные выражения и легкий юмор.",
            "brief": "Будь кратким и четким. Фокусируйся только на самых важных моментах.",
        }
        return styles.get(communication_style, styles["friendly"])

    def _style_explanation(self, explanation, lesson_title, communication_style):
        """
        Применяет HTML-стилизацию к объяснению для правильного отображения в Jupyter.

        Args:
            explanation (str): Сгенерированное объяснение
            lesson_title (str): Название урока
            communication_style (str): Стиль общения

        Returns:
            str: HTML-стилизованное объяснение
        """
        # Конвертируем Markdown-подобное форматирование в HTML
        html_explanation = self._convert_markdown_to_html(explanation)

        # Добавляем заголовок
        title_html = (
            """
        <h3 style="color: #1f2937; margin-bottom: 15px; border-bottom: 2px solid #22c55e; padding-bottom: 8px;">
            📚 Подробное объяснение урока: """
            + lesson_title
            + """
        </h3>
        """
        )

        # Форматируем основной текст
        content_html = (
            '<div style="font-size: 14px; line-height: 1.4;">'
            + html_explanation
            + "</div>"
        )

        # Собираем полный HTML
        styled_explanation = title_html + content_html

        # Добавляем завершающую фразу в зависимости от стиля
        if communication_style == "friendly":
            styled_explanation += """
            <div style="margin-top: 15px; padding: 12px; background: #f0fdf4; border-radius: 8px; border-left: 4px solid #22c55e;">
                <p style="margin: 0; color: #15803d; font-weight: 500;">
                    💡 <strong>Надеюсь, это объяснение помогло вам лучше понять материал!</strong>
                </p>
            </div>
            """
        elif communication_style == "formal":
            styled_explanation += """
            <div style="margin-top: 15px; padding: 12px; background: #f8fafc; border-radius: 8px; border-left: 4px solid #64748b;">
                <p style="margin: 0; color: #475569; font-weight: 500;">
                    <strong>Данное объяснение представляет детальный анализ ключевых концепций урока.</strong>
                </p>
            </div>
            """
        elif communication_style == "casual":
            styled_explanation += """
            <div style="margin-top: 15px; padding: 12px; background: #fef3c7; border-radius: 8px; border-left: 4px solid #f59e0b;">
                <p style="margin: 0; color: #92400e; font-weight: 500;">
                    😊 <strong>Вот и все! Теперь материал должен быть понятнее.</strong>
                </p>
            </div>
            """

        return styled_explanation

    def _convert_markdown_to_html(self, text):
        """
        Конвертирует основные Markdown элементы в HTML.

        Args:
            text (str): Текст с Markdown разметкой

        Returns:
            str: HTML-форматированный текст
        """
        import re

        # Создаем CSS стили заранее чтобы избежать проблем с кавычками
        h4_style = "color: #374151; margin: 15px 0 8px 0; font-weight: 600;"
        strong_style = "color: #1f2937;"
        python_code_style = "background: #1f2937; color: #f1f5f9; padding: 15px; border-radius: 6px; margin: 8px 0; font-family: monospace; white-space: pre-wrap; overflow-x: auto; line-height: 1.3;"
        general_code_style = "background: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; margin: 8px 0; font-family: monospace; white-space: pre-wrap; overflow-x: auto; line-height: 1.3;"
        inline_code_style = "background: #f1f5f9; padding: 2px 4px; border-radius: 3px; font-family: monospace; color: #1e40af;"
        ol_style = "margin: 10px 0; padding-left: 25px;"
        ul_style = "margin: 10px 0; padding-left: 25px;"
        li_style = "margin: 5px 0; line-height: 1.4;"
        p_style = "margin: 8px 0; line-height: 1.4;"

        # Конвертируем заголовки (жирный текст в начале строки)
        text = re.sub(
            r"^\*\*([^*]+)\*\*$",
            '<h4 style="' + h4_style + '">\\1</h4>',
            text,
            flags=re.MULTILINE,
        )

        # Конвертируем жирный текст
        text = re.sub(
            r"\*\*([^*]+)\*\*",
            '<strong style="' + strong_style + '">\\1</strong>',
            text,
        )

        # Конвертируем блоки кода Python
        text = re.sub(
            r"```python\n(.*?)\n```",
            '<div style="' + python_code_style + '">\\1</div>',
            text,
            flags=re.DOTALL,
        )

        # Конвертируем общие блоки кода
        text = re.sub(
            r"```(.*?)```",
            '<div style="' + general_code_style + '">\\1</div>',
            text,
            flags=re.DOTALL,
        )

        # Конвертируем инлайн код
        text = re.sub(
            r"`([^`]+)`", '<code style="' + inline_code_style + '">\\1</code>', text
        )

        # Обрабатываем списки построчно
        lines = text.split("\n")
        in_numbered_list = False
        result_lines = []

        for line in lines:
            # Обрабатываем нумерованные списки
            if re.match(r"^\d+\.\s+", line):
                if not in_numbered_list:
                    result_lines.append('<ol style="' + ol_style + '">')
                    in_numbered_list = True
                content = re.sub(r"^\d+\.\s+", "", line)
                result_lines.append('<li style="' + li_style + '">' + content + "</li>")
            else:
                if in_numbered_list:
                    result_lines.append("</ol>")
                    in_numbered_list = False
                if line.strip():
                    result_lines.append('<p style="' + p_style + '">' + line + "</p>")
                elif result_lines and not result_lines[-1].startswith("<"):
                    result_lines.append("<br>")

        if in_numbered_list:
            result_lines.append("</ol>")

        # Конвертируем маркированные списки
        text = "\n".join(result_lines)
        text = re.sub(
            r"^-\s+(.+)$",
            '<li style="' + li_style + '">\\1</li>',
            text,
            flags=re.MULTILINE,
        )

        # Оборачиваем последовательные элементы списка в ul
        text = re.sub(
            r"(<li[^>]*>.*?</li>(?:\s*<li[^>]*>.*?</li>)*)",
            '<ul style="' + ul_style + '">\\1</ul>',
            text,
            flags=re.DOTALL,
        )

        return text
