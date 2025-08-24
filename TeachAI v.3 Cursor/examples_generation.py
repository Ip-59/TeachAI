"""
Модуль для генерации практических примеров по материалам уроков.
Отвечает за создание конкретных примеров кода, задач и практических упражнений.
ИСПРАВЛЕНО: Видимые примеры кода вместо черных блоков
ИСПРАВЛЕНО: Строгий контроль релевантности примеров теме курса (проблема #88)
"""

from content_utils import BaseContentGenerator, ContentUtils


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
                    "content": f"Ты - опытный преподаватель в области {course_subject}. СТРОГО генерируй примеры ТОЛЬКО по этой предметной области, НЕ отклоняйся от темы курса.",
                },
                {"role": "user", "content": prompt},
            ]

            examples = self.make_api_request(
                messages=messages,
                temperature=0.5,  # Снижаем для более точного следования теме
                max_tokens=3500,
            )

            # Очищаем от возможных markdown меток
            examples = self.clean_markdown_code_blocks(examples)

            # Сохраняем отладочную информацию
            self.save_debug_response(
                "examples",
                prompt,
                examples,
                {
                    "lesson_title": lesson_title,
                    "lesson_description": lesson_description,
                    "keywords": keywords_str,
                    "communication_style": communication_style,
                    "course_subject": course_subject,
                },
            )

            # Применяем ВИДИМЫЕ стили для примеров
            styled_examples = self._apply_visible_styles(examples, communication_style)

            self.logger.info(
                f"Примеры по теме '{course_subject}' успешно сгенерированы"
            )
            return styled_examples

        except Exception as e:
            self.logger.error(f"Критическая ошибка при генерации примеров: {str(e)}")
            raise Exception(f"Не удалось сгенерировать примеры: {str(e)}")

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
        ИСПРАВЛЕННЫЙ МЕТОД: Умно исправляет отступы в Python коде.
        
        Args:
            examples (str): HTML с примерами кода
            
        Returns:
            str: HTML с правильно отформатированным кодом
        """
        try:
            import re
            
            # Ищем все блоки <pre><code> и исправляем отступы
            def fix_code_indentation(code_block):
                lines = code_block.split('\n')
                fixed_lines = []
                current_indent_level = 0
                in_function = False
                
                # Проверяем, есть ли в коде функции
                has_functions = any('def ' in line or 'class ' in line for line in lines)
                
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    
                    if stripped.startswith('def ') or stripped.startswith('class '):
                        # Определение функции/класса - сбрасываем уровень отступа
                        current_indent_level = 0
                        in_function = True
                        fixed_lines.append(stripped)  # Убираем все лишние пробелы
                    elif stripped.startswith('if ') or stripped.startswith('elif ') or stripped.startswith('else:') or stripped.startswith('for ') or stripped.startswith('while ') or stripped.startswith('try:') or stripped.startswith('except') or stripped.startswith('finally:') or stripped.startswith('with '):
                        # Условные конструкции - увеличиваем уровень отступа
                        current_indent_level += 1
                        fixed_lines.append(stripped)  # Убираем все лишние пробелы
                    elif stripped.startswith('print(') or stripped.startswith('return ') or stripped.startswith('break') or stripped.startswith('continue') or stripped.startswith('pass') or stripped.startswith('raise '):
                        # Команды, которые должны быть в блоке - добавляем правильный отступ
                        if in_function or current_indent_level > 0 or has_functions:
                            indent = '    ' * (current_indent_level + 1)
                            fixed_lines.append(indent + stripped)
                        else:
                            fixed_lines.append(stripped)
                    elif stripped.startswith('import ') or stripped.startswith('from '):
                        # Импорты - НЕ должны иметь отступы, они на уровне модуля
                        fixed_lines.append(stripped)  # Убираем все лишние пробелы
                    elif stripped.startswith('#') or stripped == '':
                        # Комментарии и пустые строки - оставляем как есть
                        fixed_lines.append(stripped)
                    elif stripped.startswith('X,') or stripped.startswith('y,') or stripped.startswith('X_train,') or stripped.startswith('y_train,') or stripped.startswith('clf =') or stripped.startswith('clf.fit(') or stripped.startswith('y_pred =') or stripped.startswith('accuracy ='):
                        # Команды, которые должны быть в блоке - добавляем правильный отступ
                        if in_function or current_indent_level > 0 or has_functions:
                            indent = '    ' * (current_indent_level + 1)
                            fixed_lines.append(indent + stripped)
                        else:
                            fixed_lines.append(stripped)
                    else:
                        # Остальные строки - проверяем, нужен ли отступ
                        # Вызовы функций на уровне модуля НЕ должны иметь отступы
                        if stripped.endswith('()') and not (in_function or current_indent_level > 0):
                            # Вызов функции на уровне модуля
                            fixed_lines.append(stripped)
                        elif stripped.startswith('machine_learning_') or stripped.startswith('ml_') or stripped.startswith('test_'):
                            # Вызовы конкретных функций - НЕ должны иметь отступы
                            fixed_lines.append(stripped)
                        elif (in_function or current_indent_level > 0 or has_functions) and not stripped.startswith('#'):
                            # Если мы в блоке, добавляем отступ
                            indent = '    ' * (current_indent_level + 1)
                            fixed_lines.append(indent + stripped)
                        else:
                            # Если на уровне модуля, убираем лишние пробелы
                            fixed_lines.append(stripped)
                
                return '\n'.join(fixed_lines)
            
            # Применяем исправление ко всем блокам кода
            pattern = r'<pre><code>([\s\S]*?)</code></pre>'
            
            def replace_code_block(match):
                code_content = match.group(1)
                fixed_code = fix_code_indentation(code_content)
                return f'<pre><code>{fixed_code}</code></pre>'
            
            fixed_examples = re.sub(pattern, replace_code_block, examples)
            
            self.logger.info("Отступы в коде умно исправлены")
            return fixed_examples
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке кода: {str(e)}")
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

        prompt_template = """
Создай практические примеры СТРОГО по теме "{course_subject}" для следующего урока:

Название урока: {lesson_title}
Описание урока: {lesson_description}
Ключевые слова: {keywords_str}
Предметная область: {course_subject}

Содержание урока (для понимания контекста):
{lesson_content}

Стиль общения: {style_description}

КРИТИЧЕСКИ ВАЖНЫЕ ТРЕБОВАНИЯ:
1. ВСЕ примеры должны быть ТОЛЬКО на Python - никаких других языков!
2. НЕ ИСПОЛЬЗУЙ HTML, JavaScript, CSS, Java, C++ или любые другие языки
3. Каждый пример должен содержать исполняемый Python код
4. Примеры должны иллюстрировать концепции именно из данного урока
5. Показывай практическое применение изученного материала
6. Используй Python синтаксис: def, import, print(), if, for, while, class, etc.

ФОРМАТИРОВАНИЕ КОДА (КРИТИЧЕСКИ ВАЖНО - Python требует правильные отступы!):
- ОБЯЗАТЕЛЬНО: используй правильные отступы для определения блоков кода
- ОБЯЗАТЕЛЬНО: тело функции должно иметь отступ (обычно 4 пробела)
- ОБЯЗАТЕЛЬНО: вложенные блоки (if, for, while) должны иметь больший отступ
- ОБЯЗАТЕЛЬНО: все строки в одном блоке должны иметь одинаковый отступ

- НЕ добавляй лишние пробелы в начале строк, которые не являются кодом
- НЕ используй неправильные отступы (например, 3 пробела вместо 4)
- НЕ смешивай табы и пробелы

🚨 КРИТИЧЕСКИ ВАЖНО - БЕЗ ОТСТУПОВ КОД НЕ РАБОТАЕТ! 🚨
- Каждая строка в теле функции ДОЛЖНА начинаться с 4 пробелов
- Каждая строка в условном блоке ДОЛЖНА начинаться с 4 пробелов
- Каждая строка в цикле ДОЛЖНА начинаться с 4 пробелов
- Импорты НЕ должны иметь отступы - они на уровне модуля!
- Без этого Python выдаст IndentationError и код не выполнится!

📋 СТРУКТУРА ОТСТУПОВ:
- Уровень 0 (модуль): import, from, def, class, вызовы функций
- Уровень 1 (4 пробела): тело функции, тело класса, тело условия
- Уровень 2 (8 пробелов): вложенные блоки
- Уровень 3 (12 пробелов): глубоко вложенные блоки

ПРИМЕРЫ ПРАВИЛЬНОГО ФОРМАТИРОВАНИЯ:
```python
# ✅ ПРАВИЛЬНО - с правильными отступами Python (4 пробела!)
def example_function():
    print("Это правильный код с отступами")
    if True:
        print("Это тоже правильно - вложенный блок")
        for i in range(3):
            print(f"Отступ: {{i}}")

# ✅ ПРАВИЛЬНО - функция с комментариями
def machine_learning_definition():
    print("Машинное обучение - это область ИИ")
    print("которая позволяет компьютерам учиться")
    return "Определение выведено"

# ❌ НЕПРАВИЛЬНО - без отступов (вызовет IndentationError!)
def example_function():
print("Это неправильно - нет отступа")
if True:
print("Это тоже неправильно")

# ❌ НЕПРАВИЛЬНО - неправильные отступы (вызовет IndentationError!)
def example_function():
  print("Это неправильно - только 2 пробела")
   print("Это неправильно - 3 пробела")
```

🚨 ПОМНИ: В Python отступы ОБЯЗАТЕЛЬНЫ для определения блоков кода! 🚨
- Без правильных отступов код НЕ ВЫПОЛНИТСЯ и выдаст IndentationError
- Каждая строка в блоке ДОЛЖНА иметь одинаковый отступ (4 пробела)
- Это НЕ просто стиль - это требование синтаксиса Python!

ИМПОРТЫ (КРИТИЧЕСКИ ВАЖНО - ЗАПРЕЩЕНО ИСПОЛЬЗОВАТЬ НЕПРАВИЛЬНЫЕ ИМПОРТЫ):
- СТРОГО ЗАПРЕЩЕНО: from sklearn import datasets (это вызовет NameError!)
- СТРОГО ЗАПРЕЩЕНО: from sklearn import model_selection (это вызовет NameError!)
- СТРОГО ЗАПРЕЩЕНО: from sklearn import ensemble (это вызовет NameError!)

- ВМЕСТО ЭТОГО используй ТОЛЬКО правильные импорты:
  * from sklearn.datasets import load_iris, make_classification, make_regression
  * from sklearn.model_selection import train_test_split, cross_val_score
  * from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
  * from sklearn.linear_model import LinearRegression, LogisticRegression
  * from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
  * from sklearn.cluster import KMeans, DBSCAN

- Если используешь pandas - добавь: import pandas as pd
- Если используешь numpy - добавь: import numpy as np
- Если используешь matplotlib - добавь: import matplotlib.pyplot as plt

- НЕ используй функции без импорта - это вызовет NameError!
- НЕ используй сокращения типа 'datasets' - всегда указывай полный путь!

ДАННЫЕ (КРИТИЧЕСКИ ВАЖНО - ЗАПРЕЩЕНО ИСПОЛЬЗОВАТЬ ВНЕШНИЕ ФАЙЛЫ):
- СТРОГО ЗАПРЕЩЕНО: pd.read_csv('data.csv'), pd.read_excel('file.xlsx'), open('file.txt')
- СТРОГО ЗАПРЕЩЕНО: любые пути к файлам, которые могут не существовать
- СТРОГО ЗАПРЕЩЕНО: загрузка данных из внешних источников

- ВМЕСТО ЭТОГО используй ТОЛЬКО:
  * numpy.random для генерации случайных данных
  * sklearn.datasets для встроенных датасетов
  * pandas.DataFrame для создания таблиц
  * Встроенные возможности Python для создания тестовых данных

ПРИМЕРЫ ПРАВИЛЬНОЙ ГЕНЕРАЦИИ ДАННЫХ:
```python
# ✅ ПРАВИЛЬНО - генерация данных
import numpy as np
import pandas as pd

# Создание случайных данных
np.random.seed(42)
n_samples = 1000
feature1 = np.random.randn(n_samples) * 2 + 5
feature2 = np.random.randn(n_samples) * 1.5 + 3
y = 2 * feature1 + 1.5 * feature2 + np.random.randn(n_samples) * 0.5

# Создание DataFrame
data = pd.DataFrame({{
    'feature1': feature1,
    'feature2': feature2,
    'target': y
}})

# ✅ ПРАВИЛЬНО - встроенные датасеты sklearn
from sklearn.datasets import load_iris, make_classification
iris = load_iris()
X, y = make_classification(n_samples=1000, n_features=20)
```

ПРИМЕРЫ НЕПРАВИЛЬНОЙ ЗАГРУЗКИ ДАННЫХ (СТРОГО ЗАПРЕЩЕНО):
```python
# ❌ ЗАПРЕЩЕНО - внешние файлы
data = pd.read_csv('data.csv')           # FileNotFoundError!
data = pd.read_excel('dataset.xlsx')     # FileNotFoundError!
data = pd.read_json('data.json')         # FileNotFoundError!
with open('data.txt', 'r') as f:         # FileNotFoundError!
    data = f.read()

# ❌ ЗАПРЕЩЕНО - неправильные импорты
from sklearn import datasets              # NameError!
from sklearn import model_selection      # NameError!
from sklearn import ensemble             # NameError!
```

ПРИОРИТЕТ ПРИМЕРОВ:
1. **Встроенные возможности Python** (без внешних библиотек) - ВЫСШИЙ ПРИОРИТЕТ
2. **Стандартная библиотека Python** (os, sys, datetime, json, etc.)
3. **Популярные библиотеки** (если нужны) - добавляй инструкции по установке

ПРАВИЛА ДЛЯ ВНЕШНИХ БИБЛИОТЕК:
- Если используешь sklearn, pandas, numpy, matplotlib - добавляй в начало примера:
  "# Для работы примера установите: pip install scikit-learn pandas numpy matplotlib"
- Предпочитай встроенные возможности Python
- Создавай альтернативные примеры без внешних зависимостей

Генерируй разнообразные примеры:
1. Простые примеры для начинающих (только Python)
2. Средние примеры с пояснениями
3. Практические применения
4. Избегай частых ошибок

СТРОГО ЗАПРЕЩЕНО:
- HTML теги (html, head, body, div, script, etc.)
- JavaScript код (var, function, document, onclick, etc.)
- CSS стили и свойства
- Любые языки программирования кроме Python
- **НЕПРАВИЛЬНЫЕ ОТСТУПЫ (например, 3 пробела вместо 4, смешивание табов и пробелов)**
- **ОТСУТСТВИЕ ОТСТУПОВ в блоках кода (вызовет IndentationError!)**
- Использование функций без импорта (NameError)
- Загрузка внешних файлов (FileNotFoundError)
- Использование несуществующих путей к файлам
- Использование сокращений типа 'datasets' вместо 'sklearn.datasets'
- pd.read_csv(), pd.read_excel(), open() с внешними файлами
- from sklearn import datasets, from sklearn import model_selection, from sklearn import ensemble

**КРИТИЧЕСКИ ВАЖНО - ОТСТУПЫ В КОДЕ:**
- ОБЯЗАТЕЛЬНО используй правильные отступы для блоков кода
- ОБЯЗАТЕЛЬНО тело функции должно иметь отступ (4 пробела)
- ОБЯЗАТЕЛЬНО вложенные блоки должны иметь больший отступ
- Это критически важно для выполнения кода!

Используй ТОЛЬКО HTML для форматирования ответа:
- <h3> для заголовков примеров
- <pre><code> для Python кода (с правильными отступами!)
- <p> для объяснений
- <div class="example-block"> для группировки примеров

Каждый пример должен быть самодостаточным и исполняемым в Python.
"""
        
        return prompt_template.format(
            course_subject=course_subject,
            lesson_title=lesson_title,
            lesson_description=lesson_description,
            keywords_str=keywords_str,
            lesson_content=lesson_content[:2000],
            style_description=style_description
        )
