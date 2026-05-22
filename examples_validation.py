"""
Модуль для валидации и повторной генерации практических примеров.
"""

import io
import logging
from contextlib import redirect_stdout
from typing import List

from content_utils import BaseContentGenerator
from examples_html_utils import (
    contains_forbidden_non_python_code,
    extract_code_blocks_from_html,
    has_runnable_examples,
    normalize_markdown_fences_to_html,
    parse_examples_json_response,
    render_examples_json_to_html,
    strip_examples_wrapper,
    validate_examples_payload,
    normalize_examples_payload,
)


class ExamplesValidation(BaseContentGenerator):
    """Валидатор и генератор повторных примеров."""

    MIN_EXAMPLES = 3
    MIN_CODE_LINES = 3

    def __init__(self, api_key):
        super().__init__(api_key)
        self.logger = logging.getLogger(__name__)

    def validate_examples_quality(self, examples: str) -> bool:
        """Проверяет, что примеры содержат реальный исполняемый код."""
        content = strip_examples_wrapper(normalize_markdown_fences_to_html(examples))
        if not has_runnable_examples(
            content, min_blocks=self.MIN_EXAMPLES, min_lines=self.MIN_CODE_LINES
        ):
            self.logger.warning("Недостаточно блоков исполняемого кода в примерах")
            return False
        if contains_forbidden_non_python_code(content):
            self.logger.warning("Найден запрещённый не-Python код в примерах")
            return False
        return True

    def validate_examples_execute(self, examples: str) -> bool:
        """Пробует выполнить каждый блок кода."""
        content = strip_examples_wrapper(examples)
        blocks = extract_code_blocks_from_html(content)
        if len(blocks) < self.MIN_EXAMPLES:
            return False
        for index, code in enumerate(blocks[: self.MIN_EXAMPLES], start=1):
            try:
                with redirect_stdout(io.StringIO()):
                    exec(code, {})
            except Exception as exc:
                self.logger.warning("Пример %s не выполняется: %s", index, exc)
                return False
        return True

    def regenerate_with_strict_prompt(
        self,
        lesson_title,
        lesson_description,
        keywords_str,
        lesson_content,
        communication_style,
        course_subject,
    ) -> str:
        """Повторная генерация с жёстким JSON-промптом."""
        strict_prompt = f"""
Сгенерируй РОВНО 3 примера Python для урока "{lesson_title}" ({course_subject}).

Описание: {lesson_description}
Ключевые слова: {keywords_str}

Материал урока:
{lesson_content[:2500]}

ОБЯЗАТЕЛЬНО:
- JSON с массивом examples из 3 элементов
- У каждого элемента поля title, description, code
- code — минимум 5 строк рабочего Python-кода, готового к запуску
- ЗАПРЕЩЕНЫ заглушки без кода («в этом примере мы создадим...»)
- Без внешних файлов, без input()

Формат:
{{
  "examples": [
    {{"title": "...", "description": "...", "code": "..."}},
    {{"title": "...", "description": "...", "code": "..."}},
    {{"title": "...", "description": "...", "code": "..."}}
  ]
}}
"""
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты генерируешь только JSON с рабочими Python-примерами. "
                    "Каждый пример обязан содержать исполняемый код в поле code."
                ),
            },
            {"role": "user", "content": strict_prompt},
        ]
        response = self.make_api_request(
            messages=messages,
            temperature=0.2,
            max_tokens=4000,
            response_format={"type": "json_object"},
        )
        payload = parse_examples_json_response(response)
        validate_examples_payload(payload, min_examples=3)
        return render_examples_json_to_html(normalize_examples_payload(payload))

    def _create_fallback_python_example(self, lesson_title: str, lesson_content: str = "") -> str:
        """Создаёт три готовых примера с кодом по основам Python."""
        content_lower = (lesson_content or lesson_title).lower()
        examples: List[dict] = []

        if any(word in content_lower for word in ("переменн", "тип", "python", "основ")):
            examples.extend(
                [
                    {
                        "title": "Переменные и типы данных",
                        "description": "Создаём переменные разных типов и выводим их значения.",
                        "code": (
                            'name = "Игорь"\n'
                            "age = 25\n"
                            "height = 1.75\n"
                            "is_student = True\n"
                            'print(name, age, height, is_student)\n'
                            "print(type(name), type(age), type(height), type(is_student))"
                        ),
                    },
                    {
                        "title": "Операторы и выражения",
                        "description": "Складываем числа и сохраняем результат в переменную.",
                        "code": (
                            "a = 10\n"
                            "b = 5\n"
                            "sum_result = a + b\n"
                            "product = a * b\n"
                            'print("sum:", sum_result)\n'
                            'print("product:", product)'
                        ),
                    },
                    {
                        "title": "Условия и циклы",
                        "description": "Проверяем возраст и выводим числа циклом for.",
                        "code": (
                            "age = 18\n"
                            'status = "Взрослый" if age >= 18 else "Несовершеннолетний"\n'
                            "print(status)\n"
                            "for i in range(5):\n"
                            "    print(i)"
                        ),
                    },
                ]
            )
        else:
            examples.extend(
                [
                    {
                        "title": f"Пример 1: {lesson_title}",
                        "description": "Базовая демонстрация переменных и вывода.",
                        "code": (
                            f'topic = "{lesson_title}"\n'
                            "values = [1, 2, 3, 4, 5]\n"
                            "total = sum(values)\n"
                            'print("Тема:", topic)\n'
                            'print("Сумма:", total)'
                        ),
                    },
                    {
                        "title": f"Пример 2: {lesson_title}",
                        "description": "Цикл for для обработки списка.",
                        "code": (
                            "numbers = [2, 4, 6, 8]\n"
                            "squares = []\n"
                            "for n in numbers:\n"
                            "    squares.append(n ** 2)\n"
                            "print(squares)"
                        ),
                    },
                    {
                        "title": f"Пример 3: {lesson_title}",
                        "description": "Функция для переиспользования логики.",
                        "code": (
                            "def normalize(value, min_val, max_val):\n"
                            "    return (value - min_val) / (max_val - min_val)\n"
                            "result = normalize(5, 0, 10)\n"
                            "print(round(result, 2))"
                        ),
                    },
                ]
            )

        return render_examples_json_to_html({"examples": examples})

    def validate_and_regenerate_if_needed(
        self,
        examples,
        course_subject,
        lesson_title,
        lesson_description,
        keywords_str,
        lesson_content,
        communication_style,
    ) -> str:
        """Проверяет качество примеров и перегенерирует при необходимости."""
        if self.validate_examples_quality(examples) and self.validate_examples_execute(examples):
            return examples

        self.logger.warning("Примеры не прошли проверку качества, повторная генерация...")
        examples = self.regenerate_with_strict_prompt(
            lesson_title,
            lesson_description,
            keywords_str,
            lesson_content,
            communication_style,
            course_subject,
        )

        if self.validate_examples_quality(examples) and self.validate_examples_execute(examples):
            return examples

        self.logger.error("Повторная генерация не дала рабочих примеров, используем fallback")
        return self._create_fallback_python_example(lesson_title, lesson_content)

    # Обратная совместимость
    def validate_examples_relevance(self, examples, course_subject) -> bool:
        return self.validate_examples_quality(examples)
