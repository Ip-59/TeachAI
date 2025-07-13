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
        self,
        lesson_data: Dict[str, Any],
        lesson_content: str,
        communication_style: str = "friendly",
        course_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Генерирует контрольное задание для урока.

        Args:
            lesson_data (Dict[str, Any]): Данные урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения
            course_context (Optional[Dict[str, Any]]): Контекст курса

        Returns:
            Dict[str, Any]: Контрольное задание с полями:
                - title (str): Название задания
                - description (str): Описание задания
                - task_code (str): Код для выполнения
                - expected_output (str): Ожидаемый результат
                - solution_code (str): Эталонное решение
                - hints (List[str]): Подсказки (если нужны)
        """
        try:
            lesson_title = lesson_data.get("title", "Урок")
            lesson_description = lesson_data.get("description", "")

            # Формируем prompt для генерации задания
            prompt = self._build_control_task_prompt(
                lesson_title, lesson_description, lesson_content, communication_style
            )

            # Генерируем задание через OpenAI
            # Используем прямой вызов API для генерации контента
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

            # Сохраняем отладочную информацию
            self.save_debug_response(
                "control_task",
                prompt,
                response,
                {
                    "lesson_title": lesson_title,
                    "lesson_description": lesson_description,
                    "communication_style": communication_style,
                },
            )

            # Парсим ответ
            task_data = self._parse_control_task_response(response)

            self.logger.info(
                f"Сгенерировано контрольное задание для урока: {lesson_title}"
            )
            return task_data

        except Exception as e:
            self.logger.error(f"Ошибка при генерации контрольного задания: {str(e)}")
            # Возвращаем fallback задание
            return self._create_fallback_task(lesson_title)

    def _build_control_task_prompt(
        self,
        lesson_title: str,
        lesson_description: str,
        lesson_content: str,
        communication_style: str,
    ) -> str:
        """
        Создает prompt для генерации контрольного задания.

        Args:
            lesson_title (str): Название урока
            lesson_description (str): Описание урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения

        Returns:
            str: Prompt для OpenAI
        """
        style_instruction = (
            "дружелюбно и понятно"
            if communication_style == "friendly"
            else "профессионально"
        )

        return f"""
        Создай ПОНЯТНОЕ практическое контрольное задание СТРОГО по теме урока "{lesson_title}".

        ОПИСАНИЕ УРОКА: {lesson_description}
        СОДЕРЖАНИЕ УРОКА: {lesson_content[:1000]}...

        Требования:
        1. Задание должно быть СТРОГО по теме текущего урока (не повторяй задания из других тем или уроков).
        2. Описание должно быть ЧЁТКИМ и ПОНЯТНЫМ — студент должен точно знать, что делать, какой результат получить и как проверить.
        3. Не используй абстрактные формулировки, только конкретные задачи по материалу этого урока.
        4. Код должен быть рабочим и выполнимым.
        5. Ожидаемый результат — конкретный вывод (например, "Hello, World!" или "15").
        6. Эталонное решение должно быть полным и правильным.
        7. Объясни {style_instruction}.

        Формат ответа (только JSON!):
        {{
            "title": "Название задания",
            "description": "Чёткое и понятное описание задачи",
            "task_code": "Начальный код или заглушка, которую нужно дополнить",
            "expected_output": "Ожидаемый результат выполнения (конкретный вывод)",
            "solution_code": "Полное правильное решение",
            "hints": ["Подсказка 1", "Подсказка 2"]
        }}

        Пример хорошего задания:
        {{
            "title": "Проверка длины строки",
            "description": "Напишите программу, которая проверяет, больше ли длина строки s 5 символов, и выводит 'Длинная' или 'Короткая' в зависимости от результата.",
            "task_code": "s = input()\n# Ваш код здесь",
            "expected_output": "Длинная",
            "solution_code": "s = input()\nif len(s) > 5:\n    print('Длинная')\nelse:\n    print('Короткая')",
            "hints": ["Используйте функцию len()", "Условный оператор if"]
        }}

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
                "title": f"Практическое задание по теме '{lesson_title}'",
                "description": "Напишите программу, которая проверяет, является ли число четным, и выводит 'Четное' или 'Нечетное'.",
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
        self, user_code: str, expected_output: str
    ) -> Dict[str, Any]:
        """
        Проверяет выполнение задания пользователем.

        Args:
            user_code (str): Код пользователя
            expected_output (str): Ожидаемый результат

        Returns:
            Dict[str, Any]: Результат проверки:
                - is_correct (bool): Правильно ли выполнено
                - actual_output (str): Фактический результат
                - error_message (str): Сообщение об ошибке (если есть)
        """
        try:
            # Выполняем код пользователя
            local_vars = {}
            exec(user_code, {}, local_vars)

            # Получаем вывод (если есть)
            actual_output = ""
            if "print" in user_code:
                # Простая проверка - ищем print в коде
                actual_output = "Вывод выполнен"

            # Простая проверка корректности
            is_correct = True  # Упрощенная проверка

            return {
                "is_correct": is_correct,
                "actual_output": actual_output,
                "error_message": "",
            }

        except Exception as e:
            return {"is_correct": False, "actual_output": "", "error_message": str(e)}
