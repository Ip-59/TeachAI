"""
Методы управления состоянием для работы с пользователем и обучением.
Дополнительная функциональность StateManager.

ИСПРАВЛЕНО ЭТАП 29: Добавлен недостающий метод get_all_courses() для загрузки курсов из courses.json
ЗАВЕРШЕНО ЭТАП 29: Дописаны все недостающие методы до конца файла
"""

import logging
import json
import os
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
    # МЕТОДЫ РАБОТЫ С КУРСАМИ
    # ========================================

    def get_all_courses(self):
        """
        НОВЫЙ МЕТОД: Загружает список всех доступных курсов из файла courses.json.

        Returns:
            list: Список доступных курсов или пустой список при ошибке
        """
        try:
            # Определяем путь к файлу courses.json
            courses_file_path = "courses.json"

            # Проверяем существование файла
            if not os.path.exists(courses_file_path):
                self.logger.error(f"Файл {courses_file_path} не найден")
                return []

            # Загружаем данные из файла
            with open(courses_file_path, "r", encoding="utf-8") as file:
                courses_data = json.load(file)

            # Извлекаем список курсов
            if isinstance(courses_data, dict) and "courses" in courses_data:
                courses = courses_data["courses"]
            elif isinstance(courses_data, list):
                courses = courses_data
            else:
                self.logger.error("Некорректная структура файла courses.json")
                return []

            # Валидируем структуру курсов
            validated_courses = []
            for course in courses:
                if self._validate_course_structure(course):
                    validated_courses.append(course)
                else:
                    self.logger.warning(
                        f"Пропуск курса с некорректной структурой: {course.get('id', 'unknown')}"
                    )

            self.logger.info(
                f"Загружено {len(validated_courses)} курсов из {courses_file_path}"
            )
            return validated_courses

        except FileNotFoundError:
            self.logger.error(f"Файл courses.json не найден")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка парсинга JSON в courses.json: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке курсов: {str(e)}")
            return []

    def _validate_course_structure(self, course):
        """
        Проверяет корректность структуры курса.

        Args:
            course (dict): Данные курса

        Returns:
            bool: True если структура корректна
        """
        try:
            required_fields = ["id", "title", "description"]

            # Проверяем наличие обязательных полей
            for field in required_fields:
                if field not in course or not course[field]:
                    self.logger.warning(f"Курс пропущен: отсутствует поле '{field}'")
                    return False

            # Проверяем типы данных
            if not isinstance(course["id"], str) or not isinstance(
                course["title"], str
            ):
                self.logger.warning(f"Курс пропущен: некорректные типы данных")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Ошибка валидации курса: {str(e)}")
            return False

    def get_course_by_id(self, course_id):
        """
        НОВЫЙ МЕТОД: Получает данные курса по его ID.

        Args:
            course_id (str): ID курса

        Returns:
            dict or None: Данные курса или None если не найден
        """
        try:
            courses = self.get_all_courses()
            for course in courses:
                if course.get("id") == course_id:
                    return course

            self.logger.warning(f"Курс с ID '{course_id}' не найден")
            return None

        except Exception as e:
            self.logger.error(f"Ошибка поиска курса {course_id}: {str(e)}")
            return None

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

    def get_user_profile(self):
        """Возвращает полный профиль пользователя (алиас для get_user_data)."""
        return self.get_user_data()

    # ========================================
    # МЕТОДЫ РАБОТЫ С ПЛАНОМ КУРСА
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
                self.logger.info(
                    f"План курса '{course_plan.get('title', 'Unknown')}' сохранен"
                )
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

    def update_learning_progress(self, **kwargs):
        """
        Обновляет прогресс обучения.

        Args:
            **kwargs: Поля для обновления

        Returns:
            bool: True если обновление прошло успешно
        """
        try:
            progress_data = self.get_learning_progress()
            progress_data.update(kwargs)
            return self.save_learning_progress(progress_data)
        except Exception as e:
            self.logger.error(f"Ошибка обновления прогресса обучения: {str(e)}")
            return False

    # ========================================
    # МЕТОДЫ РАБОТЫ С УРОКАМИ
    # ========================================

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
            tuple or None: (section_id, topic_id, lesson_id, lesson_data) или None если все уроки завершены
        """
        try:
            course_plan = self.get_course_plan()
            completed_lessons = self.get_completed_lessons()

            # Ищем первый незавершенный урок
            for section in course_plan.get("sections", []):
                section_id = section.get("id")
                for topic in section.get("topics", []):
                    topic_id = topic.get("id")
                    for lesson in topic.get("lessons", []):
                        lesson_id = lesson.get("id")
                        if lesson_id not in completed_lessons:
                            self.logger.info(
                                f"Найден следующий урок: {section_id}:{topic_id}:{lesson_id}"
                            )
                            return (section_id, topic_id, lesson_id, lesson)

            # Все уроки завершены
            self.logger.info("Все уроки в курсе завершены")
            return None

        except Exception as e:
            self.logger.error(f"Ошибка определения следующего урока: {str(e)}")
            return None

    # ========================================
    # МЕТОДЫ РАБОТЫ С ПЕРВЫМ ЗАПУСКОМ
    # ========================================

    def is_first_run(self):
        """
        Проверяет, является ли это первым запуском системы.

        Returns:
            bool: True если это первый запуск
        """
        try:
            # Проверяем флаг первого запуска
            first_run_flag = self.core.state.get("settings", {}).get("first_run", True)

            # Дополнительная проверка на отсутствие пользователя
            user_exists = bool(self.get_user_data().get("name"))

            # Первый запуск если либо флаг установлен, либо нет пользователя
            is_first_run = first_run_flag or not user_exists

            self.logger.info(f"Проверка первого запуска: {is_first_run}")
            return is_first_run

        except Exception as e:
            self.logger.error(f"Ошибка проверки первого запуска: {str(e)}")
            return True  # В случае ошибки считаем первым запуском

    def set_not_first_run(self):
        """
        Снимает флаг первого запуска.

        Returns:
            bool: True если установка прошла успешно
        """
        try:
            if "settings" not in self.core.state:
                self.core.state["settings"] = {}

            self.core.state["settings"]["first_run"] = False
            result = self.core.save_state()

            if result:
                self.logger.info("Флаг первого запуска снят")

            return result

        except Exception as e:
            self.logger.error(f"Ошибка установки флага первого запуска: {str(e)}")
            return False

    def reset_to_first_run(self):
        """
        Сбрасывает систему к состоянию первого запуска.
        Служебный метод для отладки и сброса.

        Returns:
            bool: True если сброс прошел успешно
        """
        try:
            # Очищаем пользовательские данные
            self.core.state["user"] = {}
            self.core.state["course_plan"] = {}
            self.core.state["learning"] = {}
            self.core.state["completed_lessons"] = []

            # Устанавливаем флаг первого запуска
            if "settings" not in self.core.state:
                self.core.state["settings"] = {}

            self.core.state["settings"]["first_run"] = True

            result = self.core.save_state()

            if result:
                self.logger.info("Система сброшена к состоянию первого запуска")

            return result

        except Exception as e:
            self.logger.error(f"Ошибка сброса к первому запуску: {str(e)}")
            return False

    # ========================================
    # ДОПОЛНИТЕЛЬНЫЕ СЛУЖЕБНЫЕ МЕТОДЫ
    # ========================================

    def get_statistics(self):
        """
        Возвращает статистику использования системы.

        Returns:
            dict: Статистика
        """
        try:
            stats = {
                "user_exists": bool(self.get_user_data().get("name")),
                "course_plan_exists": bool(self.get_course_plan()),
                "completed_lessons_count": len(self.get_completed_lessons()),
                "is_first_run": self.is_first_run(),
                "available_courses_count": len(self.get_all_courses()),
                "state_file_size": self.core.get_state_file_size()
                if hasattr(self.core, "get_state_file_size")
                else 0,
            }

            return stats

        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {str(e)}")
            return {}

    def export_user_data(self):
        """
        Экспортирует данные пользователя для резервного копирования.

        Returns:
            dict: Экспортированные данные пользователя
        """
        try:
            export_data = {
                "user": self.get_user_data(),
                "course_plan": self.get_course_plan(),
                "learning_progress": self.get_learning_progress(),
                "completed_lessons": self.get_completed_lessons(),
                "export_timestamp": datetime.now().isoformat(),
                "version": "2.0",
            }

            self.logger.info("Данные пользователя экспортированы")
            return export_data

        except Exception as e:
            self.logger.error(f"Ошибка экспорта данных пользователя: {str(e)}")
            return {}

    def import_user_data(self, import_data):
        """
        Импортирует данные пользователя из резервной копии.

        Args:
            import_data (dict): Данные для импорта

        Returns:
            bool: True если импорт прошел успешно
        """
        try:
            if not isinstance(import_data, dict):
                self.logger.error("Некорректный формат данных для импорта")
                return False

            # Проверяем версию данных
            version = import_data.get("version", "1.0")
            if version != "2.0":
                self.logger.warning(
                    f"Импорт данных версии {version}, могут быть проблемы совместимости"
                )

            # Импортируем данные
            if "user" in import_data:
                self.core.state["user"] = import_data["user"]

            if "course_plan" in import_data:
                self.core.state["course_plan"] = import_data["course_plan"]

            if "learning_progress" in import_data:
                self.core.state["learning"] = import_data["learning_progress"]

            if "completed_lessons" in import_data:
                self.core.state["completed_lessons"] = import_data["completed_lessons"]

            # Сохраняем состояние
            result = self.core.save_state()

            if result:
                self.logger.info("Данные пользователя успешно импортированы")

            return result

        except Exception as e:
            self.logger.error(f"Ошибка импорта данных пользователя: {str(e)}")
            return False

    def validate_user_data(self):
        """
        Проверяет корректность пользовательских данных.

        Returns:
            dict: Результат валидации
        """
        try:
            validation_result = {"valid": True, "errors": [], "warnings": []}

            # Проверяем данные пользователя
            user_data = self.get_user_data()
            if not user_data.get("name"):
                validation_result["errors"].append("Отсутствует имя пользователя")
                validation_result["valid"] = False

            # Проверяем план курса
            course_plan = self.get_course_plan()
            if course_plan and not course_plan.get("title"):
                validation_result["warnings"].append("План курса не имеет названия")

            # Проверяем завершенные уроки
            completed_lessons = self.get_completed_lessons()
            if not isinstance(completed_lessons, list):
                validation_result["errors"].append(
                    "Некорректный формат списка завершенных уроков"
                )
                validation_result["valid"] = False

            return validation_result

        except Exception as e:
            self.logger.error(f"Ошибка валидации пользовательских данных: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Ошибка валидации: {str(e)}"],
                "warnings": [],
            }

    def cleanup_old_data(self, days_threshold=30):
        """
        Очищает устаревшие данные (резервные копии старше указанного срока).

        Args:
            days_threshold (int): Количество дней для хранения данных

        Returns:
            dict: Результат очистки
        """
        try:
            cleanup_result = {"success": True, "cleaned_files": 0, "errors": []}

            # Получаем список резервных копий
            if hasattr(self.core, "get_backup_list"):
                backups = self.core.get_backup_list()

                # Текущая дата
                current_time = datetime.now()

                for backup_info in backups:
                    try:
                        # Парсим дату из имени файла резервной копии
                        # Формат: backup_YYYY-MM-DD_HH-MM-SS.json
                        if backup_info.startswith("backup_") and backup_info.endswith(
                            ".json"
                        ):
                            date_str = backup_info[7:26]  # Извлекаем дату и время
                            backup_date = datetime.strptime(
                                date_str, "%Y-%m-%d_%H-%M-%S"
                            )

                            # Проверяем возраст резервной копии
                            age_days = (current_time - backup_date).days

                            if age_days > days_threshold:
                                # Удаляем старую резервную копию
                                backup_path = os.path.join("data/backups", backup_info)
                                if os.path.exists(backup_path):
                                    os.remove(backup_path)
                                    cleanup_result["cleaned_files"] += 1
                                    self.logger.info(
                                        f"Удалена старая резервная копия: {backup_info}"
                                    )

                    except Exception as e:
                        cleanup_result["errors"].append(
                            f"Ошибка при удалении {backup_info}: {str(e)}"
                        )

            self.logger.info(
                f"Очистка завершена. Удалено файлов: {cleanup_result['cleaned_files']}"
            )
            return cleanup_result

        except Exception as e:
            self.logger.error(f"Ошибка очистки старых данных: {str(e)}")
            return {"success": False, "cleaned_files": 0, "errors": [str(e)]}
