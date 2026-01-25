#!/usr/bin/env python3
"""
Генератор контрольных заданий для TeachAI.
Создает практические задачи с эталонным кодом для проверки знаний.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from content_utils import BaseContentGenerator


class ControlTasksGenerator(BaseContentGenerator):
    """Генератор контрольных заданий."""

    def __init__(self, api_key: str):
        """
        Инициализация генератора.

        Args:
            api_key (str): API ключ для OpenAI
        """
        super().__init__(api_key)
        self.logger = logging.getLogger(__name__)

    def generate_control_task(
        self, lesson_data: Dict[str, Any], lesson_content: str, communication_style: str = "friendly", course_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Генерирует контрольное задание для урока.

        Args:
            lesson_data (Dict[str, Any]): Данные урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения
            course_context (Optional[Dict[str, Any]]): Контекст курса

        Returns:
            Dict[str, Any]: Данные контрольного задания
        """
        print("\n" + "="*80)
        print("🔍 [DIAGNOSTIC] generate_control_task ВЫЗВАН")
        print("="*80)
        
        try:
            # Строим промпт для генерации контрольного задания
            prompt = self._build_control_task_prompt(lesson_data, lesson_content, communication_style, course_context)
            
            print(f"\n📤 [DIAGNOSTIC] Промпт, отправляемый в OpenAI:")
            print(f"Длина промпта: {len(prompt)} символов")
            print(f"Первые 500 символов: {prompt[:500]}...")
            
            # Отправляем запрос к OpenAI
            messages = [
                {
                    "role": "system",
                    "content": "Ты - опытный преподаватель программирования, создающий практические контрольные задания. Все ответы должны быть на русском языке и в формате JSON.",
                },
                {"role": "user", "content": prompt},
            ]
            
            response = self.make_api_request(
                messages=messages,
                temperature=0.7,
                max_tokens=1500,
                response_format={"type": "json_object"},
            )
            
            print(f"\n📥 [DIAGNOSTIC] Ответ от OpenAI:")
            print(f"Длина ответа: {len(response)} символов")
            print(f"Первые 500 символов: {response[:500]}...")
            
            # Парсим ответ
            task_data = self._parse_control_task_response(response)
            
            print(f"\n✅ [DIAGNOSTIC] Результат парсинга:")
            print(f"title: {task_data.get('title', 'НЕТ')}")
            print(f"description: {task_data.get('description', 'НЕТ')[:100]}...")
            print(f"task_code: {task_data.get('task_code', 'НЕТ')[:100]}...")
            print(f"expected_output: {task_data.get('expected_output', 'НЕТ')}")
            print("="*80 + "\n")
            
            return task_data

        except Exception as e:
            print(f"\n❌ [DIAGNOSTIC] ОШИБКА в generate_control_task: {str(e)}")
            print("="*80 + "\n")
            self.logger.error(f"Ошибка при генерации контрольного задания: {str(e)}")
            return {
                "title": "Ошибка генерации",
                "description": f"Не удалось сгенерировать задание: {str(e)}",
                "task_code": "",
                "expected_output": "",
                "solution_code": "",
                "is_needed": False,
                "skip_reason": f"Ошибка генерации: {str(e)}"
            }

    def _check_task_relevance(
        self,
        lesson_title: str,
        lesson_description: str,
        lesson_content: str,
        communication_style: str,
    ) -> Dict[str, Any]:
        """
        Проверяет, нужно ли контрольное задание с кодом для данного урока.

        Args:
            lesson_title (str): Название урока
            lesson_description (str): Описание урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения

        Returns:
            Dict[str, Any]: Результат проверки:
                - is_needed (bool): Нужно ли задание
                - reason (str): Причина решения
        """
        try:
            # Расширяем анализируемый материал урока
            extended_content = lesson_content[:2000] if len(lesson_content) > 2000 else lesson_content
            
            prompt = f"""
            Проанализируй урок и определи, нужно ли создавать контрольное задание с написанием кода на Python.

            НАЗВАНИЕ УРОКА: {lesson_title}
            ОПИСАНИЕ УРОКА: {lesson_description}
            СОДЕРЖАНИЕ УРОКА: {extended_content}

            КРИТЕРИИ АНАЛИЗА:
            1. Если урок о настройке среды, установке программ, теории без кода - задание НЕ НУЖНО
            2. Если урок содержит примеры кода и объясняет как что-то программировать - задание НУЖНО
            3. Если урок для начинающих, которые еще не умеют программировать - задание НЕ НУЖНО
            4. Если урок объясняет концепции без практики - задание НЕ НУЖНО
            5. Если урок показывает как писать код или содержит практические примеры - задание НУЖНО

            ПРИМЕРЫ УРОКОВ БЕЗ ЗАДАНИЯ:
            - "Установка Python и настройка среды"
            - "Что такое программирование"
            - "История Python"
            - "Настройка IDE"

            ПРИМЕРЫ УРОКОВ С ЗАДАНИЕМ:
            - "Переменные и типы данных"
            - "Условные операторы"
            - "Циклы в Python"
            - "Функции"

            Формат ответа (только JSON):
            {{
                "is_needed": true/false,
                "reason": "Объяснение почему задание нужно или не нужно"
            }}

            Верни только JSON без дополнительного текста.
            """

            # Генерируем анализ через OpenAI
            messages = [
                {
                    "role": "system",
                    "content": "Ты - опытный преподаватель программирования, анализирующий уроки. Все ответы должны быть на русском языке и в формате JSON.",
                },
                {"role": "user", "content": prompt},
            ]

            response = self.make_api_request(
                messages=messages,
                temperature=0.3,  # Низкая температура для более точного анализа
                max_tokens=500,
                response_format={"type": "json_object"},
            )

            # Парсим ответ
            import json
            try:
                # Ищем JSON в ответе
                start_idx = response.find("{")
                end_idx = response.rfind("}") + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = response[start_idx:end_idx]
                    result = json.loads(json_str)
                    
                    # Проверяем обязательные поля
                    if "is_needed" not in result:
                        result["is_needed"] = True  # По умолчанию создаем задание
                    if "reason" not in result:
                        result["reason"] = "Анализ показал необходимость задания"
                    
                    return result
                else:
                    # Fallback - создаем задание
                    return {"is_needed": True, "reason": "Не удалось проанализировать урок"}
                    
            except json.JSONDecodeError:
                # Fallback - создаем задание
                return {"is_needed": True, "reason": "Ошибка парсинга анализа"}

        except Exception as e:
            self.logger.error(f"Ошибка при проверке необходимости задания: {str(e)}")
            # Fallback - создаем задание
            return {"is_needed": True, "reason": "Ошибка анализа, создаем задание"}

    def _build_control_task_prompt(
        self,
        lesson_data: Dict[str, Any],
        lesson_content: str,
        communication_style: str,
        course_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Создает prompt для генерации контрольного задания.

        Args:
            lesson_data (Dict[str, Any]): Данные урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения
            course_context (Dict[str, Any]): Контекст курса

        Returns:
            str: Prompt для OpenAI
        """
        style_instruction = (
            "дружелюбно и понятно"
            if communication_style == "friendly"
            else "профессионально"
        )

        extended_content = lesson_content

        return f"""
Создай практическое контрольное задание СТРОГО на основе lesson_content.

lesson_content:
{extended_content}

КРИТИЧЕСКИЕ ТРЕБОВАНИЯ:
- Задание должно проверять понимание КОНКРЕТНОГО материала, примеров и кода из lesson_content.
- Используй только те концепции, примеры и код, которые реально объяснены и показаны в lesson_content.
- НЕ создавай generic задания типа "Привет, мир!" или "Выведите числа от 1 до 5".
- Если в lesson_content нет кода или практики — верни is_needed: false и skip_reason: "В уроке нет кода для практики".
- Все переменные, структуры данных и исходные значения должны быть явно заданы в task_code.
- expected_output должен соответствовать выводу print из эталонного решения.
- Не используй input() и другие интерактивные функции.
- Задание должно быть СЛОЖНЫМ и проверять реальное понимание материала.

ВАЖНО: В УСЛОВИИ ЗАДАНИЯ ВСЕГДА ПРИВОДИ ВЕСЬ НЕОБХОДИМЫЙ КОД!
- Не используй формулировки типа "вам предоставлен фрагмент кода", "см. пример выше", "анализируйте код из урока" и т.п.
- Задание должно быть полностью понятно без обращения к другим материалам.
- В description всегда должен быть приведён весь код, который требуется анализировать, запускать или дополнять.

КРИСТАЛЬНО ЧЕТКИЕ ФОРМУЛИРОВКИ:
- Если требуется список результатов — явно укажи "соберите результаты в список", "накопите результаты", "создайте список"
- Если требуется вывод каждого элемента — явно укажи "выведите каждое число", "выведите каждый результат"
- Если требуется сумма — явно укажи "найдите сумму", "вычислите сумму", "сложите все числа"
- НЕ допускай двусмысленностей типа "выведите результаты" (непонятно: каждый отдельно или список)
- Используй конкретные глаголы: "соберите", "накопите", "выведите каждое", "найдите сумму"

ВАЖНО: Эталонное решение (solution_code) должно точно соответствовать формулировке задания!
- Если задание говорит "вставьте по индексу 2" - в solution_code должно быть insert(2, ...)
- Если задание говорит "удалите элемент X" - в solution_code должно быть remove(X)
- Проверь, что expected_output соответствует реальному выводу solution_code

КРИТИЧЕСКО ВАЖНО: task_code должен содержать ВСЕ начальные данные!
- Если в description упоминается "список my_list = [1, 2, 3]" - в task_code должно быть "my_list = [1, 2, 3]"
- Если в description упоминается "словарь my_dict = {{'a': 'apple'}}" - в task_code должно быть "my_dict = {{'a': 'apple'}}"
- НЕ оставляй пустые структуры данных в task_code!
- Студент должен получить ВСЕ начальные данные в task_code

Формат ответа (ТОЛЬКО JSON!):
{{{{
  "title": "Название задания",
  "description": "Описание задачи, с явным указанием исходных данных и ПОЛНЫМ КОДОМ, который требуется анализировать или запускать",
  "task_code": "Исходные переменные и структуры данных, которые используются в решении",
  "expected_output": "Ожидаемый результат выполнения (конкретный вывод)",
  "solution_code": "Полное правильное решение",
  "hints": ["Подсказка 1", "Подсказка 2"],
  "is_needed": true/false,
  "skip_reason": "Причина, если задание не требуется"
}}}}

Пример хорошего задания:
{{{{
  "title": "Работа со списками и словарями",
  "description": "Дан список my_list = [1, 2, 3, 'apple', 'banana', 'cherry'] и словарь my_dict = {{{{'a': 'apple', 'b': 'banana', 'c': 'cherry'}}}}. Добавьте число 5 в список, вставьте строку 'grape' по индексу 2, удалите элемент 'cherry' из списка. Затем добавьте новую пару ключ-значение 'd'-'dog' в словарь. В конце выведите получившийся список и словарь.",
  "task_code": "my_list = [1, 2, 3, 'apple', 'banana', 'cherry']\nmy_dict = {{{{'a': 'apple', 'b': 'banana', 'c': 'cherry'}}}}\n# Ваш код здесь",
  "expected_output": "[1, 2, 'grape', 3, 'apple', 'banana', 5]\n{{{{'a': 'apple', 'b': 'banana', 'c': 'cherry', 'd': 'dog'}}}}",
  "solution_code": "my_list = [1, 2, 3, 'apple', 'banana', 'cherry']\nmy_dict = {{{{'a': 'apple', 'b': 'banana', 'c': 'cherry'}}}}\nmy_list.append(5)\nmy_list.insert(2, 'grape')\nmy_list.remove('cherry')\nmy_dict['d'] = 'dog'\nprint(my_list)\nprint(my_dict)",
  "hints": ["Используйте методы append и insert для списка", "Для удаления используйте remove", "Для добавления пары в словарь используйте my_dict['d'] = 'dog'"],
  "is_needed": true,
  "skip_reason": ""
}}}}

Верни только JSON без дополнительного текста.
"""

    def _parse_control_task_response(self, response: str) -> Dict[str, Any]:
        """
        Парсит ответ от OpenAI в структурированные данные.

        Args:
            response (str): Ответ от OpenAI

        Returns:
            Dict[str, Any]: Структурированные данные задания
        """
        try:
            # Ищем JSON в ответе
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                task_data = json.loads(json_str)

                # Проверяем обязательные поля
                required_fields = [
                    "title",
                    "description",
                    "task_code",
                    "expected_output",
                    "solution_code",
                ]
                for field in required_fields:
                    if field not in task_data:
                        task_data[field] = ""

                # Добавляем hints если нет
                if "hints" not in task_data:
                    task_data["hints"] = []

                # --- ПРОВЕРКА СООТВЕТСТВИЯ ЭТАЛОННОГО РЕШЕНИЯ ---
                # Проверяем, что solution_code соответствует expected_output
                try:
                    import io
                    from contextlib import redirect_stdout
                    output_buffer = io.StringIO()
                    local_vars = {}
                    with redirect_stdout(output_buffer):
                        exec(task_data["solution_code"], {}, local_vars)
                    actual_solution_output = output_buffer.getvalue().strip()
                    
                    # Если expected_output не соответствует реальному выводу solution_code
                    if task_data["expected_output"] and actual_solution_output != task_data["expected_output"].strip():
                        print(f"⚠️ [DIAGNOSTIC] Несоответствие в эталонном решении:")
                        print(f"   expected_output: '{task_data['expected_output']}'")
                        print(f"   actual_solution_output: '{actual_solution_output}'")
                        # Исправляем expected_output
                        task_data["expected_output"] = actual_solution_output
                        print(f"   ✅ Исправлен expected_output")
                except Exception as e:
                    print(f"⚠️ [DIAGNOSTIC] Ошибка проверки эталонного решения: {e}")

                # --- ПРОВЕРКА ПОЛНОТЫ TASK_CODE ---
                # Проверяем, что task_code содержит все необходимые начальные данные
                try:
                    import re
                    
                    # Ищем упоминания структур данных в description
                    description = task_data.get("description", "")
                    task_code = task_data.get("task_code", "")
                    
                    # Ищем упоминания списков и словарей в description
                    list_patterns = [
                        r"список\s+(\w+)\s*=\s*\[([^\]]+)\]",
                        r"(\w+)\s*=\s*\[([^\]]+)\].*список",
                        r"список\s+(\w+).*=\s*\[([^\]]+)\]"
                    ]
                    
                    dict_patterns = [
                        r"словарь\s+(\w+)\s*=\s*\{([^}]+)\}",
                        r"(\w+)\s*=\s*\{([^}]+)\}.*словарь",
                        r"словарь\s+(\w+).*=\s*\{([^}]+)\}"
                    ]
                    
                    missing_data = []
                    
                    # Проверяем списки
                    for pattern in list_patterns:
                        matches = re.findall(pattern, description, re.IGNORECASE)
                        for var_name, var_content in matches:
                            if f"{var_name} = [" not in task_code:
                                missing_data.append(f"Список {var_name} = [{var_content}]")
                    
                    # Проверяем словари
                    for pattern in dict_patterns:
                        matches = re.findall(pattern, description, re.IGNORECASE)
                        for var_name, var_content in matches:
                            if f"{var_name} = {{" not in task_code:
                                missing_data.append(f"Словарь {var_name} = {{{var_content}}}")
                    
                    if missing_data:
                        print(f"⚠️ [DIAGNOSTIC] В task_code отсутствуют начальные данные:")
                        for item in missing_data:
                            print(f"   - {item}")
                        print(f"   task_code: '{task_code}'")
                        print(f"   ⚠️ Проблема: Студент не получит начальные данные!")
                        
                except Exception as e:
                    print(f"⚠️ [DIAGNOSTIC] Ошибка проверки task_code: {e}")

                # --- УЛУЧШЕНО: эвристика для проверки переменной ---
                # Если expected_output пустой, а в solution_code есть присваивание
                if not task_data["expected_output"].strip():
                    import re
                    # Ищем строку вида: имя = значение (более гибкий поиск)
                    lines = task_data["solution_code"].strip().split('\n')
                    for line in lines:
                        # Ищем присваивание переменной
                        match = re.search(r"^(\w+)\s*=\s*(.+)$", line.strip())
                        if match:
                            var_name = match.group(1)
                            var_value = match.group(2).strip()
                            # Пробуем вычислить значение (безопасно)
                            try:
                                # Создаем безопасное окружение для eval
                                safe_dict = {}
                                expected_value = eval(var_value, {"__builtins__": {}}, safe_dict)
                                task_data["check_variable"] = var_name
                                task_data["expected_variable_value"] = expected_value
                                print(f"🔍 [DIAGNOSTIC] Найдена переменная: {var_name} = {expected_value}")
                                break
                            except Exception as e:
                                print(f"⚠️ [DIAGNOSTIC] Не удалось вычислить значение {var_value}: {e}")
                                # Используем строковое значение как fallback
                                task_data["check_variable"] = var_name
                                task_data["expected_variable_value"] = var_value
                                break
                # --- ДИАГНОСТИКА: проверяем, что в description есть код ---
                description = task_data.get("description", "")
                if not ("code:" in description.lower() or "код:" in description.lower() or "```" in description or "\n" in description and any(word in description for word in ["=", "print", "if", "for", "while", "def", "class"])):
                    print(f"⚠️ [DIAGNOSTIC] ВНИМАНИЕ: В description нет явного кода! Задание может быть неполным или непонятным.")
                    print(f"   description: {description}")

                # --- ДИАГНОСТИКА: проверяем соответствие description и expected_output ---
                expected_output = task_data.get("expected_output", "")
                description_lower = description.lower()
                
                # Проверка на двусмысленность: если в expected_output есть список [...], но в description нет слов о списке
                if "[" in expected_output and "]" in expected_output and not any(word in description_lower for word in ["список", "соберите", "накопите", "создайте список"]):
                    print(f"⚠️ [DIAGNOSTIC] ВНИМАНИЕ: В expected_output ожидается список, но в description нет явного указания 'соберите в список'!")
                    print(f"   description: {description}")
                    print(f"   expected_output: {expected_output}")
                
                # Проверка на двусмысленность: если в expected_output есть print() для каждого элемента, но в description нет "каждое"
                if "print(" in expected_output and not any(word in description_lower for word in ["каждое", "каждый", "отдельно"]):
                    print(f"⚠️ [DIAGNOSTIC] ВНИМАНИЕ: В expected_output ожидается вывод каждого элемента, но в description нет явного указания 'каждое'!")
                    print(f"   description: {description}")
                    print(f"   expected_output: {expected_output}")
                return task_data
            else:
                raise ValueError("JSON не найден в ответе")

        except Exception as e:
            self.logger.error(f"Ошибка при парсинге ответа: {str(e)}")
            return self._create_fallback_task("Задание")

    def _create_fallback_task(self, lesson_title: str) -> Dict[str, Any]:
        """
        Создает fallback задание при ошибке генерации.

        Args:
            lesson_title (str): Название урока

        Returns:
            Dict[str, Any]: Fallback задание
        """
        self.logger.warning(
            f"Сработал fallback для контрольного задания по теме: {lesson_title}"
        )

        # Создаем тематическое fallback задание в зависимости от темы урока
        if "цикл" in lesson_title.lower() or "циклы" in lesson_title.lower():
            return {
                "is_needed": True,
                "title": f"Практическое задание по теме '{lesson_title}'",
                "description": "Напишите программу, которая выводит числа от 1 до 5, используя цикл for.",
                "task_code": "# Напишите ваш код здесь\n# Используйте цикл for для вывода чисел от 1 до 5",
                "expected_output": "1\n2\n3\n4\n5",
                "solution_code": "# Правильное решение\nfor i in range(1, 6):\n    print(i)",
                "hints": [
                    "Используйте цикл for",
                    "Функция range(1, 6) создает последовательность от 1 до 5",
                    "Используйте print() для вывода",
                ],
            }
        elif "условн" in lesson_title.lower() or "if" in lesson_title.lower():
            return {
                "is_needed": True,
                "title": f"Практическое задание по теме '{lesson_title}'",
                "description": "Дано число number = 10. Напишите программу, которая проверяет, является ли это число четным, и выводит 'Четное' или 'Нечетное'.",
                "task_code": "number = 10\n# Напишите ваш код здесь\n# Проверьте, является ли number четным",
                "expected_output": "Четное",
                "solution_code": "number = 10\nif number % 2 == 0:\n    print('Четное')\nelse:\n    print('Нечетное')",
                "hints": [
                    "Используйте оператор % для проверки остатка",
                    "Условие: если остаток от деления на 2 равен 0",
                    "Используйте if-else",
                ],
            }
        else:
            return {
                "is_needed": True,
                "title": f"Практическое задание по теме '{lesson_title}'",
                "description": "Напишите программу, которая выводит на экран текст 'Привет, мир!'. Используйте функцию print().",
                "task_code": "# Напишите ваш код здесь\n# Используйте print() для вывода текста",
                "expected_output": "Привет, мир!",
                "solution_code": "# Правильное решение\nprint('Привет, мир!')",
                "hints": [
                    "Используйте функцию print()",
                    "Текст должен быть в кавычках",
                    "Проверьте синтаксис",
                ],
            }

    def validate_task_execution(
        self, user_code: str, expected_output: str, check_variable: Optional[str] = None, expected_variable_value: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Проверяет выполнение задания пользователем.

        Args:
            user_code (str): Код пользователя
            expected_output (str): Ожидаемый результат (stdout)
            check_variable (Optional[str], optional): Имя переменной для проверки
            expected_variable_value (Optional[Any], optional): Ожидаемое значение переменной

        Returns:
            Dict[str, Any]: Результат проверки:
                - is_correct (bool): Правильно ли выполнено
                - actual_output (str): Фактический результат
                - actual_variable (Any): Значение переменной (если проверяется)
                - error_message (str): Сообщение об ошибке (если есть)
        """
        try:
            import io
            from contextlib import redirect_stdout
            output_buffer = io.StringIO()
            local_vars = {}
            with redirect_stdout(output_buffer):
                exec(user_code, {}, local_vars)
            actual_output = output_buffer.getvalue().strip()
            # Если требуется проверка переменной
            if check_variable is not None:
                actual_var = local_vars.get(check_variable, None)
                is_correct = actual_var == expected_variable_value
                return {
                    "is_correct": is_correct,
                    "actual_output": actual_output,
                    "actual_variable": actual_var,
                    "error_message": "",
                }
            # Обычная проверка вывода
            is_correct = actual_output == expected_output.strip()
            return {
                "is_correct": is_correct,
                "actual_output": actual_output,
                "actual_variable": None,
                "error_message": "",
            }
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return {"is_correct": False, "actual_output": "", "actual_variable": None, "error_message": f"{e}\n{tb}"}
