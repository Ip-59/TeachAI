"""
Методы управления состоянием для работы с пользователем и обучением.
Дополнительная функциональность StateManager.
"""

import logging
from datetime import datetime


class StateManagerMethods:
    """Дополнительные методы для управления состоянием."""

    def __init__(self, core_manager):
        """
        Инициализация методов с ядром управления состоянием.

        Args:
            core_manager: Экземпляр StateManagerCore
        """
        self.core = core_manager
        self.logger = logging.getLogger(__name__)

    # ========================================
    # МЕТОДЫ РАБОТЫ С ПОЛЬЗОВАТЕЛЕМ
    # ========================================

    def save_user_profile(self, user_data):
        """
        Сохраняет профиль пользователя.

        Args:
            user_data (dict): Данные пользователя

        Returns:
            bool: True если сохранение прошло успешно, иначе False
        """
        try:
            self.core.state["user"] = user_data
            result = self.core.save_state()
            if result:
                self.logger.info(
                    f"Профиль пользователя '{user_data.get('name', 'Unknown')}' сохранен"
                )
            return result
        except Exception as e:
            self.logger.error(f"Ошибка сохранения профиля пользователя: {str(e)}")
            return False

    def get_user_data(self):
        """
        Возвращает данные пользователя.

        Returns:
            dict: Данные пользователя
        """
        return self.core.state.get("user", {})

    def clear_user_data(self):
        """Очищает данные пользователя."""
        try:
            self.core.state["user"] = {}
            result = self.core.save_state()
            if result:
                self.logger.info("Данные пользователя очищены")
            return result
        except Exception as e:
            self.logger.error(f"Ошибка очистки данных пользователя: {str(e)}")
            return False

    # ========================================
    # МЕТОДЫ РАБОТЫ С ОБУЧЕНИЕМ
    # ========================================

    def save_course_plan(self, course_plan):
        """
        Сохраняет план курса.

        Args:
            course_plan (dict): План курса

        Returns:
            bool: True если сохранение прошло успешно, иначе False
        """
        try:
            self.core.state["course_plan"] = course_plan
            result = self.core.save_state()
            if result:
                course_title = course_plan.get("title", "Неизвестный курс")
                self.logger.info(f"План курса '{course_title}' сохранен")
            return result
        except Exception as e:
            self.logger.error(f"Ошибка сохранения плана курса: {str(e)}")
            return False

    def get_course_plan(self):
        """
        Возвращает план курса.

        Returns:
            dict: План курса
        """
        return self.core.state.get("course_plan", {})

    def clear_course_plan(self):
        """Очищает план курса."""
        try:
            self.core.state["course_plan"] = {}
            result = self.core.save_state()
            if result:
                self.logger.info("План курса очищен")
            return result
        except Exception as e:
            self.logger.error(f"Ошибка очистки плана курса: {str(e)}")
            return False

    def save_learning_progress(self, progress_data):
        """
        Сохраняет прогресс обучения.

        Args:
            progress_data (dict): Данные прогресса обучения

        Returns:
            bool: True если сохранение прошло успешно, иначе False
        """
        try:
            self.core.state["learning"] = progress_data
            result = self.core.save_state()
            if result:
                self.logger.info("Прогресс обучения сохранен")
            return result
        except Exception as e:
            self.logger.error(f"Ошибка сохранения прогресса обучения: {str(e)}")
            return False

    def get_learning_progress(self):
        """
        Возвращает прогресс обучения.

        Returns:
            dict: Прогресс обучения
        """
        return self.core.state.get("learning", {})

    def clear_learning_progress(self):
        """Очищает прогресс обучения."""
        try:
            self.core.state["learning"] = {}
            result = self.core.save_state()
            if result:
                self.logger.info("Прогресс обучения очищен")
            return result
        except Exception as e:
            self.logger.error(f"Ошибка очистки прогресса обучения: {str(e)}")
            return False

    def get_completed_lessons(self):
        """
        Возвращает список завершенных уроков.

        Returns:
            list: Список ID завершенных уроков
        """
        return self.core.state.get("completed_lessons", [])

    def mark_lesson_completed(self, lesson_id):
        """
        Отмечает урок как завершенный.

        Args:
            lesson_id (str): ID урока

        Returns:
            bool: True если отметка прошла успешно, иначе False
        """
        try:
            completed_lessons = self.get_completed_lessons()
            if lesson_id not in completed_lessons:
                completed_lessons.append(lesson_id)
                self.core.state["completed_lessons"] = completed_lessons
                result = self.core.save_state()
                if result:
                    self.logger.info(f"Урок {lesson_id} отмечен как завершенный")
                return result
            else:
                self.logger.info(f"Урок {lesson_id} уже был завершен")
                return True
        except Exception as e:
            self.logger.error(f"Ошибка отметки урока как завершенного: {str(e)}")
            return False

    # ========================================
    # МЕТОДЫ ПЕРВОГО ЗАПУСКА
    # ========================================

    def is_first_run(self):
        """
        Проверяет, является ли это первым запуском системы.

        Returns:
            bool: True если первый запуск, иначе False
        """
        try:
            # Проверяем флаг в настройках
            settings_first_run = self.core.state.get("settings", {}).get(
                "first_run", True
            )

            # Проверяем наличие имени пользователя
            user_name = self.core.state.get("user", {}).get("name")
            user_first_run = not bool(user_name)

            # Первый запуск если оба условия True или флаг в настройках True
            result = settings_first_run or user_first_run

            self.logger.debug(
                f"Проверка первого запуска: settings={settings_first_run}, user={user_first_run}, result={result}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Ошибка проверки первого запуска: {str(e)}")
            return True  # По умолчанию считаем первым запуском

    def set_not_first_run(self):
        """
        Устанавливает флаг того, что первый запуск завершен.

        Returns:
            bool: True если установка прошла успешно, иначе False
        """
        try:
            if "settings" not in self.core.state:
                self.core.state["settings"] = {}

            self.core.state["settings"]["first_run"] = False
            self.core.state["settings"][
                "first_run_completed_at"
            ] = datetime.now().isoformat()

            result = self.core.save_state()
            if result:
                self.logger.info("Флаг первого запуска снят")

            return result

        except Exception as e:
            self.logger.error(f"Ошибка установки флага первого запуска: {str(e)}")
            return False

    def get_user_profile(self):
        """
        Возвращает профиль пользователя (псевдоним для get_user_data).

        Returns:
            dict: Профиль пользователя
        """
        return self.get_user_data()

    def update_user_profile(self, **kwargs):
        """
        Обновляет профиль пользователя.

        Args:
            **kwargs: Данные для обновления

        Returns:
            bool: True если обновление прошло успешно, иначе False
        """
        try:
            current_profile = self.get_user_data()
            current_profile.update(kwargs)
            result = self.save_user_profile(current_profile)

            if result:
                self.logger.info(
                    f"Профиль пользователя обновлен: {list(kwargs.keys())}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Ошибка обновления профиля пользователя: {str(e)}")
            return False

    def update_learning_progress(self, **kwargs):
        """
        Обновляет прогресс обучения.

        Args:
            **kwargs: Данные для обновления

        Returns:
            bool: True если обновление прошло успешно, иначе False
        """
        try:
            current_progress = self.get_learning_progress()
            current_progress.update(kwargs)
            current_progress["last_updated"] = datetime.now().isoformat()

            result = self.save_learning_progress(current_progress)

            if result:
                self.logger.info(f"Прогресс обучения обновлен: {list(kwargs.keys())}")

            return result

        except Exception as e:
            self.logger.error(f"Ошибка обновления прогресса обучения: {str(e)}")
            return False

    def get_lesson_data(self, lesson_id):
        """
        Получает данные урока по ID.

        Args:
            lesson_id (str): ID урока

        Returns:
            dict: Данные урока или None
        """
        try:
            course_plan = self.get_course_plan()

            # Поиск урока в структуре курса
            for section in course_plan.get("sections", []):
                for topic in section.get("topics", []):
                    for lesson in topic.get("lessons", []):
                        if lesson.get("id") == lesson_id:
                            return lesson

            # Если урок не найден
            self.logger.warning(f"Урок с ID {lesson_id} не найден в плане курса")
            return None

        except Exception as e:
            self.logger.error(f"Ошибка получения данных урока: {str(e)}")
            return None

    def get_next_lesson(self):
        """
        Определяет следующий урок для изучения.

        Returns:
            dict: Данные следующего урока или None
        """
        try:
            course_plan = self.get_course_plan()
            completed_lessons = self.get_completed_lessons()

            # Поиск первого незавершенного урока
            for section in course_plan.get("sections", []):
                for topic in section.get("topics", []):
                    for lesson in topic.get("lessons", []):
                        lesson_id = lesson.get("id")
                        if lesson_id and lesson_id not in completed_lessons:
                            self.logger.info(
                                f"Следующий урок для изучения: {lesson_id}"
                            )
                            return lesson

            # Все уроки завершены
            self.logger.info("Все уроки курса завершены")
            return None

        except Exception as e:
            self.logger.error(f"Ошибка определения следующего урока: {str(e)}")
            return None

    def reset_to_first_run(self):
        """
        Сбрасывает систему к состоянию первого запуска.
        Служебный метод для отладки и сброса.

        Returns:
            bool: True если сброс прошел успешно, иначе False
        """
        try:
            # Очищаем данные пользователя
            self.core.state["user"] = {}

            # Устанавливаем флаг первого запуска
            if "settings" not in self.core.state:
                self.core.state["settings"] = {}

            self.core.state["settings"]["first_run"] = True
            self.core.state["settings"]["reset_at"] = datetime.now().isoformat()

            # Очищаем прогресс обучения
            self.core.state["learning"] = {}
            self.core.state["course_plan"] = {}
            self.core.state["completed_lessons"] = []

            result = self.core.save_state()
            if result:
                self.logger.info("Система сброшена к первому запуску")

            return result

        except Exception as e:
            self.logger.error(f"Ошибка при сбросе к первому запуску: {str(e)}")
            return False

    # ========================================
    # МЕТОДЫ СТАТИСТИКИ И ОТЧЕТНОСТИ
    # ========================================

    def get_course_statistics(self):
        """
        Возвращает статистику по курсу.

        Returns:
            dict: Статистика курса
        """
        try:
            course_plan = self.get_course_plan()
            completed_lessons = self.get_completed_lessons()

            # Подсчет общего количества уроков
            total_lessons = 0
            for section in course_plan.get("sections", []):
                for topic in section.get("topics", []):
                    total_lessons += len(topic.get("lessons", []))

            # Расчет прогресса
            completed_count = len(completed_lessons)
            progress_percentage = (
                (completed_count / total_lessons * 100) if total_lessons > 0 else 0
            )

            statistics = {
                "total_lessons": total_lessons,
                "completed_lessons": completed_count,
                "remaining_lessons": total_lessons - completed_count,
                "progress_percentage": round(progress_percentage, 2),
                "course_title": course_plan.get("title", "Неизвестный курс"),
                "sections_count": len(course_plan.get("sections", [])),
                "last_updated": datetime.now().isoformat(),
            }

            self.logger.debug(f"Статистика курса: {statistics}")
            return statistics

        except Exception as e:
            self.logger.error(f"Ошибка получения статистики курса: {str(e)}")
            return {
                "total_lessons": 0,
                "completed_lessons": 0,
                "remaining_lessons": 0,
                "progress_percentage": 0,
                "course_title": "Ошибка",
                "sections_count": 0,
                "error": str(e),
            }

    def get_user_summary(self):
        """
        Возвращает сводку по пользователю.

        Returns:
            dict: Сводка пользователя
        """
        try:
            user_data = self.get_user_data()
            learning_progress = self.get_learning_progress()
            course_stats = self.get_course_statistics()

            summary = {
                "user_name": user_data.get("name", "Не указано"),
                "learning_style": user_data.get("learning_style", "Не указан"),
                "session_duration": user_data.get("session_duration", "Не указана"),
                "course_title": course_stats.get("course_title", "Курс не выбран"),
                "progress_percentage": course_stats.get("progress_percentage", 0),
                "completed_lessons": course_stats.get("completed_lessons", 0),
                "total_lessons": course_stats.get("total_lessons", 0),
                "last_lesson_date": learning_progress.get("last_lesson_date"),
                "first_run": self.is_first_run(),
                "generated_at": datetime.now().isoformat(),
            }

            return summary

        except Exception as e:
            self.logger.error(f"Ошибка получения сводки пользователя: {str(e)}")
            return {"error": str(e)}
