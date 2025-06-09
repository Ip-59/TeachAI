def is_first_run(self):
    """
    Проверяет, является ли это первым запуском системы.

    Returns:
        bool: True если первый запуск, иначе False
    """
    try:
        # Проверяем наличие данных пользователя
        user_data = self.state.get("user", {})

        # Если нет имени пользователя, это первый запуск
        if not user_data.get("name"):
            return True

        # Проверяем специальный флаг first_run
        settings = self.state.get("settings", {})
        if settings.get("first_run", True):
            return True

        return False

    except Exception as e:
        self.logger.error(f"Ошибка при проверке первого запуска: {str(e)}")
        # В случае ошибки считаем первым запуском для безопасности
        return True


def set_not_first_run(self):
    """
    Устанавливает флаг, что это не первый запуск системы.

    Returns:
        bool: True если установка прошла успешно, иначе False
    """
    try:
        if "settings" not in self.state:
            self.state["settings"] = {}

        self.state["settings"]["first_run"] = False
        self.state["settings"]["first_run_completed_at"] = datetime.now().isoformat()

        result = self.save_state()
        if result:
            self.logger.info("Флаг первого запуска снят")

        return result

    except Exception as e:
        self.logger.error(f"Ошибка при установке флага первого запуска: {str(e)}")
        return False


def reset_to_first_run(self):
    """
    СЛУЖЕБНЫЙ: Сбрасывает систему к состоянию первого запуска.
    Используется для тестирования или полного сброса.

    Returns:
        bool: True если сброс прошел успешно, иначе False
    """
    try:
        # Очищаем данные пользователя
        self.state["user"] = {}

        # Устанавливаем флаг первого запуска
        if "settings" not in self.state:
            self.state["settings"] = {}

        self.state["settings"]["first_run"] = True
        self.state["settings"]["reset_at"] = datetime.now().isoformat()

        # Очищаем прогресс обучения
        self.state["learning"] = {}
        self.state["course_plan"] = {}
        self.state["completed_lessons"] = []

        result = self.save_state()
        if result:
            self.logger.info("Система сброшена к первому запуску")

        return result

    except Exception as e:
        self.logger.error(f"Ошибка при сбросе к первому запуску: {str(e)}")
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
        **kwargs: Данные для обновления (name, total_study_hours, etc.)

    Returns:
        bool: True если обновление прошло успешно, иначе False
    """
    try:
        # Получаем текущий профиль
        current_profile = self.get_user_data()

        # Обновляем переданными данными
        current_profile.update(kwargs)

        # Сохраняем обновленный профиль
        result = self.save_user_profile(current_profile)

        if result:
            self.logger.info(f"Профиль пользователя обновлен: {list(kwargs.keys())}")

        return result

    except Exception as e:
        self.logger.error(f"Ошибка обновления профиля пользователя: {str(e)}")
        return False


def update_learning_progress(self, **kwargs):
    """
    Обновляет прогресс обучения.

    Args:
        **kwargs: Данные для обновления (course, section, topic, lesson, etc.)

    Returns:
        bool: True если обновление прошло успешно, иначе False
    """
    try:
        # Получаем текущий прогресс
        if "learning" not in self.state:
            self.state["learning"] = {}

        current_progress = self.state["learning"]

        # Обновляем переданными данными
        current_progress.update(kwargs)

        # Добавляем timestamp
        current_progress["last_updated"] = datetime.now().isoformat()

        # Сохраняем
        result = self.save_state()

        if result:
            self.logger.debug(f"Прогресс обучения обновлен: {list(kwargs.keys())}")

        return result

    except Exception as e:
        self.logger.error(f"Ошибка обновления прогресса обучения: {str(e)}")
        return False


def get_lesson_data(self, section_id, topic_id, lesson_id):
    """
    Возвращает данные урока из плана курса.

    Args:
        section_id (str): ID раздела
        topic_id (str): ID темы
        lesson_id (str): ID урока

    Returns:
        dict или None: Данные урока
    """
    try:
        course_plan = self.get_course_plan()

        for section in course_plan.get("sections", []):
            if section.get("id") == section_id:
                for topic in section.get("topics", []):
                    if topic.get("id") == topic_id:
                        for lesson in topic.get("lessons", []):
                            if lesson.get("id") == lesson_id:
                                return lesson

        self.logger.warning(f"Урок не найден: {section_id}:{topic_id}:{lesson_id}")
        return None

    except Exception as e:
        self.logger.error(f"Ошибка получения данных урока: {str(e)}")
        return None


def get_next_lesson(self):
    """
    Определяет следующий незавершенный урок.

    Returns:
        tuple или None: (section_id, topic_id, lesson_id, lesson_data) или None
    """
    try:
        course_plan = self.get_course_plan()
        completed_lessons = self.get_completed_lessons()

        # Ищем первый незавершенный урок
        for section in course_plan.get("sections", []):
            for topic in section.get("topics", []):
                for lesson in topic.get("lessons", []):
                    lesson_id = lesson.get("id")
                    if lesson_id and lesson_id not in completed_lessons:
                        return (section.get("id"), topic.get("id"), lesson_id, lesson)

        # Все уроки завершены
        return None

    except Exception as e:
        self.logger.error(f"Ошибка определения следующего урока: {str(e)}")
        return None
