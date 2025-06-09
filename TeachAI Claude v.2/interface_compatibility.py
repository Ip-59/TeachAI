"""
Модуль обратной совместимости для UserInterface.
Обеспечивает полную совместимость со старым API интерфейсов.
"""

import logging
from datetime import datetime


class InterfaceCompatibility:
    """
    Класс обеспечивающий обратную совместимость со старым API UserInterface.
    """

    def __init__(self, facade):
        """
        Инициализация модуля совместимости.

        Args:
            facade: Экземпляр InterfaceFacade
        """
        self.facade = facade
        self.logger = logging.getLogger(__name__)

        # Данные текущего урока для совместимости
        self.current_course = None
        self.current_section = None
        self.current_topic = None
        self.current_lesson = None
        self.current_lesson_content = None
        self.current_questions = None
        self.current_answers = []

        self.logger.info("InterfaceCompatibility инициализирован")

    # ========================================
    # СТАРЫЕ МЕТОДЫ - ПОЛНАЯ СОВМЕСТИМОСТЬ
    # ========================================

    def show_welcome_message(self):
        """
        УСТАРЕЛО: Используйте show_initial_setup().
        Обеспечивает совместимость со старым API.
        """
        self.logger.warning(
            "Используется устаревший метод show_welcome_message, рекомендуется show_initial_setup"
        )
        return self.facade.show_initial_setup()

    def display_course_selection(self):
        """
        УСТАРЕЛО: Используйте show_course_selection().
        Обеспечивает совместимость со старым API.
        """
        self.logger.warning(
            "Используется устаревший метод display_course_selection, рекомендуется show_course_selection"
        )
        return self.facade.show_course_selection()

    def display_lesson(self, lesson_id=None):
        """
        УСТАРЕЛО: Используйте show_lesson().
        Обеспечивает совместимость со старым API.
        """
        self.logger.warning(
            "Используется устаревший метод display_lesson, рекомендуется show_lesson"
        )
        return self.facade.show_lesson(lesson_id)

    def display_assessment(self, lesson_id=None):
        """
        УСТАРЕЛО: Используйте show_assessment().
        Обеспечивает совместимость со старым API.
        """
        self.logger.warning(
            "Используется устаревший метод display_assessment, рекомендуется show_assessment"
        )
        return self.facade.show_assessment(lesson_id)

    def display_results(self, assessment_results=None):
        """
        УСТАРЕЛО: Используйте show_results().
        Обеспечивает совместимость со старым API.
        """
        self.logger.warning(
            "Используется устаревший метод display_results, рекомендуется show_results"
        )
        return self.facade.show_results(assessment_results)

    def show_completion_message(self):
        """
        УСТАРЕЛО: Используйте show_completion().
        Обеспечивает совместимость со старым API.
        """
        self.logger.warning(
            "Используется устаревший метод show_completion_message, рекомендуется show_completion"
        )
        return self.facade.show_completion()

    # ========================================
    # МЕТОДЫ РАБОТЫ С ДАННЫМИ УРОКА
    # ========================================

    def set_current_lesson_data(
        self, course=None, section=None, topic=None, lesson=None, content=None
    ):
        """
        Устанавливает данные текущего урока для обратной совместимости.

        Args:
            course: Данные курса
            section: Данные секции
            topic: Данные темы
            lesson: Данные урока
            content: Содержание урока
        """
        self.current_course = course
        self.current_section = section
        self.current_topic = topic
        self.current_lesson = lesson
        self.current_lesson_content = content

        self.logger.debug("Установлены данные текущего урока для совместимости")

    def get_current_lesson_data(self):
        """
        Возвращает данные текущего урока.

        Returns:
            dict: Данные текущего урока
        """
        return {
            "course": self.current_course,
            "section": self.current_section,
            "topic": self.current_topic,
            "lesson": self.current_lesson,
            "content": self.current_lesson_content,
            "questions": self.current_questions,
            "answers": self.current_answers,
        }

    def clear_current_lesson_data(self):
        """Очищает данные текущего урока."""
        self.current_course = None
        self.current_section = None
        self.current_topic = None
        self.current_lesson = None
        self.current_lesson_content = None
        self.current_questions = None
        self.current_answers = []

        self.logger.debug("Очищены данные текущего урока")

    def set_current_questions(self, questions):
        """
        Устанавливает вопросы для текущего теста.

        Args:
            questions (list): Список вопросов
        """
        self.current_questions = questions
        self.current_answers = []  # Сбрасываем ответы

        self.logger.debug(f"Установлены вопросы: {len(questions) if questions else 0}")

    def add_answer(self, answer):
        """
        Добавляет ответ к списку ответов.

        Args:
            answer: Ответ пользователя
        """
        if self.current_answers is None:
            self.current_answers = []

        self.current_answers.append(answer)
        self.logger.debug(f"Добавлен ответ. Всего ответов: {len(self.current_answers)}")

    def get_current_answers(self):
        """
        Возвращает текущие ответы пользователя.

        Returns:
            list: Список ответов
        """
        return self.current_answers or []

    # ========================================
    # МЕТОДЫ СОСТОЯНИЯ (устаревшие)
    # ========================================

    def get_interface_state(self):
        """
        УСТАРЕЛО: Используйте facade.get_current_state().
        Возвращает текущее состояние интерфейса.
        """
        self.logger.warning("Используется устаревший метод get_interface_state")
        return self.facade.get_current_state()

    def set_interface_state(self, state):
        """
        УСТАРЕЛО: Используйте facade.navigate_to().
        Устанавливает состояние интерфейса.
        """
        self.logger.warning("Используется устаревший метод set_interface_state")
        try:
            self.facade.current_state = state
            self.logger.debug(f"Состояние установлено: {state}")
        except Exception as e:
            self.logger.error(f"Ошибка установки состояния: {str(e)}")

    # ========================================
    # МЕТОДЫ МИГРАЦИИ ДАННЫХ
    # ========================================

    def migrate_old_interface_data(self, old_data):
        """
        Мигрирует данные интерфейса из старого формата.

        Args:
            old_data (dict): Данные в старом формате

        Returns:
            dict: Данные в новом формате
        """
        try:
            # Проверяем, нужна ли миграция
            if (
                "interface_version" in old_data
                and old_data["interface_version"] >= "2.0"
            ):
                return old_data

            # Выполняем миграцию
            migrated = {
                "interface_version": "2.0",
                "migrated_at": datetime.now().isoformat(),
                "current_state": old_data.get("state", "initial_setup"),
                "lesson_data": {
                    "course": old_data.get("current_course"),
                    "section": old_data.get("current_section"),
                    "topic": old_data.get("current_topic"),
                    "lesson": old_data.get("current_lesson"),
                    "content": old_data.get("current_lesson_content"),
                },
                "assessment_data": {
                    "questions": old_data.get("current_questions", []),
                    "answers": old_data.get("current_answers", []),
                },
            }

            self.logger.info("Выполнена миграция данных интерфейса")
            return migrated

        except Exception as e:
            self.logger.error(f"Ошибка миграции данных интерфейса: {str(e)}")
            # Возвращаем безопасный минимум
            return {
                "interface_version": "2.0",
                "current_state": "initial_setup",
                "lesson_data": {},
                "assessment_data": {},
            }

    def restore_from_migrated_data(self, migrated_data):
        """
        Восстанавливает состояние интерфейса из мигрированных данных.

        Args:
            migrated_data (dict): Мигрированные данные

        Returns:
            bool: True если восстановление прошло успешно
        """
        try:
            # Восстанавливаем данные урока
            lesson_data = migrated_data.get("lesson_data", {})
            self.set_current_lesson_data(
                course=lesson_data.get("course"),
                section=lesson_data.get("section"),
                topic=lesson_data.get("topic"),
                lesson=lesson_data.get("lesson"),
                content=lesson_data.get("content"),
            )

            # Восстанавливаем данные оценивания
            assessment_data = migrated_data.get("assessment_data", {})
            self.current_questions = assessment_data.get("questions", [])
            self.current_answers = assessment_data.get("answers", [])

            # Восстанавливаем состояние (если возможно)
            current_state = migrated_data.get("current_state", "initial_setup")
            try:
                from interface_utils import InterfaceState

                state_enum = InterfaceState(current_state)
                self.facade.current_state = state_enum
            except (ValueError, ImportError):
                self.logger.warning(
                    f"Не удалось восстановить состояние: {current_state}"
                )

            self.logger.info(
                "Состояние интерфейса восстановлено из мигрированных данных"
            )
            return True

        except Exception as e:
            self.logger.error(f"Ошибка восстановления состояния: {str(e)}")
            return False

    # ========================================
    # СЛУЖЕБНЫЕ МЕТОДЫ
    # ========================================

    def log_deprecated_usage(self, method_name, recommended_method):
        """
        Логирует использование устаревших методов.

        Args:
            method_name (str): Название устаревшего метода
            recommended_method (str): Рекомендуемый метод
        """
        self.logger.warning(
            f"DEPRECATED: Метод '{method_name}' устарел. "
            f"Рекомендуется использовать '{recommended_method}'"
        )

    def get_compatibility_info(self):
        """
        Возвращает информацию о совместимости интерфейсов.

        Returns:
            dict: Информация о совместимости
        """
        return {
            "compatibility_version": "2.0",
            "supported_versions": ["1.0", "1.1", "1.2", "2.0"],
            "deprecated_methods": [
                "show_welcome_message",
                "display_course_selection",
                "display_lesson",
                "display_assessment",
                "display_results",
                "show_completion_message",
                "get_interface_state",
                "set_interface_state",
            ],
            "migration_available": True,
            "backward_compatible": True,
            "lesson_data_preserved": True,
            "assessment_data_preserved": True,
        }

    def get_migration_status(self, data):
        """
        Проверяет статус миграции данных интерфейса.

        Args:
            data (dict): Данные для проверки

        Returns:
            dict: Статус миграции
        """
        try:
            version = data.get("interface_version", "1.0")
            needs_migration = version < "2.0"

            return {
                "current_version": version,
                "target_version": "2.0",
                "needs_migration": needs_migration,
                "migration_available": True,
                "data_preserved": True,
                "checked_at": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "error": str(e),
                "needs_migration": True,
                "migration_available": True,
            }

    def validate_old_data_format(self, data):
        """
        Валидирует данные в старом формате.

        Args:
            data (dict): Данные для валидации

        Returns:
            dict: Результат валидации
        """
        try:
            validation = {"valid": True, "issues": [], "warnings": []}

            # Проверяем обязательные поля старого формата
            if "state" not in data:
                validation["warnings"].append("Отсутствует поле 'state'")

            # Проверяем данные урока
            lesson_fields = ["current_course", "current_lesson"]
            missing_lesson_fields = [
                field for field in lesson_fields if field not in data
            ]
            if missing_lesson_fields:
                validation["warnings"].append(
                    f"Отсутствуют поля урока: {missing_lesson_fields}"
                )

            # Проверяем данные оценивания
            if "current_questions" in data and not isinstance(
                data["current_questions"], list
            ):
                validation["issues"].append("current_questions должно быть списком")
                validation["valid"] = False

            if "current_answers" in data and not isinstance(
                data["current_answers"], list
            ):
                validation["issues"].append("current_answers должно быть списком")
                validation["valid"] = False

            return validation

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "issues": [f"Ошибка валидации: {str(e)}"],
            }
