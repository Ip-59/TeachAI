"""
Модуль для управления данными курсов.
Отвечает за планы курсов, данные уроков, загрузку курсов и навигацию по урокам.
РЕФАКТОРИНГ: Выделен из state_manager.py для лучшей модульности
"""

import json
import logging


class CourseDataManager:
    """Менеджер данных курсов."""

    def __init__(self, state_manager):
        """
        Инициализация менеджера данных курсов.

        Args:
            state_manager: Ссылка на основной StateManager
        """
        self.state_manager = state_manager
        self.logger = logging.getLogger(__name__)

    def save_course_plan(self, course_plan):
        """
        Сохраняет сгенерированный учебный план.

        Args:
            course_plan (dict): Структура учебного плана

        Returns:
            bool: True если обновление прошло успешно, иначе False
        """
        try:
            self.state_manager.state["course_plan"] = course_plan

            course_title = course_plan.get("title", "Неизвестный курс")
            self.logger.info(f"Учебный план для курса '{course_title}' сохранен")

            # Сохраняем обновленное состояние
            return self.state_manager.save_state()
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении учебного плана: {str(e)}")
            return False

    def get_course_plan(self):
        """
        Получает текущий учебный план.

        Returns:
            dict: Словарь с учебным планом
        """
        try:
            return self.state_manager.state["course_plan"]
        except Exception as e:
            self.logger.error(f"Ошибка при получении учебного плана: {str(e)}")
            return {
                "id": "",
                "title": "",
                "description": "",
                "total_duration_minutes": 0,
                "sections": [],
            }

    def get_course_by_id(self, course_id):
        """
        Загружает информацию о курсе из файла courses.json.

        Args:
            course_id (str): Идентификатор курса

        Returns:
            dict: Данные о курсе или None, если курс не найден
        """
        try:
            courses_file = self.state_manager.project_dir / "courses.json"
            with open(courses_file, "r", encoding="utf-8") as f:
                courses_data = json.load(f)

            for course in courses_data["courses"]:
                if course["id"] == course_id:
                    self.logger.debug(f"Найден курс: {course_id}")
                    return course

            self.logger.warning(f"Курс с ID '{course_id}' не найден")
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке данных о курсе: {str(e)}")
            return None

    def get_all_courses(self):
        """
        Загружает список всех доступных курсов из файла courses.json.

        Returns:
            list: Список курсов или пустой список в случае ошибки
        """
        try:
            courses_file = self.state_manager.project_dir / "courses.json"
            with open(courses_file, "r", encoding="utf-8") as f:
                courses_data = json.load(f)

            courses_count = len(courses_data["courses"])
            self.logger.debug(f"Загружено {courses_count} курсов")
            return courses_data["courses"]
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке списка курсов: {str(e)}")
            return []

    def get_next_lesson(self):
        """
        ИСПРАВЛЕНО: Определяет следующий урок с проверкой завершенности текущего.

        Returns:
            tuple: (section_id, topic_id, lesson_id, lesson_data) или (None, None, None, None) если следующего урока нет
        """
        try:
            current_section = self.state_manager.state["learning"]["current_section"]
            current_topic = self.state_manager.state["learning"]["current_topic"]
            current_lesson = self.state_manager.state["learning"]["current_lesson"]
            course_plan = self.state_manager.state["course_plan"]

            # Если план курса пуст, возвращаем None
            if not course_plan.get("sections"):
                self.logger.warning("План курса пуст или не содержит разделов")
                return None, None, None, None

            # ИСПРАВЛЕНО: Если есть текущий урок, проверяем его завершенность
            if current_section and current_topic and current_lesson:
                current_lesson_id = (
                    f"{current_section}:{current_topic}:{current_lesson}"
                )

                # Если текущий урок НЕ завершен - возвращаем его для повторного прохождения
                if not self.state_manager.learning_progress.is_lesson_completed(
                    current_lesson_id
                ):
                    self.logger.info(
                        f"Текущий урок {current_lesson_id} не завершен - возвращаем его для повторного изучения"
                    )

                    # Находим данные текущего урока
                    lesson_data = self.get_lesson_data(
                        current_section, current_topic, current_lesson
                    )
                    if lesson_data:
                        return (
                            current_section,
                            current_topic,
                            current_lesson,
                            lesson_data,
                        )
                    else:
                        self.logger.warning(
                            f"Данные текущего урока {current_lesson_id} не найдены"
                        )
                        # Продолжаем поиск следующего урока

            # Если текущего урока нет или он завершен, ищем следующий урок
            if not current_section or not current_topic or not current_lesson:
                self.logger.info(
                    "Текущий урок не найден, возвращаем первый урок из плана"
                )
                return self._get_first_lesson_from_plan(course_plan)

            # ИСПРАВЛЕНО: Ищем следующий урок после завершенного текущего
            next_lesson = self._find_next_lesson_in_plan(
                course_plan, current_section, current_topic, current_lesson
            )

            if next_lesson:
                section_id, topic_id, lesson_id, lesson_data = next_lesson
                self.logger.info(
                    f"Найден следующий урок: {section_id}:{topic_id}:{lesson_id}"
                )
                return section_id, topic_id, lesson_id, lesson_data
            else:
                self.logger.info("Все уроки курса пройдены")
                return None, None, None, None

        except Exception as e:
            self.logger.error(f"Ошибка при определении следующего урока: {str(e)}")
            return None, None, None, None

    def _get_first_lesson_from_plan(self, course_plan):
        """
        Получает первый урок из плана курса.

        Args:
            course_plan (dict): План курса

        Returns:
            tuple: (section_id, topic_id, lesson_id, lesson_data) или (None, None, None, None)
        """
        try:
            # Получаем первый раздел
            first_section = course_plan["sections"][0]
            if not first_section.get("topics"):
                self.logger.warning(f"Раздел {first_section.get('id')} не содержит тем")
                return None, None, None, None

            # Получаем первую тему
            first_topic = first_section["topics"][0]
            if not first_topic.get("lessons"):
                self.logger.warning(f"Тема {first_topic.get('id')} не содержит уроков")
                return None, None, None, None

            # Получаем первый урок
            first_lesson = first_topic["lessons"][0]
            return (
                first_section["id"],
                first_topic["id"],
                first_lesson["id"],
                first_lesson,
            )

        except Exception as e:
            self.logger.error(f"Ошибка при получении первого урока: {str(e)}")
            return None, None, None, None

    def _find_next_lesson_in_plan(
        self, course_plan, current_section, current_topic, current_lesson
    ):
        """
        Находит следующий урок в плане курса.

        Args:
            course_plan (dict): План курса
            current_section, current_topic, current_lesson (str): Текущие ID

        Returns:
            tuple: (section_id, topic_id, lesson_id, lesson_data) или None
        """
        try:
            # Ищем текущее положение в курсе
            for section in course_plan["sections"]:
                if section["id"] == current_section:
                    # Проверяем наличие тем в разделе
                    if not section.get("topics"):
                        self.logger.warning(f"Раздел {section['id']} не содержит тем")
                        continue

                    for topic in section["topics"]:
                        if topic["id"] == current_topic:
                            # Проверяем наличие уроков в теме
                            if not topic.get("lessons"):
                                self.logger.warning(
                                    f"Тема {topic['id']} не содержит уроков"
                                )
                                continue

                            # Ищем текущий урок и определяем следующий
                            for i, lesson in enumerate(topic["lessons"]):
                                if lesson["id"] == current_lesson:
                                    # Если есть еще уроки в текущей теме
                                    if i < len(topic["lessons"]) - 1:
                                        next_lesson = topic["lessons"][i + 1]
                                        return (
                                            section["id"],
                                            topic["id"],
                                            next_lesson["id"],
                                            next_lesson,
                                        )

                                    # Если уроки в теме закончились, ищем следующую тему
                                    topic_index = section["topics"].index(topic)
                                    if topic_index < len(section["topics"]) - 1:
                                        next_topic = section["topics"][topic_index + 1]

                                        # Проверяем наличие уроков в следующей теме
                                        if not next_topic.get("lessons"):
                                            self.logger.warning(
                                                f"Тема {next_topic['id']} не содержит уроков"
                                            )
                                            return None

                                        next_lesson = next_topic["lessons"][0]
                                        return (
                                            section["id"],
                                            next_topic["id"],
                                            next_lesson["id"],
                                            next_lesson,
                                        )

                                    # Если темы в разделе закончились, ищем следующий раздел
                                    section_index = course_plan["sections"].index(
                                        section
                                    )
                                    if section_index < len(course_plan["sections"]) - 1:
                                        next_section = course_plan["sections"][
                                            section_index + 1
                                        ]

                                        # Проверяем наличие тем в следующем разделе
                                        if not next_section.get("topics"):
                                            self.logger.warning(
                                                f"Раздел {next_section['id']} не содержит тем"
                                            )
                                            return None

                                        next_topic = next_section["topics"][0]

                                        # Проверяем наличие уроков в первой теме следующего раздела
                                        if not next_topic.get("lessons"):
                                            self.logger.warning(
                                                f"Тема {next_topic['id']} не содержит уроков"
                                            )
                                            return None

                                        next_lesson = next_topic["lessons"][0]
                                        return (
                                            next_section["id"],
                                            next_topic["id"],
                                            next_lesson["id"],
                                            next_lesson,
                                        )

                                    # Если все разделы закончились, курс завершен
                                    return None

            # Если текущее положение не найдено, возвращаем первый урок
            self.logger.warning(
                "Текущее положение в курсе не найдено, возвращаем первый урок"
            )
            return self._get_first_lesson_from_plan(course_plan)

        except Exception as e:
            self.logger.error(f"Ошибка при поиске следующего урока: {str(e)}")
            return None

    def get_lesson_data(self, section_id, topic_id, lesson_id):
        """
        Получает данные урока из учебного плана.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            dict: Данные урока или None, если урок не найден
        """
        try:
            course_plan = self.state_manager.state["course_plan"]

            for section in course_plan["sections"]:
                if section["id"] == section_id:
                    # Проверяем наличие тем в разделе
                    if "topics" not in section:
                        self.logger.warning(
                            f"Раздел {section_id} не содержит ключа 'topics'"
                        )
                        continue

                    for topic in section["topics"]:
                        if topic["id"] == topic_id:
                            # Проверяем наличие уроков в теме
                            if "lessons" not in topic:
                                self.logger.warning(
                                    f"Тема {topic_id} не содержит ключа 'lessons'"
                                )
                                continue

                            for lesson in topic["lessons"]:
                                if lesson["id"] == lesson_id:
                                    self.logger.debug(
                                        f"Найден урок: {section_id}:{topic_id}:{lesson_id}"
                                    )
                                    return lesson

            self.logger.warning(
                f"Урок не найден: section={section_id}, topic={topic_id}, lesson={lesson_id}"
            )
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении данных урока: {str(e)}")
            return None
