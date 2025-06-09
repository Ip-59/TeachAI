"""
Ядро интерфейса личного кабинета студента.
Основная логика координации и управления компонентами профиля.
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
from datetime import datetime
from interface_utils import InterfaceUtils, InterfaceState


class StudentProfileCore:
    """
    Ядро интерфейса личного кабинета студента.
    Координирует основную логику отображения профиля.
    """

    def __init__(
        self, state_manager, content_generator, system_logger, assessment=None
    ):
        """
        Инициализация ядра интерфейса личного кабинета.

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

        # Утилиты интерфейса
        self.utils = InterfaceUtils()

        # Контейнер для основного интерфейса
        self.main_container = None

        # Выходной контейнер для управления
        self.output_container = widgets.Output()

        self.logger.info("StudentProfileCore инициализирован")

    def create_main_profile_interface(self):
        """
        Создает основной интерфейс личного кабинета студента.

        Returns:
            widgets.VBox: Полный интерфейс личного кабинета
        """
        try:
            self.logger.info("Создание основного интерфейса личного кабинета")

            # Создаем заголовок
            header = self.utils.create_header("📊 Личный кабинет")

            # Получаем данные о прогрессе
            progress_data = self._get_progress_data()
            detailed_stats = self._get_detailed_statistics()

            # Создаем секции интерфейса (методы будут делегированы в sections)
            profile_info = self._create_profile_info_section(progress_data)
            course_progress = self._create_course_progress_section(detailed_stats)
            lessons_statistics = self._create_lessons_statistics_section(detailed_stats)
            control_tasks_stats = self._create_control_tasks_section(detailed_stats)
            detailed_breakdown = self._create_detailed_breakdown_section()

            # Создаем кнопки действий (метод будет делегирован в handlers)
            action_buttons = self._create_action_buttons()

            # Собираем все в контейнер
            self.main_container = widgets.VBox(
                [
                    header,
                    profile_info,
                    course_progress,
                    lessons_statistics,
                    control_tasks_stats,
                    detailed_breakdown,
                    action_buttons,
                    self.output_container,
                ],
                layout=widgets.Layout(gap="20px", padding="20px"),
            )

            self.logger.info("Интерфейс личного кабинета успешно создан")
            return self.main_container

        except Exception as e:
            self.logger.error(f"Ошибка при создании личного кабинета: {str(e)}")
            return self._create_error_interface(str(e))

    def _get_progress_data(self):
        """
        Получает данные о прогрессе обучения.

        Returns:
            dict: Данные о прогрессе
        """
        try:
            return self.state_manager.learning_progress.get_learning_progress()
        except Exception as e:
            self.logger.error(f"Ошибка при получении данных прогресса: {str(e)}")
            return {}

    def _get_detailed_statistics(self):
        """
        Получает детальную статистику по курсу.

        Returns:
            dict: Детальная статистика
        """
        try:
            return self.state_manager.learning_progress.get_detailed_course_statistics()
        except Exception as e:
            self.logger.error(f"Ошибка при получении детальной статистики: {str(e)}")
            return {}

    def _get_user_profile_data(self):
        """
        Получает данные профиля пользователя.

        Returns:
            dict: Данные профиля пользователя
        """
        try:
            return self.state_manager.user_profile.get_user_profile()
        except Exception as e:
            self.logger.error(f"Ошибка при получении профиля пользователя: {str(e)}")
            return {"name": "Пользователь"}

    def _create_error_interface(self, error_message):
        """
        Создает интерфейс ошибки.

        Args:
            error_message (str): Сообщение об ошибке

        Returns:
            widgets.VBox: Интерфейс ошибки
        """
        error_widget = widgets.HTML(
            value=f"""
            <div style="
                background-color: #f8d7da;
                color: #721c24;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #f5c6cb;
                text-align: center;
            ">
                <h3>❌ Ошибка при загрузке личного кабинета</h3>
                <p>{error_message}</p>
                <p>Попробуйте перезагрузить страницу или обратитесь к администратору.</p>
            </div>
            """
        )

        return widgets.VBox([error_widget], layout=widgets.Layout(padding="20px"))

    def validate_dependencies(self):
        """
        Проверяет наличие всех необходимых зависимостей.

        Returns:
            dict: Результат проверки зависимостей
        """
        dependencies = {
            "state_manager": self.state_manager is not None,
            "content_generator": self.content_generator is not None,
            "system_logger": self.system_logger is not None,
            "utils": self.utils is not None,
        }

        dependencies["all_dependencies"] = all(dependencies.values())

        self.logger.info(f"Проверка зависимостей: {dependencies}")
        return dependencies

    def get_status(self):
        """
        Возвращает статус ядра интерфейса.

        Returns:
            dict: Статус ядра
        """
        return {
            "core_initialized": True,
            "dependencies": self.validate_dependencies(),
            "main_container_created": self.main_container is not None,
            "logger_name": self.logger.name,
        }

    # ========================================
    # МЕТОДЫ-ЗАГЛУШКИ ДЛЯ ДЕЛЕГИРОВАНИЯ
    # (Будут переопределены в фасаде)
    # ========================================

    def _create_profile_info_section(self, progress_data):
        """Заглушка - будет делегирована в sections."""
        return widgets.HTML(value="<div>Profile info section placeholder</div>")

    def _create_course_progress_section(self, detailed_stats):
        """Заглушка - будет делегирована в sections."""
        return widgets.HTML(value="<div>Course progress section placeholder</div>")

    def _create_lessons_statistics_section(self, detailed_stats):
        """Заглушка - будет делегирована в sections."""
        return widgets.HTML(value="<div>Lessons statistics section placeholder</div>")

    def _create_control_tasks_section(self, detailed_stats):
        """Заглушка - будет делегирована в sections."""
        return widgets.HTML(value="<div>Control tasks section placeholder</div>")

    def _create_detailed_breakdown_section(self):
        """Заглушка - будет делегирована в sections."""
        return widgets.HTML(value="<div>Detailed breakdown section placeholder</div>")

    def _create_action_buttons(self):
        """Заглушка - будет делегирована в handlers."""
        return widgets.HBox([])
