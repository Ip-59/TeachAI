"""
Интерфейс для настройки профиля пользователя и выбора курса.
Отвечает за первоначальную настройку системы и выбор обучающего курса.
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
import time
from interface_utils import InterfaceUtils, InterfaceState

# Подписи полей формы знакомства: без фиксированной узкой колонки и обрезки
_SETUP_FIELD_STYLE = {"description_width": "initial"}
_SETUP_FIELD_LAYOUT = widgets.Layout(width="520px")
_SETUP_FORM_CSS = widgets.HTML(
    value="""
<style>
.teachai-setup-form .widget-label {
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
    max-width: none !important;
    flex-shrink: 0 !important;
    line-height: 1.35;
}
</style>
"""
)


class SetupInterface:
    """Интерфейс для первоначальной настройки и выбора курса."""

    def __init__(
        self, state_manager, content_generator, system_logger, assessment=None
    ):
        """
        Инициализация интерфейса настройки.

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

    def show_initial_setup(self):
        """
        Отображает форму первоначальной настройки.

        Returns:
            widgets.VBox: Виджет с формой настройки
        """
        # Создаем заголовок
        from project_identity import PROJECT_NAME, scope_banner_html

        header = self.utils.create_header(f"Настройка профиля {PROJECT_NAME}")
        scope_banner = widgets.HTML(value=scope_banner_html())
        description = widgets.HTML(
            value=(
                "<p>Имя и стиль общения — общие. Тему курса, общее время "
                "и длительность занятия вы зададите на следующем шаге, "
                "отдельно для каждого курса.</p>"
            )
        )

        # Создаем форму с полями ввода
        name_widget = widgets.Text(
            description="Имя:",
            placeholder="Введите ваше имя",
            style=_SETUP_FIELD_STYLE,
            layout=_SETUP_FIELD_LAYOUT,
        )

        communication_style_widget = widgets.Dropdown(
            options=[
                ("Формальный", "formal"),
                ("Дружелюбный", "friendly"),
                ("Непринужденный", "casual"),
                ("Краткий", "brief"),
            ],
            value="friendly",
            description="Стиль общения:",
            style=_SETUP_FIELD_STYLE,
            layout=_SETUP_FIELD_LAYOUT,
        )

        # Создаем кнопку подтверждения
        submit_button = widgets.Button(
            description="Сохранить настройки",
            button_style="primary",
            tooltip="Нажмите для сохранения настроек",
            icon="check",
            layout=widgets.Layout(width="200px", height="40px"),
        )

        # Создаем контейнер для вывода сообщений
        output = widgets.Output()

        # Функция обработки нажатия кнопки
        def on_submit_button_clicked(b):
            with output:
                clear_output()

                # Проверяем валидность введенных данных
                name = name_widget.value.strip()
                if not name:
                    display(
                        self.utils.create_styled_message(
                            "Пожалуйста, введите ваше имя", "warning"
                        )
                    )
                    return

                # Время курса здесь не спрашиваем: оно задаётся на экране курса.
                current = self.state_manager.get_user_profile()
                success = self.state_manager.update_user_profile(
                    name=name,
                    total_study_hours=current.get("total_study_hours") or 0,
                    lesson_duration_minutes=current.get("lesson_duration_minutes") or 0,
                    communication_style=communication_style_widget.value,
                )

                if success:
                    # Сбрасываем старые данные курса и прогресса при новом профиле
                    self.state_manager.reset_learning_and_course_data()

                    # Устанавливаем флаг, что это не первый запуск
                    self.state_manager.set_not_first_run()

                    # Логируем действие
                    self.system_logger.log_activity(
                        action_type="user_profile_created",
                        details={
                            "name": name,
                            "communication_style": communication_style_widget.value,
                        },
                    )

                    display(
                        self.utils.create_styled_message(
                            f"Профиль успешно создан. Добро пожаловать, {name}!",
                            "correct",
                        )
                    )

                    # Переходим к выбору курса
                    time.sleep(1)
                    clear_output(wait=True)
                    
                    # ИСПРАВЛЕНО: Создаем виджет выбора курса и показываем его
                    course_selection_widget = self.show_course_selection()
                    display(course_selection_widget)
                    
                else:
                    display(
                        self.utils.create_styled_message(
                            "Произошла ошибка при сохранении профиля. Пожалуйста, попробуйте еще раз.",
                            "incorrect",
                        )
                    )

        # Привязываем функцию к кнопке
        submit_button.on_click(on_submit_button_clicked)

        # Собираем все в один контейнер
        form = widgets.VBox(
            [
                _SETUP_FORM_CSS,
                header,
                scope_banner,
                description,
                widgets.VBox(
                    [
                        name_widget,
                        communication_style_widget,
                    ],
                    layout=widgets.Layout(gap="10px"),
                ),
                submit_button,
                output,
            ],
            layout=widgets.Layout(gap="15px"),
        )
        form.add_class("teachai-setup-form")

        return form

    def show_course_selection(self):
        """
        Отображает интерфейс выбора курса (каталог или своё название).

        Returns:
            widgets.VBox: Виджет с интерфейсом выбора курса
        """
        from course_selection_ui import build_course_selection

        return build_course_selection(self)

    def _create_settings_display(self, user_profile):
        """
        Создает отображение настроек пользователя.

        Args:
            user_profile (dict): Профиль пользователя

        Returns:
            widgets.HTML: Виджет с настройками
        """
        settings_html = f"""
        <div style="padding: 15px; background-color: #e9ecef; border-radius: 8px; margin: 15px 0; border: 1px solid #adb5bd;">
            <h3 style="margin-top: 0; color: #495057;">Настройки обучения</h3>
            <p><strong>Имя:</strong> {user_profile['name']}</p>
            <p><strong>Стиль общения:</strong> {user_profile['communication_style'].capitalize()}</p>
            <p>Общее время и длительность занятия задаются отдельно для каждого курса.</p>
        </div>
        """
        return widgets.HTML(value=settings_html)

    def _create_courses_error_interface(
        self,
        message="Не удалось загрузить список доступных курсов. Пожалуйста, проверьте файл courses.json.",
    ):
        """
        Создает интерфейс ошибки загрузки курсов.

        Args:
            message (str): Сообщение об ошибке

        Returns:
            widgets.VBox: Интерфейс ошибки
        """
        header = self.utils.create_header("Ошибка при загрузке курсов")
        error_message = self.utils.create_styled_message(message, "incorrect")

        return widgets.VBox([header, error_message])
