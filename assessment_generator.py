"""
Модуль для генерации тестов и вопросов для проверки знаний.
Отвечает за создание оценочных материалов на основе содержания уроков.
"""

import json
import re
import random
from content_utils import BaseContentGenerator


class AssessmentGenerator(BaseContentGenerator):
    """Генератор тестов и вопросов для проверки знаний."""

    def __init__(self, api_key):
        """
        Инициализация генератора тестов.

        Args:
            api_key (str): API ключ OpenAI
        """
        super().__init__(api_key)
        self.logger.info("AssessmentGenerator инициализирован")

    def generate_assessment(
        self, course, section, topic, lesson, lesson_content, num_questions=5
    ):
        """
        Генерирует вопросы для проверки знаний по уроку.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson (str): Название урока
            lesson_content (str): Содержание урока
            num_questions (int): Количество вопросов

        Returns:
            list: Список вопросов с вариантами ответов

        Raises:
            Exception: Если не удалось сгенерировать вопросы
        """
        try:
            lesson_title = str(lesson) if lesson is not None else "Урок"

            # Очищаем HTML теги для лучшего анализа содержания
            clean_content = self._clean_html_for_analysis(lesson_content)

            # Ограничиваем длину, но берем больше текста для более точных вопросов
            content_for_questions = (
                clean_content[:4000] if len(clean_content) > 4000 else clean_content
            )

            prompt = self._build_assessment_prompt(
                course,
                section,
                topic,
                lesson_title,
                content_for_questions,
                num_questions,
            )

            messages = [
                {
                    "role": "system",
                    "content": "Ты - опытный преподаватель, создающий тесты для проверки знаний строго по предоставленному материалу урока. Все твои ответы должны быть на русском языке. Формируй вопросы только на основе информации, представленной в уроке.",
                },
                {"role": "user", "content": prompt},
            ]

            content = self.make_api_request(
                messages=messages,
                temperature=0.5,  # Уменьшаем temperature для более точного следования материалу
                max_tokens=3000,
                response_format={"type": "json_object"},
            )

            # Сохраняем отладочную информацию
            self.save_debug_response(
                "assessment",
                prompt,
                content,
                {
                    "course": course,
                    "section": section,
                    "topic": topic,
                    "lesson": lesson_title,
                    "num_questions": num_questions,
                },
            )

            questions_data = json.loads(content)
            questions = self._extract_questions_from_response(questions_data)

            if not questions or len(questions) == 0:
                raise Exception("API вернул пустой список вопросов")

            # ПРИНУДИТЕЛЬНАЯ РАНДОМИЗАЦИЯ - поскольку API не следует инструкциям
            randomized_questions = self._force_randomize_questions(questions)

            self.logger.info(
                f"Успешно сгенерировано {len(randomized_questions)} вопросов с принудительной рандомизацией"
            )
            return randomized_questions

        except Exception as e:
            self.logger.error(f"Критическая ошибка при генерации вопросов: {str(e)}")
            raise Exception(
                f"Не удалось сгенерировать вопросы для урока '{lesson}': {str(e)}"
            )

    def _clean_html_for_analysis(self, lesson_content):
        """
        Очищает HTML теги для анализа содержания.

        Args:
            lesson_content (str): Содержание урока с HTML

        Returns:
            str: Очищенное содержание
        """
        clean_content = re.sub(r"<[^>]+>", " ", lesson_content)
        clean_content = re.sub(r"\s+", " ", clean_content).strip()
        return clean_content

    def _extract_questions_from_response(self, questions_data):
        """
        Извлекает вопросы из ответа API.

        Args:
            questions_data (dict): Ответ API в формате JSON

        Returns:
            list: Список вопросов
        """
        # Логируем структуру ответа для отладки
        self.logger.debug(
            f"Структура ответа API: {type(questions_data)} - {questions_data}"
        )

        # Проверяем, есть ли в ответе ключ "questions"
        if "questions" in questions_data:
            questions = questions_data["questions"]
        elif isinstance(questions_data, list):
            # Если API вернул сразу список вопросов
            questions = questions_data
        else:
            # Проверяем, содержит ли ответ другие ключи, которые могут быть списком вопросов
            for key, value in questions_data.items():
                if isinstance(value, list) and len(value) > 0:
                    questions = value
                    self.logger.info(f"Найден список вопросов в ключе '{key}'")
                    break
            else:
                # Если ничего не найдено, попробуем обработать как один вопрос
                if isinstance(questions_data, dict) and "text" in questions_data:
                    self.logger.warning("API вернул только один вопрос вместо списка")
                    questions = [questions_data]
                else:
                    raise Exception(
                        f"API вернул некорректный формат вопросов: {questions_data}"
                    )

        # Проверяем, что получили список вопросов
        if not isinstance(questions, list):
            raise Exception(f"Ожидался список вопросов, получен: {type(questions)}")

        # НОРМАЛИЗАЦИЯ correct_option: если 0 — приводим к 1, если не 1-3 — выбрасываем ошибку
        for i, q in enumerate(questions):
            if not isinstance(q, dict):
                raise Exception(f"Вопрос {i+1} не является словарем: {q}")

            if "text" not in q:
                raise Exception(f"Вопрос {i+1} не содержит поле 'text': {q}")

            if "options" not in q:
                raise Exception(f"Вопрос {i+1} не содержит поле 'options': {q}")

            if "correct_option" in q:
                if q["correct_option"] == 0:
                    q["correct_option"] = 1
                if q["correct_option"] not in [1, 2, 3]:
                    raise Exception(
                        f"Некорректный индекс правильного ответа в вопросе {i+1}: {q['correct_option']}"
                    )
            else:
                raise Exception(f"Вопрос {i+1} не содержит поле 'correct_option': {q}")

        self.logger.info(f"Успешно извлечено {len(questions)} вопросов")
        return questions

    def _force_randomize_questions(self, questions):
        """
        Принудительно перемешивает варианты ответов для каждого вопроса.
        Это необходимо, так как API не всегда следует инструкциям по рандомизации.

        Args:
            questions (list): Список вопросов

        Returns:
            list: Список вопросов с перемешанными вариантами ответов
        """
        randomized_questions = []
        
        for question in questions:
            if "options" not in question or "correct_option" not in question:
                # Если структура неполная, оставляем как есть
                randomized_questions.append(question)
                continue
                
            original_options = question["options"].copy()
            original_correct_option = question["correct_option"]
            
            # Проверяем, что correct_option в допустимых пределах
            if original_correct_option < 1 or original_correct_option > len(original_options):
                self.logger.warning(f"Некорректный correct_option: {original_correct_option}, оставляем как есть")
                randomized_questions.append(question)
                continue
            
            # Получаем правильный ответ (индекс с 1)
            correct_answer_text = original_options[original_correct_option - 1]
            
            # Перемешиваем варианты
            shuffled_options = original_options.copy()
            random.shuffle(shuffled_options)
            
            # Находим новую позицию правильного ответа
            new_correct_option = shuffled_options.index(correct_answer_text) + 1
            
            # Создаем новый вопрос с перемешанными вариантами
            new_question = question.copy()
            new_question["options"] = shuffled_options
            new_question["correct_option"] = new_correct_option
            
            randomized_questions.append(new_question)
            
            self.logger.debug(f"Вопрос рандомизирован: правильный ответ переместился с позиции {original_correct_option} на позицию {new_correct_option}")
        
        return randomized_questions

    def _build_assessment_prompt(
        self, course, section, topic, lesson_title, content_for_questions, num_questions
    ):
        """
        Создает промпт для генерации вопросов.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson_title (str): Название урока
            content_for_questions (str): Очищенное содержание урока
            num_questions (int): Количество вопросов

        Returns:
            str: Промпт для API
        """
        return f"""
        На основе СТРОГО следующего урока создай РОВНО {num_questions} вопросов для проверки знаний НА РУССКОМ ЯЗЫКЕ:

        Курс: {course}
        Раздел: {section}
        Тема: {topic}
        Урок: {lesson_title}

        ПОЛНОЕ содержание урока:
        {content_for_questions}

        КРИТИЧЕСКИ ВАЖНЫЕ ТРЕБОВАНИЯ:
        1. ВСЕ вопросы и варианты ответов должны быть ОБЯЗАТЕЛЬНО на русском языке!
        2. Вопросы должны основываться ТОЛЬКО на КОНКРЕТНОМ материале этого урока
        3. НЕ задавай общие вопросы вроде "Что такое Python?" или "Что такое функция?"
        4. Вопросы должны проверять понимание КОНКРЕТНЫХ примеров, кода и объяснений из урока
        5. Правильные ответы должны быть ТОЧНО представлены в содержании урока
        6. Неправильные варианты должны быть реалистичными, но четко отличимыми от правильного
        7. Каждый вопрос должен иметь РОВНО 3 варианта ответа
        8. Указывай номер правильного ответа (1, 2 или 3), где 1 — первый вариант, 2 — второй, 3 — третий
        9. НЕ используй варианты "все вышеперечисленное", "нет правильного ответа", "другое"
        10. Вопросы должны быть ЛОГИЧЕСКИ ОБОСНОВАННЫМИ и ОДНОЗНАЧНЫМИ
        11. НЕ создавай вопросы где ВСЕ варианты ответов правильные!
        12. НЕ создавай вопросы где правильный ответ "Синтаксическая ошибка" если это не так!
        13. Каждый вопрос должен иметь ТОЛЬКО ОДИН правильный ответ!

        ПРИМЕРЫ ХОРОШИХ ВОПРОСОВ (основанных на конкретном материале):
        - "Какой результат выведет код [конкретный код из урока]?"
        - "В примере с [конкретный пример] какой метод используется?"
        - "Согласно уроку, что происходит когда [конкретная ситуация из урока]?"

        ПРИМЕРЫ ПЛОХИХ ВОПРОСОВ (слишком общие или некорректные):
        - "Что такое модуль?" (слишком общий)
        - "Для чего нужны функции?" (не из урока)
        - "Какие бывают типы данных?" (не по теме урока)
        - "Как объявляется переменная в Python?" (все варианты правильные)
        - "Какая ошибка возникает при использовании переменной без объявления?" (неправильный ответ)

        ПРАВИЛЬНЫЕ ПРИМЕРЫ ВОПРОСОВ:
        - "В примере 'x = 5' какой тип данных присваивается переменной x?" (int)
        - "При попытке использовать переменную 'y' без её объявления возникает ошибка:" (NameError)
        - "Какой результат выведет код 'print(2 + 3)'?" (5)

        ОБЯЗАТЕЛЬНЫЙ ФОРМАТ ОТВЕТА - JSON с {num_questions} вопросами:
        {{
          "questions": [
            {{
              "text": "Конкретный вопрос по материалу урока",
              "options": ["Вариант 1", "Вариант 2", "Вариант 3"],
              "correct_option": 2
            }},
            {{
              "text": "Еще один конкретный вопрос",
              "options": ["Другой вариант 1", "Другой вариант 2", "Другой вариант 3"],
              "correct_option": 1
            }}
            // ... и так далее для всех {num_questions} вопросов
          ]
        }}

        КРИТИЧЕСКИ ВАЖНО: 
        - Ответ должен содержать РОВНО {num_questions} вопросов в массиве "questions"!
        - Каждый вопрос должен проверять КОНКРЕТНОЕ знание из урока!
        - Убедись, что ВСЕ тексты написаны НА РУССКОМ ЯЗЫКЕ!
        - Каждый вопрос должен иметь ТОЛЬКО ОДИН правильный ответ!
        """
