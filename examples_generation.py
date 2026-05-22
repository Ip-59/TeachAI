"""
Модуль для генерации практических примеров по материалам уроков.
Отвечает за создание конкретных примеров кода, задач и практических упражнений.
ИСПРАВЛЕНО: Видимые примеры кода вместо черных блоков
ИСПРАВЛЕНО: Строгий контроль релевантности примеров теме курса (проблема #88)
"""

from content_utils import BaseContentGenerator, ContentUtils
from examples_html_utils import (
    normalize_markdown_fences_to_html,
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

    def generate_examples(
        self,
        lesson_data,
        lesson_content,
        communication_style="friendly",
        course_context=None,
    ):
        """
        ИСПРАВЛЕНО: Генерирует практические примеры строго по материалу урока и теме курса.

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
            # Проверяем наличие необходимых ключей в lesson_data
            lesson_title = lesson_data.get("title", "Урок")
            lesson_description = lesson_data.get("description", "Нет описания")
            lesson_keywords = lesson_data.get("keywords", [])

            # Преобразуем keywords в строку, если это список
            keywords_str = (
                ", ".join(lesson_keywords)
                if isinstance(lesson_keywords, list)
                else str(lesson_keywords)
            )

            # НОВОЕ: Определяем контекст курса и предметную область
            course_subject = self._determine_course_subject(
                course_context, lesson_content, lesson_keywords
            )

            prompt = self._build_enhanced_examples_prompt(
                lesson_title,
                lesson_description,
                keywords_str,
                lesson_content,
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

            examples = self.make_api_request(
                messages=messages,
                temperature=0.35,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )

            examples_html = self._parse_and_render_examples(examples)

            # Очищаем от возможных markdown меток (fallback для старого формата)
            examples_html = normalize_markdown_fences_to_html(examples_html)
            examples_html = self.clean_markdown_code_blocks(examples_html)

            # Сохраняем отладочную информацию
            self.save_debug_response(
                "examples",
                prompt,
                examples_html,
                {
                    "lesson_title": lesson_title,
                    "lesson_description": lesson_description,
                    "keywords": keywords_str,
                    "communication_style": communication_style,
                    "course_subject": course_subject,
                    "raw_llm_response": examples[:2000],
                },
            )

            self.logger.info(
                f"Примеры по теме '{course_subject}' успешно сгенерированы"
            )
            return examples_html

        except Exception as e:
            self.logger.error(f"Критическая ошибка при генерации примеров: {str(e)}")
            raise Exception(f"Не удалось сгенерировать примеры: {str(e)}")

    def _parse_and_render_examples(self, response: str) -> str:
        """Парсит JSON-ответ LLM и рендерит HTML с блоками кода."""
        payload = parse_examples_json_response(response)
        validate_examples_payload(payload, min_examples=3)
        normalized = normalize_examples_payload(payload)
        html_output = render_examples_json_to_html(normalized)
        if not html_output.strip():
            raise ValueError("LLM вернул примеры без исполняемого кода")
        return html_output

    def _determine_course_subject(
        self, course_context, lesson_content, lesson_keywords
    ):
        """
        НОВОЕ: Определяет предметную область курса для обеспечения релевантности примеров.

        Args:
            course_context (dict): Контекст курса
            lesson_content (str): Содержание урока
            lesson_keywords (list): Ключевые слова урока

        Returns:
            str: Предметная область курса
        """
        # Если передан контекст курса
        if course_context and isinstance(course_context, dict):
            course_title = course_context.get("course_title", "").lower()
            if "python" in course_title:
                return "программирование на Python"
            elif "анализ данных" in course_title or "data" in course_title:
                return "анализ данных с Python"
            elif (
                "машинное обучение" in course_title
                or "machine learning" in course_title
            ):
                return "машинное обучение с Python"
            elif "веб" in course_title or "web" in course_title:
                return "веб-разработка на Python"
            elif "финанс" in course_title:
                return "программирование на Python для финансов"

        # Анализируем содержание урока
        content_lower = lesson_content.lower()
        if any(
            keyword in content_lower
            for keyword in [
                "python",
                "def ",
                "import ",
                "print(",
                "list",
                "dict",
                "for i in",
            ]
        ):
            return "программирование на Python"
        elif any(
            keyword in content_lower
            for keyword in ["pandas", "numpy", "matplotlib", "dataframe"]
        ):
            return "анализ данных с Python"
        elif any(
            keyword in content_lower
            for keyword in ["sklearn", "tensorflow", "keras", "модель", "алгоритм"]
        ):
            return "машинное обучение с Python"
        elif any(
            keyword in content_lower
            for keyword in ["flask", "django", "api", "веб", "сайт"]
        ):
            return "веб-разработка на Python"

        # Анализируем ключевые слова
        if isinstance(lesson_keywords, list):
            keywords_str = " ".join(lesson_keywords).lower()
            if "python" in keywords_str:
                return "программирование на Python"

        # По умолчанию
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
            # Очищаем лишние отступы в коде
            examples = self._clean_code_indentation(examples)
            
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
                line-height: 1.05;
                border: 2px solid #dee2e6;
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

    def _clean_code_indentation(self, examples):
        """
        НОВЫЙ МЕТОД: Очищает лишние отступы в блоках кода.
        
        Args:
            examples (str): HTML с примерами кода
            
        Returns:
            str: HTML с очищенными отступами в коде
        """
        try:
            import re
            
            # Находим все блоки кода <pre><code>...</code></pre>
            code_pattern = r'<pre><code>(.*?)</code></pre>'
            
            def clean_code_block(match):
                code_content = match.group(1)
                
                # Разбиваем на строки
                lines = code_content.split('\n')
                
                # Находим минимальный отступ среди строк С ОТСТУПАМИ (исключая строки без отступов)
                min_indent = float('inf')
                lines_with_indent = []
                
                for line in lines:
                    if line.strip():  # Пропускаем пустые строки
                        indent = len(line) - len(line.lstrip())
                        
                        if indent > 0:  # Только строки с отступами
                            lines_with_indent.append(indent)
                            if indent < min_indent:
                                min_indent = indent
                
                # Если есть строки с отступами, убираем минимальный отступ
                if min_indent > 0 and min_indent != float('inf'):
                    cleaned_lines = []
                    for line in lines:
                        if line.strip():  # Для непустых строк
                            if len(line) - len(line.lstrip()) > 0:  # Если есть отступ
                                cleaned_line = line[min_indent:]
                                cleaned_lines.append(cleaned_line)
                            else:  # Если отступа нет, оставляем как есть
                                cleaned_lines.append(line)
                        else:  # Пустые строки оставляем как есть
                            cleaned_lines.append('')
                    code_content = '\n'.join(cleaned_lines)
                    self.logger.debug(f"Очищены отступы в блоке кода (минимальный отступ: {min_indent})")
                else:
                    self.logger.debug("Отступы не найдены или не требуют очистки")
                
                return f'<pre><code>{code_content}</code></pre>'
            
            # Применяем очистку ко всем блокам кода
            cleaned_examples = re.sub(code_pattern, clean_code_block, examples, flags=re.DOTALL)
            
            self.logger.info("Отступы в коде успешно очищены")
            return cleaned_examples
            
        except Exception as e:
            self.logger.error(f"Ошибка при очистке отступов в коде: {str(e)}")
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
Создай РОВНО 3 практических примера на Python для урока по теме "{course_subject}".

Название урока: {lesson_title}
Описание урока: {lesson_description}
Ключевые слова: {keywords_str}

Содержание урока:
{lesson_content[:3000]}

Стиль пояснений: {style_description}

КРИТИЧЕСКИ ВАЖНО:
1. Каждый пример — это РЕАЛЬНЫЙ исполняемый Python-код в поле "code" (минимум 5 строк кода).
2. ЗАПРЕЩЕНО писать заглушки: «в этом примере мы создадим», «здесь мы создадим».
3. Поле description — в настоящем времени: «Создаёт переменные…», «Суммирует список…».
4. Код должен работать при запуске (без внешних файлов, без input()).
5. Примеры должны иллюстрировать концепции ИМЕННО из lesson_content выше.
6. Для ML-уроков: random_state=42, правильные импорты sklearn (from sklearn.datasets import ...).
7. НЕ используй pd.read_csv(), open('file.txt') и другие внешние файлы.

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
