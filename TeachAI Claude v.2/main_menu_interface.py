"""
Интерфейс главного меню для повторных запусков TeachAI.
Показывается при не первом запуске системы и предоставляет пользователю выбор действий.
НОВОЕ: Стартовая страница с опциями вместо прямого перехода к уроку
НОВОЕ: Интеграция с личным кабинетом студента
НОВОЕ: Информация о текущем прогрессе на главной странице
ИСПРАВЛЕНО: Проблема #99 - реализованы фактические переходы к урокам вместо TODO
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
from datetime import datetime
from interface_utils import InterfaceUtils, InterfaceState


class MainMenuInterface:
    """Интерфейс главного меню TeachAI."""

    def __init__(
        self, state_manager, content_generator, system_logger, assessment=None
    ):
        """
        Инициализация интерфейса главного меню.

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

        # Выходной контейнер для управления отображением
        self.output_container = widgets.Output()

        # Импортируем интерфейс личного кабинета
        try:
            from student_profile_interface import StudentProfileInterface

            self.profile_interface = StudentProfileInterface(
                state_manager, content_generator, system_logger, assessment
            )
            self.profile_available = True
        except ImportError:
            self.logger.warning("Модуль student_profile_interface не найден")
            self.profile_interface = None
            self.profile_available = False

    def show_main_menu(self):
        """
        Отображает главное меню с опциями для пользователя.

        Returns:
            widgets.VBox: Интерфейс главного меню
        """
        try:
            # Создаем заголовок
            header = self.utils.create_header("🏠 Главное меню TeachAI")

            # Получаем данные о прогрессе для отображения
            progress_data = self.state_manager.get_learning_progress()

            # Создаем секции интерфейса
            welcome_section = self._create_welcome_section(progress_data)
            quick_access_section = self._create_quick_access_section(progress_data)
            action_buttons = self._create_action_buttons()

            # Собираем все в контейнер
            self.main_container = widgets.VBox(
                [
                    header,
                    welcome_section,
                    quick_access_section,
                    action_buttons,
                    self.output_container,
                ],
                layout=widgets.Layout(gap="20px", padding="20px"),
            )

            return self.main_container

        except Exception as e:
            self.logger.error(f"Ошибка при создании главного меню: {str(e)}")
            return self._create_error_interface(str(e))

    def _create_welcome_section(self, progress_data):
        """
        Создает секцию приветствия с информацией о пользователе.

        Args:
            progress_data (dict): Данные о прогрессе

        Returns:
            widgets.HTML: Секция приветствия
        """
        user_data = self.state_manager.user_profile.get_user_profile()
        current_time = datetime.now().strftime("%H:%M")

        # Определяем приветствие в зависимости от времени
        hour = datetime.now().hour
        if 5 <= hour < 12:
            greeting = "Доброе утро"
        elif 12 <= hour < 17:
            greeting = "Добрый день"
        elif 17 <= hour < 22:
            greeting = "Добрый вечер"
        else:
            greeting = "Доброй ночи"

        current_course = progress_data.get("current_course", "Не выбран")

        welcome_html = f"""
        <div style="
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        ">
            <h2 style="margin: 0 0 15px 0; font-size: 26px;">
                {greeting}, {user_data['name']}! 👋
            </h2>
            <p style="margin: 5px 0; opacity: 0.9; font-size: 16px;">
                📚 Текущий курс: <strong>{current_course}</strong>
            </p>
            <p style="margin: 5px 0; opacity: 0.8; font-size: 14px;">
                🕐 {current_time} | Готовы продолжить обучение?
            </p>
        </div>
        """

        return widgets.HTML(value=welcome_html)

    def _create_quick_access_section(self, progress_data):
        """
        Создает секцию быстрого доступа с актуальной информацией.

        Args:
            progress_data (dict): Данные о прогрессе

        Returns:
            widgets.HTML: Секция быстрого доступа
        """
        # Получаем информацию о текущем уроке
        current_lesson_info = self._get_current_lesson_info()

        if current_lesson_info:
            section_id, topic_id, lesson_id = current_lesson_info
            quick_access_html = f"""
            <div style="
                background: white;
                padding: 20px;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            ">
                <h3 style="margin: 0 0 15px 0; color: #374151;">⚡ Быстрый доступ</h3>
                <div style="
                    background: #f3f4f6;
                    padding: 15px;
                    border-radius: 8px;
                    border-left: 4px solid #3b82f6;
                ">
                    <p style="margin: 0; color: #374151;">
                        <strong>📖 Незавершенный урок:</strong><br>
                        {section_id} → {topic_id} → {lesson_id}
                    </p>
                </div>
            </div>
            """
        else:
            quick_access_html = """
            <div style="
                background: white;
                padding: 20px;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            ">
                <h3 style="margin: 0 0 15px 0; color: #374151;">⚡ Быстрый доступ</h3>
                <div style="
                    background: #f9fafb;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                    color: #6b7280;
                ">
                    <p style="margin: 0;">Все уроки пройдены! 🎉<br>Выберите новый курс для изучения.</p>
                </div>
            </div>
            """

        return widgets.HTML(value=quick_access_html)

    def _create_action_buttons(self):
        """
        Создает кнопки действий в главном меню.

        Returns:
            widgets.VBox: Контейнер с кнопками
        """
        # Кнопка "Продолжить обучение"
        continue_button = widgets.Button(
            description="📚 Продолжить обучение",
            button_style="primary",
            layout=widgets.Layout(width="240px", height="50px", margin="5px"),
        )

        # Кнопка "Личный кабинет"
        profile_button = widgets.Button(
            description="👤 Личный кабинет",
            button_style="info",
            layout=widgets.Layout(width="240px", height="50px", margin="5px"),
        )

        # Кнопка "Каталог курсов"
        courses_button = widgets.Button(
            description="📖 Каталог курсов",
            button_style="success",
            layout=widgets.Layout(width="240px", height="50px", margin="5px"),
        )

        # Кнопка "Настройки"
        settings_button = widgets.Button(
            description="⚙️ Настройки",
            button_style="warning",
            layout=widgets.Layout(width="240px", height="50px", margin="5px"),
        )

        def on_continue_clicked(b):
            """ИСПРАВЛЕНО: Обработчик кнопки продолжения обучения (проблема #99)."""
            with self.output_container:
                clear_output(wait=True)
                try:
                    current_lesson_info = self._get_current_lesson_info()
                    if current_lesson_info:
                        # Есть незавершенный урок - переходим к нему
                        section_id, topic_id, lesson_id = current_lesson_info
                        display(
                            self.utils.create_styled_message(
                                f"Переход к уроку: {section_id} → {topic_id} → {lesson_id}",
                                "info",
                            )
                        )

                        # ИСПРАВЛЕНО: Реализован фактический переход к уроку
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

                    else:
                        # Нет незавершенного урока - показываем выбор курса
                        display(
                            self.utils.create_styled_message(
                                "Переход к выбору курса...", "info"
                            )
                        )

                        # ИСПРАВЛЕНО: Реализован переход к выбору курса
                        from interface import UserInterface

                        interface = UserInterface(
                            self.state_manager,
                            self.content_generator,
                            self.assessment,
                            self.system_logger,
                        )

                        clear_output(wait=True)
                        display(interface.show_course_selection())

                except Exception as e:
                    self.logger.error(f"Ошибка при продолжении обучения: {str(e)}")
                    display(
                        self.utils.create_styled_message(
                            f"Ошибка при переходе: {str(e)}", "incorrect"
                        )
                    )

        def on_profile_clicked(b):
            """Обработчик кнопки личного кабинета."""
            with self.output_container:
                clear_output(wait=True)
                if self.profile_available:
                    try:
                        profile_interface = (
                            self.profile_interface.show_student_profile()
                        )
                        display(profile_interface)
                    except Exception as e:
                        self.logger.error(
                            f"Ошибка при открытии личного кабинета: {str(e)}"
                        )
                        display(
                            self.utils.create_styled_message(
                                f"Ошибка при открытии личного кабинета: {str(e)}",
                                "incorrect",
                            )
                        )
                else:
                    display(
                        self.utils.create_styled_message(
                            "Личный кабинет временно недоступен", "warning"
                        )
                    )

        def on_courses_clicked(b):
            """ИСПРАВЛЕНО: Обработчик кнопки каталога курсов (проблема #99)."""
            with self.output_container:
                clear_output(wait=True)
                display(
                    self.utils.create_styled_message(
                        "Переход к каталогу курсов...", "info"
                    )
                )

                # ИСПРАВЛЕНО: Реализован переход к каталогу курсов
                try:
                    from interface import UserInterface

                    interface = UserInterface(
                        self.state_manager,
                        self.content_generator,
                        self.assessment,
                        self.system_logger,
                    )

                    clear_output(wait=True)
                    display(interface.show_course_selection())

                except Exception as e:
                    self.logger.error(
                        f"Ошибка при переходе к каталогу курсов: {str(e)}"
                    )
                    display(
                        self.utils.create_styled_message(
                            f"Ошибка при переходе к каталогу: {str(e)}", "incorrect"
                        )
                    )

        def on_settings_clicked(b):
            """ИСПРАВЛЕНО: Обработчик кнопки настроек (проблема #99)."""
            with self.output_container:
                clear_output(wait=True)
                display(
                    self.utils.create_styled_message(
                        "Переход к настройкам профиля...", "info"
                    )
                )

                # ИСПРАВЛЕНО: Реализован переход к настройкам
                try:
                    from interface import UserInterface

                    interface = UserInterface(
                        self.state_manager,
                        self.content_generator,
                        self.assessment,
                        self.system_logger,
                    )

                    clear_output(wait=True)
                    display(interface.show_initial_setup())

                except Exception as e:
                    self.logger.error(f"Ошибка при переходе к настройкам: {str(e)}")
                    display(
                        self.utils.create_styled_message(
                            f"Ошибка при переходе к настройкам: {str(e)}", "incorrect"
                        )
                    )

        # Привязываем обработчики
        continue_button.on_click(on_continue_clicked)
        profile_button.on_click(on_profile_clicked)
        courses_button.on_click(on_courses_clicked)
        settings_button.on_click(on_settings_clicked)

        # Группируем кнопки
        buttons_row1 = widgets.HBox(
            [continue_button, profile_button],
            layout=widgets.Layout(justify_content="center", gap="20px"),
        )
        buttons_row2 = widgets.HBox(
            [courses_button, settings_button],
            layout=widgets.Layout(justify_content="center", gap="20px"),
        )

        return widgets.VBox(
            [buttons_row1, buttons_row2], layout=widgets.Layout(gap="15px")
        )

    def _get_current_lesson_info(self):
        """
        Получает информацию о текущем незавершенном уроке.

        Returns:
            tuple: (section_id, topic_id, lesson_id) или None если нет незавершенного урока
        """
        try:
            # Получаем информацию о следующем уроке (он же текущий незавершенный)
            next_lesson_data = self.state_manager.get_next_lesson()

            if next_lesson_data and next_lesson_data[0]:
                section_id, topic_id, lesson_id, _ = next_lesson_data
                return section_id, topic_id, lesson_id
            else:
                return None

        except Exception as e:
            self.logger.error(
                f"Ошибка при получении информации о текущем уроке: {str(e)}"
            )
            return None

    def _create_error_interface(self, error_message):
        """
        Создает интерфейс ошибки.

        Args:
            error_message (str): Сообщение об ошибке

        Returns:
            widgets.VBox: Интерфейс ошибки
        """
        error_header = self.utils.create_header("❌ Ошибка главного меню")
        error_widget = self.utils.create_styled_message(
            f"Произошла ошибка при создании главного меню: {error_message}", "incorrect"
        )

        back_button = widgets.Button(
            description="🔄 Попробовать снова",
            button_style="primary",
            layout=widgets.Layout(width="200px", margin="20px auto"),
        )

        def try_again(b):
            """Повторная попытка создания главного меню."""
            clear_output(wait=True)
            try:
                display(self.show_main_menu())
            except Exception as e:
                self.logger.error(f"Повторная ошибка главного меню: {str(e)}")
                display(
                    self.utils.create_styled_message(
                        "Критическая ошибка главного меню. Обратитесь к администратору.",
                        "incorrect",
                    )
                )

        back_button.on_click(try_again)

        return widgets.VBox(
            [error_header, error_widget, back_button],
            layout=widgets.Layout(align_items="center", padding="20px"),
        )
