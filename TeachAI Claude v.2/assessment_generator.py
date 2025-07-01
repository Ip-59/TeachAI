"""
Модуль для генерации тестов и вопросов для проверки знаний.
Отвечает за создание оценочных материалов на основе содержания уроков.
ИСПРАВЛЕНО ЭТАП 37: Увеличен лимит контента для более точных вопросов (проблема #154)
ИСПРАВЛЕНО ЭТАП 38: Подтверждение передачи полного контента урока (проблема #159)
ИСПРАВЛЕНО ЭТАП 38: Исправлена инициализация model и client (проблема #160)
"""

import json
import re
import random
import logging
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

        # ИСПРАВЛЕНО ЭТАП 38: Добавляем модель и клиент для правильной работы API (проблема #160)
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo-16k"

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

            # ИСПРАВЛЕНО ЭТАП 38: Максимальная передача контента урока для точных вопросов (проблема #162)
            # Используем практически весь контент урока для генерации релевантных вопросов
            max_content_limit = 20000  # Увеличен лимит до 20000 символов
            content_for_questions = (
                clean_content[:max_content_limit]
                if len(clean_content) > max_content_limit
                else clean_content
            )

            # Подробное логирование информации о контенте урока
            self.logger.info(f"=== ГЕНЕРАЦИЯ ВОПРОСОВ для урока '{lesson_title}' ===")
            self.logger.info(
                f"  📄 Исходный размер HTML контента: {len(lesson_content)} символов"
            )
            self.logger.info(
                f"  🧹 Размер после очистки HTML: {len(clean_content)} символов"
            )
            self.logger.info(
                f"  🔗 Передается в API: {len(content_for_questions)} символов"
            )
            self.logger.info(
                f"  📊 Процент использования: {(len(content_for_questions)/len(clean_content)*100):.1f}%"
            )
            self.logger.info(f"  🎯 Лимит контента: {max_content_limit} символов")

            if len(content_for_questions) < 500:
                self.logger.warning(
                    f"⚠️  ВНИМАНИЕ: Очень мало контента для генерации вопросов ({len(content_for_questions)} символов)"
                )

            # Показываем превью того, что отправляется в API
            preview_length = min(300, len(content_for_questions))
            content_preview = (
                content_for_questions[:preview_length]
                .replace("\n", " ")
                .replace("\r", " ")
            )
            self.logger.info(f"  👀 Превью контента для API: {content_preview}...")

            if lesson_content != content_for_questions:
                self.logger.info(
                    f"  ✂️  Контент был обрезан с {len(clean_content)} до {len(content_for_questions)} символов"
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

            # Логируем размер промпта
            prompt_size = len(prompt)
            self.logger.info(f"  • Размер итогового промпта: {prompt_size} символов")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            response_content = response.choices[0].message.content.strip()
            self.logger.info(f"Получен ответ от API: {len(response_content)} символов")

            try:
                questions_data = json.loads(response_content)
            except json.JSONDecodeError as e:
                self.logger.error(f"Ошибка парсинга JSON: {str(e)}")
                self.logger.error(f"Ответ API: {response_content[:500]}...")
                raise Exception(f"API вернул некорректный JSON: {str(e)}")

            questions = self._extract_questions_from_response(questions_data)

            if not questions or len(questions) == 0:
                raise Exception("API не вернул вопросы или вернул пустой список")

            # Рандомизируем порядок вопросов для разнообразия
            random.shuffle(questions)

            self.logger.info(
                f"Успешно сгенерировано {len(questions)} вопросов для урока '{lesson_title}'"
            )
            return questions[:num_questions]  # Возвращаем только нужное количество

        except Exception as e:
            self.logger.error(f"Критическая ошибка при генерации тестов: {str(e)}")
            raise

    def _clean_html_for_analysis(self, lesson_content):
        """
        Очищает HTML теги из содержания урока для лучшего анализа.

        Args:
            lesson_content (str): Содержание урока с HTML

        Returns:
            str: Очищенное содержание
        """
        # Удаляем HTML теги
        clean_content = re.sub(r"<[^>]+>", " ", lesson_content)

        # Удаляем множественные пробелы и переносы строк
        clean_content = re.sub(r"\s+", " ", clean_content).strip()

        # Удаляем специальные символы, которые могут мешать анализу
        clean_content = re.sub(r"&[^;]+;", " ", clean_content)

        return clean_content

    def _extract_questions_from_response(self, questions_data):
        """
        Извлекает вопросы из ответа API.

        Args:
            questions_data (dict): Ответ API в формате JSON

        Returns:
            list: Список вопросов
        """
        # Проверяем, есть ли в ответе ключ "questions"
        if "questions" in questions_data:
            return questions_data["questions"]
        elif isinstance(questions_data, list):
            # Если API вернул сразу список вопросов
            return questions_data
        else:
            # Проверяем, содержит ли ответ другие ключи, которые могут быть списком вопросов
            for key, value in questions_data.items():
                if isinstance(value, list) and len(value) > 0:
                    # Проверяем, что это действительно вопросы
                    if isinstance(value[0], dict) and (
                        "text" in value[0] or "question" in value[0]
                    ):
                        return value
            raise Exception("API вернул некорректный формат вопросов")

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
        КРИТИЧЕСКИ ВАЖНО: Создавай вопросы СТРОГО на основе предоставленного материала урока!

        На основе СЛЕДУЮЩЕГО урока создай {num_questions} вопросов для проверки знаний НА РУССКОМ ЯЗЫКЕ:

        Курс: {course}
        Раздел: {section}
        Тема: {topic}
        Урок: {lesson_title}

        ПОЛНОЕ содержание урока для генерации вопросов:
        {content_for_questions}

        СТРОГИЕ ТРЕБОВАНИЯ:
        1. ✅ ВСЕ вопросы и варианты ответов ОБЯЗАТЕЛЬНО на русском языке!
        2. ✅ Вопросы должны основываться ТОЛЬКО на материале, представленном в данном уроке
        3. ✅ НЕ добавляй информацию, которой нет в тексте урока
        4. ✅ Правильные ответы должны быть явно представлены в содержании урока
        5. ✅ Неправильные варианты должны быть логически связаны с темой, но четко отличимы от правильного ответа
        6. ✅ Каждый вопрос должен проверять конкретные знания из предоставленного материала
        7. ✅ Используй конкретные примеры, термины и концепции из урока

        ФОРМАТ ОТВЕТА (строго JSON):
        {{
            "questions": [
                {{
                    "text": "Текст вопроса на русском языке",
                    "options": [
                        "A. Первый вариант ответа",
                        "B. Второй вариант ответа",
                        "C. Третий вариант ответа"
                    ],
                    "correct_option": "A"
                }}
            ]
        }}

        ВАЖНО:
        - Вопросы должны проверять понимание ключевых концепций, представленных именно в этом уроке
        - Студент должен легко найти ответы на все вопросы, внимательно изучив предоставленный материал
        - НЕ используй общие знания - только информацию из урока
        - Каждый неправильный вариант должен быть правдоподобным, но однозначно неверным согласно материалу урока

        Создай именно {num_questions} вопросов в указанном JSON формате.
        """

    def _randomize_answer_options(self, questions):
        """
        Рандомизирует порядок вариантов ответов для каждого вопроса.

        Args:
            questions (list): Список вопросов

        Returns:
            list: Список вопросов с рандомизированными вариантами ответов
        """
        randomized_questions = []

        for question in questions:
            if "options" not in question or "correct_option" not in question:
                # Если структура вопроса неправильная, оставляем как есть
                randomized_questions.append(question)
                continue

            options = question["options"][:]  # Копируем список
            correct_option = question["correct_option"]

            # Находим правильный ответ
            correct_answer = None
            for option in options:
                if option.startswith(correct_option):
                    correct_answer = option
                    break

            if correct_answer is None:
                # Если не нашли правильный ответ, оставляем как есть
                randomized_questions.append(question)
                continue

            # Рандомизируем порядок
            random.shuffle(options)

            # Находим новую позицию правильного ответа
            new_correct_option = None
            for i, option in enumerate(options):
                if option == correct_answer:
                    # Обновляем букву в соответствии с новой позицией
                    letter = chr(ord("A") + i)
                    options[i] = f"{letter}. {option.split('. ', 1)[1]}"
                    new_correct_option = letter
                else:
                    # Обновляем букву для остальных вариантов
                    letter = chr(ord("A") + i)
                    options[i] = f"{letter}. {option.split('. ', 1)[1]}"

            # Создаем новый вопрос с рандомизированными вариантами
            new_question = question.copy()
            new_question["options"] = options
            new_question["correct_option"] = new_correct_option

            randomized_questions.append(new_question)

        return randomized_questions
