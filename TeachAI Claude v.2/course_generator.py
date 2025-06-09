"""
Модуль для генерации курсов и их планов.
Отвечает за создание структурированных курсов на основе названия, описания и данных пользователя.

ИСПРАВЛЕНО ЭТАП 30: Создан недостающий модуль для устранения ImportError.
"""

import json
import logging
from content_utils import BaseContentGenerator


class CourseGenerator(BaseContentGenerator):
    """Генератор курсов и учебных планов."""

    def __init__(self, api_key):
        """
        Инициализация генератора курсов.

        Args:
            api_key (str): API ключ OpenAI
        """
        super().__init__(api_key)
        self.logger = logging.getLogger(__name__)
        self.logger.info("CourseGenerator инициализирован")

    def generate_course_plan(self, course_name, course_description, user_data):
        """
        Генерирует план курса на основе названия, описания и данных пользователя.

        Args:
            course_name (str): Название курса
            course_description (str): Описание курса
            user_data (dict): Данные пользователя (имя, уровень, интересы)

        Returns:
            dict: Структурированный план курса

        Raises:
            Exception: Если не удалось сгенерировать план курса
        """
        try:
            self.logger.info(f"Генерация плана курса: {course_name}")

            # Извлекаем данные пользователя
            user_name = user_data.get("name", "Пользователь")
            user_level = user_data.get("level", "beginner")
            user_interests = user_data.get("interests", [])

            # Формируем промпт для генерации плана курса
            prompt = self._build_course_plan_prompt(
                course_name, course_description, user_name, user_level, user_interests
            )

            messages = [
                {
                    "role": "system",
                    "content": "Ты - опытный методист образовательных программ, создающий персонализированные учебные планы.",
                },
                {"role": "user", "content": prompt},
            ]

            # Запрашиваем план курса от API
            response_content = self.make_api_request(
                messages=messages,
                temperature=0.4,  # Умеренная температура для баланса креативности и структурированности
                max_tokens=3000,
                response_format={"type": "json_object"},
            )

            # Парсим ответ
            course_plan = json.loads(response_content)

            # Валидируем и исправляем структуру плана
            validated_plan = self._validate_and_fix_course_plan(
                course_plan, course_name, course_description, user_data
            )

            # Сохраняем отладочную информацию
            self.save_debug_response(
                "course_plan",
                prompt,
                response_content,
                {
                    "course_name": course_name,
                    "course_description": course_description,
                    "user_name": user_name,
                    "user_level": user_level,
                    "user_interests": user_interests,
                },
            )

            if not validated_plan or not validated_plan.get("sections"):
                raise Exception("API вернул некорректную структуру плана курса")

            self.logger.info(f"План курса '{course_name}' успешно сгенерирован")
            return validated_plan

        except Exception as e:
            self.logger.error(f"Критическая ошибка при генерации плана курса: {str(e)}")
            # Возвращаем резервный план
            return self._create_fallback_course_plan(
                course_name, course_description, user_data
            )

    def _build_course_plan_prompt(
        self, course_name, course_description, user_name, user_level, user_interests
    ):
        """
        Создает промпт для генерации плана курса.

        Args:
            course_name (str): Название курса
            course_description (str): Описание курса
            user_name (str): Имя пользователя
            user_level (str): Уровень пользователя
            user_interests (list): Интересы пользователя

        Returns:
            str: Промпт для API
        """
        interests_str = ", ".join(user_interests) if user_interests else "общие знания"

        prompt = f"""
        Создай персонализированный учебный план для курса "{course_name}".

        ИНФОРМАЦИЯ О КУРСЕ:
        - Название: {course_name}
        - Описание: {course_description}

        ИНФОРМАЦИЯ О СТУДЕНТЕ:
        - Имя: {user_name}
        - Уровень: {user_level}
        - Интересы: {interests_str}

        ТРЕБОВАНИЯ К ПЛАНУ:
        1. Структура должна быть логичной и последовательной
        2. Разделы должны быть связаны между собой
        3. Каждый урок должен иметь четкие цели
        4. Учитывай уровень студента ({user_level})
        5. Включи практические задания и примеры

        ОБЯЗАТЕЛЬНАЯ СТРУКТУРА JSON:
        {{
            "id": "course-id",
            "title": "{course_name}",
            "description": "{course_description}",
            "total_duration_minutes": 1800,
            "target_audience": "{user_level}",
            "sections": [
                {{
                    "id": "section-1",
                    "title": "Название раздела",
                    "description": "Описание раздела",
                    "duration_minutes": 600,
                    "topics": [
                        {{
                            "id": "topic-1-1",
                            "title": "Название темы",
                            "description": "Описание темы",
                            "duration_minutes": 300,
                            "lessons": [
                                {{
                                    "id": "lesson-1-1-1",
                                    "title": "Название урока",
                                    "description": "Описание урока",
                                    "duration_minutes": 30,
                                    "objectives": ["Цель 1", "Цель 2"],
                                    "keywords": ["ключевое_слово1", "ключевое_слово2"]
                                }}
                            ]
                        }}
                    ]
                }}
            ]
        }}

        Создай план из 2-4 разделов, каждый с 2-3 темами, каждая тема с 3-5 уроками.
        Все ID должны быть уникальными и в формате "section-N", "topic-N-M", "lesson-N-M-K".
        """

        return prompt

    def _validate_and_fix_course_plan(
        self, course_plan, course_name, course_description, user_data
    ):
        """
        Валидирует и исправляет структуру плана курса.

        Args:
            course_plan (dict): План курса от API
            course_name (str): Название курса
            course_description (str): Описание курса
            user_data (dict): Данные пользователя

        Returns:
            dict: Исправленный план курса
        """
        try:
            # Основные поля курса
            if "id" not in course_plan:
                course_plan["id"] = "course-1"
            if "title" not in course_plan:
                course_plan["title"] = course_name
            if "description" not in course_plan:
                course_plan["description"] = course_description
            if "total_duration_minutes" not in course_plan:
                course_plan["total_duration_minutes"] = 1800
            if "target_audience" not in course_plan:
                course_plan["target_audience"] = user_data.get("level", "beginner")

            # Проверяем наличие разделов
            if "sections" not in course_plan or not isinstance(
                course_plan["sections"], list
            ):
                self.logger.warning("Создаем минимальную структуру разделов...")
                course_plan["sections"] = self._create_minimal_sections(course_name)

            # Валидируем каждый раздел
            for i, section in enumerate(course_plan["sections"]):
                if not isinstance(section, dict):
                    continue

                # Исправляем ключи раздела
                if "id" not in section:
                    section["id"] = f"section-{i+1}"
                if "title" not in section:
                    section["title"] = f"Раздел {i+1}"
                if "description" not in section:
                    section["description"] = f"Описание раздела {i+1}"
                if "duration_minutes" not in section:
                    section["duration_minutes"] = 600

                # Проверяем темы
                if "topics" not in section or not isinstance(section["topics"], list):
                    section["topics"] = self._create_minimal_topics(i + 1)

                # Валидируем каждую тему
                for j, topic in enumerate(section["topics"]):
                    if not isinstance(topic, dict):
                        continue

                    # Исправляем ключи темы
                    if "id" not in topic:
                        topic["id"] = f"topic-{i+1}-{j+1}"
                    if "title" not in topic:
                        topic["title"] = f"Тема {j+1}"
                    if "description" not in topic:
                        topic["description"] = f"Описание темы {j+1}"
                    if "duration_minutes" not in topic:
                        topic["duration_minutes"] = 300

                    # Проверяем уроки
                    if "lessons" not in topic or not isinstance(topic["lessons"], list):
                        topic["lessons"] = self._create_minimal_lessons(i + 1, j + 1)

                    # Валидируем каждый урок
                    for k, lesson in enumerate(topic["lessons"]):
                        if not isinstance(lesson, dict):
                            continue

                        # Исправляем ключи урока
                        if "id" not in lesson:
                            lesson["id"] = f"lesson-{i+1}-{j+1}-{k+1}"
                        if "title" not in lesson:
                            lesson["title"] = f"Урок {k+1}"
                        if "description" not in lesson:
                            lesson["description"] = f"Описание урока {k+1}"
                        if "duration_minutes" not in lesson:
                            lesson["duration_minutes"] = 30
                        if "objectives" not in lesson:
                            lesson["objectives"] = [
                                "Изучить основы",
                                "Получить практические навыки",
                            ]
                        if "keywords" not in lesson:
                            lesson["keywords"] = ["основы", "практика"]

            self.logger.info("План курса валидирован и исправлен")
            return course_plan

        except Exception as e:
            self.logger.error(f"Ошибка при валидации плана курса: {str(e)}")
            return self._create_fallback_course_plan(
                course_name, course_description, user_data
            )

    def _create_minimal_sections(self, course_name):
        """Создает минимальную структуру разделов."""
        return [
            {
                "id": "section-1",
                "title": f"Введение в {course_name}",
                "description": f"Основы и базовые концепции {course_name}",
                "duration_minutes": 600,
                "topics": self._create_minimal_topics(1),
            }
        ]

    def _create_minimal_topics(self, section_num):
        """Создает минимальную структуру тем."""
        return [
            {
                "id": f"topic-{section_num}-1",
                "title": "Основные концепции",
                "description": "Изучение фундаментальных понятий",
                "duration_minutes": 300,
                "lessons": self._create_minimal_lessons(section_num, 1),
            }
        ]

    def _create_minimal_lessons(self, section_num, topic_num):
        """Создает минимальную структуру уроков."""
        return [
            {
                "id": f"lesson-{section_num}-{topic_num}-1",
                "title": "Первый урок",
                "description": "Знакомство с основными концепциями",
                "duration_minutes": 30,
                "objectives": ["Понять основы", "Получить первые навыки"],
                "keywords": ["введение", "основы", "концепции"],
            }
        ]

    def _create_fallback_course_plan(self, course_name, course_description, user_data):
        """Создает резервный план курса при полном сбое."""
        self.logger.warning("Создание резервного плана курса")

        return {
            "id": "course-1",
            "title": course_name,
            "description": course_description,
            "total_duration_minutes": 1800,
            "target_audience": user_data.get("level", "beginner"),
            "sections": [
                {
                    "id": "section-1",
                    "title": f"Введение в {course_name}",
                    "description": "Начальные знания и основы",
                    "duration_minutes": 600,
                    "topics": [
                        {
                            "id": "topic-1-1",
                            "title": "Основы",
                            "description": "Фундаментальные понятия",
                            "duration_minutes": 300,
                            "lessons": [
                                {
                                    "id": "lesson-1-1-1",
                                    "title": "Первый урок",
                                    "description": "Знакомство с основными концепциями",
                                    "duration_minutes": 30,
                                    "objectives": [
                                        "Понять основы",
                                        "Получить первые навыки",
                                    ],
                                    "keywords": [
                                        "введение",
                                        "основы",
                                        course_name.lower(),
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
