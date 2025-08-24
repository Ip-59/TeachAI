"""
Утилиты для работы с примерами.
Вынесены из examples_generator.py для улучшения модульности.
"""

import logging
from content_utils import ContentUtils


class ExamplesUtils:
    """Утилиты для работы с примерами."""

    def __init__(self):
        """Инициализация утилит."""
        self.logger = logging.getLogger(__name__)
        self.content_utils = ContentUtils()

    def determine_course_subject(self, course_context, lesson_content, lesson_keywords):
        """
        Определяет предметную область курса для обеспечения релевантности примеров.

        Args:
            course_context (dict): Контекст курса
            lesson_content (str): Содержание урока
            lesson_keywords (list): Ключевые слова урока

        Returns:
            str: Предметная область курса
        """
        try:
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
                    "for ",
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

        except Exception as e:
            self.logger.error(f"Ошибка при определении предметной области: {str(e)}")
            return "программирование на Python"

    def validate_examples_relevance(self, examples, course_subject):
        """
        Проверяет релевантность сгенерированных примеров предметной области.

        Args:
            examples (str): Сгенерированные примеры
            course_subject (str): Предметная область курса

        Returns:
            bool: True если примеры релевантны, иначе False
        """
        try:
            examples_lower = examples.lower()

            # Проверяем на наличие нерелевантных технологий
            irrelevant_patterns = [
                "html",
                "<html>",
                "<head>",
                "<body>",
                "<div>",
                "<script>",
                "javascript",
                "css",
                "var ",
                "document.",
                "function(",
                "onclick",
                "onload",
                "jquery",
                "$(",
                "java ",
                "c++",
                "c#",
                "php",
                "ruby",
                "go ",
            ]

            # Если найдены нерелевантные паттерны
            for pattern in irrelevant_patterns:
                if pattern in examples_lower:
                    self.logger.warning(f"Найден нерелевантный паттерн: {pattern}")
                    return False

            # Проверяем наличие релевантных Python паттернов
            if "python" in course_subject.lower():
                relevant_patterns = [
                    "python",
                    "def ",
                    "import ",
                    "print(",
                    "if __name__",
                    "for ",
                    "while ",
                    "class ",
                    "return ",
                    "# ",
                    ".py",
                    "список",
                    "словарь",
                    "кортеж",
                ]

                has_relevant = any(
                    pattern in examples_lower for pattern in relevant_patterns
                )
                if not has_relevant:
                    self.logger.warning("Не найдено релевантных Python паттернов")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Ошибка при проверке релевантности примеров: {str(e)}")
            return True  # В случае ошибки считаем релевантными

    def create_fallback_python_example(self, lesson_title):
        """
        Создает базовый Python пример в случае сбоя генерации.

        Args:
            lesson_title (str): Название урока

        Returns:
            str: Базовый Python пример
        """
        try:
            return f"""
            <h3>Базовый пример Python по теме: {lesson_title}</h3>
            <p>Вот простой пример, демонстрирующий основные концепции Python:</p>
            <pre><code># Пример Python кода
print("Изучаем тему: {lesson_title}")

# Переменные
название_урока = "{lesson_title}"
изучено = True

# Условная конструкция
if изучено:
    print(f"Урок '{{название_урока}}' изучен!")
else:
    print("Продолжайте изучение")

# Функция
def показать_прогресс(урок):
    return f"Прогресс по уроку: {{урок}}"

результат = показать_прогресс(название_урока)
print(результат)</code></pre>
            <p>Этот пример демонстрирует базовые элементы Python: переменные, условия, функции и вывод.</p>
            """
        except Exception as e:
            self.logger.error(f"Ошибка при создании базового примера: {str(e)}")
            return "<p>Ошибка при создании примера</p>"

    def apply_visible_styles(self, examples, communication_style):
        """
        Применяет ВИДИМЫЕ стили к примерам.

        Args:
            examples (str): Исходные примеры
            communication_style (str): Стиль общения

        Returns:
            str: Стилизованные примеры
        """
        try:
            # Получаем префикс в зависимости от стиля общения
            prefix = self.content_utils.get_style_prefix(
                communication_style, "examples"
            )

            # ВИДИМЫЕ CSS стили вместо контрастных черных блоков
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
            self.logger.error(f"Ошибка при применении стилей: {str(e)}")
            return examples  # Возвращаем без стилей в случае ошибки

    def build_enhanced_examples_prompt(
        self,
        lesson_title,
        lesson_description,
        keywords_str,
        lesson_content,
        communication_style,
        course_subject,
    ):
        """
        Создает улучшенный промпт для генерации примеров с учетом предметной области.

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
        try:
            style_description = ContentUtils.COMMUNICATION_STYLES.get(
                communication_style, ContentUtils.COMMUNICATION_STYLES["friendly"]
            )

            return f"""
            Создай практические примеры СТРОГО по теме "{course_subject}" для следующего урока:

            Название урока: {lesson_title}
            Описание урока: {lesson_description}
            Ключевые слова: {keywords_str}
            Предметная область: {course_subject}

            Содержание урока (для понимания контекста):
            {lesson_content[:2000]}

            Стиль общения: {style_description}

            КРИТИЧЕСКИ ВАЖНЫЕ ТРЕБОВАНИЯ:
            1. ВСЕ примеры должны быть ТОЛЬКО на Python - никаких других языков!
            2. НЕ ИСПОЛЬЗУЙ HTML, JavaScript, CSS, Java, C++ или любые другие языки
            3. Каждый пример должен содержать исполняемый Python код
            4. Примеры должны иллюстрировать концепции именно из данного урока
            5. Показывай практическое применение изученного материала
            6. Используй Python синтаксис: def, import, print(), if, for, while, class, etc.

            Генерируй разнообразные примеры:
            1. Простые примеры для начинающих
            2. Средние примеры с пояснениями
            3. Практические применения
            4. Избегай частых ошибок

            СТРОГО ЗАПРЕЩЕНО:
            - HTML теги (html, head, body, div, script, etc.)
            - JavaScript код (var, function, document, onclick, etc.)
            - CSS стили и свойства
            - Любые языки программирования кроме Python

            Используй ТОЛЬКО HTML для форматирования ответа:
            - <h3> для заголовков примеров
            - <pre><code> для Python кода
            - <p> для объяснений
            - <div class="example-block"> для группировки примеров

            Каждый пример должен быть самодостаточным и исполняемым в Python.
            """

        except Exception as e:
            self.logger.error(f"Ошибка при создании промпта: {str(e)}")
            return f"Создай примеры Python для урока: {lesson_title}"
