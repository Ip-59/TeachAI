"""
Модуль для генерации практических примеров по материалам уроков.
Отвечает за создание конкретных примеров кода, задач и практических упражнений.
ИСПРАВЛЕНО: Видимые примеры кода вместо черных блоков
ИСПРАВЛЕНО: Строгий контроль релевантности примеров теме курса (проблема #88)
"""

import json
from typing import Any, Dict, List

from content_utils import BaseContentGenerator, ContentUtils
from examples_html_utils import (
    interpret_examples_payload,
    is_examples_notice,
    parse_examples_json_response,
    render_examples_json_to_html,
)


class ExamplesGeneration(BaseContentGenerator):
    """Генератор практических примеров для уроков."""

    def __init__(self, api_key):
        """
        Инициализация генератора примеров.

        Args:
            api_key (str): API ключ OpenAI
        """
        super().__init__(api_key)
        self.logger.info("ExamplesGeneration инициализирован")

    def generate_examples_data(
        self,
        lesson_data,
        lesson_content,
        communication_style="friendly",
        course_context=None,
    ) -> List[Dict[str, str]]:
        """Возвращает примеры в виде структурированного списка словарей.

        Это основной (чистый) путь генерации. HTML здесь не строится.

        Returns:
            list[dict]: Каждый элемент — {"title": str, "description": str, "code": str}.

        Raises:
            Exception: Если не удалось сгенерировать примеры.
        """
        try:
            lesson_title = lesson_data.get("title", "Урок")
            lesson_description = lesson_data.get("description", "Нет описания")
            lesson_keywords = lesson_data.get("keywords", [])

            keywords_str = (
                ", ".join(lesson_keywords)
                if isinstance(lesson_keywords, list)
                else str(lesson_keywords)
            )

            from learning_prompt_context import FULL_LESSON_MAX_CHARS

            content_for_prompt = self.prepare_lesson_text_for_analysis(
                lesson_content,
                course_context=course_context,
                max_chars=FULL_LESSON_MAX_CHARS,
                lesson_title=lesson_title,
            )

            course_subject = self._determine_course_subject(
                course_context,
                content_for_prompt,
                lesson_keywords,
                lesson_data=lesson_data,
            )

            prompt = self._build_enhanced_examples_prompt(
                lesson_title,
                lesson_description,
                keywords_str,
                content_for_prompt,
                communication_style,
                course_subject,
            )

            messages = [
                {
                    "role": "system",
                    "content": (
                        f"Ты — преподаватель {course_subject}. "
                        "Отвечаешь только JSON. Сначала реши, есть ли у этого урока "
                        "пример, который честно выполняется как Python в редакторе. "
                        "Если нет — practice_possible false и короткое notice ученику. "
                        "Не подменяй тему другим кодом и не клади в code шаги установки."
                    ),
                },
                {"role": "user", "content": prompt},
            ]

            raw_response = self.make_api_request(
                messages=messages,
                temperature=0.35,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )

            examples_data = self._parse_and_validate(raw_response)

            self.save_debug_response(
                "examples",
                prompt,
                json.dumps({"examples": examples_data}, ensure_ascii=False, indent=2),
                {
                    "lesson_title": lesson_title,
                    "lesson_description": lesson_description,
                    "keywords": keywords_str,
                    "communication_style": communication_style,
                    "course_subject": course_subject,
                    "raw_llm_response": raw_response[:2000],
                },
            )

            if is_examples_notice(examples_data):
                self.logger.info(
                    "По уроку нет исполняемого примера: %s",
                    examples_data["notice"],
                )
            else:
                self.logger.info(
                    "Примеры по теме '%s' сгенерированы (%s шт.)",
                    course_subject,
                    len(examples_data),
                )
            return examples_data

        except Exception as e:
            self.logger.exception("Критическая ошибка при генерации примеров")
            cause = str(e.__cause__ or e)
            if "401" in cause or "invalid_api_key" in cause or "Incorrect API key" in cause:
                raise Exception(
                    "Модель отклонила ключ доступа. Если на дашборде меняли маршрут, "
                    "перезапустите ядро и откройте урок заново."
                ) from e
            raise Exception(
                "Не получилось запросить примеры у модели. Повторите попытку."
            ) from e

    def generate_examples(
        self,
        lesson_data,
        lesson_content,
        communication_style="friendly",
        course_context=None,
    ) -> str:
        """Возвращает примеры в виде HTML (для обратной совместимости).

        Внутри использует generate_examples_data и рендерит финальный HTML.
        Никакого обратного парсинга HTML не происходит.
        """
        examples_data = self.generate_examples_data(
            lesson_data=lesson_data,
            lesson_content=lesson_content,
            communication_style=communication_style,
            course_context=course_context,
        )
        if is_examples_notice(examples_data):
            import html as html_lib

            return f"<p>{html_lib.escape(examples_data['notice'])}</p>"
        return render_examples_json_to_html({"examples": examples_data})

    def _parse_and_validate(self, response: str) -> List[Dict[str, str]]:
        """Парсит JSON-ответ LLM, валидирует и нормализует. Возвращает list[dict]."""
        payload = parse_examples_json_response(response)
        return interpret_examples_payload(payload)

    def _determine_course_subject(
        self, course_context, lesson_content, lesson_keywords, lesson_data=None
    ):
        """Предметная область для примеров — только запросом к LLM."""
        from control_task_llm_judge import classify_lesson_subject

        del lesson_keywords  # больше не используем keyword-эвристики
        lesson_data = lesson_data or {}
        return classify_lesson_subject(
            self,
            lesson_title=str(lesson_data.get("title") or ""),
            lesson_content=lesson_content or "",
            course_context=course_context,
        )

    def _apply_visible_styles(self, examples, communication_style):
        """
        Применяет видимые стили к примерам.

        Args:
            examples (str): Сгенерированные примеры
            communication_style (str): Стиль общения

        Returns:
            str: Примеры с примененными стилями
        """
        try:
            # Получаем префикс стиля
            utils = ContentUtils()
            prefix = utils.get_style_prefix(communication_style, "examples")

            # ИСПРАВЛЕНО: ВИДИМЫЕ CSS стили вместо контрастных черных блоков
            visible_css = """
            <style>
            .examples-visible {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 16px;
                line-height: 1.4;
                padding: 20px;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 10px;
                margin: 15px 0;
                border-left: 4px solid #28a745;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .examples-visible h1, .examples-visible h2, .examples-visible h3, .examples-visible h4 {
                color: #495057;
                margin-top: 15px;
                margin-bottom: 8px;
                line-height: 1.2;
                border-bottom: 2px solid #28a745;
                padding-bottom: 4px;
            }
            .examples-visible h1 { font-size: 20px; }
            .examples-visible h2 { font-size: 18px; }
            .examples-visible h3 { font-size: 17px; }
            .examples-visible h4 { font-size: 16px; }
            .examples-visible p {
                margin-bottom: 8px;
                line-height: 1.3;
                text-align: justify;
            }
            .examples-visible ul, .examples-visible ol {
                margin-bottom: 10px;
                padding-left: 25px;
                line-height: 1.3;
            }
            .examples-visible li {
                margin-bottom: 4px;
            }
            .examples-visible code {
                background-color: #f8f9fa;
                color: #d63384;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                font-weight: 600;
                border: 1px solid #dee2e6;
            }
            .examples-visible pre {
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
                white-space: pre;
            }
            .examples-visible pre code {
                background: none;
                color: inherit;
                padding: 0;
                font-size: inherit;
                border: none;
            }
            .examples-visible .example-block {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
                margin: 10px 0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .examples-visible strong {
                color: #495057;
                font-weight: 600;
            }
            .examples-visible em {
                color: #6c757d;
                font-style: italic;
            }
            </style>
            <div class="examples-visible">
            """

            return f"{visible_css}{prefix}{examples}</div>"

        except Exception as e:
            self.logger.error(f"Ошибка при применении стилей к примерам: {str(e)}")
            return examples

    def _build_enhanced_examples_prompt(
        self,
        lesson_title,
        lesson_description,
        keywords_str,
        lesson_content,
        communication_style,
        course_subject,
    ):
        """
        ИСПРАВЛЕНО: Создает улучшенный промпт для генерации примеров с учетом предметной области.

        Args:
            lesson_title (str): Название урока
            lesson_description (str): Описание урока
            keywords_str (str): Ключевые слова урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения
            course_subject (str): Предметная область курса

        Returns:
            str: Промпт для API
        """
        style_description = ContentUtils.COMMUNICATION_STYLES.get(
            communication_style, ContentUtils.COMMUNICATION_STYLES["friendly"]
        )

        from learning_prompt_context import (
            lesson_context_block,
            practice_runtime_rules_ru,
        )

        return f"""
Создай 3 практических примера СТРОГО по материалу урока «{lesson_title}».
Предметная область курса (контекст): {course_subject}.
Каждый пример показывает только приём из этого урока. Не добирай число примерами из других занятий.

Название урока: {lesson_title}
Описание урока: {lesson_description}
Ключевые слова: {keywords_str}

{practice_runtime_rules_ru()}
{lesson_context_block(lesson_content)}

Стиль пояснений: {style_description}

КРИТИЧЕСКИ ВАЖНО:
1. Сначала реши, можно ли по ЭТОМУ уроку показать код, который ученик запускает в редакторе TeachAI, не меняя тему урока.
2. Если нельзя (урок про установку, кнопки программы, действия вне редактора) — "practice_possible": false, в "notice" 1–2 предложения ученику почему примера нет, "examples": [].
3. Если можно — "practice_possible": true и примеры. Поле code — только Python по этому уроку. Без команд терминала, без пошаговых инструкций в code.
4. ЗАПРЕЩЕНО писать заглушки: «в этом примере мы создадим», «здесь мы создадим».
5. Поле description — в настоящем времени и про этот пример.
6. Без внешних файлов и без input(). Библиотеки — только те, что уже есть в тексте урока.
7. Если в уроке есть случайные данные, зафиксируй seed.

Формат ответа — ТОЛЬКО JSON:
{{
  "practice_possible": true,
  "notice": "",
  "examples": [
    {{
      "title": "Краткий заголовок примера 1",
      "description": "1-2 предложения: что делает код в этом уроке.",
      "code": "import ...\\n\\n# рабочий код\\nprint(...)"
    }},
    {{
      "title": "Пример 2",
      "description": "...",
      "code": "..."
    }},
    {{
      "title": "Пример 3",
      "description": "...",
      "code": "..."
    }}
  ]
}}

Поле "code" — только Python этого урока, без markdown, без HTML и без команд терминала.
"""
