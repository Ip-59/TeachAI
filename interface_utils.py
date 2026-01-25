"""
Базовые утилиты и стили для пользовательского интерфейса.
Содержит общие стили, константы и вспомогательные классы для всех интерфейсов.
ИСПРАВЛЕНО: значительно уменьшены интервалы в тестах для компактности
"""

import logging
from enum import Enum


class InterfaceState(Enum):
    """Перечисление для состояний интерфейса."""

    INITIAL_SETUP = "initial_setup"
    COURSE_SELECTION = "course_selection"
    LESSON_VIEW = "lesson_view"
    ASSESSMENT = "assessment"
    QUESTION_ANSWER = "question_answer"
    RESULTS_VIEW = "results_view"
    COURSE_COMPLETION = "course_completion"


class InterfaceStyles:
    """Класс с базовыми стилями для интерфейса."""

    # Базовые стили для сообщений и элементов
    STYLES = {
        "correct": "background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin: 5px 0;",
        "incorrect": "background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 5px 0;",
        "info": "background-color: #d1ecf1; color: #0c5460; padding: 10px; border-radius: 5px; margin: 5px 0;",
        "warning": "background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; margin: 5px 0;",
        "header": "font-size: 24px; font-weight: bold; color: #495057; margin: 20px 0 10px 0;",
        "subheader": "font-size: 18px; font-weight: bold; color: #6c757d; margin: 15px 0 10px 0;",
        "button": "font-weight: bold;",
    }

    # ИСПРАВЛЕНО: Значительно уменьшены интервалы для компактного отображения!
    ASSESSMENT_CSS = """
    <style>
    .test-container {
        font-family: Arial, sans-serif;
        line-height: 1.4;
        max-width: 800px;
        margin: 0 auto;
        padding: 0;
    }

    .test-container h1 {
        font-size: 24px;
        font-weight: bold;
        color: #495057;
        margin: 10px 0 8px 0;
        padding: 0;
    }

    .test-container p {
        margin: 8px 0;
        padding: 0;
        line-height: 1.3;
    }

    .question-box {
        background-color: #ffffff;
        border: 2px solid #e9ecef;
        border-radius: 8px;
        padding: 15px;
        margin: 12px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .question-title {
        font-size: 18px;
        font-weight: bold;
        color: #212529;
        margin-bottom: 10px;
        line-height: 1.3;
        display: block;
        padding-bottom: 8px;
        border-bottom: 1px solid #dee2e6;
    }

    .radio-options {
        margin-top: 10px;
    }

    .radio-option {
        display: block;
        margin: 6px 0;
        padding: 8px 10px;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 16px;
        line-height: 1.3;
        min-height: 35px;
        position: relative;
    }

    .radio-option:hover {
        background-color: #e9ecef;
        border-color: #adb5bd;
    }

    .radio-option.selected {
        background-color: #e7f3ff;
        border-color: #007bff;
        font-weight: 500;
    }

    .radio-option input[type="radio"] {
        margin-right: 8px;
        transform: scale(1.1);
        vertical-align: top;
        margin-top: 2px;
    }

    .radio-option label {
        cursor: pointer;
        display: block;
        margin: 0;
        padding: 0;
        font-size: 16px;
        line-height: 1.3;
        word-wrap: break-word;
        width: calc(100% - 22px);
        margin-left: 22px;
    }

    .results-container {
        margin-top: 20px;
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }

    .score-display {
        text-align: center;
        padding: 15px;
        margin: 15px 0;
        border-radius: 8px;
        font-size: 24px;
        font-weight: bold;
    }

    .score-high {
        background-color: #d4edda;
        color: #155724;
        border: 2px solid #c3e6cb;
    }

    .score-medium {
        background-color: #fff3cd;
        color: #856404;
        border: 2px solid #ffeaa7;
    }

    .score-low {
        background-color: #f8d7da;
        color: #721c24;
        border: 2px solid #f5c6cb;
    }

    .result-question {
        margin: 15px 0;
        padding: 12px;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        background-color: #ffffff;
    }

    .result-question-title {
        font-weight: bold;
        margin-bottom: 8px;
        font-size: 16px;
        color: #212529;
        line-height: 1.3;
    }

    .result-option {
        margin: 4px 0;
        padding: 6px 10px;
        border-radius: 4px;
        font-size: 15px;
        line-height: 1.3;
    }

    .result-option.correct {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }

    .result-option.incorrect {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }

    .result-option.neutral {
        background-color: #f8f9fa;
        color: #495057;
        border: 1px solid #dee2e6;
    }
    </style>
    """


class InterfaceUtils:
    """Утилиты для работы с интерфейсом."""

    def __init__(self):
        """Инициализация утилит интерфейса."""
        self.logger = logging.getLogger(__name__)
        self.styles = InterfaceStyles.STYLES

    def create_navigation_info(
        self, course_title, section_title, topic_title, lesson_title, additional=""
    ):
        """
        Создает навигационную информацию для отображения пути.

        Args:
            course_title (str): Название курса
            section_title (str): Название раздела
            topic_title (str): Название темы
            lesson_title (str): Название урока
            additional (str): Дополнительная информация (например, "Тест")

        Returns:
            str: HTML навигационной информации
        """
        nav_path = f"{course_title} > {section_title} > {topic_title} > {lesson_title}"
        if additional:
            nav_path += f" > {additional}"

        return f"<p style='margin: 0px; font-size: 14px;'><small>{nav_path}</small></p>"

    def create_progress_info(self, progress_data):
        """
        Создает информацию о прогрессе обучения.

        Args:
            progress_data (dict): Данные о прогрессе

        Returns:
            tuple: (progress_bar_widget, progress_text_widget)
        """
        import ipywidgets as widgets

        progress_bar = widgets.IntProgress(
            value=int(progress_data["percent"]),
            min=0,
            max=100,
            description="Прогресс:",
            bar_style="info",
            orientation="horizontal",
        )

        progress_text = widgets.HTML(
            value=f"<p>Пройдено {progress_data['completed']} из {progress_data['total']} уроков</p>"
        )

        return progress_bar, progress_text

    def create_styled_message(self, message, style_type="info"):
        """
        Создает стилизованное сообщение.

        Args:
            message (str): Текст сообщения
            style_type (str): Тип стиля (correct, incorrect, info, warning)

        Returns:
            widgets.HTML: Виджет с сообщением
        """
        import ipywidgets as widgets

        style = self.styles.get(style_type, self.styles["info"])
        return widgets.HTML(value=f"<p style='{style}'>{message}</p>")

    def create_header(self, title, level="header"):
        """
        Создает заголовок с соответствующим стилем.

        Args:
            title (str): Текст заголовка
            level (str): Уровень заголовка (header, subheader)

        Returns:
            widgets.HTML: Виджет заголовка
        """
        import ipywidgets as widgets

        style = self.styles.get(level, self.styles["header"])
        tag = "h1" if level == "header" else "h2"
        return widgets.HTML(value=f"<{tag} style='{style}'>{title}</{tag}>")

    def get_safe_title(self, data, fallback="Элемент"):
        """
        Безопасно получает название из данных.

        Args:
            data (dict): Данные с возможными ключами title, name, id
            fallback (str): Значение по умолчанию

        Returns:
            str: Название элемента
        """
        if not data or not isinstance(data, dict):
            return fallback

        return data.get("title") or data.get("name") or data.get("id") or fallback

    def safe_str(self, value, fallback=""):
        """
        Безопасно преобразует значение в строку.

        Args:
            value: Значение для преобразования
            fallback (str): Значение по умолчанию

        Returns:
            str: Строковое представление
        """
        if value is None:
            return fallback
        return str(value)

    def log_interface_action(self, action_type, details=None):
        """
        Логирует действие интерфейса.

        Args:
            action_type (str): Тип действия
            details (dict): Дополнительные детали
        """
        self.logger.info(f"Interface action: {action_type}")
        if details:
            self.logger.debug(f"Details: {details}")
