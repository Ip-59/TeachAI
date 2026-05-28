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

    # Базовые темы Python — релевантны для уроков «Основы Python» и подобных,
    # даже если конкретная генерация урока не упомянула термин явно.
    _PYTHON_BASICS_STEMS = {
        "функци": "функции",
        "переменн": "переменные",
        "тип": "типы данных",
        "данн": "данные",
        "спис": "списки",
        "кортеж": "кортежи",
        "словар": "словари",
        "множеств": "множества",
        "услов": "условия",
        "цикл": "циклы",
        "оператор": "операторы",
        "синтакс": "синтаксис",
        "строк": "строки",
        "числ": "числа",
        "def": "определение функций",
        "return": "return",
        "import": "импорт",
        "class": "классы",
        "метод": "методы",
        "модул": "модули",
    }

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
            content_for_check = self.prepare_lesson_text_for_analysis(
                analysis_source,
                course_context,
                max_chars=6000,
                lesson_title=lesson_title,
            )
            if headers:
                outline = "; ".join(headers)
                content_for_check = f"СТРУКТУРА УРОКА: {outline}\n\n{content_for_check}"

            local_result = self._quick_local_relevance_check(
                user_question, content_for_check, lesson_data
            )
            if local_result is not None:
                self.logger.info(
                    "Локальная проверка релевантности: %s",
                    local_result["is_relevant"],
                )
                return local_result

            topic_result = self._topic_based_relevance_check(
                user_question, lesson_data
            )
            if topic_result is not None:
                self.logger.info(
                    "Тематическая проверка релевантности: %s",
                    topic_result["is_relevant"],
                )
                return topic_result

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
                    "used_raw_content": bool(lesson_raw_content),
                    "analysis_text_preview": content_for_check[:500],
                },
            )

            relevance_data = json.loads(response_content)
            result = self._extract_relevance_from_response(relevance_data)

            # LLM иногда отвергает базовые темы Python, не упомянутые
            # в конкретной генерации. Перепроверяем тематически.
            if not result["is_relevant"] and result.get("confidence", 100) <= 85:
                topic_result = self._topic_based_relevance_check(
                    user_question, lesson_data
                )
                if topic_result is not None:
                    return topic_result

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

    def _lesson_metadata_blob(self, lesson_data):
        """Собирает метаданные урока в одну строку для поиска."""
        if not isinstance(lesson_data, dict):
            return ""
        keywords = lesson_data.get("keywords", [])
        if not isinstance(keywords, list):
            keywords = [str(keywords)]
        return " ".join(
            [
                str(lesson_data.get("title", "")),
                str(lesson_data.get("description", "")),
                " ".join(keywords),
            ]
        )

    def _is_python_basics_lesson(self, lesson_data):
        """True, если урок относится к основам Python."""
        blob = self._lesson_metadata_blob(lesson_data).lower()
        return any(
            marker in blob
            for marker in ("python", "питон", "основы python", "синтаксис")
        )

    def _term_in_text(self, term, text):
        """Проверяет наличие термина с учётом словоформ."""
        if not term or not text:
            return False
        term = term.lower()
        text = text.lower()
        if term in text:
            return True
        if len(term) >= 4:
            stem = term[: max(4, len(term) - 2)]
            if stem in text:
                return True
        return False

    def _topic_based_relevance_check(self, user_question, lesson_data):
        """Тематическая проверка для уроков по основам Python.

        Args:
            user_question (str): Вопрос студента.
            lesson_data (dict): Метаданные урока.

        Returns:
            dict | None: Результат, если вопрос относится к базовым темам Python.
        """
        if not user_question or not self._is_python_basics_lesson(lesson_data):
            return None

        question_lower = user_question.lower()
        for stem, label in self._PYTHON_BASICS_STEMS.items():
            if stem in question_lower:
                return {
                    "is_relevant": True,
                    "confidence": 88,
                    "reason": (
                        f"Вопрос относится к базовой теме Python («{label}»), "
                        f"которая изучается в уроке «{lesson_data.get('title', 'урок')}»."
                    ),
                    "suggestions": [],
                }
        return None

    def _quick_local_relevance_check(self, user_question, lesson_text, lesson_data=None):
        """Быстрая проверка: есть ли слова из вопроса в тексте урока.

        Возвращает результат dict, если совпадение найдено.
        None — если нужна проверка через LLM.

        Args:
            user_question (str): Вопрос студента.
            lesson_text (str): Очищенный текст урока.
            lesson_data (dict | None): Метаданные урока (title, keywords).

        Returns:
            dict | None: Результат проверки или None для делегирования LLM.
        """
        if not user_question:
            return None

        question_lower = user_question.lower()
        search_parts = [lesson_text or ""]
        if lesson_data:
            search_parts.append(self._lesson_metadata_blob(lesson_data))
        search_corpus = " ".join(search_parts).lower()
        if not search_corpus.strip():
            return None

        stop_words = {
            "что", "такое", "как", "почему", "зачем", "где", "когда", "кто",
            "это", "ли", "в", "и", "на", "по", "для", "из", "от", "до", "не",
            "а", "the", "is", "are", "what", "how", "why", "можно", "нужно",
            "расскажи", "объясни", "покажи", "пример", "урок", "тема",
        }

        keywords = re.findall(r"[a-zа-яё0-9_]{3,}", question_lower)
        keywords = [w for w in keywords if w not in stop_words]
        if not keywords:
            return None

        for keyword in keywords:
            if self._term_in_text(keyword, search_corpus):
                return {
                    "is_relevant": True,
                    "confidence": 95,
                    "reason": (
                        f"Термин «{keyword}» связан с темой текущего урока."
                    ),
                    "suggestions": [],
                }

        return None

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
Определи, относится ли вопрос к теме урока. Опирайся в первую очередь на
ТЕКСТ УРОКА: если понятие или термин из вопроса встречается/разбирается в
тексте урока — вопрос РЕЛЕВАНТЕН, даже если этого нет в названии или
описании.

Вопрос считается релевантным, если:
1. Понятие/термин из вопроса упоминается или разбирается в тексте урока.
2. Вопрос касается практического применения материала урока.
3. Вопрос просит уточнения или дополнительной информации по теме урока.
4. Вопрос касается примеров или случаев использования из области урока.

Вопрос НЕ релевантен, если:
1. Он касается совершенно других тем или предметных областей,
   не упомянутых ни в тексте урока, ни в его метаданных.
2. Он касается общих вопросов жизни, не связанных с обучением.
3. Он относится к техническим проблемам системы (а не к материалу).

ВАЖНО: лучше склониться к «релевантен», если есть разумные основания
(термин упомянут хотя бы кратко). Не отбрасывай вопрос только потому,
что термин не вынесен в название или описание урока.

ВЕРНИ РЕЗУЛЬТАТ В ФОРМАТЕ JSON:
{{
    "is_relevant": true/false,
    "confidence": число от 0 до 100,
    "reason": "Подробное объяснение почему вопрос релевантен/нерелевантен",
    "suggestions": ["Предложение 1", "Предложение 2", "Предложение 3"]
}}

Если вопрос нерелевантен, в поле suggestions укажи альтернативные источники
информации (поисковики, специализированные ресурсы, форумы и т.д.).
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
