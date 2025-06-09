"""
Модуль пользовательского интерфейса TeachAI.
Отвечает за отображение всех экранов и взаимодействие с пользователем.

НОВАЯ АРХИТЕКТУРА: Этот модуль теперь служит фасадом для специализированных интерфейсов.
Обеспечивает полную обратную совместимость со старым интерфейсом.

РЕФАКТОРИНГ ЭТАП 27: Разделен на компоненты для соблюдения лимитов размера модулей.
"""

import logging
from interface_facade import InterfaceFacade
from interface_compatibility import InterfaceCompatibility
from interface_utils import InterfaceState


class UserInterface:
    """
    Основной класс пользовательского интерфейса TeachAI.

    ВАЖНО: Обеспечивает полную обратную совместимость с предыдущей версией.
    Все методы работают точно так же, как раньше!
    """

    def __init__(self, state_manager, content_generator, assessment, system_logger):
        """
        Инициализация интерфейса.

        Args:
            state_manager (StateManager): Объект менеджера состояния
            content_generator (ContentGenerator): Объект генератора контента
            assessment (Assessment): Объект модуля оценивания
            system_logger (Logger): Объект логгера
        """
        self.state_manager = state_manager
        self.content_generator = content_generator
        self.assessment = assessment
        self.system_logger = system_logger
        self.logger = logging.getLogger(__name__)

        try:
            # Инициализируем основной фасад
            self.facade = InterfaceFacade(
                state_manager, content_generator, assessment, system_logger
            )

            # Инициализируем модуль обратной совместимости
            self.compatibility = InterfaceCompatibility(self.facade)

            self.logger.info("UserInterface (объединенный) успешно инициализирован")

        except Exception as e:
            self.logger.error(f"Ошибка при инициализации UserInterface: {str(e)}")
            raise

        # Прямой доступ к атрибутам для совместимости
        self.current_state = self.facade.current_state

    # ========================================
    # ДЕЛЕГИРОВАНИЕ К FACADE (новые методы)
    # ========================================

    def show_initial_setup(self):
        """Отображает интерфейс первоначальной настройки."""
        result = self.facade.show_initial_setup()
        self.current_state = self.facade.current_state
        return result

    def show_course_selection(self):
        """Отображает интерфейс выбора курса."""
        result = self.facade.show_course_selection()
        self.current_state = self.facade.current_state
        return result

    def show_lesson(self, lesson_id=None):
        """Отображает интерфейс урока."""
        result = self.facade.show_lesson(lesson_id)
        self.current_state = self.facade.current_state
        return result

    def show_assessment(self, lesson_id=None):
        """Отображает интерфейс тестирования."""
        result = self.facade.show_assessment(lesson_id)
        self.current_state = self.facade.current_state
        return result

    def show_results(self, assessment_results=None):
        """Отображает результаты тестирования."""
        result = self.facade.show_results(assessment_results)
        self.current_state = self.facade.current_state
        return result

    def show_completion(self):
        """Отображает интерфейс завершения курса."""
        result = self.facade.show_completion()
        self.current_state = self.facade.current_state
        return result

    def show_main_menu(self):
        """Отображает главное меню."""
        result = self.facade.show_main_menu()
        self.current_state = self.facade.current_state
        return result

    def show_student_profile(self):
        """Отображает профиль студента."""
        result = self.facade.show_student_profile()
        self.current_state = self.facade.current_state
        return result

    # ========================================
    # ДЕЛЕГИРОВАНИЕ К COMPATIBILITY (старые методы)
    # ========================================

    def show_welcome_message(self):
        """УСТАРЕЛО: Используйте show_initial_setup()."""
        result = self.compatibility.show_welcome_message()
        self.current_state = self.facade.current_state
        return result

    def display_course_selection(self):
        """УСТАРЕЛО: Используйте show_course_selection()."""
        result = self.compatibility.display_course_selection()
        self.current_state = self.facade.current_state
        return result

    def display_lesson(self, lesson_id=None):
        """УСТАРЕЛО: Используйте show_lesson()."""
        result = self.compatibility.display_lesson(lesson_id)
        self.current_state = self.facade.current_state
        return result

    def display_assessment(self, lesson_id=None):
        """УСТАРЕЛО: Используйте show_assessment()."""
        result = self.compatibility.display_assessment(lesson_id)
        self.current_state = self.facade.current_state
        return result

    def display_results(self, assessment_results=None):
        """УСТАРЕЛО: Используйте show_results()."""
        result = self.compatibility.display_results(assessment_results)
        self.current_state = self.facade.current_state
        return result

    def show_completion_message(self):
        """УСТАРЕЛО: Используйте show_completion()."""
        result = self.compatibility.show_completion_message()
        self.current_state = self.facade.current_state
        return result

    # ========================================
    # МЕТОДЫ РАБОТЫ С ДАННЫМИ УРОКА
    # ========================================

    def set_current_lesson_data(
        self, course=None, section=None, topic=None, lesson=None, content=None
    ):
        """Устанавливает данные текущего урока."""
        return self.compatibility.set_current_lesson_data(
            course, section, topic, lesson, content
        )

    def get_current_lesson_data(self):
        """Возвращает данные текущего урока."""
        return self.compatibility.get_current_lesson_data()

    def clear_current_lesson_data(self):
        """Очищает данные текущего урока."""
        return self.compatibility.clear_current_lesson_data()

    def set_current_questions(self, questions):
        """Устанавливает вопросы для текущего теста."""
        return self.compatibility.set_current_questions(questions)

    def add_answer(self, answer):
        """Добавляет ответ к списку ответов."""
        return self.compatibility.add_answer(answer)

    def get_current_answers(self):
        """Возвращает текущие ответы пользователя."""
        return self.compatibility.get_current_answers()

    # ========================================
    # МЕТОДЫ НАВИГАЦИИ И СОСТОЯНИЯ
    # ========================================

    def get_current_state(self):
        """Возвращает текущее состояние интерфейса."""
        return self.facade.get_current_state()

    def can_navigate_to(self, target_state):
        """Проверяет возможность перехода к указанному состоянию."""
        return self.facade.can_navigate_to(target_state)

    def navigate_to(self, target_state, **kwargs):
        """Выполняет навигацию к указанному состоянию."""
        result = self.facade.navigate_to(target_state, **kwargs)
        self.current_state = self.facade.current_state
        return result

    # Устаревшие методы состояния
    def get_interface_state(self):
        """УСТАРЕЛО: Используйте get_current_state()."""
        return self.compatibility.get_interface_state()

    def set_interface_state(self, state):
        """УСТАРЕЛО: Используйте navigate_to()."""
        self.compatibility.set_interface_state(state)
        self.current_state = self.facade.current_state

    # ========================================
    # МЕТОДЫ МИГРАЦИИ И СОВМЕСТИМОСТИ
    # ========================================

    def migrate_old_interface_data(self, old_data):
        """Мигрирует данные интерфейса из старого формата."""
        return self.compatibility.migrate_old_interface_data(old_data)

    def restore_from_migrated_data(self, migrated_data):
        """Восстанавливает состояние интерфейса из мигрированных данных."""
        result = self.compatibility.restore_from_migrated_data(migrated_data)
        self.current_state = self.facade.current_state
        return result

    def get_compatibility_info(self):
        """Возвращает информацию о совместимости интерфейсов."""
        return self.compatibility.get_compatibility_info()

    def get_migration_status(self, data):
        """Проверяет статус миграции данных интерфейса."""
        return self.compatibility.get_migration_status(data)

    def validate_old_data_format(self, data):
        """Валидирует данные в старом формате."""
        return self.compatibility.validate_old_data_format(data)

    # ========================================
    # ИНФОРМАЦИОННЫЕ МЕТОДЫ
    # ========================================

    def get_interface_info(self):
        """Возвращает информацию о доступных интерфейсах."""
        return self.facade.get_interface_info()

    def validate_dependencies(self):
        """Проверяет наличие всех зависимостей."""
        return self.facade.validate_dependencies()

    def get_status(self):
        """Возвращает полный статус интерфейса."""
        try:
            facade_status = self.facade.get_status()
            compatibility_info = self.get_compatibility_info()

            return {
                "interface_initialized": True,
                "current_state": self.current_state.value
                if self.current_state
                else None,
                "facade_status": facade_status,
                "compatibility_info": compatibility_info,
                "lesson_data": self.get_current_lesson_data(),
                "version": "2.0",
                "architecture": "modular_facade",
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса интерфейса: {str(e)}")
            return {"error": str(e)}

    # ========================================
    # МЕТОДЫ ДЛЯ ОТЛАДКИ И МОНИТОРИНГА
    # ========================================

    def run_diagnostics(self):
        """
        Выполняет диагностику интерфейса.

        Returns:
            dict: Результаты диагностики
        """
        try:
            diagnostics = {"timestamp": datetime.now().isoformat(), "tests": []}

            # Тест 1: Проверка инициализации
            try:
                assert self.facade is not None
                assert self.compatibility is not None
                diagnostics["tests"].append(
                    {
                        "name": "initialization",
                        "status": "passed",
                        "message": "Все компоненты инициализированы",
                    }
                )
            except Exception as e:
                diagnostics["tests"].append(
                    {"name": "initialization", "status": "failed", "error": str(e)}
                )

            # Тест 2: Проверка зависимостей
            dependencies = self.validate_dependencies()
            dependencies_ok = dependencies.get(
                "all_core_dependencies", False
            ) and dependencies.get("all_interfaces", False)
            diagnostics["tests"].append(
                {
                    "name": "dependencies",
                    "status": "passed" if dependencies_ok else "failed",
                    "message": f"Зависимости: {'все в порядке' if dependencies_ok else 'есть проблемы'}",
                    "details": dependencies,
                }
            )

            # Тест 3: Проверка навигации
            try:
                current_state = self.get_current_state()
                can_navigate = self.can_navigate_to(InterfaceState.COURSE_SELECTION)
                diagnostics["tests"].append(
                    {
                        "name": "navigation",
                        "status": "passed",
                        "message": f"Текущее состояние: {current_state}, навигация работает: {can_navigate}",
                    }
                )
            except Exception as e:
                diagnostics["tests"].append(
                    {"name": "navigation", "status": "failed", "error": str(e)}
                )

            # Подсчет результатов
            passed = len([t for t in diagnostics["tests"] if t["status"] == "passed"])
            total = len(diagnostics["tests"])
            diagnostics["summary"] = {
                "total_tests": total,
                "passed": passed,
                "failed": total - passed,
                "success_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            }

            return diagnostics

        except Exception as e:
            from datetime import datetime

            self.logger.error(f"Ошибка диагностики интерфейса: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def __str__(self):
        """Строковое представление UserInterface."""
        interface_count = self.get_interface_info().get("total_interfaces", 0)
        current_state = self.current_state.value if self.current_state else "unknown"
        return f"UserInterface(interfaces={interface_count}, state='{current_state}')"

    def __repr__(self):
        """Представление UserInterface для отладки."""
        return f"UserInterface(facade={bool(self.facade)}, compatibility={bool(self.compatibility)})"


# ========================================
# BACKWARD COMPATIBILITY
# ========================================


# Для обратной совместимости со старым кодом
def create_user_interface(state_manager, content_generator, assessment, system_logger):
    """
    Фабричная функция для создания UserInterface.
    Обеспечивает обратную совместимость.

    Args:
        state_manager: Менеджер состояния
        content_generator: Генератор контента
        assessment: Модуль оценивания
        system_logger: Системный логгер

    Returns:
        UserInterface: Экземпляр пользовательского интерфейса
    """
    return UserInterface(state_manager, content_generator, assessment, system_logger)
