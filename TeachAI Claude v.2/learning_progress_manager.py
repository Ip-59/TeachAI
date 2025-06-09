"""
Модуль для управления прогрессом обучения.
Отвечает за отслеживание завершенности уроков, оценки, счетчики вопросов и статистику.
РЕФАКТОРИНГ: Выделен из state_manager.py для лучшей модульности
НОВОЕ: Поддержка контрольных заданий и интеграция с control_tasks_logger
НОВОЕ: Расширенная логика завершенности урока (тест + контрольные задания)
"""

import logging
from datetime import datetime

# НОВОЕ: Импорт логгера контрольных заданий
try:
    from control_tasks_logger import get_cell_stats, is_cell_completed

    CONTROL_TASKS_LOGGER_AVAILABLE = True
except ImportError:
    logging.warning(
        "Модуль control_tasks_logger не найден, логирование контрольных заданий будет недоступно"
    )
    CONTROL_TASKS_LOGGER_AVAILABLE = False

    def get_cell_stats(cell_id):
        return {"total_attempts": 0, "successful_attempts": 0, "is_completed": False}

    def is_cell_completed(cell_id):
        return False


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

        # НОВОЕ: Инициализируем структуры для контрольных заданий
        self._init_control_tasks_structures()

    def _init_control_tasks_structures(self):
        """
        НОВОЕ: Инициализирует структуры данных для контрольных заданий.
        """
        try:
            learning = self.state_manager.state["learning"]

            # Структуры для контрольных заданий
            if "control_tasks_status" not in learning:
                learning[
                    "control_tasks_status"
                ] = {}  # lesson_id -> {task_id: is_completed}

            if "control_tasks_attempts" not in learning:
                learning[
                    "control_tasks_attempts"
                ] = {}  # lesson_id -> {task_id: attempts_count}

            if "lesson_control_tasks_completed" not in learning:
                learning["lesson_control_tasks_completed"] = {}  # lesson_id -> bool

            self.logger.debug("Структуры контрольных заданий инициализированы")

        except Exception as e:
            self.logger.error(
                f"Ошибка инициализации структур контрольных заданий: {str(e)}"
            )

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
        МОДИФИЦИРОВАНО: Сохраняет результат теста по уроку с учетом контрольных заданий.

        Args:
            lesson_id (str): ID урока
            score (float): Оценка за тест (0-100)
            is_passed (bool): Считается ли тест пройденным

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
                "assessment_type": "test",  # НОВОЕ: Различаем тесты и контрольные задания
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

                self.logger.info(
                    f"Тест по уроку {lesson_id} пройден с оценкой {score}%"
                )

            # МОДИФИЦИРОВАНО: Проверяем общую завершенность урока (тест + контрольные задания)
            self._update_lesson_completion_status(lesson_id)

            # Пересчитываем общую статистику
            self._recalculate_course_statistics()

            return self.state_manager.save_state()
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении результата теста: {str(e)}")
            return False

    def save_control_task_result(
        self, lesson_id, task_id, is_completed=True, attempts_count=1
    ):
        """
        НОВОЕ: Сохраняет результат выполнения контрольного задания.

        Args:
            lesson_id (str): ID урока
            task_id (str): ID контрольного задания
            is_completed (bool): Выполнено ли задание
            attempts_count (int): Количество попыток

        Returns:
            bool: True если сохранение прошло успешно, иначе False
        """
        try:
            self._init_control_tasks_structures()

            # Инициализируем структуры для урока, если их нет
            if (
                lesson_id
                not in self.state_manager.state["learning"]["control_tasks_status"]
            ):
                self.state_manager.state["learning"]["control_tasks_status"][
                    lesson_id
                ] = {}
            if (
                lesson_id
                not in self.state_manager.state["learning"]["control_tasks_attempts"]
            ):
                self.state_manager.state["learning"]["control_tasks_attempts"][
                    lesson_id
                ] = {}

            # Сохраняем статус задания
            self.state_manager.state["learning"]["control_tasks_status"][lesson_id][
                task_id
            ] = is_completed
            self.state_manager.state["learning"]["control_tasks_attempts"][lesson_id][
                task_id
            ] = attempts_count

            # Добавляем попытку в общий лог
            if "lesson_attempts" not in self.state_manager.state["learning"]:
                self.state_manager.state["learning"]["lesson_attempts"] = {}
            if lesson_id not in self.state_manager.state["learning"]["lesson_attempts"]:
                self.state_manager.state["learning"]["lesson_attempts"][lesson_id] = []

            attempt_data = {
                "score": 100 if is_completed else 0,
                "timestamp": datetime.now().isoformat(),
                "is_passed": is_completed,
                "assessment_type": "control_task",  # НОВОЕ: Тип оценки
                "task_id": task_id,
                "attempts_count": attempts_count,
            }
            self.state_manager.state["learning"]["lesson_attempts"][lesson_id].append(
                attempt_data
            )

            if is_completed:
                self.logger.info(
                    f"Контрольное задание {task_id} урока {lesson_id} выполнено"
                )
            else:
                self.logger.info(
                    f"Контрольное задание {task_id} урока {lesson_id} не выполнено"
                )

            # Проверяем, выполнены ли все контрольные задания урока
            self._update_lesson_control_tasks_status(lesson_id)

            # Обновляем общую завершенность урока
            self._update_lesson_completion_status(lesson_id)

            # Пересчитываем статистику
            self._recalculate_course_statistics()

            return self.state_manager.save_state()

        except Exception as e:
            self.logger.error(
                f"Ошибка при сохранении результата контрольного задания: {str(e)}"
            )
            return False

    def sync_control_tasks_from_logger(self, lesson_id, control_tasks_list):
        """
        НОВОЕ: Синхронизирует статус контрольных заданий с логгером control_tasks_logger.

        Args:
            lesson_id (str): ID урока
            control_tasks_list (List[Dict]): Список контрольных заданий урока

        Returns:
            bool: True если синхронизация прошла успешно
        """
        try:
            if not CONTROL_TASKS_LOGGER_AVAILABLE or not control_tasks_list:
                return True

            updated = False

            for i, task in enumerate(control_tasks_list):
                task_cell_id = f"{lesson_id}_task_{i+1}"

                # Получаем статистику из логгера Jupiter ячеек
                cell_stats = get_cell_stats(task_cell_id)
                is_completed = is_cell_completed(task_cell_id)

                # Обновляем наш статус, если есть изменения
                if cell_stats["total_attempts"] > 0:
                    current_status = self.get_control_task_status(
                        lesson_id, task_cell_id
                    )
                    if current_status != is_completed:
                        self.save_control_task_result(
                            lesson_id=lesson_id,
                            task_id=task_cell_id,
                            is_completed=is_completed,
                            attempts_count=cell_stats["total_attempts"],
                        )
                        updated = True
                        self.logger.debug(
                            f"Синхронизирован статус задания {task_cell_id}: {is_completed}"
                        )

            if updated:
                self.logger.info(
                    f"Синхронизированы контрольные задания для урока {lesson_id}"
                )

            return True

        except Exception as e:
            self.logger.error(f"Ошибка синхронизации контрольных заданий: {str(e)}")
            return False

    def get_control_task_status(self, lesson_id, task_id):
        """
        НОВОЕ: Получает статус выполнения контрольного задания.

        Args:
            lesson_id (str): ID урока
            task_id (str): ID задания

        Returns:
            bool: True если задание выполнено
        """
        try:
            control_tasks_status = self.state_manager.state["learning"].get(
                "control_tasks_status", {}
            )
            lesson_tasks = control_tasks_status.get(lesson_id, {})
            return lesson_tasks.get(task_id, False)
        except Exception as e:
            self.logger.error(
                f"Ошибка получения статуса контрольного задания: {str(e)}"
            )
            return False

    def get_lesson_control_tasks_progress(self, lesson_id):
        """
        НОВОЕ: Получает прогресс выполнения контрольных заданий урока.

        Args:
            lesson_id (str): ID урока

        Returns:
            Dict: Информация о прогрессе контрольных заданий
        """
        try:
            control_tasks_status = self.state_manager.state["learning"].get(
                "control_tasks_status", {}
            )
            lesson_tasks = control_tasks_status.get(lesson_id, {})

            if not lesson_tasks:
                return {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "completion_rate": 0,
                    "all_completed": True,  # Если заданий нет, считаем выполненными
                }

            total_tasks = len(lesson_tasks)
            completed_tasks = sum(1 for completed in lesson_tasks.values() if completed)
            completion_rate = (
                (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
            )
            all_completed = completed_tasks == total_tasks

            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": completion_rate,
                "all_completed": all_completed,
            }

        except Exception as e:
            self.logger.error(
                f"Ошибка получения прогресса контрольных заданий: {str(e)}"
            )
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "completion_rate": 0,
                "all_completed": True,
            }

    def _update_lesson_control_tasks_status(self, lesson_id):
        """
        НОВОЕ: Обновляет общий статус контрольных заданий для урока.

        Args:
            lesson_id (str): ID урока
        """
        try:
            progress = self.get_lesson_control_tasks_progress(lesson_id)
            self.state_manager.state["learning"]["lesson_control_tasks_completed"][
                lesson_id
            ] = progress["all_completed"]

            if progress["all_completed"] and progress["total_tasks"] > 0:
                self.logger.info(f"Все контрольные задания урока {lesson_id} выполнены")

        except Exception as e:
            self.logger.error(
                f"Ошибка обновления статуса контрольных заданий урока: {str(e)}"
            )

    def _update_lesson_completion_status(self, lesson_id):
        """
        МОДИФИЦИРОВАНО: Обновляет общий статус завершенности урока (тест + контрольные задания).

        Args:
            lesson_id (str): ID урока
        """
        try:
            # Проверяем тест
            lesson_scores = self.state_manager.state["learning"].get(
                "lesson_scores", {}
            )
            test_passed = lesson_id in lesson_scores and lesson_scores[lesson_id] > 0

            # Проверяем контрольные задания
            control_tasks_completed = self.state_manager.state["learning"].get(
                "lesson_control_tasks_completed", {}
            )
            control_tasks_passed = control_tasks_completed.get(
                lesson_id, True
            )  # True если заданий нет

            # НОВАЯ ЛОГИКА: Урок завершен = тест пройден И контрольные задания выполнены
            lesson_completed = test_passed and control_tasks_passed

            # Обновляем статус
            if "lesson_completion_status" not in self.state_manager.state["learning"]:
                self.state_manager.state["learning"]["lesson_completion_status"] = {}

            self.state_manager.state["learning"]["lesson_completion_status"][
                lesson_id
            ] = lesson_completed

            if lesson_completed:
                self.logger.info(
                    f"Урок {lesson_id} полностью завершен (тест + контрольные задания)"
                )
            else:
                incomplete_parts = []
                if not test_passed:
                    incomplete_parts.append("тест")
                if not control_tasks_passed:
                    incomplete_parts.append("контрольные задания")
                self.logger.info(
                    f"Урок {lesson_id} не завершен: {', '.join(incomplete_parts)}"
                )

        except Exception as e:
            self.logger.error(
                f"Ошибка обновления статуса завершенности урока: {str(e)}"
            )

    def is_lesson_completed(self, lesson_id):
        """
        МОДИФИЦИРОВАНО: Проверяет, завершен ли урок полностью (тест + контрольные задания).

        Args:
            lesson_id (str): ID урока

        Returns:
            bool: True если урок полностью завершен, иначе False
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
        МОДИФИЦИРОВАНО: Отмечает урок как незавершенный (сбрасывает тест и контрольные задания).

        Args:
            lesson_id (str): ID урока

        Returns:
            bool: True если операция прошла успешно, иначе False
        """
        try:
            # Инициализируем структуры
            if "lesson_completion_status" not in self.state_manager.state["learning"]:
                self.state_manager.state["learning"]["lesson_completion_status"] = {}
            self._init_control_tasks_structures()

            # Отмечаем урок как незавершенный
            self.state_manager.state["learning"]["lesson_completion_status"][
                lesson_id
            ] = False

            # Сбрасываем оценку теста
            if "lesson_scores" in self.state_manager.state["learning"]:
                self.state_manager.state["learning"]["lesson_scores"].pop(
                    lesson_id, None
                )

            # НОВОЕ: Сбрасываем контрольные задания
            if (
                lesson_id
                in self.state_manager.state["learning"]["control_tasks_status"]
            ):
                self.state_manager.state["learning"]["control_tasks_status"][
                    lesson_id
                ] = {}
            if (
                lesson_id
                in self.state_manager.state["learning"]["control_tasks_attempts"]
            ):
                self.state_manager.state["learning"]["control_tasks_attempts"][
                    lesson_id
                ] = {}
            if (
                lesson_id
                in self.state_manager.state["learning"][
                    "lesson_control_tasks_completed"
                ]
            ):
                self.state_manager.state["learning"]["lesson_control_tasks_completed"][
                    lesson_id
                ] = False

            self.logger.info(
                f"Урок {lesson_id} отмечен как незавершенный (тест и контрольные задания сброшены)"
            )

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
            bool: True если операция прошла успешно, иначе False
        """
        try:
            # Инициализируем структуру, если её нет
            if "lesson_questions_count" not in self.state_manager.state["learning"]:
                self.state_manager.state["learning"]["lesson_questions_count"] = {}

            current_count = self.state_manager.state["learning"][
                "lesson_questions_count"
            ].get(lesson_id, 0)
            self.state_manager.state["learning"]["lesson_questions_count"][
                lesson_id
            ] = (current_count + 1)

            self.logger.debug(
                f"Счетчик вопросов урока {lesson_id}: {current_count + 1}"
            )

            return self.state_manager.save_state()
        except Exception as e:
            self.logger.error(f"Ошибка при увеличении счетчика вопросов: {str(e)}")
            return False

    def get_questions_count(self, lesson_id):
        """
        Получает счетчик вопросов для урока.

        Args:
            lesson_id (str): ID урока

        Returns:
            int: Количество заданных вопросов
        """
        try:
            questions_count = self.state_manager.state["learning"].get(
                "lesson_questions_count", {}
            )
            return questions_count.get(lesson_id, 0)
        except Exception as e:
            self.logger.error(f"Ошибка при получении счетчика вопросов: {str(e)}")
            return 0

    def reset_questions_count(self, lesson_id):
        """
        Сбрасывает счетчик вопросов для урока.

        Args:
            lesson_id (str): ID урока

        Returns:
            bool: True если операция прошла успешно, иначе False
        """
        try:
            if "lesson_questions_count" not in self.state_manager.state["learning"]:
                self.state_manager.state["learning"]["lesson_questions_count"] = {}

            self.state_manager.state["learning"]["lesson_questions_count"][
                lesson_id
            ] = 0

            return self.state_manager.save_state()
        except Exception as e:
            self.logger.error(f"Ошибка при сбросе счетчика вопросов: {str(e)}")
            return False

    def _recalculate_course_statistics(self):
        """
        МОДИФИЦИРОВАНО: Пересчитывает статистику курса с учетом контрольных заданий.
        """
        try:
            lesson_scores = self.state_manager.state["learning"].get(
                "lesson_scores", {}
            )

            if lesson_scores:
                # Рассчитываем средний балл по тестам
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
        МОДИФИЦИРОВАНО: Получает детальную статистику по курсу с контрольными заданиями.

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
            control_tasks_status = self.state_manager.state["learning"].get(
                "control_tasks_status", {}
            )
            progress_data = self.calculate_course_progress()

            # НОВОЕ: Статистика по контрольным заданиям
            total_control_tasks = 0
            completed_control_tasks = 0

            for lesson_id, tasks in control_tasks_status.items():
                total_control_tasks += len(tasks)
                completed_control_tasks += sum(
                    1 for completed in tasks.values() if completed
                )

            control_tasks_completion_rate = (
                (completed_control_tasks / total_control_tasks * 100)
                if total_control_tasks > 0
                else 100
            )

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
                # НОВЫЕ поля для контрольных заданий
                "total_control_tasks": total_control_tasks,
                "completed_control_tasks": completed_control_tasks,
                "control_tasks_completion_rate": control_tasks_completion_rate,
                "control_tasks_status": control_tasks_status,
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
        МОДИФИЦИРОВАНО: Рассчитывает прогресс на основе полностью завершенных уроков.

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

            # МОДИФИЦИРОВАНО: Считаем полностью завершенные уроки (тест + контрольные задания)
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
