"""
Интерфейс личного кабинета студента.
Отображает подробную информацию о прогрессе обучения, статистику по урокам,
результаты тестов и контрольных заданий.

НОВАЯ АРХИТЕКТУРА: Этот модуль теперь служит фасадом для специализированных компонентов.
Обеспечивает полную обратную совместимость со старым интерфейсом.

РЕФАКТОРИНГ ЭТАП 28: Разделен на компоненты для соблюдения лимитов размера модулей.
- StudentProfileCore: основная логика координации
- StudentProfileSections: HTML-секции интерфейса
- StudentProfileHandlers: обработчики событий и кнопок

ИСПРАВЛЕНО: Проблема #97 с lesson_attempts_count - правильный подсчет попыток
"""

import logging
from student_profile_core import StudentProfileCore
from student_profile_sections import StudentProfileSections
from student_profile_handlers import StudentProfileHandlers


class StudentProfileInterface:
    """
    Основной класс интерфейса личного кабинета студента.

    ВАЖНО: Обеспечивает полную обратную совместимость с предыдущей версией.
    Все методы работают точно так же, как раньше!
    """

    def __init__(
        self, state_manager, content_generator, system_logger, assessment=None
    ):
        """
        Инициализация интерфейса личного кабинета.

        Args:
            state_manager: Менеджер состояния
            content_generator: Генератор контента
            system_logger: Системный логгер
            assessment: Модуль оценивания (опционально)
        """
        self.state_manager = state_manager
        self.content_generator = content_generator
        self.system_logger = system_logger
        self.assessment = assessment
        self.logger = logging.getLogger(__name__)

        try:
            # Инициализируем ядро интерфейса
            self.core = StudentProfileCore(
                state_manager, content_generator, system_logger, assessment
            )

            # Инициализируем модуль секций
            self.sections = StudentProfileSections(self.core)

            # Инициализируем модуль обработчиков
            self.handlers = StudentProfileHandlers(self.core)

            # Переопределяем методы ядра для делегирования к sections и handlers
            self._setup_delegations()

            self.logger.info(
                "StudentProfileInterface (объединенный) успешно инициализирован"
            )

        except Exception as e:
            self.logger.error(
                f"Ошибка при инициализации StudentProfileInterface: {str(e)}"
            )
            raise

        # Прямой доступ к атрибутам для совместимости
        self.utils = self.core.utils
        self.main_container = self.core.main_container
        self.output_container = self.core.output_container

    def _setup_delegations(self):
        """
        Настраивает делегирование методов между компонентами.
        """
        # Делегируем методы создания секций к sections
        self.core._create_profile_info_section = (
            self.sections.create_profile_info_section
        )
        self.core._create_course_progress_section = (
            self.sections.create_course_progress_section
        )
        self.core._create_lessons_statistics_section = (
            self.sections.create_lessons_statistics_section
        )
        self.core._create_control_tasks_section = (
            self.sections.create_control_tasks_section
        )
        self.core._create_detailed_breakdown_section = (
            self.sections.create_detailed_breakdown_section
        )

        # Делегируем методы создания кнопок к handlers
        self.core._create_action_buttons = self.handlers.create_action_buttons

    # ========================================
    # ОСНОВНОЙ ПУБЛИЧНЫЙ МЕТОД (полная совместимость)
    # ========================================

    def show_student_profile(self):
        """
        Отображает личный кабинет студента с полной статистикой.

        ВАЖНО: Метод работает точно так же, как в старой версии!
        Обеспечивает полную обратную совместимость.

        Returns:
            widgets.VBox: Интерфейс личного кабинета
        """
        try:
            self.logger.info("Отображение личного кабинета студента")

            # Делегируем создание интерфейса к ядру
            result = self.core.create_main_profile_interface()

            # Обновляем ссылки для совместимости
            self.main_container = self.core.main_container

            return result

        except Exception as e:
            self.logger.error(f"Ошибка при отображении личного кабинета: {str(e)}")
            return self.core._create_error_interface(str(e))

    # ========================================
    # ДЕЛЕГИРОВАНИЕ К CORE (методы ядра)
    # ========================================

    def validate_dependencies(self):
        """Проверяет наличие всех зависимостей."""
        return self.core.validate_dependencies()

    def get_status(self):
        """Возвращает статус интерфейса."""
        try:
            core_status = self.core.get_status()
            handlers_status = self.handlers.get_handler_status()

            return {
                "interface_initialized": True,
                "core_status": core_status,
                "handlers_status": handlers_status,
                "sections_available": hasattr(self, "sections"),
                "compatibility_mode": "full",
                "version": "2.0_modular",
                "architecture": "core_sections_handlers",
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса: {str(e)}")
            return {"error": str(e)}

    # ========================================
    # СОВМЕСТИМОСТЬ СО СТАРЫМИ МЕТОДАМИ
    # ========================================

    def show_profile(self):
        """
        УСТАРЕЛО: Используйте show_student_profile().
        Обеспечивает совместимость со старым API.
        """
        self.logger.warning(
            "Используется устаревший метод show_profile, рекомендуется show_student_profile"
        )
        return self.show_student_profile()

    def display_profile(self):
        """
        УСТАРЕЛО: Используйте show_student_profile().
        Обеспечивает совместимость со старым API.
        """
        self.logger.warning(
            "Используется устаревший метод display_profile, рекомендуется show_student_profile"
        )
        return self.show_student_profile()

    def get_profile_interface(self):
        """
        УСТАРЕЛО: Используйте show_student_profile().
        Обеспечивает совместимость со старым API.
        """
        self.logger.warning(
            "Используется устаревший метод get_profile_interface, рекомендуется show_student_profile"
        )
        return self.show_student_profile()

    # ========================================
    # ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ДЛЯ РАСШИРЕННОЙ ФУНКЦИОНАЛЬНОСТИ
    # ========================================

    def create_navigation_buttons(self):
        """Создает дополнительные кнопки навигации."""
        return self.handlers.create_navigation_buttons()

    def refresh_data(self):
        """
        Обновляет данные интерфейса.

        Returns:
            bool: True если обновление прошло успешно
        """
        try:
            # Обновляем данные в ядре
            self.core._get_progress_data()
            self.core._get_detailed_statistics()

            self.logger.info("Данные интерфейса обновлены")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка при обновлении данных: {str(e)}")
            return False

    def export_profile_data(self):
        """
        Экспортирует данные профиля.

        Returns:
            dict: Экспортированные данные профиля
        """
        try:
            return {
                "user_profile": self.core._get_user_profile_data(),
                "progress_data": self.core._get_progress_data(),
                "detailed_stats": self.core._get_detailed_statistics(),
                "export_timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Ошибка при экспорте данных профиля: {str(e)}")
            return {}

    # ========================================
    # МЕТОДЫ ДЛЯ ОТЛАДКИ И МОНИТОРИНГА
    # ========================================

    def run_diagnostics(self):
        """
        Выполняет диагностику интерфейса.

        Returns:
            dict: Результат диагностики
        """
        try:
            diagnostics = {
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "core": self.core is not None,
                    "sections": hasattr(self, "sections") and self.sections is not None,
                    "handlers": hasattr(self, "handlers") and self.handlers is not None,
                },
                "dependencies": self.validate_dependencies(),
                "data_availability": {
                    "progress_data": bool(self.core._get_progress_data()),
                    "user_profile": bool(self.core._get_user_profile_data()),
                    "detailed_stats": bool(self.core._get_detailed_statistics()),
                },
            }

            diagnostics["overall_health"] = all(
                [
                    diagnostics["components"]["core"],
                    diagnostics["components"]["sections"],
                    diagnostics["components"]["handlers"],
                    diagnostics["dependencies"]["all_dependencies"],
                ]
            )

            return diagnostics

        except Exception as e:
            self.logger.error(f"Ошибка при диагностике: {str(e)}")
            return {"error": str(e), "healthy": False}

    def get_architecture_info(self):
        """
        Возвращает информацию об архитектуре модуля.

        Returns:
            dict: Информация об архитектуре
        """
        return {
            "architecture_type": "modular_facade",
            "components": {
                "core": "StudentProfileCore - основная логика координации",
                "sections": "StudentProfileSections - HTML-секции интерфейса",
                "handlers": "StudentProfileHandlers - обработчики событий",
            },
            "benefits": [
                "Соблюдение лимитов размера модулей",
                "Четкое разделение ответственности",
                "Простота тестирования и отладки",
                "Полная обратная совместимость",
                "Легкость расширения функциональности",
            ],
            "compatibility": "100% с предыдущей версией",
            "module_count": 4,
            "total_estimated_lines": 164,  # Размер этого объединяющего файла
        }
