"""
Модуль для управления состоянием системы.
Отвечает за сохранение и загрузку данных о пользователе, прогрессе обучения и настройках.
РАСШИРЕНО: детальный прогресс по урокам, счетчик вопросов, улучшенная статистика
ИСПРАВЛЕНО: правильная логика завершенности уроков (проблема #87)
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime


class StateManager:
    """Менеджер состояния для управления данными пользователя и прогрессом обучения."""

    def __init__(self, state_file="data/state.json"):
        """
        Инициализация менеджера состояния.

        Args:
            state_file (str): Путь к файлу состояния
        """
        # Определяем абсолютный путь к файлу состояния
        self.project_dir = Path(__file__).parent.absolute()
        self.state_file = self.project_dir / state_file
        self.logger = logging.getLogger(__name__)

        # Создаем директорию для данных, если она не существует
        self._ensure_data_directory()

        # Загружаем состояние
        self.state = self._load_state()

    def _ensure_data_directory(self):
        """Убеждается, что директория для данных существует."""
        try:
            data_dir = self.state_file.parent
            data_dir.mkdir(exist_ok=True, parents=True)
            self.logger.debug(
                f"Директория данных создана или уже существует: {data_dir}"
            )
        except Exception as e:
            self.logger.error(f"Ошибка при создании директории данных: {str(e)}")
            # Пытаемся создать в текущей директории
            try:
                import os

                os.makedirs("data", exist_ok=True)
                self.state_file = Path("data") / "state.json"
                self.logger.info(
                    f"Используется альтернативный путь для файла состояния: {self.state_file}"
                )
            except Exception as alt_e:
                self.logger.error(
                    f"Альтернативный способ также не сработал: {str(alt_e)}"
                )

    def _load_state(self):
        """
        Загружает состояние системы из файла.

        Returns:
            dict: Состояние системы или пустой словарь, если файл не существует
        """
        try:
            if self.state_file.exists():
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                self.logger.debug(f"Состояние успешно загружено из {self.state_file}")
                return state
            else:
                self.logger.info(
                    f"Файл состояния {self.state_file} не найден, создаем новое состояние"
                )
                return self._create_default_state()
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке состояния: {str(e)}")
            return self._create_default_state()

    def _create_default_state(self):
        """
        Создает структуру состояния по умолчанию.

        Returns:
            dict: Структура состояния по умолчанию
        """
        return {
            "user": {
                "name": "",
                "total_study_hours": 0,
                "lesson_duration_minutes": 0,
                "communication_style": "friendly",
            },
            "learning": {
                "current_course": "",
                "current_section": "",
                "current_topic": "",
                "current_lesson": "",
                "completed_lessons": [],
                "lesson_scores": {},  # НОВОЕ: {lesson_id: score}
                "lesson_attempts": {},  # НОВОЕ: {lesson_id: [attempt1, attempt2, ...]}
                "lesson_completion_status": {},  # НОВОЕ: {lesson_id: is_completed}
                "questions_count": {},  # НОВОЕ: {lesson_id: question_count}
                "average_score": 0,
                "total_assessments": 0,
                "total_score": 0,
                "course_progress_percent": 0,  # НОВОЕ: общий прогресс по курсу
            },
            "course_plan": {
                "id": "",
                "title": "",
                "description": "",
                "total_duration_minutes": 0,
                "sections": [],
            },
            "system": {
                "first_run": True,
                "last_access": datetime.now().isoformat(),
                "version": "1.0.0",
            },
        }

    def save_state(self):
        """
        Сохраняет текущее состояние в файл.

        Returns:
            bool: True если сохранение прошло успешно, иначе False
        """
        try:
            # Обновляем время последнего доступа
            self.state["system"]["last_access"] = datetime.now().isoformat()

            # Создаем директорию, если она не существует
            self.state_file.parent.mkdir(exist_ok=True, parents=True)

            # Сохраняем состояние в файл
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)

            self.logger.debug(f"Состояние успешно сохранено в {self.state_file}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении состояния: {str(e)}")
            return False

    def update_user_profile(
        self, name, total_study_hours, lesson_duration_minutes, communication_style
    ):
        """
        Обновляет профиль пользователя.

        Args:
            name (str): Имя пользователя
            total_study_hours (int): Общая продолжительность обучения в часах
            lesson_duration_minutes (int): Длительность одного занятия в минутах
            communication_style (str): Формат общения (formal, friendly, casual, brief)

        Returns:
            bool: True если обновление прошло успешно, иначе False
        """
        try:
            self.state["user"]["name"] = name
            self.state["user"]["total_study_hours"] = total_study_hours
            self.state["user"]["lesson_duration_minutes"] = lesson_duration_minutes
            self.state["user"]["communication_style"] = communication_style

            # Сохраняем обновленное состояние
            return self.save_state()
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении профиля пользователя: {str(e)}")
            return False

    def update_learning_progress(
        self, course=None, section=None, topic=None, lesson=None
    ):
        """
        Обновляет прогресс обучения.

        Args:
            course (str, optional): Текущий курс
            section (str, optional): Текущий раздел
            topic (str, optional): Текущая тема
            lesson (str, optional): Текущий урок

        Returns:
            bool: True если обновление прошло успешно, иначе False
        """
        try:
            if course is not None:
                self.state["learning"]["current_course"] = course
            if section is not None:
                self.state["learning"]["current_section"] = section
            if topic is not None:
                self.state["learning"]["current_topic"] = topic

            if lesson is not None:
                self.state["learning"]["current_lesson"] = lesson
                # Добавляем урок в список пройденных, если его там еще нет
                lesson_id = f"{section}:{topic}:{lesson}"
                if lesson_id not in self.state["learning"]["completed_lessons"]:
                    self.state["learning"]["completed_lessons"].append(lesson_id)

            # Сохраняем обновленное состояние
            return self.save_state()
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении прогресса обучения: {str(e)}")
            return False

    def save_lesson_assessment(self, lesson_id, score, is_passed=True):
        """
        ИСПРАВЛЕНО: Сохраняет результат теста по уроку с правильной логикой завершенности.

        Args:
            lesson_id (str): ID урока
            score (float): Оценка за тест (0-100)
            is_passed (bool): Считается ли урок пройденным

        Returns:
            bool: True если сохранение прошло успешно, иначе False
        """
        try:
            # Инициализируем структуры, если их нет
            if "lesson_scores" not in self.state["learning"]:
                self.state["learning"]["lesson_scores"] = {}
            if "lesson_attempts" not in self.state["learning"]:
                self.state["learning"]["lesson_attempts"] = {}
            if "lesson_completion_status" not in self.state["learning"]:
                self.state["learning"]["lesson_completion_status"] = {}

            # Добавляем попытку
            if lesson_id not in self.state["learning"]["lesson_attempts"]:
                self.state["learning"]["lesson_attempts"][lesson_id] = []

            attempt_data = {
                "score": score,
                "timestamp": datetime.now().isoformat(),
                "is_passed": is_passed,
            }
            self.state["learning"]["lesson_attempts"][lesson_id].append(attempt_data)

            # Сохраняем лучший результат как текущий
            if is_passed:
                current_best = self.state["learning"]["lesson_scores"].get(lesson_id, 0)
                if score > current_best:
                    self.state["learning"]["lesson_scores"][lesson_id] = score

                # ИСПРАВЛЕНО: Урок считается завершенным только при is_passed=True
                self.state["learning"]["lesson_completion_status"][lesson_id] = True
                self.logger.info(
                    f"Урок {lesson_id} отмечен как завершенный с оценкой {score}%"
                )

            # Пересчитываем общую статистику
            self._recalculate_course_statistics()

            return self.save_state()
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении результата теста: {str(e)}")
            return False

    def is_lesson_completed(self, lesson_id):
        """
        НОВОЕ: Проверяет, завершен ли урок.

        Args:
            lesson_id (str): ID урока

        Returns:
            bool: True если урок завершен, иначе False
        """
        try:
            # Инициализируем структуру, если её нет
            if "lesson_completion_status" not in self.state["learning"]:
                self.state["learning"]["lesson_completion_status"] = {}

            completion_status = self.state["learning"]["lesson_completion_status"].get(
                lesson_id, False
            )
            self.logger.debug(
                f"Проверка завершенности урока {lesson_id}: {completion_status}"
            )
            return completion_status

        except Exception as e:
            self.logger.error(
                f"Ошибка при проверке завершенности урока {lesson_id}: {str(e)}"
            )
            return False

    def mark_lesson_incomplete(self, lesson_id):
        """
        НОВОЕ: Отмечает урок как незавершенный (для повторного прохождения).

        Args:
            lesson_id (str): ID урока

        Returns:
            bool: True если операция прошла успешно, иначе False
        """
        try:
            # Инициализируем структуру, если её нет
            if "lesson_completion_status" not in self.state["learning"]:
                self.state["learning"]["lesson_completion_status"] = {}

            # Отмечаем урок как незавершенный
            self.state["learning"]["lesson_completion_status"][lesson_id] = False

            # Также удаляем оценку (урок нужно пересдать)
            if "lesson_scores" in self.state["learning"]:
                self.state["learning"]["lesson_scores"].pop(lesson_id, None)

            self.logger.info(f"Урок {lesson_id} отмечен как незавершенный")

            # Пересчитываем статистику
            self._recalculate_course_statistics()

            return self.save_state()
        except Exception as e:
            self.logger.error(f"Ошибка при отметке урока как незавершенного: {str(e)}")
            return False

    def increment_questions_count(self, lesson_id):
        """
        НОВОЕ: Увеличивает счетчик вопросов для урока.

        Args:
            lesson_id (str): ID урока

        Returns:
            int: Текущее количество вопросов
        """
        try:
            if "questions_count" not in self.state["learning"]:
                self.state["learning"]["questions_count"] = {}

            if lesson_id not in self.state["learning"]["questions_count"]:
                self.state["learning"]["questions_count"][lesson_id] = 0

            self.state["learning"]["questions_count"][lesson_id] += 1
            self.save_state()

            return self.state["learning"]["questions_count"][lesson_id]
        except Exception as e:
            self.logger.error(f"Ошибка при увеличении счетчика вопросов: {str(e)}")
            return 0

    def get_questions_count(self, lesson_id):
        """
        НОВОЕ: Получает количество заданных вопросов для урока.

        Args:
            lesson_id (str): ID урока

        Returns:
            int: Количество вопросов
        """
        if "questions_count" not in self.state["learning"]:
            return 0
        return self.state["learning"]["questions_count"].get(lesson_id, 0)

    def reset_questions_count(self, lesson_id):
        """
        НОВОЕ: Сбрасывает счетчик вопросов для урока.

        Args:
            lesson_id (str): ID урока
        """
        try:
            if "questions_count" not in self.state["learning"]:
                self.state["learning"]["questions_count"] = {}

            self.state["learning"]["questions_count"][lesson_id] = 0
            self.save_state()
        except Exception as e:
            self.logger.error(f"Ошибка при сбросе счетчика вопросов: {str(e)}")

    def _recalculate_course_statistics(self):
        """
        НОВОЕ: Пересчитывает общую статистику по курсу.
        """
        try:
            lesson_scores = self.state["learning"].get("lesson_scores", {})

            if lesson_scores:
                # Рассчитываем средний балл
                total_score = sum(lesson_scores.values())
                total_lessons = len(lesson_scores)
                self.state["learning"]["average_score"] = total_score / total_lessons
                self.state["learning"]["total_score"] = total_score
                self.state["learning"]["total_assessments"] = total_lessons
            else:
                self.state["learning"]["average_score"] = 0
                self.state["learning"]["total_score"] = 0
                self.state["learning"]["total_assessments"] = 0

            # Рассчитываем общий прогресс по курсу
            progress_data = self.calculate_course_progress()
            self.state["learning"]["course_progress_percent"] = progress_data["percent"]

        except Exception as e:
            self.logger.error(f"Ошибка при пересчете статистики курса: {str(e)}")

    def get_lesson_score(self, lesson_id):
        """
        НОВОЕ: Получает лучший результат по уроку.

        Args:
            lesson_id (str): ID урока

        Returns:
            float: Лучший результат или 0, если тестов не было
        """
        lesson_scores = self.state["learning"].get("lesson_scores", {})
        return lesson_scores.get(lesson_id, 0)

    def get_detailed_course_statistics(self):
        """
        НОВОЕ: Получает детальную статистику по курсу.

        Returns:
            dict: Детальная статистика
        """
        try:
            lesson_scores = self.state["learning"].get("lesson_scores", {})
            lesson_attempts = self.state["learning"].get("lesson_attempts", {})
            progress_data = self.calculate_course_progress()

            return {
                "average_score": self.state["learning"].get("average_score", 0),
                "total_assessments": self.state["learning"].get("total_assessments", 0),
                "course_progress_percent": progress_data["percent"],
                "completed_lessons": progress_data["completed"],
                "total_lessons": progress_data["total"],
                "lesson_scores": lesson_scores,
                "lesson_attempts": lesson_attempts,
                "lessons_passed": len(lesson_scores),
                "highest_score": max(lesson_scores.values()) if lesson_scores else 0,
                "lowest_score": min(lesson_scores.values()) if lesson_scores else 0,
            }
        except Exception as e:
            self.logger.error(f"Ошибка при получении детальной статистики: {str(e)}")
            return {}

    def update_assessment_results(self, score):
        """
        Обновляет результаты тестирования (УСТАРЕВШИЙ метод для совместимости).

        Args:
            score (float): Оценка за тест (0-100)

        Returns:
            bool: True если обновление прошло успешно, иначе False
        """
        try:
            # Увеличиваем счетчик тестов
            self.state["learning"]["total_assessments"] += 1

            # Добавляем текущую оценку к общей сумме
            self.state["learning"]["total_score"] += score

            # Пересчитываем средний балл
            self.state["learning"]["average_score"] = (
                self.state["learning"]["total_score"]
                / self.state["learning"]["total_assessments"]
            )

            # Сохраняем обновленное состояние
            return self.save_state()
        except Exception as e:
            self.logger.error(
                f"Ошибка при обновлении результатов тестирования: {str(e)}"
            )
            return False

    def is_first_run(self):
        """
        Проверяет, является ли текущий запуск первым.

        Returns:
            bool: True если это первый запуск, иначе False
        """
        return self.state["system"]["first_run"]

    def set_not_first_run(self):
        """
        Устанавливает флаг, что это не первый запуск.

        Returns:
            bool: True если обновление прошло успешно, иначе False
        """
        try:
            self.state["system"]["first_run"] = False
            return self.save_state()
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении флага первого запуска: {str(e)}")
            return False

    def get_user_profile(self):
        """
        Получает профиль пользователя.

        Returns:
            dict: Словарь с данными пользователя
        """
        return self.state["user"]

    def get_learning_progress(self):
        """
        Получает текущий прогресс обучения.

        Returns:
            dict: Словарь с данными о прогрессе обучения
        """
        # Добавляем имя пользователя к прогрессу для удобства
        progress = self.state["learning"].copy()
        progress["user_name"] = self.state["user"]["name"]
        return progress

    def save_course_plan(self, course_plan):
        """
        Сохраняет сгенерированный учебный план.

        Args:
            course_plan (dict): Структура учебного плана

        Returns:
            bool: True если обновление прошло успешно, иначе False
        """
        try:
            self.state["course_plan"] = course_plan

            # Сохраняем обновленное состояние
            return self.save_state()
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении учебного плана: {str(e)}")
            return False

    def get_course_plan(self):
        """
        Получает текущий учебный план.

        Returns:
            dict: Словарь с учебным планом
        """
        return self.state["course_plan"]

    def get_course_by_id(self, course_id):
        """
        Загружает информацию о курсе из файла courses.json.

        Args:
            course_id (str): Идентификатор курса

        Returns:
            dict: Данные о курсе или None, если курс не найден
        """
        try:
            courses_file = self.project_dir / "courses.json"
            with open(courses_file, "r", encoding="utf-8") as f:
                courses_data = json.load(f)

            for course in courses_data["courses"]:
                if course["id"] == course_id:
                    return course

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
            courses_file = self.project_dir / "courses.json"
            with open(courses_file, "r", encoding="utf-8") as f:
                courses_data = json.load(f)

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
            current_section = self.state["learning"]["current_section"]
            current_topic = self.state["learning"]["current_topic"]
            current_lesson = self.state["learning"]["current_lesson"]
            course_plan = self.state["course_plan"]

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
                if not self.is_lesson_completed(current_lesson_id):
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
        НОВОЕ: Получает первый урок из плана курса.

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
        НОВОЕ: Находит следующий урок в плане курса.

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
            course_plan = self.state["course_plan"]

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
                                    return lesson

            self.logger.warning(
                f"Урок не найден: section={section_id}, topic={topic_id}, lesson={lesson_id}"
            )
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении данных урока: {str(e)}")
            return None

    def calculate_course_progress(self):
        """
        ИСПРАВЛЕНО: Рассчитывает прогресс на основе завершенных уроков.

        Returns:
            dict: Данные о прогрессе (процент, пройдено/всего)
        """
        try:
            course_plan = self.state["course_plan"]

            # Считаем общее количество уроков в курсе
            total_lessons = 0
            for section in course_plan.get("sections", []):
                for topic in section.get("topics", []):
                    total_lessons += len(topic.get("lessons", []))

            # Если уроков нет, возвращаем нулевой прогресс
            if total_lessons == 0:
                return {"percent": 0, "completed": 0, "total": 0}

            # ИСПРАВЛЕНО: Считаем завершенные уроки на основе completion_status
            completed_count = 0
            completion_status = self.state["learning"].get(
                "lesson_completion_status", {}
            )

            for lesson_id, is_completed in completion_status.items():
                if is_completed:
                    completed_count += 1

            # Рассчитываем процент прогресса
            progress_percent = (completed_count / total_lessons) * 100

            self.logger.debug(
                f"Прогресс курса: {completed_count}/{total_lessons} ({progress_percent:.1f}%)"
            )

            return {
                "percent": progress_percent,
                "completed": completed_count,
                "total": total_lessons,
            }
        except Exception as e:
            self.logger.error(f"Ошибка при расчете прогресса курса: {str(e)}")
            return {"percent": 0, "completed": 0, "total": 0}
