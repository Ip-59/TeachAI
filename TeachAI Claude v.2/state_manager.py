"""
Модуль управления состоянием TeachAI.
Отвечает за сохранение и загрузку данных о пользователе, прогрессе обучения и настройках.

Этот модуль объединяет функциональность:
- StateManagerCore: базовые операции с состоянием (загрузка/сохранение)
- StateManagerMethods: дополнительные методы для работы с пользователем и обучением

ИСПРАВЛЕНО ЭТАП 33: Добавлено делегирование методов работы с курсами (проблема #137)
"""

import logging
from state_manager_core import StateManagerCore
from state_manager_methods import StateManagerMethods


class StateManager:
    """
    Основной класс управления состоянием TeachAI.
    Объединяет базовую функциональность и дополнительные методы.
    """

    def __init__(self, state_file="data/state.json"):
        """
        Инициализация менеджера состояния.

        Args:
            state_file (str): Путь к файлу состояния (по умолчанию в папке data/)
        """
        self.logger = logging.getLogger(__name__)

        # Инициализируем ядро управления состоянием
        self.core = StateManagerCore(state_file)

        # Инициализируем дополнительные методы
        self.methods = StateManagerMethods(self.core)

        self.logger.info(
            f"StateManager полностью инициализирован с файлом: {state_file}"
        )

    # ========================================
    # ДЕЛЕГИРОВАНИЕ К CORE (базовые операции)
    # ========================================

    @property
    def state(self):
        """Возвращает текущее состояние."""
        return self.core.state

    @state.setter
    def state(self, value):
        """Устанавливает состояние."""
        self.core.state = value

    def save_state(self):
        """Сохраняет состояние в файл."""
        return self.core.save_state()

    def load_state(self):
        """Перезагружает состояние из файла."""
        return self.core.load_state()

    def get_state(self):
        """Возвращает копию текущего состояния."""
        return self.core.get_state()

    def update_state(self, updates):
        """Обновляет состояние системы."""
        return self.core.update_state(updates)

    def clear_state(self):
        """Очищает состояние, создавая новое по умолчанию."""
        return self.core.clear_state()

    def get_backup_list(self):
        """Возвращает список доступных резервных копий."""
        return self.core.get_backup_list()

    def restore_from_backup(self, backup_filename):
        """Восстанавливает состояние из резервной копии."""
        return self.core.restore_from_backup(backup_filename)

    def validate_state_integrity(self):
        """Проверяет целостность состояния."""
        return self.core.validate_state_integrity()

    # ========================================
    # ДЕЛЕГИРОВАНИЕ К METHODS (пользователь и обучение)
    # ========================================

    # ИСПРАВЛЕНО ЭТАП 33: Методы работы с курсами
    def get_all_courses(self):
        """Загружает список всех доступных курсов."""
        return self.methods.get_all_courses()

    def get_course_by_id(self, course_id):
        """Получает данные курса по его ID."""
        return self.methods.get_course_by_id(course_id)

    # Методы работы с пользователем
    def save_user_profile(self, user_data):
        """Сохраняет профиль пользователя."""
        return self.methods.save_user_profile(user_data)

    def get_user_data(self):
        """Возвращает данные пользователя."""
        return self.methods.get_user_data()

    def clear_user_data(self):
        """Очищает данные пользователя."""
        return self.methods.clear_user_data()

    def get_user_profile(self):
        """Возвращает профиль пользователя (псевдоним для get_user_data)."""
        return self.methods.get_user_profile()

    def update_user_profile(self, **kwargs):
        """Обновляет профиль пользователя."""
        return self.methods.update_user_profile(**kwargs)

    # Методы работы с обучением
    def save_course_plan(self, course_plan):
        """Сохраняет план курса."""
        return self.methods.save_course_plan(course_plan)

    def get_course_plan(self):
        """Возвращает план курса."""
        return self.methods.get_course_plan()

    def clear_course_plan(self):
        """Очищает план курса."""
        return self.methods.clear_course_plan()

    def save_learning_progress(self, progress_data):
        """Сохраняет прогресс обучения."""
        return self.methods.save_learning_progress(progress_data)

    def get_learning_progress(self):
        """Возвращает прогресс обучения."""
        return self.methods.get_learning_progress()

    def clear_learning_progress(self):
        """Очищает прогресс обучения."""
        return self.methods.clear_learning_progress()

    def update_learning_progress(self, **kwargs):
        """Обновляет прогресс обучения."""
        return self.methods.update_learning_progress(**kwargs)

    # Методы работы с уроками
    def get_completed_lessons(self):
        """Возвращает список завершенных уроков."""
        return self.methods.get_completed_lessons()

    def mark_lesson_completed(self, lesson_id):
        """Отмечает урок как завершенный."""
        return self.methods.mark_lesson_completed(lesson_id)

    def get_lesson_data(self, lesson_id):
        """Получает данные урока по ID."""
        return self.methods.get_lesson_data(lesson_id)

    def get_next_lesson(self):
        """Определяет следующий урок для изучения."""
        return self.methods.get_next_lesson()

    # Методы первого запуска
    def is_first_run(self):
        """Проверяет, является ли это первым запуском системы."""
        return self.methods.is_first_run()

    def mark_first_run_complete(self):
        """Отмечает первый запуск как завершенный."""
        return self.methods.mark_first_run_complete()

    # Методы аналитики
    def get_statistics(self):
        """Возвращает статистику использования системы."""
        return self.methods.get_statistics()

    def export_user_data(self):
        """Экспортирует данные пользователя для резервного копирования."""
        return self.methods.export_user_data()

    def import_user_data(self, import_data):
        """Импортирует данные пользователя из резервной копии."""
        return self.methods.import_user_data(import_data)
