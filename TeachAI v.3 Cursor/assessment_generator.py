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

            # НОВОЕ: Рандомизируем порядок вариантов ответов
            randomized_questions = self._randomize_answer_options(questions)

            self.logger.info(
                f"Успешно сгенерировано {len(randomized_questions)} вопросов на русском языке с рандомизированными ответами"
            )
            return randomized_questions

        except Exception as e:
            self.logger.error(f"Критическая ошибка при генерации вопросов: {str(e)}")
            raise Exception(
                f"Не удалось сгенерировать вопросы для урока '{lesson}': {str(e)}"
            )

    def _randomize_answer_options(self, questions):
        """
        Рандомизирует порядок вариантов ответов в вопросах.

        Args:
            questions (list): Список вопросов с вариантами ответов

        Returns:
            list: Список вопросов с перемешанными вариантами ответов
        """
        try:
            randomized_questions = []

            for question in questions:
                # Получаем исходные данные
                original_options = question.get("options", [])
                original_correct = question.get(
                    "correct_option", question.get("correct_answer", 1)
                )

                if not original_options or len(original_options) < 2:
                    # Если вариантов мало, оставляем как есть
                    randomized_questions.append(question)
                    continue

                # Создаем список индексов для перемешивания
                indices = list(range(len(original_options)))
                random.shuffle(indices)

                # Создаем новый порядок вариантов
                new_options = []
                new_correct_option = 1  # По умолчанию

                for new_index, old_index in enumerate(indices):
                    new_options.append(original_options[old_index])
                    # Находим где теперь находится правильный ответ
                    if (
                        old_index + 1
                    ) == original_correct:  # +1 потому что индексы начинаются с 1
                        new_correct_option = new_index + 1

                # Создаем новый вопрос с перемешанными вариантами
                new_question = question.copy()
                new_question["options"] = new_options
                new_question["correct_option"] = new_correct_option

                # Обеспечиваем совместимость со старым форматом
                if "correct_answer" in new_question:
                    new_question["correct_answer"] = new_correct_option

                randomized_questions.append(new_question)

                # Отладочная информация
                self.logger.debug(
                    f"Вопрос рандомизирован: правильный ответ перемещен с позиции {original_correct} на позицию {new_correct_option}"
                )

            return randomized_questions

        except Exception as e:
            self.logger.error(f"Ошибка при рандомизации вариантов ответов: {str(e)}")
            # В случае ошибки возвращаем исходные вопросы
            return questions

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
        На основе СТРОГО следующего урока создай {num_questions} вопросов для проверки знаний НА РУССКОМ ЯЗЫКЕ:

        Курс: {course}
        Раздел: {section}
        Тема: {topic}
        Урок: {lesson_title}

        ПОЛНОЕ содержание урока:
        {content_for_questions}

        ВАЖНЫЕ ТРЕБОВАНИЯ:
        1. ВСЕ вопросы и варианты ответов должны быть ОБЯЗАТЕЛЬНО на русском языке!
        2. Вопросы должны основываться ТОЛЬКО на материале, представленном в данном уроке
        3. НЕ добавляй информацию, которой нет в тексте урока
        4. Правильные ответы должны быть явно представлены в содержании урока
        5. Неправильные варианты должны быть логически связаны с темой, но четко отличимы от правильного ответа

        Для каждого вопроса предоставь:
        1. Текст вопроса (на русском языке)
        2. Три варианта ответа (на русском языке)
        3. Номер правильного ответа (1, 2 или 3)

        Вопросы должны проверять понимание ключевых концепций, представленных именно в этом уроке.
        Убедись, что студент сможет найти ответы на все вопросы, внимательно изучив предоставленный материал урока.

        Ответ должен быть в формате JSON - массив объектов, где каждый объект имеет поля:
        - text: текст вопроса (на русском языке)
        - options: массив из трех вариантов ответа (на русском языке)
        - correct_option: номер правильного ответа (1, 2 или 3)

        Убедись, что ВСЕ тексты в ответе написаны НА РУССКОМ ЯЗЫКЕ!
        """
