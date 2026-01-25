"""
Модуль для генерации учебных планов курсов.
Отвечает за создание структурированных планов обучения на основе данных о курсе и времени.
"""

import json
from content_utils import BaseContentGenerator


class CoursePlanGenerator(BaseContentGenerator):
    """Генератор учебных планов курсов."""

    def __init__(self, api_key):
        """
        Инициализация генератора учебных планов.

        Args:
            api_key (str): API ключ OpenAI
        """
        super().__init__(api_key)
        self.logger.info("CoursePlanGenerator инициализирован")

    def generate_course_plan(
        self, course_data, total_study_hours, lesson_duration_minutes
    ):
        """
        Генерирует учебный план курса на основе данных о курсе и времени обучения.

        Args:
            course_data (dict): Данные о курсе (id, title, description)
            total_study_hours (int): Общее время обучения в часах
            lesson_duration_minutes (int): Длительность одного занятия в минутах

        Returns:
            dict: Структурированный учебный план

        Raises:
            Exception: Если не удалось сгенерировать план курса
        """
        try:
            prompt = self._build_course_plan_prompt(
                course_data, total_study_hours, lesson_duration_minutes
            )

            messages = [
                {
                    "role": "system",
                    "content": "Ты - опытный методист образовательных программ.",
                },
                {"role": "user", "content": prompt},
            ]

            response_content = self.make_api_request(
                messages=messages,
                temperature=0.7,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )

            # Сохраняем отладочную информацию
            self.save_debug_response(
                "course_plan",
                prompt,
                response_content,
                {
                    "course_id": course_data.get("id"),
                    "total_study_hours": total_study_hours,
                    "lesson_duration_minutes": lesson_duration_minutes,
                },
            )

            course_plan = json.loads(response_content)

            # ОТЛАДКА: Выводим структуру плана для диагностики
            print("🔍 ОТЛАДКА: Структура полученного плана курса:")
            print(f"Ключи верхнего уровня: {list(course_plan.keys())}")

            # ВАЛИДАЦИЯ И ИСПРАВЛЕНИЕ структуры
            course_plan = self._validate_and_fix_course_plan(
                course_plan, course_data, total_study_hours, lesson_duration_minutes
            )

            if "sections" in course_plan:
                print(f"✅ Количество разделов: {len(course_plan['sections'])}")
                if course_plan["sections"]:
                    first_section = course_plan["sections"][0]
                    print(f"✅ Ключи первого раздела: {list(first_section.keys())}")
                    if "topics" in first_section:
                        print(
                            f"✅ Количество тем в первом разделе: {len(first_section['topics'])}"
                        )
                        if first_section["topics"]:
                            first_topic = first_section["topics"][0]
                            print(f"✅ Ключи первой темы: {list(first_topic.keys())}")
                            if "lessons" in first_topic:
                                print(
                                    f"✅ Количество уроков в первой теме: {len(first_topic['lessons'])}"
                                )
                                if first_topic["lessons"]:
                                    first_lesson = first_topic["lessons"][0]
                                    print(
                                        f"✅ Ключи первого урока: {list(first_lesson.keys())}"
                                    )
            else:
                print("❌ Проблема с валидацией плана курса!")

            self.logger.info("Учебный план успешно сгенерирован через OpenAI API")
            return course_plan

        except Exception as e:
            self.logger.error(
                f"Критическая ошибка при генерации учебного плана: {str(e)}"
            )
            raise Exception(f"Не удалось сгенерировать учебный план: {str(e)}")

    def _build_course_plan_prompt(
        self, course_data, total_study_hours, lesson_duration_minutes
    ):
        """
        Создает промпт для генерации учебного плана.

        Args:
            course_data (dict): Данные о курсе
            total_study_hours (int): Общее время обучения в часах
            lesson_duration_minutes (int): Длительность одного занятия в минутах

        Returns:
            str: Промпт для API
        """
        return f"""
        Создай детальный учебный план для курса:

        Название курса: {course_data["title"]}
        Описание курса: {course_data["description"]}

        Общее время обучения: {total_study_hours} часов
        Длительность одного занятия: {lesson_duration_minutes} минут

        ВАЖНО: Ответ должен быть в СТРОГО ОПРЕДЕЛЕННОМ формате JSON:

        {{
            "id": "{course_data.get('id', 'course-1')}",
            "title": "{course_data['title']}",
            "description": "{course_data['description']}",
            "total_duration_minutes": {total_study_hours * 60},
            "sections": [
                {{
                    "id": "section-1",
                    "title": "Название раздела",
                    "description": "Описание раздела",
                    "duration_minutes": 180,
                    "topics": [
                        {{
                            "id": "topic-1",
                            "title": "Название темы",
                            "description": "Описание темы",
                            "duration_minutes": 90,
                            "lessons": [
                                {{
                                    "id": "lesson-1",
                                    "title": "Название урока",
                                    "description": "Описание урока",
                                    "duration_minutes": {lesson_duration_minutes},
                                    "keywords": ["ключевое_слово1", "ключевое_слово2"]
                                }}
                            ]
                        }}
                    ]
                }}
            ]
        }}

        Создай реалистичный план с 2-3 разделами, 2-3 темами в каждом разделе, и 2-3 уроками в каждой теме.
        Учебный план должен соответствовать общему времени обучения {total_study_hours} часов.
        Продолжительность каждого урока должна быть примерно {lesson_duration_minutes} минут.

        ОБЯЗАТЕЛЬНО используй точно такую структуру JSON с ключами: id, title, description, duration_minutes, sections, topics, lessons, keywords.
        """

    def _validate_and_fix_course_plan(
        self, course_plan, course_data, total_study_hours, lesson_duration_minutes
    ):
        """
        Валидирует и исправляет структуру плана курса.

        Args:
            course_plan (dict): План курса от API
            course_data (dict): Исходные данные курса
            total_study_hours (int): Общее время обучения
            lesson_duration_minutes (int): Длительность урока

        Returns:
            dict: Исправленный план курса
        """
        try:
            # Убеждаемся, что есть основные ключи
            if "id" not in course_plan:
                course_plan["id"] = course_data.get("id", "course-1")

            if "title" not in course_plan:
                course_plan["title"] = course_data.get("title", "Курс")

            if "description" not in course_plan:
                course_plan["description"] = course_data.get(
                    "description", "Описание курса"
                )

            if "total_duration_minutes" not in course_plan:
                course_plan["total_duration_minutes"] = total_study_hours * 60

            # Проверяем наличие sections
            if "sections" not in course_plan or not isinstance(
                course_plan["sections"], list
            ):
                print("⚠️ Создаем минимальную структуру разделов...")
                course_plan["sections"] = self._create_minimal_sections(
                    course_data, lesson_duration_minutes
                )

            # Проверяем каждый раздел
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
                    section["duration_minutes"] = lesson_duration_minutes * 3

                # Проверяем наличие topics
                if "topics" not in section or not isinstance(section["topics"], list):
                    section["topics"] = self._create_minimal_topics(
                        i + 1, lesson_duration_minutes
                    )

                # Проверяем каждую тему
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
                        topic["duration_minutes"] = lesson_duration_minutes * 2

                    # Проверяем наличие lessons
                    if "lessons" not in topic or not isinstance(topic["lessons"], list):
                        topic["lessons"] = self._create_minimal_lessons(
                            i + 1, j + 1, lesson_duration_minutes
                        )

                    # Проверяем каждый урок
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
                            lesson["duration_minutes"] = lesson_duration_minutes
                        if "keywords" not in lesson:
                            lesson["keywords"] = ["основы", "практика"]

            print("✅ План курса валидирован и исправлен")
            return course_plan

        except Exception as e:
            self.logger.error(f"Ошибка при валидации плана курса: {str(e)}")
            # Возвращаем минимальный работающий план
            return self._create_fallback_plan(
                course_data, total_study_hours, lesson_duration_minutes
            )

    def _create_minimal_sections(self, course_data, lesson_duration_minutes):
        """Создает минимальную структуру разделов."""
        return [
            {
                "id": "section-1",
                "title": "Введение",
                "description": "Введение в курс",
                "duration_minutes": lesson_duration_minutes * 2,
                "topics": self._create_minimal_topics(1, lesson_duration_minutes),
            }
        ]

    def _create_minimal_topics(self, section_num, lesson_duration_minutes):
        """Создает минимальную структуру тем."""
        return [
            {
                "id": f"topic-{section_num}-1",
                "title": "Основы",
                "description": "Основные концепции",
                "duration_minutes": lesson_duration_minutes,
                "lessons": self._create_minimal_lessons(
                    section_num, 1, lesson_duration_minutes
                ),
            }
        ]

    def _create_minimal_lessons(self, section_num, topic_num, lesson_duration_minutes):
        """Создает минимальную структуру уроков."""
        return [
            {
                "id": f"lesson-{section_num}-{topic_num}-1",
                "title": "Первый урок",
                "description": "Введение в тему",
                "duration_minutes": lesson_duration_minutes,
                "keywords": ["введение", "основы"],
            }
        ]

    def _create_fallback_plan(
        self, course_data, total_study_hours, lesson_duration_minutes
    ):
        """Создает резервный план курса при полном сбое."""
        return {
            "id": course_data.get("id", "course-1"),
            "title": course_data.get("title", "Курс"),
            "description": course_data.get("description", "Описание курса"),
            "total_duration_minutes": total_study_hours * 60,
            "sections": [
                {
                    "id": "section-1",
                    "title": "Введение в курс",
                    "description": "Начальные знания и основы",
                    "duration_minutes": lesson_duration_minutes * 2,
                    "topics": [
                        {
                            "id": "topic-1-1",
                            "title": "Основы",
                            "description": "Фундаментальные понятия",
                            "duration_minutes": lesson_duration_minutes,
                            "lessons": [
                                {
                                    "id": "lesson-1-1-1",
                                    "title": "Первый урок",
                                    "description": "Знакомство с основными концепциями",
                                    "duration_minutes": lesson_duration_minutes,
                                    "keywords": ["введение", "основы", "начало"],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
