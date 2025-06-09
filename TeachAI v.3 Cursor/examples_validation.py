"""
Модуль для валидации и повторной генерации практических примеров.
Отвечает за проверку релевантности примеров и их повторную генерацию при необходимости.
ИСПРАВЛЕНО: Строгий контроль релевантности примеров теме курса (проблема #88)
"""

from content_utils import BaseContentGenerator


class ExamplesValidation(BaseContentGenerator):
    """Валидатор и генератор повторных примеров."""

    def __init__(self, api_key):
        """
        Инициализация валидатора примеров.

        Args:
            api_key (str): API ключ OpenAI
        """
        super().__init__(api_key)
        self.logger.info("ExamplesValidation инициализирован")

    def validate_examples_relevance(self, examples, course_subject):
        """
        НОВОЕ: Проверяет релевантность сгенерированных примеров предметной области.

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

    def regenerate_with_strict_prompt(
        self,
        lesson_title,
        lesson_description,
        keywords_str,
        lesson_content,
        communication_style,
        course_subject,
    ):
        """
        НОВОЕ: Повторная генерация с более строгим промптом.

        Returns:
            str: Примеры с повышенной релевантностью
        """
        try:
            strict_prompt = f"""
            КРИТИЧЕСКИ ВАЖНО: Создай примеры СТРОГО по теме "{course_subject}".

            Урок: {lesson_title}
            Описание: {lesson_description}
            Ключевые слова: {keywords_str}

            Содержание урока (первые 1500 символов):
            {lesson_content[:1500]}

            СТРОЖАЙШИЕ ТРЕБОВАНИЯ:
            1. ВСЕ примеры должны быть ТОЛЬКО на Python
            2. НЕ ИСПОЛЬЗУЙ HTML, JavaScript, CSS или другие языки
            3. Каждый пример должен содержать Python код
            4. Показывай практическое применение концепций из урока
            5. Все примеры должны быть исполняемыми Python скриптами
            6. Используй синтаксис Python: def, import, print(), if, for, while, class

            ЗАПРЕЩЕНО:
            - HTML теги (<html>, <body>, <script>, etc.)
            - JavaScript код (var, function, document., etc.)
            - CSS стили
            - Любые языки кроме Python

            Формат: HTML с <h3> заголовками, <pre><code> для Python кода, <p> для объяснений.
            """

            messages = [
                {
                    "role": "system",
                    "content": f"Ты - эксперт по {course_subject}. Генерируй ТОЛЬКО Python примеры, НИКАКИХ других языков программирования.",
                },
                {"role": "user", "content": strict_prompt},
            ]

            examples = self.make_api_request(
                messages=messages,
                temperature=0.3,  # Еще более низкая температура для точности
                max_tokens=3000,
            )

            # Очищаем от markdown
            examples = self.clean_markdown_code_blocks(examples)

            self.logger.info("Повторная генерация с строгим промптом завершена")
            return examples

        except Exception as e:
            self.logger.error(f"Ошибка при повторной генерации: {str(e)}")
            # Возвращаем базовый пример Python
            return self._create_fallback_python_example(lesson_title)

    def _create_fallback_python_example(self, lesson_title):
        """
        НОВОЕ: Создает базовый Python пример в случае сбоя генерации.

        Args:
            lesson_title (str): Название урока

        Returns:
            str: Базовый Python пример
        """
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

    def validate_and_regenerate_if_needed(
        self,
        examples,
        course_subject,
        lesson_title,
        lesson_description,
        keywords_str,
        lesson_content,
        communication_style,
    ):
        """
        Проверяет релевантность примеров и при необходимости выполняет повторную генерацию.

        Args:
            examples (str): Исходные примеры
            course_subject (str): Предметная область курса
            lesson_title (str): Название урока
            lesson_description (str): Описание урока
            keywords_str (str): Ключевые слова урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения

        Returns:
            str: Валидные примеры (исходные или повторно сгенерированные)
        """
        # Проверяем релевантность
        if not self.validate_examples_relevance(examples, course_subject):
            self.logger.warning(
                "Сгенерированные примеры не прошли проверку релевантности, повторная генерация..."
            )
            # Повторная генерация с более строгим промптом
            examples = self.regenerate_with_strict_prompt(
                lesson_title,
                lesson_description,
                keywords_str,
                lesson_content,
                communication_style,
                course_subject,
            )

            # Проверяем повторно сгенерированные примеры
            if not self.validate_examples_relevance(examples, course_subject):
                self.logger.error(
                    "Повторная генерация не дала релевантных примеров, используем fallback"
                )
                examples = self._create_fallback_python_example(lesson_title)

        return examples
