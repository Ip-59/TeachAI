"""
Модуль для управления прогрессом обучения.
Отвечает за отслеживание завершенности уроков, оценки, счетчики вопросов и статистику.
РЕФАКТОРИНГ: Выделен из state_manager.py для лучшей модульности
"""

import logging
from datetime import datetime


class LearningProgressManager:
    """Менеджер прогресса обучения."""

    def __init__(self, state_manager):
        """
        Инициализация менеджера прогресса.

        Args:
            state_manager: Ссылка на основной StateManager
        """
        self.state_manager = state_manager
        self.logger = logging.getLogger(__name__)

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
                self.state_manager.state["learning"]["current_course"] = course
            if section is not None:
                self.state_manager.state["learning"]["current_section"] = section
            if topic is not None:
                self.state_manager.state["learning"]["current_topic"] = topic

            if lesson is not None:
                self.state_manager.state["learning"]["current_lesson"] = lesson
                # Добавляем урок в список пройденных, если его там еще нет
                lesson_id = f"{section}:{topic}:{lesson}"
                if (
                    lesson_id
                    not in self.state_manager.state["learning"]["completed_lessons"]
                ):
                    self.state_manager.state["learning"]["completed_lessons"].append(
                        lesson_id
                    )

            self.logger.debug(
                f"Прогресс обучения обновлен: course={course}, section={section}, topic={topic}, lesson={lesson}"
            )

            # Сохраняем обновленное состояние
            return self.state_manager.save_state()
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении прогресса обучения: {str(e)}")
            return False

    def save_lesson_assessment(self, lesson_id, score, is_passed=True):
        """
        Сохраняет результат теста по уроку с правильной логикой завершенности.

        Args:
            lesson_id (str): ID урока
            score (float): Оценка за тест (0-100)
            is_passed (bool): Считается ли урок пройденным

        Returns:
            bool: True если сохранение прошло успешно, иначе False
        """
        try:
            # Инициализируем структуры, если их нет
            if "lesson_scores" not in self.state_manager.state["learning"]:
                self.state_manager.state["learning"]["lesson_scores"] = {}
            if "lesson_attempts" not in self.state_manager.state["learning"]:
                self.state_manager.state["learning"]["lesson_attempts"] = {}
            if "lesson_completion_status" not in self.state_manager.state["learning"]:
                self.state_manager.state["learning"]["lesson_completion_status"] = {}

            # Добавляем попытку
            if lesson_id not in self.state_manager.state["learning"]["lesson_attempts"]:
                self.state_manager.state["learning"]["lesson_attempts"][lesson_id] = []

            attempt_data = {
                "score": score,
                "timestamp": datetime.now().isoformat(),
                "is_passed": is_passed,
            }
            self.state_manager.state["learning"]["lesson_attempts"][lesson_id].append(
                attempt_data
            )

            # Сохраняем лучший результат как текущий
            if is_passed:
                current_best = self.state_manager.state["learning"][
                    "lesson_scores"
                ].get(lesson_id, 0)
                if score > current_best:
                    self.state_manager.state["learning"]["lesson_scores"][
                        lesson_id
                    ] = score

                # ИСПРАВЛЕНО: Урок считается завершенным только при is_passed=True
                self.state_manager.state["learning"]["lesson_completion_status"][
                    lesson_id
                ] = True
                self.logger.info(
                    f"Урок {lesson_id} отмечен как завершенный с оценкой {score}%"
                )

            # Пересчитываем общую статистику
            self._recalculate_course_statistics()

            return self.state_manager.save_state()
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении результата теста: {str(e)}")
            return False

    def is_lesson_completed(self, lesson_id):
        """
        Проверяет, завершен ли урок.

        Args:
            lesson_id (str): ID урока

        Returns:
            bool: True если урок завершен, иначе False
        """
        try:
            # Инициализируем структуру, если её нет
            if "lesson_completion_status" not in self.state_manager.state["learning"]:
                self.state_manager.state["learning"]["lesson_completion_status"] = {}

            completion_status = self.state_manager.state["learning"][
                "lesson_completion_status"
            ].get(lesson_id, False)
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
        Отмечает урок как незавершенный (для повторного прохождения).

        Args:
            lesson_id (str): ID урока

        Returns:
            bool: True если операция прошла успешно, иначе False
        """
        try:
            # Инициализируем структуру, если её нет
            if "lesson_completion_status" not in self.state_manager.state["learning"]:
                self.state_manager.state["learning"]["lesson_completion_status"] = {}

            # Отмечаем урок как незавершенный
            self.state_manager.state["learning"]["lesson_completion_status"][
                lesson_id
            ] = False

            # Также удаляем оценку (урок нужно пересдать)
            if "lesson_scores" in self.state_manager.state["learning"]:
                self.state_manager.state["learning"]["lesson_scores"].pop(
                    lesson_id, None
                )

            self.logger.info(f"Урок {lesson_id} отмечен как незавершенный")

            # Пересчитываем статистику
            self._recalculate_course_statistics()

            return self.state_manager.save_state()
        except Exception as e:
            self.logger.error(f"Ошибка при отметке урока как незавершенного: {str(e)}")
            return False

    def increment_questions_count(self, lesson_id):
        """
        Увеличивает счетчик вопросов для урока.

        Args:
            lesson_id (str): ID урока

        Returns:
            int: Текущее количество вопросов
        """
        try:
            if "questions_count" not in self.state_manager.state["learning"]:
                self.state_manager.state["learning"]["questions_count"] = {}

            if lesson_id not in self.state_manager.state["learning"]["questions_count"]:
                self.state_manager.state["learning"]["questions_count"][lesson_id] = 0

            self.state_manager.state["learning"]["questions_count"][lesson_id] += 1
            self.state_manager.save_state()

            count = self.state_manager.state["learning"]["questions_count"][lesson_id]
            self.logger.debug(f"Счетчик вопросов для урока {lesson_id}: {count}")
            return count
        except Exception as e:
            self.logger.error(f"Ошибка при увеличении счетчика вопросов: {str(e)}")
            return 0

    def get_questions_count(self, lesson_id):
        """
        Получает количество заданных вопросов для урока.

        Args:
            lesson_id (str): ID урока

        Returns:
            int: Количество вопросов
        """
        if "questions_count" not in self.state_manager.state["learning"]:
            return 0
        return self.state_manager.state["learning"]["questions_count"].get(lesson_id, 0)

    def reset_questions_count(self, lesson_id):
        """
        Сбрасывает счетчик вопросов для урока.

        Args:
            lesson_id (str): ID урока
        """
        try:
            if "questions_count" not in self.state_manager.state["learning"]:
                self.state_manager.state["learning"]["questions_count"] = {}

            self.state_manager.state["learning"]["questions_count"][lesson_id] = 0
            self.state_manager.save_state()
            self.logger.debug(f"Счетчик вопросов для урока {lesson_id} сброшен")
        except Exception as e:
            self.logger.error(f"Ошибка при сбросе счетчика вопросов: {str(e)}")

    def _recalculate_course_statistics(self):
        """
        Пересчитывает общую статистику по курсу.
        """
        try:
            lesson_scores = self.state_manager.state["learning"].get(
                "lesson_scores", {}
            )

            if lesson_scores:
                # Рассчитываем средний балл
                total_score = sum(lesson_scores.values())
                total_lessons = len(lesson_scores)
                self.state_manager.state["learning"]["average_score"] = (
                    total_score / total_lessons
                )
                self.state_manager.state["learning"]["total_score"] = total_score
                self.state_manager.state["learning"][
                    "total_assessments"
                ] = total_lessons
            else:
                self.state_manager.state["learning"]["average_score"] = 0
                self.state_manager.state["learning"]["total_score"] = 0
                self.state_manager.state["learning"]["total_assessments"] = 0

            # Рассчитываем общий прогресс по курсу
            progress_data = self.calculate_course_progress()
            self.state_manager.state["learning"][
                "course_progress_percent"
            ] = progress_data["percent"]

        except Exception as e:
            self.logger.error(f"Ошибка при пересчете статистики курса: {str(e)}")

    def get_lesson_score(self, lesson_id):
        """
        Получает лучший результат по уроку.

        Args:
            lesson_id (str): ID урока

        Returns:
            float: Лучший результат или 0, если тестов не было
        """
        lesson_scores = self.state_manager.state["learning"].get("lesson_scores", {})
        return lesson_scores.get(lesson_id, 0)

    def get_detailed_course_statistics(self):
        """
        Получает детальную статистику по курсу.

        Returns:
            dict: Детальная статистика
        """
        try:
            lesson_scores = self.state_manager.state["learning"].get(
                "lesson_scores", {}
            )
            lesson_attempts = self.state_manager.state["learning"].get(
                "lesson_attempts", {}
            )
            progress_data = self.calculate_course_progress()

            return {
                "average_score": self.state_manager.state["learning"].get(
                    "average_score", 0
                ),
                "total_assessments": self.state_manager.state["learning"].get(
                    "total_assessments", 0
                ),
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
            self.state_manager.state["learning"]["total_assessments"] += 1

            # Добавляем текущую оценку к общей сумме
            self.state_manager.state["learning"]["total_score"] += score

            # Пересчитываем средний балл
            self.state_manager.state["learning"]["average_score"] = (
                self.state_manager.state["learning"]["total_score"]
                / self.state_manager.state["learning"]["total_assessments"]
            )

            # Сохраняем обновленное состояние
            return self.state_manager.save_state()
        except Exception as e:
            self.logger.error(
                f"Ошибка при обновлении результатов тестирования: {str(e)}"
            )
            return False

    def get_learning_progress(self):
        """
        Получает текущий прогресс обучения.

        Returns:
            dict: Словарь с данными о прогрессе обучения
        """
        try:
            # Добавляем имя пользователя к прогрессу для удобства
            progress = self.state_manager.state["learning"].copy()
            progress["user_name"] = self.state_manager.state["user"]["name"]
            return progress
        except Exception as e:
            self.logger.error(f"Ошибка при получении прогресса обучения: {str(e)}")
            return {"user_name": ""}

    def calculate_course_progress(self):
        """
        Рассчитывает прогресс на основе завершенных уроков.

        Returns:
            dict: Данные о прогрессе (процент, пройдено/всего)
        """
        try:
            course_plan = self.state_manager.state["course_plan"]

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
            completion_status = self.state_manager.state["learning"].get(
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
