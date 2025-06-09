"""
Модуль для генерации контрольных заданий по материалам уроков.
Отвечает за создание интерактивных заданий для выполнения в Jupiter Notebook ячейках.
НОВОЕ: Анализ содержимого урока для определения количества и типов заданий
НОВОЕ: Генерация заданий различных типов: функции, алгоритмы, структуры данных
НОВОЕ: Адаптивное количество заданий на основе изученных концепций
"""

from content_utils import BaseContentGenerator, ContentUtils
import re
import logging
from typing import List, Dict, Tuple, Optional


class ControlTasksGenerator(BaseContentGenerator):
    """Генератор контрольных заданий для уроков."""

    def __init__(self, api_key):
        """
        Инициализация генератора контрольных заданий.

        Args:
            api_key (str): API ключ OpenAI
        """
        super().__init__(api_key)
        self.logger.info("ControlTasksGenerator инициализирован")

        # Типы заданий и их приоритеты
        self.task_types = {
            "function_creation": {
                "name": "Создание функции",
                "priority": 1,
                "keywords": ["def ", "function", "функция", "return"],
                "description": "Задание на создание функции",
            },
            "algorithm_implementation": {
                "name": "Реализация алгоритма",
                "priority": 2,
                "keywords": [
                    "алгоритм",
                    "сортировка",
                    "поиск",
                    "цикл",
                    "for ",
                    "while ",
                ],
                "description": "Задание на реализацию алгоритма",
            },
            "data_structures": {
                "name": "Работа со структурами данных",
                "priority": 3,
                "keywords": ["список", "словарь", "кортеж", "list", "dict", "tuple"],
                "description": "Задание на работу со структурами данных",
            },
            "object_oriented": {
                "name": "Объектно-ориентированное программирование",
                "priority": 4,
                "keywords": ["class ", "объект", "метод", "__init__", "self."],
                "description": "Задание на ОOP",
            },
            "string_processing": {
                "name": "Обработка строк",
                "priority": 5,
                "keywords": [
                    "строка",
                    "string",
                    "текст",
                    ".split(",
                    ".join(",
                    ".replace(",
                ],
                "description": "Задание на обработку строк",
            },
            "mathematical_operations": {
                "name": "Математические операции",
                "priority": 6,
                "keywords": [
                    "математика",
                    "вычисление",
                    "формула",
                    "math.",
                    "сумма",
                    "произведение",
                ],
                "description": "Задание на математические вычисления",
            },
        }

    def generate_control_tasks(
        self,
        lesson_data: Dict,
        lesson_content: str,
        communication_style: str = "friendly",
        course_context: Dict = None,
    ) -> List[Dict]:
        """
        ОСНОВНОЙ МЕТОД: Генерирует контрольные задания по материалу урока.

        Args:
            lesson_data (dict): Данные об уроке
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения
            course_context (dict, optional): Контекст курса

        Returns:
            List[Dict]: Список заданий для контрольных работ

        Raises:
            Exception: Если не удалось сгенерировать задания
        """
        try:
            self.logger.info("Начинаем генерацию контрольных заданий")

            # Проверяем, нужны ли контрольные задания для этого урока
            if not self._is_practical_lesson(lesson_content):
                self.logger.info(
                    "Урок определен как теоретический, контрольные задания не нужны"
                )
                return []

            # Анализируем содержание урока
            lesson_analysis = self._analyze_lesson_content(lesson_content)

            # Определяем количество и типы заданий
            task_requirements = self._determine_task_requirements(
                lesson_analysis, lesson_data
            )

            if not task_requirements:
                self.logger.info("Концепции для контрольных заданий не найдены")
                return []

            # Генерируем задания для каждого требования
            control_tasks = []
            for i, requirement in enumerate(task_requirements):
                try:
                    task = self._generate_single_task(
                        requirement,
                        lesson_data,
                        lesson_content,
                        communication_style,
                        course_context,
                        i + 1,
                    )
                    if task:
                        control_tasks.append(task)
                        self.logger.debug(f"Сгенерировано задание: {task['title']}")

                except Exception as task_error:
                    self.logger.error(
                        f"Ошибка генерации задания {i+1}: {str(task_error)}"
                    )
                    continue

            if not control_tasks:
                self.logger.warning("Не удалось сгенерировать ни одного задания")
                # Создаем базовое задание
                control_tasks = [
                    self._create_fallback_task(lesson_data, communication_style)
                ]

            self.logger.info(
                f"Успешно сгенерировано {len(control_tasks)} контрольных заданий"
            )
            return control_tasks

        except Exception as e:
            self.logger.error(
                f"Критическая ошибка при генерации контрольных заданий: {str(e)}"
            )
            raise Exception(f"Не удалось сгенерировать контрольные задания: {str(e)}")

    def _is_practical_lesson(self, lesson_content: str) -> bool:
        """
        Определяет, является ли урок практическим (требует контрольных заданий).

        Args:
            lesson_content (str): Содержание урока

        Returns:
            bool: True если урок практический
        """
        content_lower = lesson_content.lower()

        # Индикаторы практического урока
        practical_indicators = [
            "def ",
            "class ",
            "for ",
            "while ",
            "if ",
            "import ",
            "print(",
            "=",
            "return",
            "функция",
            "метод",
            "алгоритм",
            "код",
            "программа",
            "реализация",
            "пример",
        ]

        # Индикаторы теоретического урока
        theoretical_indicators = [
            "введение",
            "что такое",
            "определение",
            "история",
            "теория",
            "концепция",
            "понятие",
            "обзор",
        ]

        practical_score = sum(
            1 for indicator in practical_indicators if indicator in content_lower
        )
        theoretical_score = sum(
            1 for indicator in theoretical_indicators if indicator in content_lower
        )

        # Урок считается практическим, если практических индикаторов больше
        return practical_score > theoretical_score

    def _analyze_lesson_content(self, lesson_content: str) -> Dict[str, any]:
        """
        Анализирует содержание урока для определения типов заданий.

        Args:
            lesson_content (str): Содержание урока

        Returns:
            Dict: Анализ содержания урока
        """
        analysis = {
            "detected_concepts": [],
            "code_blocks_count": 0,
            "complexity_level": "basic",
            "main_topics": [],
        }

        content_lower = lesson_content.lower()

        # Подсчитываем блоки кода
        code_blocks = re.findall(
            r"<pre><code.*?</code></pre>", lesson_content, re.DOTALL
        )
        analysis["code_blocks_count"] = len(code_blocks)

        # Определяем концепции
        for task_type, info in self.task_types.items():
            for keyword in info["keywords"]:
                if keyword in content_lower:
                    analysis["detected_concepts"].append(
                        {
                            "type": task_type,
                            "name": info["name"],
                            "priority": info["priority"],
                            "keyword": keyword,
                        }
                    )
                    break

        # Сортируем концепции по приоритету
        analysis["detected_concepts"].sort(key=lambda x: x["priority"])

        # Определяем уровень сложности
        if any(
            indicator in content_lower
            for indicator in ["class ", "__init__", "наследование"]
        ):
            analysis["complexity_level"] = "advanced"
        elif any(
            indicator in content_lower for indicator in ["def ", "функция", "алгоритм"]
        ):
            analysis["complexity_level"] = "intermediate"
        else:
            analysis["complexity_level"] = "basic"

        # Извлекаем основные темы
        analysis["main_topics"] = self._extract_main_topics(lesson_content)

        return analysis

    def _extract_main_topics(self, lesson_content: str) -> List[str]:
        """
        Извлекает основные темы из содержания урока.

        Args:
            lesson_content (str): Содержание урока

        Returns:
            List[str]: Список основных тем
        """
        topics = []

        # Ищем заголовки
        headers = re.findall(
            r"<h[2-4][^>]*>(.*?)</h[2-4]>", lesson_content, re.IGNORECASE
        )
        for header in headers:
            # Удаляем HTML теги
            clean_header = re.sub(r"<[^>]+>", "", header).strip()
            if clean_header and len(clean_header) < 100:
                topics.append(clean_header)

        # Ограничиваем количество тем
        return topics[:5]

    def _determine_task_requirements(
        self, lesson_analysis: Dict, lesson_data: Dict
    ) -> List[Dict]:
        """
        Определяет количество и типы заданий на основе анализа урока.

        Args:
            lesson_analysis (Dict): Анализ содержания урока
            lesson_data (Dict): Метаданные урока

        Returns:
            List[Dict]: Требования к заданиям
        """
        requirements = []
        detected_concepts = lesson_analysis["detected_concepts"]

        if not detected_concepts:
            # Если концепции не обнаружены, создаем базовое задание
            requirements.append(
                {
                    "type": "mathematical_operations",
                    "name": "Базовое задание",
                    "description": "Простое задание по материалу урока",
                }
            )
            return requirements

        # Ограничиваем количество заданий (максимум 3)
        max_tasks = min(3, len(detected_concepts))

        for i in range(max_tasks):
            concept = detected_concepts[i]
            requirements.append(
                {
                    "type": concept["type"],
                    "name": concept["name"],
                    "description": self.task_types[concept["type"]]["description"],
                    "priority": concept["priority"],
                }
            )

        return requirements

    def _generate_single_task(
        self,
        requirement: Dict,
        lesson_data: Dict,
        lesson_content: str,
        communication_style: str,
        course_context: Dict,
        task_number: int,
    ) -> Dict:
        """
        Генерирует одно контрольное задание.

        Args:
            requirement (Dict): Требования к заданию
            lesson_data (Dict): Данные урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения
            course_context (Dict): Контекст курса
            task_number (int): Номер задания

        Returns:
            Dict: Данные контрольного задания
        """
        try:
            # Получаем информацию о курсе
            course_subject = self._determine_course_subject(
                course_context, lesson_content
            )
            lesson_title = lesson_data.get("title", "Урок")

            # Создаем промпт для генерации задания
            prompt = self._build_task_generation_prompt(
                requirement,
                lesson_title,
                lesson_content,
                communication_style,
                course_subject,
                task_number,
            )

            messages = [
                {
                    "role": "system",
                    "content": f"Ты - опытный преподаватель {course_subject}. Создавай ТОЛЬКО практические задания на Python для Jupiter Notebook.",
                },
                {"role": "user", "content": prompt},
            ]

            # Генерируем задание
            task_response = self.make_api_request(
                messages=messages,
                temperature=0.4,  # Умеренная креативность для разнообразия заданий
                max_tokens=2000,
            )

            # Парсим ответ
            parsed_task = self._parse_task_response(
                task_response, requirement, task_number
            )

            # Валидируем задание
            if self._validate_task(parsed_task):
                return parsed_task
            else:
                self.logger.warning(f"Задание {task_number} не прошло валидацию")
                return None

        except Exception as e:
            self.logger.error(f"Ошибка генерации задания {task_number}: {str(e)}")
            return None

    def _build_task_generation_prompt(
        self,
        requirement: Dict,
        lesson_title: str,
        lesson_content: str,
        communication_style: str,
        course_subject: str,
        task_number: int,
    ) -> str:
        """
        Создает промпт для генерации контрольного задания.

        Returns:
            str: Промпт для API
        """
        style_description = ContentUtils.COMMUNICATION_STYLES.get(
            communication_style, ContentUtils.COMMUNICATION_STYLES["friendly"]
        )

        return f"""
        ВАЖНО: Создай контрольное задание для выполнения в Jupiter Notebook!

        Контекст урока:
        - Название урока: {lesson_title}
        - Предметная область: {course_subject}
        - Тип задания: {requirement['name']}
        - Номер задания: {task_number}

        Содержание урока (для понимания контекста):
        {lesson_content[:2000]}

        Стиль общения: {style_description}

        🎯 ТРЕБОВАНИЯ К ЗАДАНИЮ:
        1. Задание должно быть ПРАКТИЧЕСКИМ - студент пишет код
        2. Код должен быть ИСПОЛНЯЕМЫМ в Jupiter Notebook
        3. Задание проверяет понимание концепций из урока
        4. Сложность соответствует уровню урока
        5. Задание имеет ЧЕТКОЕ условие и ПРОВЕРЯЕМЫЙ результат

        📝 СТРУКТУРА ЗАДАНИЯ:
        1. TITLE: Краткое название задания (до 60 символов)
        2. DESCRIPTION: Подробное описание задания и требований
        3. INITIAL_CODE: Начальный код-шаблон для студента (если нужен)
        4. EXPECTED_RESULT: Ожидаемый результат выполнения
        5. CHECK_TYPE: Тип проверки ('exact', 'function', 'list', 'numeric', 'output')
        6. HINTS: Подсказки для студента (опционально)

        🐍 ПРИМЕРЫ ХОРОШИХ ЗАДАНИЙ:

        Для функций:
        TITLE: Создайте функцию для вычисления факториала
        DESCRIPTION: Напишите функцию factorial(n), которая возвращает факториал числа n
        INITIAL_CODE: def factorial(n):\n    # Ваш код здесь\n    pass\n\nfactorial
        EXPECTED_RESULT: function
        CHECK_TYPE: function

        Для структур данных:
        TITLE: Найдите максимальный элемент в списке
        DESCRIPTION: Создайте список чисел и найдите максимальный элемент без использования max()
        INITIAL_CODE: numbers = [3, 7, 2, 9, 1]\n# Ваш код здесь\nmax_number =
        EXPECTED_RESULT: 9
        CHECK_TYPE: exact

        ✅ ОБЯЗАТЕЛЬНЫЕ ТРЕБОВАНИЯ:
        - Код должен быть готов к выполнению в Jupiter Notebook
        - Все переменные должны быть определены
        - Результат должен быть проверяемым
        - НЕ используйте input() - только заданные значения
        - Задание должно быть решаемым за 5-15 минут

        ❌ ЗАПРЕЩЕНО:
        - HTML, CSS, JavaScript код
        - Задания без проверяемого результата
        - Слишком сложные или слишком простые задания
        - Задания, не связанные с содержанием урока

        Формат ответа:
        TITLE: [название задания]
        DESCRIPTION: [описание задания]
        INITIAL_CODE: [начальный код]
        EXPECTED_RESULT: [ожидаемый результат]
        CHECK_TYPE: [тип проверки]
        HINTS: [подсказки]
        """

    def _parse_task_response(
        self, task_response: str, requirement: Dict, task_number: int
    ) -> Dict:
        """
        Парсит ответ API и создает структурированное задание.

        Args:
            task_response (str): Ответ от API
            requirement (Dict): Требования к заданию
            task_number (int): Номер задания

        Returns:
            Dict: Структурированное задание
        """
        try:
            # Парсим структурированный ответ
            title = (
                self._extract_field(task_response, "TITLE")
                or f"Контрольное задание #{task_number}"
            )
            description = (
                self._extract_field(task_response, "DESCRIPTION")
                or "Выполните задание согласно инструкции"
            )
            initial_code = (
                self._extract_field(task_response, "INITIAL_CODE")
                or "# Ваш код здесь\n"
            )
            expected_result = (
                self._extract_field(task_response, "EXPECTED_RESULT") or None
            )
            check_type = self._extract_field(task_response, "CHECK_TYPE") or "exact"
            hints = self._extract_field(task_response, "HINTS") or []

            # Очищаем код от markdown
            initial_code = self.clean_markdown_code_blocks(initial_code)

            # Создаем структуру задания
            task = {
                "title": title.strip(),
                "description": description.strip(),
                "initial_code": initial_code.strip(),
                "expected_result": expected_result,
                "check_type": check_type.strip().lower(),
                "task_type": requirement["type"],
                "task_number": task_number,
                "hints": hints if isinstance(hints, list) else [hints] if hints else [],
                "max_attempts": None,  # Без ограничений
                "show_solution": False,  # Решение не показываем в контрольных
            }

            return task

        except Exception as e:
            self.logger.error(f"Ошибка парсинга задания: {str(e)}")
            return self._create_fallback_single_task(requirement, task_number)

    def _extract_field(self, text: str, field_name: str) -> str:
        """
        Извлекает поле из структурированного текста.

        Args:
            text (str): Текст для парсинга
            field_name (str): Название поля

        Returns:
            str: Значение поля
        """
        pattern = rf"{field_name}:\s*(.*?)(?=\n[A-Z_]+:|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            value = match.group(1).strip()
            # Удаляем лишние символы
            value = re.sub(r"^[-\s]*", "", value)
            return value

        return None

    def _validate_task(self, task: Dict) -> bool:
        """
        Валидирует сгенерированное задание.

        Args:
            task (Dict): Задание для валидации

        Returns:
            bool: True если задание валидно
        """
        required_fields = ["title", "description", "initial_code", "check_type"]

        # Проверяем наличие обязательных полей
        for field in required_fields:
            if not task.get(field):
                self.logger.warning(f"Отсутствует обязательное поле: {field}")
                return False

        # Проверяем длину заголовка
        if len(task["title"]) > 100:
            self.logger.warning("Слишком длинный заголовок задания")
            return False

        # Проверяем тип проверки
        valid_check_types = ["exact", "function", "list", "numeric", "output"]
        if task["check_type"] not in valid_check_types:
            self.logger.warning(f"Недопустимый тип проверки: {task['check_type']}")
            return False

        # Проверяем наличие Python кода
        if not any(
            indicator in task["initial_code"]
            for indicator in ["#", "def ", "import ", "="]
        ):
            self.logger.warning("В начальном коде не найдены Python конструкции")
            return False

        return True

    def _create_fallback_task(
        self, lesson_data: Dict, communication_style: str
    ) -> Dict:
        """
        Создает базовое задание в случае ошибки генерации.

        Args:
            lesson_data (Dict): Данные урока
            communication_style (str): Стиль общения

        Returns:
            Dict: Базовое задание
        """
        lesson_title = lesson_data.get("title", "Урок")

        return {
            "title": f"Практическое задание по теме: {lesson_title}",
            "description": "Выполните задание, используя изученные в уроке концепции программирования.",
            "initial_code": f"""# Практическое задание по теме: {lesson_title}

# Создайте переменную с названием урока
lesson_name = "{lesson_title}"

# Выведите информацию об уроке
print(f"Изучаем урок: {{lesson_name}}")

# Создайте список с тремя изученными концепциями
concepts = ["концепция 1", "концепция 2", "концепция 3"]

# Выведите количество изученных концепций
concepts_count = len(concepts)
print(f"Изучено концепций: {{concepts_count}}")

# Результат для проверки
concepts_count""",
            "expected_result": 3,
            "check_type": "exact",
            "task_type": "mathematical_operations",
            "task_number": 1,
            "hints": ["Используйте функцию len() для подсчета элементов списка"],
            "max_attempts": None,
            "show_solution": False,
        }

    def _create_fallback_single_task(self, requirement: Dict, task_number: int) -> Dict:
        """
        Создает базовое задание для конкретного требования.

        Args:
            requirement (Dict): Требования к заданию
            task_number (int): Номер задания

        Returns:
            Dict: Базовое задание
        """
        task_templates = {
            "function_creation": {
                "title": "Создайте простую функцию",
                "description": "Напишите функцию, которая принимает число и возвращает его квадрат.",
                "initial_code": "def square(x):\n    # Ваш код здесь\n    pass\n\nsquare",
                "expected_result": "function",
                "check_type": "function",
            },
            "data_structures": {
                "title": "Работа со списком",
                "description": "Создайте список чисел от 1 до 5 и найдите их сумму.",
                "initial_code": "# Создайте список\nnumbers = []\n# Найдите сумму\ntotal = 0\n# Ваш код здесь\ntotal",
                "expected_result": 15,
                "check_type": "exact",
            },
        }

        template = task_templates.get(
            requirement["type"], task_templates["data_structures"]
        )

        return {
            "title": template["title"],
            "description": template["description"],
            "initial_code": template["initial_code"],
            "expected_result": template["expected_result"],
            "check_type": template["check_type"],
            "task_type": requirement["type"],
            "task_number": task_number,
            "hints": [],
            "max_attempts": None,
            "show_solution": False,
        }

    def _determine_course_subject(
        self, course_context: Dict, lesson_content: str
    ) -> str:
        """
        Определяет предметную область курса.

        Args:
            course_context (Dict): Контекст курса
            lesson_content (str): Содержание урока

        Returns:
            str: Предметная область
        """
        try:
            if course_context and isinstance(course_context, dict):
                course_title = course_context.get("course_title", "")
                if course_title:
                    return course_title

            # По умолчанию
            return "Python программирование"

        except Exception as e:
            self.logger.error(f"Ошибка определения предметной области: {str(e)}")
            return "Программирование"
