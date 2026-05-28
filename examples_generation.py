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
    normalize_examples_payload,
    parse_examples_json_response,
    render_examples_json_to_html,
    validate_examples_payload,
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

            content_for_prompt = self.prepare_lesson_text_for_analysis(
                lesson_content,
                course_context=course_context,
                max_chars=6000,
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
                        "Генерируешь ТОЛЬКО JSON с массивом examples. "
                        "Каждый example обязан содержать поле code с рабочим Python-кодом."
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

            self.logger.info(
                f"Примеры по теме '{course_subject}' успешно сгенерированы ({len(examples_data)} шт.)"
            )
            return examples_data

        except Exception as e:
            self.logger.error(f"Критическая ошибка при генерации примеров: {str(e)}")
            raise Exception(f"Не удалось сгенерировать примеры: {str(e)}")

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
        return render_examples_json_to_html({"examples": examples_data})

    def _parse_and_validate(self, response: str) -> List[Dict[str, str]]:
        """Парсит JSON-ответ LLM, валидирует и нормализует. Возвращает list[dict]."""
        payload = parse_examples_json_response(response)
        validate_examples_payload(payload, min_examples=3)
        normalized = normalize_examples_payload(payload)
        examples = normalized.get("examples", [])
        if not examples:
            raise ValueError("LLM вернул примеры без исполняемого кода")
        return examples

    def _determine_course_subject(
        self, course_context, lesson_content, lesson_keywords, lesson_data=None
    ):
        """Определяет предметную область для примеров по текущему уроку.

        Приоритет: метаданные урока → тело урока → название курса.
        """
        lesson_data = lesson_data or {}
        lesson_title = lesson_data.get("title", "").lower()
        lesson_description = lesson_data.get("description", "").lower()
        topic_title = ""
        if course_context and isinstance(course_context, dict):
            topic_title = course_context.get("topic_title", "").lower()

        keywords_str = ""
        if isinstance(lesson_keywords, list):
            keywords_str = " ".join(str(k) for k in lesson_keywords).lower()
        elif lesson_keywords:
            keywords_str = str(lesson_keywords).lower()

        lesson_signals = " ".join(
            [lesson_title, lesson_description, topic_title, keywords_str]
        )

        def _match_subject(text: str):
            text = text.lower()
            ml_markers = [
                "sklearn",
                "scikit",
                "tensorflow",
                "keras",
                "нейрон",
                "классификац",
                "регресс",
                "машинн",
                "machine learning",
                "mnist",
                "iris",
                "библиотек",
            ]
            data_markers = [
                "pandas",
                "numpy",
                "matplotlib",
                "dataframe",
                "анализ данных",
                "data analysis",
                "визуализац",
            ]
            web_markers = ["flask", "django", "fastapi", "веб", "web", "api", "сайт"]
            basics_markers = [
                "основы python",
                "синтаксис",
                "переменн",
                "цикл",
                "список",
                "словар",
                "функци",
                "условн",
                "тип данных",
                "print(",
                "def ",
            ]

            if any(m in text for m in ml_markers):
                return "машинное обучение с Python"
            if any(m in text for m in data_markers):
                return "анализ данных с Python"
            if any(m in text for m in web_markers):
                return "веб-разработка на Python"
            if any(m in text for m in basics_markers):
                return "программирование на Python"
            return None

        subject = _match_subject(lesson_signals)
        if subject:
            return subject

        content_lower = (lesson_content or "").lower()
        subject = _match_subject(content_lower)
        if subject:
            return subject

        if course_context and isinstance(course_context, dict):
            course_title = course_context.get("course_title", "").lower()
            subject = _match_subject(course_title)
            if subject:
                return subject
            if "финанс" in course_title:
                return "программирование на Python для финансов"

        return "программирование на Python"

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

        return f"""
Создай РОВНО 3 практических примера на Python СТРОГО по материалу урока «{lesson_title}».
Предметная область курса (контекст): {course_subject}.
Примеры должны иллюстрировать ТОЛЬКО то, что разбирается в этом уроке, а не другие темы курса.

Название урока: {lesson_title}
Описание урока: {lesson_description}
Ключевые слова: {keywords_str}

Содержание урока:
{lesson_content}

Стиль пояснений: {style_description}

КРИТИЧЕСКИ ВАЖНО:
1. Каждый пример — это РЕАЛЬНЫЙ исполняемый Python-код в поле "code" (минимум 5 строк кода).
2. ЗАПРЕЩЕНО писать заглушки: «в этом примере мы создадим», «здесь мы создадим».
3. Поле description — в настоящем времени: «Создаёт переменные…», «Суммирует список…».
4. Код должен работать при запуске (без внешних файлов, без input()).
5. Примеры должны иллюстрировать концепции ИМЕННО из lesson_content выше.
6. Для ML-уроков: random_state=42, импорты sklearn (from sklearn.datasets import load_iris).
7. НЕ используй make_classification с n_features меньше 5 — лучше load_iris().
8. Для TensorFlow/Keras — только простой Sequential; если сомневаешься, используй sklearn.neural_network.MLPClassifier.
9. НЕ используй pd.read_csv(), open('file.txt') и другие внешние файлы.

Формат ответа — ТОЛЬКО JSON:
{{
  "examples": [
    {{
      "title": "Краткий заголовок примера 1",
      "description": "1-2 предложения: что делает код и зачем это для ML/Python.",
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

Поле "code" обязательно в каждом примере. Без markdown, без HTML — только чистый Python-код в JSON-строке.
"""
