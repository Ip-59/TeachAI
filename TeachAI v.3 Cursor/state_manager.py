"""
Базовый модуль для управления состоянием системы.
Отвечает за загрузку, сохранение и инициализацию состояния.
РЕФАКТОРИНГ: Выделены базовые операции из большого модуля (600 строк → 200 строк)
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Импортируем специализированные менеджеры
from user_profile_manager import UserProfileManager
from learning_progress_manager import LearningProgressManager
from course_data_manager import CourseDataManager


class StateManager:
    """Базовый менеджер состояния - координирует специализированные менеджеры."""

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

        # Инициализируем специализированные менеджеры
        self.user_profile = UserProfileManager(self)
        self.learning_progress = LearningProgressManager(self)
        self.course_data = CourseDataManager(self)

        self.logger.info(
            "StateManager успешно инициализирован с специализированными менеджерами"
        )

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
                "lesson_scores": {},
                "lesson_attempts": {},
                "lesson_completion_status": {},
                "questions_count": {},
                "average_score": 0,
                "total_assessments": 0,
                "total_score": 0,
                "course_progress_percent": 0,
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

    # ========================================
    # ДЕЛЕГИРОВАНИЕ К СПЕЦИАЛИЗИРОВАННЫМ МЕНЕДЖЕРАМ
    # (Для обратной совместимости со старым API)
    # ========================================

    # Методы профиля пользователя
    def update_user_profile(
        self, name, total_study_hours, lesson_duration_minutes, communication_style
    ):
        return self.user_profile.update_user_profile(
            name, total_study_hours, lesson_duration_minutes, communication_style
        )

    def get_user_profile(self):
        return self.user_profile.get_user_profile()

    # Методы прогресса обучения
    def update_learning_progress(
        self, course=None, section=None, topic=None, lesson=None
    ):
        return self.learning_progress.update_learning_progress(
            course, section, topic, lesson
        )

    def save_lesson_assessment(self, lesson_id, score, is_passed=True):
        return self.learning_progress.save_lesson_assessment(
            lesson_id, score, is_passed
        )

    def is_lesson_completed(self, lesson_id):
        return self.learning_progress.is_lesson_completed(lesson_id)

    def mark_lesson_incomplete(self, lesson_id):
        return self.learning_progress.mark_lesson_incomplete(lesson_id)

    def increment_questions_count(self, lesson_id):
        return self.learning_progress.increment_questions_count(lesson_id)

    def get_questions_count(self, lesson_id):
        return self.learning_progress.get_questions_count(lesson_id)

    def reset_questions_count(self, lesson_id):
        return self.learning_progress.reset_questions_count(lesson_id)

    def get_lesson_score(self, lesson_id):
        return self.learning_progress.get_lesson_score(lesson_id)

    def get_detailed_course_statistics(self):
        return self.learning_progress.get_detailed_course_statistics()

    def update_assessment_results(self, score):
        return self.learning_progress.update_assessment_results(score)

    def get_learning_progress(self):
        return self.learning_progress.get_learning_progress()

    def calculate_course_progress(self):
        return self.learning_progress.calculate_course_progress()

    # Методы данных курса
    def save_course_plan(self, course_plan):
        return self.course_data.save_course_plan(course_plan)

    def get_course_plan(self):
        return self.course_data.get_course_plan()

    def get_course_by_id(self, course_id):
        return self.course_data.get_course_by_id(course_id)

    def get_all_courses(self):
        return self.course_data.get_all_courses()

    def get_next_lesson(self):
        return self.course_data.get_next_lesson()

    def get_lesson_data(self, section_id, topic_id, lesson_id):
        return self.course_data.get_lesson_data(section_id, topic_id, lesson_id)
