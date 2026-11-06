"""
Модуль для проверки релевантности вопросов пользователей к содержанию урока.
Отвечает за анализ соответствия вопросов изучаемой теме.
ИСПРАВЛЕНО: Красивое форматирование нерелевантных ответов
"""

import json
from llm_api_base import BaseContentGenerator
from llm_json import parse_llm_json


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

    def check_question_relevance(
        self,
        user_question,
        lesson_content,
        lesson_data,
        course_context=None,
        lesson_raw_content=None,
    ):
        """
        Проверяет релевантность вопроса пользователя к теме урока.

        Решение строится по СОДЕРЖАНИЮ урока (а не только по title/description):
        иначе вопрос про материал, упомянутый в теле, но отсутствующий в
        метаданных, ошибочно помечается как нерелевантный. Перед запросом
        срезается breadcrumb-шапка (названия курса/раздела/темы), чтобы LLM
        не оценивал релевантность по общему контексту курса.

        Args:
            user_question (str): Вопрос пользователя.
            lesson_content (str): HTML-содержание урока.
            lesson_data (dict): Метаданные урока.
            course_context (dict | None): Контекст курса для среза шапки.
            lesson_raw_content (str | None): Сырой текст урока от LLM до
                CSS/HTML-обёртки. Предпочтительный источник для анализа.

        Returns:
            dict: Результат проверки со следующими ключами:
                - is_relevant (bool): Релевантен ли вопрос
                - confidence (float): Уверенность в оценке (0-100)
                - reason (str): Объяснение решения
                - suggestions (list): Предложения альтернативных источников
                  (если нерелевантен)

        Raises:
            Exception: Если не удалось выполнить проверку.
        """
        try:
            lesson_title = lesson_data.get("title", "Урок")
            lesson_description = lesson_data.get("description", "Нет описания")
            lesson_keywords = lesson_data.get("keywords", [])

            analysis_source = lesson_raw_content or lesson_content
            headers = self.extract_lesson_headers(analysis_source)
            from learning_prompt_context import FULL_LESSON_MAX_CHARS

            content_for_check = self.prepare_lesson_text_for_analysis(
                analysis_source,
                course_context,
                max_chars=FULL_LESSON_MAX_CHARS,
                lesson_title=lesson_title,
            )
            if headers:
                outline = "; ".join(headers)
                content_for_check = f"СТРУКТУРА УРОКА: {outline}\n\n{content_for_check}"

            # Релевантность — только через LLM (без локальных keyword/stem-shortcut).
            prompt = self._build_relevance_prompt(
                user_question,
                lesson_title,
                lesson_description,
                lesson_keywords,
                content_for_check,
            )

            messages = [
                {
                    "role": "system",
                    "content": (
                        "Ты преподаватель этого курса. "
                        "scope=lesson — вопрос про материал этого урока. "
                        "scope=course — вопрос из предмета курса "
                        "(язык, библиотеки, фреймворки, инструменты курса), "
                        "даже если этот урок их не вводит: ответь. "
                        "scope=outside — только совсем другая область "
                        "(быт, спорт, погода). "
                        "Если в причине отказа хочется назвать тему урока — "
                        "это scope=course, не outside. "
                        "Отвечай только JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ]

            response_content = self.make_api_request(
                messages=messages,
                temperature=0.2,
                max_tokens=1500,
                response_format={"type": "json_object"},
            )

            self.save_debug_response(
                "relevance_check",
                prompt,
                response_content,
                {
                    "user_question": user_question,
                    "lesson_title": lesson_title,
                    "lesson_description": lesson_description,
                    "used_raw_content": bool(lesson_raw_content),
                    "analysis_text_preview": content_for_check[:500],
                },
            )

            relevance_data = parse_llm_json(response_content)
            result = self._extract_relevance_from_response(relevance_data)
            result = self._promote_outside_confused_with_lesson(
                result, lesson_title
            )

            self.logger.info(
                f"Проверка релевантности завершена: {result['is_relevant']} "
                f"(уверенность: {result['confidence']}%)"
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
                line-height: 1.5;
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
        """Совместимая обёртка над общим хелпером BaseContentGenerator.

        Оставлено, чтобы внешний код, который мог дёргать этот метод,
        продолжал работать. Новая логика учитывает `<style>/<script>`
        и комментарии.
        """
        return self.clean_lesson_html_for_analysis(content)

    def _build_relevance_prompt(
        self, user_question, lesson_title, lesson_description, lesson_keywords, content
    ):
        """
        Создает промпт для проверки релевантности.

        В промпт включается тело урока (без breadcrumb-шапки и тегов),
        чтобы решение строилось по фактическому материалу, а не только
        по метаданным урока.

        Args:
            user_question (str): Вопрос пользователя.
            lesson_title (str): Название урока.
            lesson_description (str): Описание урока.
            lesson_keywords (list): Ключевые слова урока.
            content (str): Очищенный текст урока (без HTML и шапки).

        Returns:
            str: Промпт для API.
        """
        keywords_str = (
            ", ".join(lesson_keywords)
            if isinstance(lesson_keywords, list)
            else str(lesson_keywords)
        )

        return f"""
Проанализируй, насколько вопрос студента релевантен (соответствует) теме урока.

ИНФОРМАЦИЯ ОБ УРОКЕ:
Название урока: {lesson_title}
Описание урока: {lesson_description}
Ключевые слова: {keywords_str}

ТЕКСТ УРОКА (главный источник для решения):
{content}

ВОПРОС СТУДЕНТА:
{user_question}

ЗАДАЧА:
Три уровня, не сверка фраз с текстом урока.

scope=lesson — вопрос про материал этого урока: ответ в основном опирается
на то, что урок уже вводит или показывает в тексте или коде.
Сюда же относятся уточнения и сравнения близких конструкций из урока
(даже если точной фразы вопроса в тексте нет).

scope=course — вопрос из предметной области этого курса,
но не из материала этого урока: другая тема курса; язык, библиотеки,
фреймворки и инструменты экосистемы курса; версии, новости и общие
факты о предмете курса. На такой вопрос отвечают.
reason — одна фраза, что это не тема текущего урока.

scope=outside — вопрос вне предмета курса целиком
(другая область: быт, спорт, погода и т.п.).
Только здесь отказ. reason — одно-два предложения ученику о том,
что вопрос вне предмета этого курса.
В reason для outside запрещено: «тема урока», «текущий урок»,
«рамки урока», название текущего урока. Если тянет объяснить отказ
через тему урока — поставь scope=course, а не outside.

Не пиши «не рассматривается в тексте», «отсутствует в материале».
Не ставь scope=course только потому, что вопрос «шире одной фразы» урока:
если ответ в основном опирается на материал этого урока — это scope=lesson.
Не ставь scope=outside только потому, что урок эту тему не вводит:
если вопрос всё ещё про предмет курса (включая его библиотеки
и инструменты) — это scope=course.

ВЕРНИ РЕЗУЛЬТАТ В ФОРМАТЕ JSON:
{{
    "scope": "lesson" или "course" или "outside",
    "is_relevant": true для lesson и course, false только для outside,
    "confidence": число от 0 до 100,
    "reason": "фраза ученику",
    "suggestions": []
}}
"""

    @staticmethod
    def _promote_outside_confused_with_lesson(result, lesson_title):
        """Если модель поставила outside, но объясняет отказ темой урока —
        это путаница lesson/course: поднимаем до course.

        Промпт уже запрещает такие формулировки; страховка нужна, потому
        что модель всё равно иногда пишет «не относится к операторам…».
        """
        if not isinstance(result, dict) or result.get("scope") != "outside":
            return result
        reason = str(result.get("reason") or "").lower()
        title = str(lesson_title or "").strip().lower()
        markers = (
            "тем урока",
            "теме урока",
            "тему урока",
            "текущего урока",
            "текущем уроке",
            "текущий урок",
            "рамки урока",
            "рамках урока",
            "предмет урока",
            "фокусируется на",
        )
        confused = any(m in reason for m in markers)
        if title and len(title) >= 4 and title in reason:
            confused = True
        if not confused:
            return result
        fixed = dict(result)
        fixed["scope"] = "course"
        fixed["is_relevant"] = True
        fixed["on_lesson"] = False
        if not fixed.get("reason"):
            fixed["reason"] = "Это не тема текущего урока."
        return fixed

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
            scope = str(relevance_data.get("scope") or "").strip().lower()
            is_relevant = relevance_data.get("is_relevant", False)
            confidence = relevance_data.get("confidence", 0)
            reason = relevance_data.get("reason", "Причина не указана")
            suggestions = relevance_data.get("suggestions", [])

            if scope in ("lesson", "урок"):
                scope = "lesson"
            elif scope in ("course", "курс"):
                scope = "course"
            elif scope in ("outside", "вне"):
                scope = "outside"
            else:
                scope = ""

            # Валидируем и нормализуем данные
            if not isinstance(is_relevant, bool):
                is_relevant = str(is_relevant).lower() in ["true", "1", "yes", "да"]

            if scope == "course":
                is_relevant = True
                on_lesson = False
            elif scope == "outside":
                is_relevant = False
                on_lesson = False
            elif scope == "lesson":
                is_relevant = True
                on_lesson = True
            else:
                on_lesson = is_relevant

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
                "on_lesson": on_lesson,
                "scope": scope or ("lesson" if on_lesson else "outside"),
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
                "on_lesson": True,
                "scope": "lesson",
                "confidence": 50,
                "reason": "Не удалось проанализировать релевантность",
                "suggestions": [],
            }
