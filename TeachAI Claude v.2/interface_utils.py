"""
Утилиты для интерфейсов TeachAI.
Содержит стили, вспомогательные функции и компоненты для создания пользовательского интерфейса.
ИСПРАВЛЕНО: Добавлен недостающий метод create_styled_message (проблема #96)
"""

import logging
from enum import Enum


class InterfaceState(Enum):
    """Перечисление состояний интерфейса."""

    INITIAL_SETUP = "initial_setup"
    COURSE_SELECTION = "course_selection"
    LESSON_VIEW = "lesson_view"
    ASSESSMENT = "assessment"
    QUESTION_ANSWER = "question_answer"
    RESULTS_VIEW = "results_view"
    COURSE_COMPLETION = "course_completion"
    COMPLETION = "completion"  # Для совместимости
    # НОВОЕ ЭТАП 22: Добавлены состояния для новых интерфейсов
    MAIN_MENU = "main_menu"
    STUDENT_PROFILE = "student_profile"


class InterfaceStyles:
    """Определения CSS стилей для интерфейса."""

    # Базовые стили для виджетов
    STYLES = {
        "header": "color: #2c3e50; font-size: 24px; font-weight: bold; margin: 15px 0; text-align: center;",
        "subheader": "color: #34495e; font-size: 18px; font-weight: bold; margin: 10px 0;",
        "info": "color: #17a2b8; padding: 10px; background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 5px; margin: 10px 0;",
        "correct": "color: #155724; padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; margin: 10px 0;",
        "incorrect": "color: #721c24; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; margin: 10px 0;",
        "warning": "color: #856404; padding: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; margin: 10px 0;",
        "navigation": "text-align: center; margin: 20px 0; padding: 15px; border-top: 1px solid #dee2e6;",
        "progress": "color: #495057; font-size: 14px; text-align: center; margin: 10px 0;",
        "lesson_content": "line-height: 1.6; font-size: 16px; color: #495057; padding: 20px; background-color: white; border-radius: 8px; border: 1px solid #dee2e6; margin: 15px 0;",
        "lesson_title": "color: #2c3e50; font-size: 22px; font-weight: bold; margin: 20px 0 15px 0; text-align: center;",
        "button_container": "text-align: center; margin: 20px 0;",
        "compact": "margin: 5px; padding: 8px;",
        "time_estimate": "color: #6c757d; font-style: italic; text-align: center; margin: 10px 0;",
        "score_display": "font-size: 18px; font-weight: bold; text-align: center; padding: 15px; background-color: #f8f9fa; border-radius: 8px; margin: 20px 0; border: 2px solid #dee2e6;",
        "error": "color: #dc3545; padding: 15px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; margin: 10px 0; font-weight: bold;",
    }

    # CSS для глобального применения
    GLOBAL_CSS = """
    <style>
    .teachai-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        max-width: 800px;
        margin: 0 auto;
        padding: 10px;
    }

    .course-info {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin: 10px 0;
    }

    .lesson-navigation {
        background-color: #e9ecef;
        padding: 12px;
        border-radius: 6px;
        margin: 15px 0;
        text-align: center;
        font-size: 14px;
        color: #495057;
    }

    .progress-info {
        background-color: #f8f9fa;
        border-radius: 8px;
        margin: 20px 0;
        border: 2px solid #dee2e6;
    }

    .score-percentage {
        font-size: 36px;
        font-weight: bold;
        margin: 10px 0;
    }

    .score-good {
        color: #28a745;
    }

    .score-average {
        color: #ffc107;
    }

    .score-poor {
        color: #dc3545;
    }

    .navigation-buttons {
        text-align: center;
        margin: 30px 0;
        padding: 20px;
        border-top: 1px solid #dee2e6;
    }

    .nav-button {
        background-color: #6c757d;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: bold;
        cursor: pointer;
        margin: 0 10px;
        transition: background-color 0.2s ease;
    }

    .nav-button:hover {
        background-color: #545b62;
    }

    .nav-button.primary {
        background-color: #007bff;
    }

    .nav-button.primary:hover {
        background-color: #0056b3;
    }

    .nav-button.success {
        background-color: #28a745;
    }

    .nav-button.success:hover {
        background-color: #1e7e34;
    }
    </style>
    """


class InterfaceUtils:
    """Утилиты для работы с интерфейсами."""

    def __init__(self):
        """Инициализация утилит интерфейса."""
        self.logger = logging.getLogger(__name__)

    def create_styled_message(self, message, style_type="info"):
        """
        ИСПРАВЛЕНО: Создает стилизованное сообщение (проблема #96).

        Args:
            message (str): Текст сообщения
            style_type (str): Тип стиля (correct, incorrect, info, warning, error)

        Returns:
            widgets.HTML: Виджет с стилизованным сообщением
        """
        import ipywidgets as widgets

        # Получаем стиль или используем info по умолчанию
        style = InterfaceStyles.STYLES.get(style_type, InterfaceStyles.STYLES["info"])

        # Создаем HTML виджет с сообщением
        return widgets.HTML(value=f'<div style="{style}">{message}</div>')

    def create_styled_html(self, content, style_class="info"):
        """
        Создает HTML элемент с применением стиля.

        Args:
            content (str): Содержимое HTML
            style_class (str): Класс стиля из InterfaceStyles.STYLES

        Returns:
            widgets.HTML: HTML виджет с примененным стилем
        """
        import ipywidgets as widgets

        style = InterfaceStyles.STYLES.get(style_class, InterfaceStyles.STYLES["info"])
        return widgets.HTML(value=f'<div style="{style}">{content}</div>')

    def create_header(self, text, level=1):
        """
        Создает заголовок с правильным стилем.

        Args:
            text (str): Текст заголовка
            level (int): Уровень заголовка (1 или 2)

        Returns:
            widgets.HTML: HTML виджет с заголовком
        """
        import ipywidgets as widgets

        if level == 1:
            style = InterfaceStyles.STYLES["header"]
            tag = "h1"
        else:
            style = InterfaceStyles.STYLES["subheader"]
            tag = "h2"

        return widgets.HTML(value=f'<{tag} style="{style}">{text}</{tag}>')

    def create_button(
        self, description, button_style="primary", icon=None, width="auto"
    ):
        """
        Создает кнопку с базовыми стилями.

        Args:
            description (str): Текст кнопки
            button_style (str): Стиль кнопки (primary, secondary, success, danger, warning, info)
            icon (str): Иконка FontAwesome (опционально)
            width (str): Ширина кнопки

        Returns:
            widgets.Button: Стилизованная кнопка
        """
        import ipywidgets as widgets

        button = widgets.Button(
            description=description,
            button_style=button_style,
            layout=widgets.Layout(width=width),
        )

        if icon:
            button.icon = icon

        return button

    def create_progress_bar(self, current, total, description=""):
        """
        Создает индикатор прогресса.

        Args:
            current (int): Текущее значение
            total (int): Максимальное значение
            description (str): Описание прогресса

        Returns:
            widgets.VBox: Контейнер с индикатором прогресса
        """
        import ipywidgets as widgets

        if total == 0:
            percentage = 0
        else:
            percentage = (current / total) * 100

        progress_bar = widgets.IntProgress(
            value=current,
            min=0,
            max=total,
            bar_style="success"
            if percentage >= 70
            else "warning"
            if percentage >= 40
            else "danger",
            layout=widgets.Layout(width="100%"),
        )

        progress_text = widgets.HTML(
            value=f'<div style="{InterfaceStyles.STYLES["progress"]}">{description} {current}/{total} ({percentage:.1f}%)</div>'
        )

        return widgets.VBox([progress_text, progress_bar])

    def create_navigation_info(
        self, course_title, section_title, topic_title, lesson_title, additional=""
    ):
        """
        Создает навигационную информацию.

        Args:
            course_title (str): Название курса
            section_title (str): Название раздела
            topic_title (str): Название темы
            lesson_title (str): Название урока
            additional (str): Дополнительная информация

        Returns:
            widgets.HTML: Навигационная информация
        """
        import ipywidgets as widgets

        nav_text = (
            f"📚 {course_title} → 📖 {section_title} → 📝 {topic_title} → 📄 {lesson_title}"
        )
        if additional:
            nav_text += f" | {additional}"

        return widgets.HTML(
            value=f'<div style="{InterfaceStyles.STYLES["navigation"]}">{nav_text}</div>'
        )

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

    def format_time_estimate(self, minutes):
        """
        Форматирует время изучения.

        Args:
            minutes (int): Время в минутах

        Returns:
            str: Отформатированное время
        """
        if minutes < 60:
            return f"⏱️ Примерное время изучения: {minutes} мин."
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                return f"⏱️ Примерное время изучения: {hours} ч."
            else:
                return (
                    f"⏱️ Примерное время изучения: {hours} ч. {remaining_minutes} мин."
                )

    def create_score_display(self, score, max_score=100):
        """
        Создает отображение оценки.

        Args:
            score (float): Оценка
            max_score (float): Максимальная оценка

        Returns:
            widgets.HTML: Виджет с отображением оценки
        """
        import ipywidgets as widgets

        percentage = (score / max_score) * 100 if max_score > 0 else 0

        if percentage >= 80:
            score_class = "score-good"
            message = "Отлично!"
        elif percentage >= 60:
            score_class = "score-average"
            message = "Хорошо!"
        else:
            score_class = "score-poor"
            message = "Нужно подтянуть"

        score_html = f"""
        <div style="{InterfaceStyles.STYLES['score_display']}">
            <div class="score-percentage {score_class}">{percentage:.1f}%</div>
            <div>{message}</div>
            <div style="font-size: 14px; color: #6c757d;">({score:.1f} из {max_score})</div>
        </div>
        """

        return widgets.HTML(value=score_html)

    def create_compact_button(self, description, button_style="primary", width="150px"):
        """
        Создает компактную кнопку.

        Args:
            description (str): Текст кнопки
            button_style (str): Стиль кнопки
            width (str): Ширина кнопки

        Returns:
            widgets.Button: Компактная кнопка
        """
        import ipywidgets as widgets

        return widgets.Button(
            description=description,
            button_style=button_style,
            layout=widgets.Layout(width=width, margin="5px"),
        )
