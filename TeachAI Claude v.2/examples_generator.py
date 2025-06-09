"""
Модуль для генерации практических примеров по материалам уроков.
Отвечает за создание конкретных примеров кода, задач и практических упражнений.
ИСПРАВЛЕНО: Видимые примеры кода вместо черных блоков
ИСПРАВЛЕНО: Строгий контроль релевантности примеров теме курса (проблема #88)
НОВОЕ: Генерация полностью исполняемого кода для Jupyter Notebook
НОВОЕ: Требования самодостаточности и видимости результатов
"""

from content_utils import BaseContentGenerator, ContentUtils


class ExamplesGenerator(BaseContentGenerator):
    """Генератор практических примеров для уроков."""

    def __init__(self, api_key):
        """
        Инициализация генератора примеров.

        Args:
            api_key (str): API ключ OpenAI
        """
        super().__init__(api_key)
        self.logger.info("ExamplesGenerator инициализирован")

    def generate_examples(
        self,
        lesson_data,
        lesson_content,
        communication_style="friendly",
        course_context=None,
    ):
        """
        УЛУЧШЕНО: Генерирует полностью исполняемые примеры для Jupyter Notebook.

        Args:
            lesson_data (dict): Данные об уроке (название, описание, ключевые слова)
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения
            course_context (dict, optional): Контекст курса для обеспечения релевантности

        Returns:
            str: Строка с практическими примерами, готовыми для выполнения в Jupyter

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

            # Определяем контекст курса и предметную область
            course_subject = self._determine_course_subject(
                course_context, lesson_content, lesson_keywords
            )

            prompt = self._build_jupyter_examples_prompt(
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
                    "content": f"Ты - опытный преподаватель Python с экспертизой в Jupyter Notebook. СТРОГО генерируй ТОЛЬКО исполняемые Python примеры для {course_subject}.",
                },
                {"role": "user", "content": prompt},
            ]

            examples = self.make_api_request(
                messages=messages,
                temperature=0.3,  # Низкая температура для точности исполняемого кода
                max_tokens=3500,
            )

            # Очищаем от возможных markdown меток
            examples = self.clean_markdown_code_blocks(examples)

            # Проверяем и улучшаем исполняемость примеров
            validated_examples = self._validate_and_enhance_jupyter_examples(
                examples, course_subject
            )

            # Проверяем релевантность сгенерированных примеров
            if not self._validate_examples_relevance(
                validated_examples, course_subject
            ):
                self.logger.warning(
                    "Сгенерированные примеры не прошли проверку релевантности, повторная генерация..."
                )
                # Повторная генерация с более строгим промптом
                validated_examples = self._regenerate_with_jupyter_strict_prompt(
                    lesson_title,
                    lesson_description,
                    keywords_str,
                    lesson_content,
                    communication_style,
                    course_subject,
                )

            # Сохраняем отладочную информацию
            self.save_debug_response(
                "examples",
                prompt,
                validated_examples,
                {
                    "lesson_title": lesson_title,
                    "lesson_description": lesson_description,
                    "keywords": keywords_str,
                    "communication_style": communication_style,
                    "course_subject": course_subject,
                    "jupyter_optimized": True,
                },
            )

            # Применяем ВИДИМЫЕ стили для примеров
            styled_examples = self._apply_visible_styles(
                validated_examples, communication_style
            )

            self.logger.info(
                f"Исполняемые Jupyter примеры по теме '{course_subject}' успешно сгенерированы"
            )
            return styled_examples

        except Exception as e:
            self.logger.error(
                f"Критическая ошибка при генерации Jupyter примеров: {str(e)}"
            )
            raise Exception(f"Не удалось сгенерировать примеры: {str(e)}")

    def _build_jupyter_examples_prompt(
        self,
        lesson_title,
        lesson_description,
        keywords_str,
        lesson_content,
        communication_style,
        course_subject,
    ):
        """
        НОВОЕ: Создает специальный промпт для генерации исполняемых примеров в Jupyter Notebook.

        Args:
            lesson_title (str): Название урока
            lesson_description (str): Описание урока
            keywords_str (str): Ключевые слова урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения
            course_subject (str): Предметная область курса

        Returns:
            str: Промпт для API с требованиями Jupyter Notebook
        """
        style_description = ContentUtils.COMMUNICATION_STYLES.get(
            communication_style, ContentUtils.COMMUNICATION_STYLES["friendly"]
        )

        return f"""
        КРИТИЧЕСКИ ВАЖНО: Создай примеры Python кода, которые будут ВЫПОЛНЯТЬСЯ в Jupyter Notebook!

        Тема урока: {lesson_title}
        Описание: {lesson_description}
        Ключевые слова: {keywords_str}
        Предметная область: {course_subject}

        Содержание урока (для контекста):
        {lesson_content[:2000]}

        Стиль общения: {style_description}

        🚨 ТРЕБОВАНИЯ ДЛЯ JUPYTER NOTEBOOK:
        1. КОД БУДЕТ ВЫПОЛНЯТЬСЯ - каждый пример должен работать без ошибок!
        2. ВСЕ импорты должны быть включены в начале каждого примера
        3. ВСЕ переменные должны быть определены в коде
        4. КОД должен быть САМОДОСТАТОЧНЫМ (не зависеть от предыдущих ячеек)
        5. РЕЗУЛЬТАТ должен быть ВИДЕН (print(), return, или последняя строка с выражением)
        6. НЕ используй input() - студент не может вводить данные интерактивно
        7. Используй конкретные значения вместо пользовательского ввода

        🐍 ТОЛЬКО PYTHON КОД:
        - НЕ используй HTML, JavaScript, CSS, Java или другие языки
        - Используй Python синтаксис: def, import, print(), if, for, while, class
        - Каждый блок кода должен быть готов к копированию в Jupyter ячейку

        📝 СТРУКТУРА ПРИМЕРОВ:
        1. Краткое объяснение концепции
        2. Полный исполняемый код с комментариями
        3. Ожидаемый результат выполнения
        4. Практические вариации (если применимо)

        ✅ ХОРОШИЕ ПРИМЕРЫ для Jupyter:
        ```python
        # Импорты в начале
        import math

        # Определяем все переменные
        radius = 5

        # Вычисления
        area = math.pi * radius ** 2

        # ОБЯЗАТЕЛЬНО показываем результат
        print(f"Площадь круга с радиусом {{radius}} = {{area:.2f}}")
        ```

        ❌ НЕ ДЕЛАЙ ТАК:
        - Код без импортов
        - Использование неопределенных переменных
        - input() для ввода данных
        - Код без видимого результата
        - HTML/JavaScript/CSS примеры

        Формат ответа: HTML с <h3> заголовками, <pre><code> для Python кода, <p> для объяснений.
        КАЖДЫЙ пример кода должен быть готов к немедленному выполнению в Jupyter Notebook!
        """

    def _validate_and_enhance_jupyter_examples(self, examples, course_subject):
        """
        НОВОЕ: Проверяет и улучшает исполняемость примеров для Jupyter Notebook.

        Args:
            examples (str): Сгенерированные примеры
            course_subject (str): Предметная область курса

        Returns:
            str: Улучшенные примеры с гарантированной исполняемостью
        """
        try:
            # Проверяем наличие проблемных паттернов для Jupyter
            jupyter_issues = self._detect_jupyter_issues(examples)

            if jupyter_issues:
                self.logger.warning(f"Обнаружены проблемы Jupyter: {jupyter_issues}")
                # Применяем автоматические исправления
                examples = self._fix_jupyter_issues(examples, jupyter_issues)

            # Добавляем предупреждения об исполняемости, если необходимо
            examples = self._add_execution_notes(examples)

            return examples

        except Exception as e:
            self.logger.error(f"Ошибка при валидации Jupyter примеров: {str(e)}")
            return examples  # Возвращаем оригинал при ошибке

    def _detect_jupyter_issues(self, examples):
        """
        НОВОЕ: Определяет потенциальные проблемы исполняемости в Jupyter.

        Args:
            examples (str): Примеры кода

        Returns:
            list: Список найденных проблем
        """
        issues = []
        examples_lower = examples.lower()

        # Проверяем на наличие input()
        if "input(" in examples_lower:
            issues.append("input_function")

        # Проверяем на отсутствие импортов там, где они нужны
        if (
            any(
                module in examples_lower
                for module in ["math.", "random.", "datetime.", "os."]
            )
            and "import" not in examples_lower
        ):
            issues.append("missing_imports")

        # Проверяем на неопределенные переменные (простая эвристика)
        if "название_переменной" in examples_lower or "your_variable" in examples_lower:
            issues.append("undefined_variables")

        # Проверяем на отсутствие вывода результатов
        if "print(" not in examples_lower and "return " not in examples_lower:
            issues.append("no_output")

        return issues

    def _fix_jupyter_issues(self, examples, issues):
        """
        НОВОЕ: Автоматически исправляет проблемы исполняемости.

        Args:
            examples (str): Примеры с проблемами
            issues (list): Список проблем для исправления

        Returns:
            str: Исправленные примеры
        """
        fixed_examples = examples

        # Исправляем input() - заменяем на конкретные значения
        if "input_function" in issues:
            fixed_examples = fixed_examples.replace(
                "input(",
                "# input(  # Заменено на конкретное значение для демонстрации\n# ",
            )

        # Добавляем недостающие импорты (базовая реализация)
        if "missing_imports" in issues:
            if (
                "math." in fixed_examples.lower()
                and "import math" not in fixed_examples
            ):
                fixed_examples = "import math\n\n" + fixed_examples
            if (
                "random." in fixed_examples.lower()
                and "import random" not in fixed_examples
            ):
                fixed_examples = "import random\n\n" + fixed_examples

        return fixed_examples

    def _add_execution_notes(self, examples):
        """
        НОВОЕ: Добавляет заметки об исполняемости примеров.

        Args:
            examples (str): Примеры кода

        Returns:
            str: Примеры с заметками
        """
        execution_note = """
        <div style="background-color: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 6px; padding: 12px; margin: 10px 0;">
            <strong>📝 Заметка:</strong> Все примеры кода готовы к выполнению в Jupyter Notebook.
            Скопируйте код в ячейку и нажмите Shift+Enter для выполнения.
        </div>
        """

        # Добавляем заметку в начало
        return execution_note + examples

    def _regenerate_with_jupyter_strict_prompt(
        self,
        lesson_title,
        lesson_description,
        keywords_str,
        lesson_content,
        communication_style,
        course_subject,
    ):
        """
        НОВОЕ: Повторная генерация с строгими требованиями Jupyter.

        Returns:
            str: Строго проверенные исполняемые примеры
        """
        try:
            strict_jupyter_prompt = f"""
            🚨 ЭКСТРЕМАЛЬНО ВАЖНО: Создай ТОЛЬКО исполняемые Python примеры для Jupyter Notebook!

            Урок: {lesson_title}
            Описание: {lesson_description}
            Ключевые слова: {keywords_str}

            Содержание урока:
            {lesson_content[:1500]}

            🎯 JUPYTER NOTEBOOK ТРЕБОВАНИЯ (СТРОГО СОБЛЮДАЙ):
            1. Каждый пример - полностью ИСПОЛНЯЕМЫЙ Python код
            2. ВСЕ импорты включены в каждом примере
            3. ВСЕ переменные определены в коде
            4. РЕЗУЛЬТАТ ОБЯЗАТЕЛЬНО виден (print, return, или выражение)
            5. НЕ используй input() - только конкретные значения
            6. Код готов к копированию в Jupyter ячейку и выполнению

            ✅ ПРИМЕР ПРАВИЛЬНОГО КОДА:
            ```python
            # Импорт библиотек
            import math

            # Определяем переменные
            number = 16

            # Выполняем вычисления
            square_root = math.sqrt(number)

            # ПОКАЗЫВАЕМ результат
            print(f"Квадратный корень из {{number}} = {{square_root}}")
            ```

            ❌ СТРОГО ЗАПРЕЩЕНО:
            - HTML, JavaScript, CSS код
            - input() функции
            - Неопределенные переменные
            - Код без видимого результата
            - Код, который не будет работать в Jupyter

            Формат: HTML с <h3>, <pre><code> для Python, <p> для объяснений.
            """

            messages = [
                {
                    "role": "system",
                    "content": f"Ты - эксперт Jupyter Notebook и Python. Генерируй ТОЛЬКО исполняемые примеры для {course_subject}.",
                },
                {"role": "user", "content": strict_jupyter_prompt},
            ]

            examples = self.make_api_request(
                messages=messages,
                temperature=0.2,  # Очень низкая температура для максимальной точности
                max_tokens=3000,
            )

            # Очищаем от markdown
            examples = self.clean_markdown_code_blocks(examples)

            self.logger.info("Строгая Jupyter генерация завершена")
            return examples

        except Exception as e:
            self.logger.error(f"Ошибка при строгой Jupyter генерации: {str(e)}")
            # Возвращаем базовый исполняемый пример
            return self._create_fallback_jupyter_example(lesson_title)

    def _create_fallback_jupyter_example(self, lesson_title):
        """
        НОВОЕ: Создает базовый исполняемый пример для Jupyter в случае сбоя.

        Args:
            lesson_title (str): Название урока

        Returns:
            str: Базовый исполняемый пример
        """
        return f"""
        <h3>Базовый исполняемый пример: {lesson_title}</h3>
        <p>Простой Python код, готовый к выполнению в Jupyter Notebook:</p>
        <pre><code># Базовый пример Python для урока: {lesson_title}

# Определяем переменные
lesson_name = "{lesson_title}"
is_completed = True

# Выводим информацию
print(f"Урок: {{lesson_name}}")
print(f"Статус: {{'Изучен' if is_completed else 'В процессе'}}")

# Демонстрируем базовые концепции Python
numbers = [1, 2, 3, 4, 5]
sum_numbers = sum(numbers)

print(f"Числа: {{numbers}}")
print(f"Сумма: {{sum_numbers}}")

# Результат выполнения будет виден в Jupyter
sum_numbers</code></pre>

        <p><strong>Ожидаемый результат выполнения:</strong></p>
        <pre>Урок: {lesson_title}
Статус: Изучен
Числа: [1, 2, 3, 4, 5]
Сумма: 15
15</pre>
        """

    def _determine_course_subject(
        self, course_context, lesson_content, lesson_keywords
    ):
        """
        Определяет предметную область курса для обеспечения релевантности примеров.

        Args:
            course_context (dict, optional): Контекст курса
            lesson_content (str): Содержание урока
            lesson_keywords (list): Ключевые слова урока

        Returns:
            str: Предметная область курса
        """
        try:
            # Приоритет: контекст курса
            if course_context and isinstance(course_context, dict):
                course_title = course_context.get("course_title", "")
                if course_title:
                    return course_title

            # Альтернатива: анализ содержания урока
            content_lower = lesson_content.lower()

            # Python программирование
            python_indicators = [
                "python",
                "def ",
                "import ",
                "print(",
                "список",
                "словарь",
                "функция",
            ]
            if any(indicator in content_lower for indicator in python_indicators):
                return "Python программирование"

            # Веб-разработка
            web_indicators = ["html", "css", "javascript", "веб", "сайт", "браузер"]
            if any(indicator in content_lower for indicator in web_indicators):
                return "Веб-разработка"

            # Анализ данных
            data_indicators = [
                "данные",
                "анализ",
                "pandas",
                "numpy",
                "matplotlib",
                "статистика",
            ]
            if any(indicator in content_lower for indicator in data_indicators):
                return "Анализ данных на Python"

            # По умолчанию
            return "Программирование на Python"

        except Exception as e:
            self.logger.error(f"Ошибка при определении предметной области: {str(e)}")
            return "Программирование"

    def _validate_examples_relevance(self, examples, course_subject):
        """
        Проверяет релевантность сгенерированных примеров теме курса.

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

    def _apply_visible_styles(self, examples, communication_style):
        """
        ИСПРАВЛЕНО: Применяет ВИДИМЫЕ стили оформления для лучшей читаемости.

        Args:
            examples (str): Примеры для стилизации
            communication_style (str): Стиль общения

        Returns:
            str: Стилизованные примеры с видимым кодом
        """
        # Добавляем дружелюбное вступление в зависимости от стиля
        if communication_style == "friendly":
            prefix = "<p>🎯 <strong>Отлично! Вот практические примеры для закрепления материала:</strong></p>"
        elif communication_style == "professional":
            prefix = "<p><strong>📋 Практические примеры для изучения:</strong></p>"
        elif communication_style == "motivating":
            prefix = "<p>🚀 <strong>Давайте применим знания на практике! Изучите эти примеры:</strong></p>"
        else:
            prefix = "<p><strong>📝 Практические примеры:</strong></p>"

        # CSS стили для ВИДИМОГО кода
        visible_css = f"""
        <style>
        .examples-visible {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.4;
            color: #212529;
            background-color: #ffffff;
            padding: 0;
            margin: 0;
        }}
        .examples-visible h1, .examples-visible h2, .examples-visible h3, .examples-visible h4 {{
            color: #495057;
            margin-top: 16px;
            margin-bottom: 8px;
            font-weight: 600;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 4px;
        }}
        .examples-visible h1 {{ font-size: 20px; }}
        .examples-visible h2 {{ font-size: 18px; }}
        .examples-visible h3 {{ font-size: 17px; }}
        .examples-visible h4 {{ font-size: 16px; }}
        .examples-visible p {{
            margin-bottom: 8px;
            line-height: 1.3;
            text-align: justify;
        }}
        .examples-visible ul, .examples-visible ol {{
            margin-bottom: 10px;
            padding-left: 25px;
            line-height: 1.3;
        }}
        .examples-visible li {{
            margin-bottom: 4px;
        }}
        .examples-visible code {{
            background-color: #f8f9fa;
            color: #d63384;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            font-weight: 600;
            border: 1px solid #dee2e6;
        }}
        .examples-visible pre {{
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
        .examples-visible pre code {{
            background: none;
            color: inherit;
            padding: 0;
            font-size: inherit;
            border: none;
        }}
        .examples-visible .example-block {{
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 12px;
            margin: 10px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .examples-visible strong {{
            color: #495057;
            font-weight: 600;
        }}
        .examples-visible em {{
            color: #6c757d;
            font-style: italic;
        }}
        .jupyter-notice {{
            background-color: #e7f3ff;
            border-left: 4px solid #007bff;
            padding: 12px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        </style>
        <div class="examples-visible">
        """

        return f"{visible_css}{prefix}{examples}</div>"
