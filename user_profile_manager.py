"""
Модуль для управления профилем пользователя.
Отвечает за обновление и получение данных профиля пользователя.
РЕФАКТОРИНГ: Выделен из state_manager.py для лучшей модульности
"""

import logging


class UserProfileManager:
    """Менеджер профиля пользователя."""

    def __init__(self, state_manager):
        """
        Инициализация менеджера профиля.

        Args:
            state_manager: Ссылка на основной StateManager
        """
        self.state_manager = state_manager
        self.logger = logging.getLogger(__name__)

    def update_user_profile(
        self, name, total_study_hours, lesson_duration_minutes, communication_style
    ):
        """
        Обновляет профиль пользователя.

        Args:
            name (str): Имя пользователя
            total_study_hours (int): Общая продолжительность обучения в часах
            lesson_duration_minutes (int): Длительность одного занятия в минутах
            communication_style (str): Формат общения (formal, friendly, casual, brief)

        Returns:
            bool: True если обновление прошло успешно, иначе False
        """
        try:
            self.state_manager.state["user"]["name"] = name
            self.state_manager.state["user"]["total_study_hours"] = total_study_hours
            self.state_manager.state["user"][
                "lesson_duration_minutes"
            ] = lesson_duration_minutes
            self.state_manager.state["user"][
                "communication_style"
            ] = communication_style

            self.logger.info(f"Профиль пользователя '{name}' успешно обновлен")

            # Сохраняем обновленное состояние
            return self.state_manager.save_state()
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении профиля пользователя: {str(e)}")
            return False

    def get_user_profile(self):
        """
        Получает профиль пользователя.

        Returns:
            dict: Словарь с данными пользователя
        """
        try:
            profile = self.state_manager.state["user"].copy()
            self.logger.debug(
                f"Получен профиль пользователя: {profile.get('name', 'Неизвестный')}"
            )
            return profile
        except Exception as e:
            self.logger.error(f"Ошибка при получении профиля пользователя: {str(e)}")
            return {
                "name": "",
                "total_study_hours": 0,
                "lesson_duration_minutes": 0,
                "communication_style": "friendly",
            }

    def get_user_name(self):
        """
        Получает имя пользователя.

        Returns:
            str: Имя пользователя
        """
        try:
            return self.state_manager.state["user"].get("name", "")
        except Exception as e:
            self.logger.error(f"Ошибка при получении имени пользователя: {str(e)}")
            return ""

    def get_communication_style(self):
        """
        Получает стиль общения пользователя.

        Returns:
            str: Стиль общения
        """
        try:
            return self.state_manager.state["user"].get(
                "communication_style", "friendly"
            )
        except Exception as e:
            self.logger.error(f"Ошибка при получении стиля общения: {str(e)}")
            return "friendly"

    def get_lesson_duration(self):
        """
        Получает длительность урока в минутах.

        Returns:
            int: Длительность урока в минутах
        """
        try:
            return self.state_manager.state["user"].get("lesson_duration_minutes", 30)
        except Exception as e:
            self.logger.error(f"Ошибка при получении длительности урока: {str(e)}")
            return 30

    def get_total_study_hours(self):
        """
        Получает общее время обучения в часах.

        Returns:
            int: Общее время обучения в часах
        """
        try:
            return self.state_manager.state["user"].get("total_study_hours", 10)
        except Exception as e:
            self.logger.error(f"Ошибка при получении общего времени обучения: {str(e)}")
            return 10

    def validate_user_profile(self):
        """
        Проверяет валидность профиля пользователя.

        Returns:
            tuple: (is_valid, missing_fields)
        """
        try:
            profile = self.state_manager.state["user"]
            missing_fields = []

            # Проверяем обязательные поля
            required_fields = {
                "name": str,
                "total_study_hours": int,
                "lesson_duration_minutes": int,
                "communication_style": str,
            }

            for field, field_type in required_fields.items():
                value = profile.get(field)
                if value is None or value == "" or not isinstance(value, field_type):
                    missing_fields.append(field)

            # Проверяем разумные границы значений
            if profile.get("total_study_hours", 0) <= 0:
                missing_fields.append("total_study_hours (должно быть > 0)")

            if profile.get("lesson_duration_minutes", 0) <= 0:
                missing_fields.append("lesson_duration_minutes (должно быть > 0)")

            valid_styles = ["formal", "friendly", "casual", "brief"]
            if profile.get("communication_style") not in valid_styles:
                missing_fields.append(
                    f"communication_style (должно быть одно из: {valid_styles})"
                )

            is_valid = len(missing_fields) == 0

            if is_valid:
                self.logger.debug("Профиль пользователя валиден")
            else:
                self.logger.warning(
                    f"Профиль пользователя невалиден. Отсутствуют/некорректны поля: {missing_fields}"
                )

            return is_valid, missing_fields

        except Exception as e:
            self.logger.error(f"Ошибка при валидации профиля пользователя: {str(e)}")
            return False, ["Ошибка валидации профиля"]
