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
        header = self.utils.create_header("Настройка профиля TeachAI")
        description = widgets.HTML(value="<p>Пожалуйста, заполните следующие поля:</p>")

        # Создаем форму с полями ввода
        name_widget = widgets.Text(
            description="Имя:",
            placeholder="Введите ваше имя",
            style=_SETUP_FIELD_STYLE,
            layout=_SETUP_FIELD_LAYOUT,
        )

        total_hours_widget = widgets.IntSlider(
            value=10,
            min=1,
            max=100,
            step=1,
            description="Общее время (часов):",
            continuous_update=False,
            style=_SETUP_FIELD_STYLE,
            layout=_SETUP_FIELD_LAYOUT,
        )

        lesson_duration_widget = widgets.IntSlider(
            value=30,
            min=5,
            max=120,
            step=5,
            description="Длительность урока (минут):",
            continuous_update=False,
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

                # Сохраняем данные пользователя
                success = self.state_manager.update_user_profile(
                    name=name,
                    total_study_hours=total_hours_widget.value,
                    lesson_duration_minutes=lesson_duration_widget.value,
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
                            "total_study_hours": total_hours_widget.value,
                            "lesson_duration_minutes": lesson_duration_widget.value,
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
                description,
                widgets.VBox(
                    [
                        name_widget,
                        total_hours_widget,
                        lesson_duration_widget,
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
        Отображает интерфейс выбора курса.

        Returns:
            widgets.VBox: Виджет с интерфейсом выбора курса
        """
        try:
            # Загружаем список доступных курсов
            courses = self.state_manager.get_all_courses()

            if not courses:
                return self._create_courses_error_interface()

            # Создаем заголовок
            header = self.utils.create_header("Выбор курса")
            description = widgets.HTML(
                value="<p>Выберите курс, который вы хотите изучить:</p>"
            )

            # Создаем выпадающий список с курсами
            course_dropdown = widgets.Dropdown(
                options=[(course["title"], course["id"]) for course in courses],
                description="Выберите курс:",
                style={"description_width": "initial"},
                layout=widgets.Layout(width="500px"),
            )

            # Поле для отображения описания курса
            course_description = widgets.HTML(value="")

            # Функция для обновления описания при выборе курса
            def on_course_change(change):
                course_id = change["new"]
                course = next((c for c in courses if c["id"] == course_id), None)
                if course:
                    description_html = f"""
                    <div style="padding: 15px; background-color: #f8f9fa; border-radius: 8px; margin: 15px 0; border: 1px solid #dee2e6;">
                        <h3 style="margin-top: 0; color: #495057;">Описание курса</h3>
                        <p><strong>Описание:</strong> {course['description']}</p>
                        <p><strong>Требования:</strong> {course.get('prerequisites', 'Не указаны')}</p>
                        <p><strong>Сложность:</strong> {course.get('difficulty', 'Не указана')}</p>
                    </div>
                    """
                    course_description.value = description_html

            # Привязываем функцию к выпадающему списку
            course_dropdown.observe(on_course_change, names="value")

            # Показываем описание первого курса
            if courses:
                first_course = courses[0]
                course_description.value = f"""
                <div style="padding: 15px; background-color: #f8f9fa; border-radius: 8px; margin: 15px 0; border: 1px solid #dee2e6;">
                    <h3 style="margin-top: 0; color: #495057;">Описание курса</h3>
                    <p><strong>Описание:</strong> {first_course['description']}</p>
                    <p><strong>Требования:</strong> {first_course.get('prerequisites', 'Не указаны')}</p>
                    <p><strong>Сложность:</strong> {first_course.get('difficulty', 'Не указана')}</p>
                </div>
                """

            # Получаем и отображаем профиль пользователя
            user_profile = self.state_manager.get_user_profile()
            settings_widget = self._create_settings_display(user_profile)

            # Кнопка начала курса
            start_button = widgets.Button(
                description="Начать курс",
                button_style="success",
                tooltip="Нажмите, чтобы начать выбранный курс",
                icon="play",
                layout=widgets.Layout(width="200px", height="40px"),
            )

            # Контейнер для вывода сообщений
            output = widgets.Output()

            # Функция обработки нажатия кнопки
            def on_start_button_clicked(b):
                with output:
                    clear_output(wait=True)

                    course_id = course_dropdown.value
                    course = next((c for c in courses if c["id"] == course_id), None)

                    if course:
                        try:
                            # Показываем сообщение о генерации плана
                            display(
                                self.utils.create_styled_message(
                                    f"Создание персонализированного учебного плана для курса '{course['title']}'...",
                                    "info",
                                )
                            )

                            # Генерируем учебный план
                            course_plan = self.content_generator.generate_course_plan(
                                course_data=course,
                                total_study_hours=user_profile["total_study_hours"],
                                lesson_duration_minutes=user_profile[
                                    "lesson_duration_minutes"
                                ],
                            )

                            # Сохраняем план курса
                            success = self.state_manager.save_course_plan(course_plan)

                            # Обновляем прогресс обучения
                            self.state_manager.update_learning_progress(
                                course=course_id
                            )

                            # Логируем действие
                            self.system_logger.log_activity(
                                action_type="course_started",
                                details={
                                    "course_id": course_id,
                                    "course_title": course["title"],
                                    "total_study_hours": user_profile[
                                        "total_study_hours"
                                    ],
                                    "lesson_duration_minutes": user_profile[
                                        "lesson_duration_minutes"
                                    ],
                                },
                            )

                            if success:
                                display(
                                    self.utils.create_styled_message(
                                        f"Персонализированный учебный план успешно создан! Начинаем курс '{course['title']}'.",
                                        "correct",
                                    )
                                )
                            else:
                                display(
                                    self.utils.create_styled_message(
                                        "Предупреждение: учебный план создан, но возникли проблемы при сохранении.",
                                        "warning",
                                    )
                                )

                            # Получаем первый урок из плана
                            (
                                section_id,
                                topic_id,
                                lesson_id,
                                lesson_data,
                            ) = self.state_manager.get_next_lesson()

                            # Немного задержки для UX
                            time.sleep(1)

                            clear_output(wait=True)
                            if section_id and topic_id and lesson_id:
                                display(
                                    self.utils.create_styled_message(
                                        "Переход к первому уроку...", "info"
                                    )
                                )

                                from lesson_interface import LessonInterface

                                lesson_ui = LessonInterface(
                                    self.state_manager,
                                    self.content_generator,
                                    self.system_logger,
                                    self.assessment,
                                )

                                clear_output(wait=True)
                                lesson_widget = lesson_ui.show_lesson(
                                    section_id, topic_id, lesson_id
                                )
                                display(lesson_widget)
                            elif (
                                section_id is None
                                and topic_id is None
                                and lesson_id is None
                            ):
                                display(
                                    self.utils.create_styled_message(
                                        "Курс завершен! Показываем экран завершения...",
                                        "info",
                                    )
                                )

                                from completion_interface import CompletionInterface

                                completion_interface = CompletionInterface(
                                    self.state_manager,
                                    self.system_logger,
                                    self.content_generator,
                                    self.assessment,
                                )

                                clear_output(wait=True)
                                completion_widget = (
                                    completion_interface.show_course_completion()
                                )
                                display(completion_widget)
                            else:
                                display(
                                    self.utils.create_styled_message(
                                        "Ошибка: не удалось найти первый урок в плане курса.",
                                        "incorrect",
                                    )
                                )

                        except Exception as e:
                            self.logger.error(
                                f"Ошибка при генерации учебного плана: {str(e)}"
                            )
                            display(
                                self.utils.create_styled_message(
                                    f"Ошибка при генерации учебного плана: {str(e)}",
                                    "incorrect",
                                )
                            )
                    else:
                        display(
                            self.utils.create_styled_message(
                                "Ошибка при выборе курса. Пожалуйста, попробуйте еще раз.",
                                "incorrect",
                            )
                        )

            # Привязываем функцию к кнопке
            start_button.on_click(on_start_button_clicked)

            # Собираем все в один контейнер
            form = widgets.VBox(
                [
                    header,
                    description,
                    course_dropdown,
                    course_description,
                    settings_widget,
                    start_button,
                    output,
                ],
                layout=widgets.Layout(gap="15px"),
            )

            return form

        except Exception as e:
            self.logger.error(f"Ошибка при отображении списка курсов: {str(e)}")
            return self._create_courses_error_interface(
                f"Произошла ошибка при загрузке списка курсов: {str(e)}"
            )

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
            <p><strong>Общее время обучения:</strong> {user_profile['total_study_hours']} часов</p>
            <p><strong>Длительность занятия:</strong> {user_profile['lesson_duration_minutes']} минут</p>
            <p><strong>Стиль общения:</strong> {user_profile['communication_style'].capitalize()}</p>
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
