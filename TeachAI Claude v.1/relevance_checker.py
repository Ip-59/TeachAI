"""
Модуль для проверки релевантности вопросов пользователей к содержанию урока.
Отвечает за анализ соответствия вопросов изучаемой теме.
ИСПРАВЛЕНО: Красивое форматирование нерелевантных ответов
"""

import json
import re
from content_utils import BaseContentGenerator


class RelevanceChecker(BaseContentGenerator):
    """Проверщик релевантности вопросов к уроку."""

    def __init__(self, api_key):
        """
        Инициализация проверщика релевантности.

        Args:
            api_key (str): API ключ OpenAI
        """
        super().__init__(api_key)
        self.logger.info("RelevanceChecker инициализирован")

    def check_question_relevance(self, user_question, lesson_content, lesson_data):
        """
        Проверяет релевантность вопроса пользователя к содержанию урока.

        Args:
            user_question (str): Вопрос пользователя
            lesson_content (str): Содержание урока
            lesson_data (dict): Метаданные урока

        Returns:
            dict: Результат проверки со следующими ключами:
                - is_relevant (bool): Релевантен ли вопрос
                - confidence (float): Уверенность в оценке (0-100)
                - reason (str): Объяснение решения
                - suggestions (list): Предложения альтернативных источников (если нерелевантен)

        Raises:
            Exception: Если не удалось выполнить проверку
        """
        try:
            # Получаем базовую информацию об уроке
            lesson_title = lesson_data.get("title", "Урок")
            lesson_description = lesson_data.get("description", "Нет описания")
            lesson_keywords = lesson_data.get("keywords", [])

            # Очищаем HTML теги для анализа
            clean_content = self._clean_html_for_analysis(lesson_content)

            # Ограничиваем длину для запроса
            content_for_analysis = (
                clean_content[:2500] if len(clean_content) > 2500 else clean_content
            )

            prompt = self._build_relevance_prompt(
                user_question,
                lesson_title,
                lesson_description,
                lesson_keywords,
                content_for_analysis,
            )

            messages = [
                {
                    "role": "system",
                    "content": "Ты - эксперт по образованию, который анализирует соответствие вопросов студентов изучаемому материалу. Твоя задача - определить, относится ли вопрос к теме урока.",
                },
                {"role": "user", "content": prompt},
            ]

            response_content = self.make_api_request(
                messages=messages,
                temperature=0.2,  # Низкая температура для точного анализа
                max_tokens=1500,
                response_format={"type": "json_object"},
            )

            # Сохраняем отладочную информацию
            self.save_debug_response(
                "relevance_check",
                prompt,
                response_content,
                {
                    "user_question": user_question,
                    "lesson_title": lesson_title,
                    "lesson_description": lesson_description,
                },
            )

            relevance_data = json.loads(response_content)
            result = self._extract_relevance_from_response(relevance_data)

            self.logger.info(
                f"Проверка релевантности завершена: {result['is_relevant']} (уверенность: {result['confidence']}%)"
            )
            return result

        except Exception as e:
            self.logger.error(
                f"Критическая ошибка при проверке релевантности: {str(e)}"
            )
            raise Exception(f"Не удалось проверить релевантность вопроса: {str(e)}")

    def generate_non_relevant_response(self, user_question, suggestions):
        """
        ИСПРАВЛЕНО: Использует ТОЧНО ТАКОЙ ЖЕ формат как релевантные ответы, только с желтым фоном.

        Args:
            user_question (str): Вопрос пользователя
            suggestions (list): Предложения альтернативных источников

        Returns:
            str: Стилизованный ответ
        """
        try:
            # Формируем список предложений
            if suggestions and len(suggestions) > 0:
                suggestions_html = "<ul>"
                for suggestion in suggestions[:3]:  # Максимум 3 предложения
                    suggestions_html += f"<li>{suggestion}</li>"
                suggestions_html += "</ul>"
            else:
                suggestions_html = "<p>Рекомендуем обратиться к специализированным ресурсам или преподавателю.</p>"

            # ИСПРАВЛЕНО: ТОЧНО ТАКОЙ ЖЕ CSS как у qa-answer, только с желтыми цветами
            response = f"""
            <style>
            .qa-answer {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 16px;
                line-height: 1.4;
                padding: 20px;
                background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
                border-radius: 10px;
                margin: 15px 0;
                border-left: 4px solid #856404;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .qa-answer h1, .qa-answer h2, .qa-answer h3, .qa-answer h4 {{
                color: #495057;
                margin-top: 15px;
                margin-bottom: 8px;
                line-height: 1.2;
                border-bottom: 2px solid #856404;
                padding-bottom: 4px;
            }}
            .qa-answer h1 {{ font-size: 20px; }}
            .qa-answer h2 {{ font-size: 18px; }}
            .qa-answer h3 {{ font-size: 17px; }}
            .qa-answer h4 {{ font-size: 16px; }}
            .qa-answer p {{
                margin-bottom: 8px;
                line-height: 1.3;
                text-align: justify;
            }}
            .qa-answer ul, .qa-answer ol {{
                margin-bottom: 10px;
                padding-left: 25px;
                line-height: 1.3;
            }}
            .qa-answer li {{
                margin-bottom: 4px;
            }}
            .qa-answer code {{
                background-color: #f8f9fa;
                color: #d63384;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                font-weight: 600;
                border: 1px solid #dee2e6;
            }}
            .qa-answer pre {{
                background-color: #f8f9fa;
                color: #212529;
                padding: 12px;
                border-radius: 8px;
                overflow-x: auto;
                margin: 10px 0;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                line-height: 1.05;
                border: 2px solid #dee2e6;
            }}
            .qa-answer pre code {{
                background: none;
                color: inherit;
                padding: 0;
                font-size: inherit;
                border: none;
            }}
            .qa-answer .answer-block {{
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
                margin: 10px 0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .qa-answer strong {{
                color: #495057;
                font-weight: 600;
            }}
            .qa-answer em {{
                color: #6c757d;
                font-style: italic;
            }}
            </style>
            <div class="qa-answer">
                <h4 style='margin-top: 0; color: #856404;'>🤔 Вопрос не связан с текущим уроком</h4>
                <p><strong>Ваш вопрос:</strong> {user_question}</p>
                <p>К сожалению, ваш вопрос не относится к теме текущего урока. Для получения ответа на этот вопрос рекомендуем:</p>
                {suggestions_html}
                <p><em>Пожалуйста, задавайте вопросы, связанные с материалом урока, чтобы получить наиболее полезные ответы.</em></p>
            </div>
            """

            self.logger.info("Сгенерирован ответ для нерелевантного вопроса")
            return response

        except Exception as e:
            self.logger.error(
                f"Ошибка при генерации ответа для нерелевантного вопроса: {str(e)}"
            )
            return f"""
            <div style='background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #ffc107;'>
                <h4 style='margin-top: 0; color: #856404;'>🤔 Вопрос не связан с текущим уроком</h4>
                <p><strong>Ваш вопрос:</strong> {user_question}</p>
                <p>К сожалению, ваш вопрос не относится к теме текущего урока. Пожалуйста, задавайте вопросы, связанные с изучаемым материалом.</p>
            </div>
            """

    def generate_multiple_questions_warning(self, questions_count):
        """
        ИСПРАВЛЕНО: Генерирует красиво оформленное предупреждение о большом количестве вопросов.

        Args:
            questions_count (int): Количество заданных вопросов

        Returns:
            str: Стилизованное предупреждение
        """
        return f"""
        <style>
        .questions-warning {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 16px;
            line-height: 1.4;
            padding: 20px;
            background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
            border-radius: 10px;
            margin: 15px 0;
            border-left: 4px solid #17a2b8;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .questions-warning h4 {{
            color: #495057;
            margin-top: 0;
            margin-bottom: 8px;
            line-height: 1.2;
            border-bottom: 2px solid #17a2b8;
            padding-bottom: 4px;
            font-size: 18px;
        }}
        .questions-warning p {{
            margin-bottom: 8px;
            line-height: 1.3;
            color: #0c5460;
        }}
        .questions-warning strong {{
            color: #495057;
            font-weight: 600;
        }}
        .questions-warning em {{
            color: #0c5460;
            font-style: italic;
        }}
        </style>
        <div class="questions-warning">
            <h4>💡 Рекомендация</h4>
            <p>Вы уже задали <strong>{questions_count} вопросов</strong> по этому уроку. Это отлично, что вы активно изучаете материал!</p>
            <p>Рекомендуем вернуться к основному содержанию урока и продолжить обучение. При необходимости вы всегда можете задать дополнительные вопросы.</p>
            <p><em>Помните: практическое применение знаний так же важно, как и изучение теории!</em></p>
        </div>
        """

    def _clean_html_for_analysis(self, content):
        """
        Очищает HTML теги для анализа содержания.

        Args:
            content (str): Содержание с HTML

        Returns:
            str: Очищенное содержание
        """
        clean_content = re.sub(r"<[^>]+>", " ", content)
        clean_content = re.sub(r"\s+", " ", clean_content).strip()
        return clean_content

    def _build_relevance_prompt(
        self, user_question, lesson_title, lesson_description, lesson_keywords, content
    ):
        """
        Создает промпт для проверки релевантности.

        Args:
            user_question (str): Вопрос пользователя
            lesson_title (str): Название урока
            lesson_description (str): Описание урока
            lesson_keywords (list): Ключевые слова урока
            content (str): Содержание урока

        Returns:
            str: Промпт для API
        """
        keywords_str = (
            ", ".join(lesson_keywords)
            if isinstance(lesson_keywords, list)
            else str(lesson_keywords)
        )

        return f"""
        Проанализируй, насколько вопрос студента релевантен (соответствует) теме и содержанию текущего урока:

        ИНФОРМАЦИЯ ОБ УРОКЕ:
        Название урока: {lesson_title}
        Описание урока: {lesson_description}
        Ключевые слова: {keywords_str}

        Содержание урока:
        {content}

        ВОПРОС СТУДЕНТА:
        {user_question}

        ЗАДАЧА:
        Определи, относится ли вопрос к теме урока. Вопрос считается релевантным, если:
        1. Он касается понятий, терминов или тем, упомянутых в уроке
        2. Он связан с практическим применением материала урока
        3. Он просит уточнения или дополнительной информации по теме урока
        4. Он касается примеров или случаев использования из области урока

        Вопрос НЕ релевантен, если:
        1. Он касается совершенно других тем или предметных областей
        2. Он не связан с содержанием урока
        3. Он касается общих вопросов жизни, не связанных с обучением
        4. Он относится к техническим проблемам системы

        ВЕРНИ РЕЗУЛЬТАТ В ФОРМАТЕ JSON:
        {{
            "is_relevant": true/false,
            "confidence": число от 0 до 100,
            "reason": "Подробное объяснение почему вопрос релевантен/нерелевантен",
            "suggestions": ["Предложение 1", "Предложение 2", "Предложение 3"]
        }}

        Если вопрос нерелевантен, в поле suggestions укажи альтернативные источники информации (поисковики, специализированные ресурсы, форумы и т.д.).
        """

    def _extract_relevance_from_response(self, relevance_data):
        """
        Извлекает результат проверки релевантности из ответа API.

        Args:
            relevance_data (dict): Ответ API в формате JSON

        Returns:
            dict: Структурированный результат проверки
        """
        try:
            # Проверяем обязательные поля
            is_relevant = relevance_data.get("is_relevant", False)
            confidence = relevance_data.get("confidence", 0)
            reason = relevance_data.get("reason", "Причина не указана")
            suggestions = relevance_data.get("suggestions", [])

            # Валидируем и нормализуем данные
            if not isinstance(is_relevant, bool):
                is_relevant = str(is_relevant).lower() in ["true", "1", "yes", "да"]

            if not isinstance(confidence, (int, float)):
                confidence = 50  # Средняя уверенность по умолчанию
            else:
                confidence = max(
                    0, min(100, float(confidence))
                )  # Ограничиваем диапазон 0-100

            if not isinstance(suggestions, list):
                suggestions = []

            return {
                "is_relevant": is_relevant,
                "confidence": confidence,
                "reason": reason,
                "suggestions": suggestions,
            }
        except Exception as e:
            self.logger.error(
                f"Ошибка при извлечении результата релевантности: {str(e)}"
            )
            # Возвращаем безопасный результат по умолчанию
            return {
                "is_relevant": True,  # По умолчанию считаем релевантным
                "confidence": 50,
                "reason": "Не удалось проанализировать релевантность",
                "suggestions": [],
            }
