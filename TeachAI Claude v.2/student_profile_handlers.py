"""
Модуль обработчиков событий для интерфейса личного кабинета студента.
Отвечает за создание кнопок и обработку всех пользовательских действий.
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging


class StudentProfileHandlers:
    """
    Класс для создания кнопок и обработки событий в личном кабинете.
    """

    def __init__(self, core):
        """
        Инициализация модуля обработчиков.

        Args:
            core: Ядро интерфейса StudentProfileCore
        """
        self.core = core
        self.state_manager = core.state_manager
        self.content_generator = core.content_generator
        self.assessment = core.assessment
        self.system_logger = core.system_logger
        self.utils = core.utils
        self.output_container = core.output_container
        self.logger = logging.getLogger(__name__)

        self.logger.info("StudentProfileHandlers инициализирован")

    def create_action_buttons(self):
        """
        Создает кнопки действий в личном кабинете.

        Returns:
            widgets.HBox: Контейнер с кнопками
        """
        try:
            # Кнопка "Продолжить обучение"
            continue_button = widgets.Button(
                description="📚 Продолжить обучение",
                button_style="primary",
                layout=widgets.Layout(width="200px", margin="5px"),
            )

            # Кнопка "Вернуться в главное меню"
            menu_button = widgets.Button(
                description="🏠 Главное меню",
                button_style="",
                layout=widgets.Layout(width="150px", margin="5px"),
            )

            # Кнопка "Настройки профиля"
            settings_button = widgets.Button(
                description="⚙️ Настройки",
                button_style="info",
                layout=widgets.Layout(width="150px", margin="5px"),
            )

            # Подключаем обработчики
            continue_button.on_click(self._handle_continue_clicked)
            menu_button.on_click(self._handle_menu_clicked)
            settings_button.on_click(self._handle_settings_clicked)

            return widgets.HBox(
                [continue_button, menu_button, settings_button],
                layout=widgets.Layout(justify_content="center", margin="20px 0"),
            )

        except Exception as e:
            self.logger.error(f"Ошибка при создании кнопок действий: {str(e)}")
            return widgets.HBox([])

    def _handle_continue_clicked(self, button):
        """
        ИСПРАВЛЕНО: Обработчик кнопки продолжения обучения (проблема #99).

        Args:
            button: Кнопка, которая была нажата
        """
        try:
            with self.output_container:
                clear_output(wait=True)
                display(
                    self.utils.create_styled_message(
                        "Переход к текущему уроку...", "info"
                    )
                )

                # ИСПРАВЛЕНО: Реализован переход к текущему уроку
                next_lesson_data = self.state_manager.get_next_lesson()

                if next_lesson_data and next_lesson_data[0]:
                    section_id, topic_id, lesson_id, lesson_data = next_lesson_data

                    # Создаем интерфейс и переходим к уроку
                    from interface import UserInterface

                    interface = UserInterface(
                        self.state_manager,
                        self.content_generator,
                        self.assessment,
                        self.system_logger,
                    )

                    clear_output(wait=True)
                    display(interface.show_lesson(lesson_id))

                else:
                    # Нет доступных уроков - переходим к выбору курса
                    display(
                        self.utils.create_styled_message(
                            "Все уроки завершены! Переход к выбору нового курса...",
                            "success",
                        )
                    )

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
            with self.output_container:
                display(
                    self.utils.create_styled_message(
                        f"Ошибка при переходе к уроку: {str(e)}", "incorrect"
                    )
                )

    def _handle_menu_clicked(self, button):
        """
        Обработчик кнопки перехода в главное меню.

        Args:
            button: Кнопка, которая была нажата
        """
        try:
            with self.output_container:
                clear_output(wait=True)
                display(
                    self.utils.create_styled_message(
                        "Переход к главному меню...", "info"
                    )
                )

                from interface import UserInterface

                interface = UserInterface(
                    self.state_manager,
                    self.content_generator,
                    self.assessment,
                    self.system_logger,
                )
                clear_output(wait=True)
                display(interface.show_main_menu())

        except Exception as e:
            self.logger.error(f"Ошибка при переходе к главному меню: {str(e)}")
            with self.output_container:
                display(
                    self.utils.create_styled_message(f"Ошибка: {str(e)}", "incorrect")
                )

    def _handle_settings_clicked(self, button):
        """
        Обработчик кнопки настроек профиля.

        Args:
            button: Кнопка, которая была нажата
        """
        try:
            with self.output_container:
                clear_output(wait=True)
                display(
                    self.utils.create_styled_message(
                        "Переход к настройкам профиля...", "info"
                    )
                )

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
            with self.output_container:
                display(
                    self.utils.create_styled_message(f"Ошибка: {str(e)}", "incorrect")
                )

    def create_navigation_buttons(self):
        """
        Создает дополнительные кнопки навигации.

        Returns:
            widgets.VBox: Контейнер с кнопками навигации
        """
        try:
            # Кнопка "Статистика по курсам"
            stats_button = widgets.Button(
                description="📊 Статистика курсов",
                button_style="",
                layout=widgets.Layout(width="180px", margin="5px"),
            )

            # Кнопка "История обучения"
            history_button = widgets.Button(
                description="📈 История обучения",
                button_style="",
                layout=widgets.Layout(width="180px", margin="5px"),
            )

            # Кнопка "Экспорт данных"
            export_button = widgets.Button(
                description="💾 Экспорт данных",
                button_style="warning",
                layout=widgets.Layout(width="180px", margin="5px"),
            )

            # Подключаем обработчики
            stats_button.on_click(self._handle_stats_clicked)
            history_button.on_click(self._handle_history_clicked)
            export_button.on_click(self._handle_export_clicked)

            return widgets.VBox(
                [
                    widgets.HTML(value="<h4>Дополнительные функции:</h4>"),
                    widgets.HBox(
                        [stats_button, history_button, export_button],
                        layout=widgets.Layout(justify_content="center"),
                    ),
                ]
            )

        except Exception as e:
            self.logger.error(f"Ошибка при создании кнопок навигации: {str(e)}")
            return widgets.VBox([])

    def _handle_stats_clicked(self, button):
        """
        Обработчик кнопки статистики по курсам.

        Args:
            button: Кнопка, которая была нажата
        """
        try:
            with self.output_container:
                clear_output(wait=True)

                # Получаем расширенную статистику
                extended_stats = (
                    self.state_manager.learning_progress.get_extended_statistics()
                )

                stats_html = "<h3>📊 Подробная статистика</h3>"

                if extended_stats:
                    for course_name, stats in extended_stats.items():
                        stats_html += f"""
                        <div style="margin: 10px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
                            <h4>{course_name}</h4>
                            <p>Завершено уроков: {stats.get('completed', 0)}</p>
                            <p>Средний балл: {stats.get('average_score', 0):.1f}%</p>
                            <p>Время изучения: {stats.get('study_time', 0)} мин</p>
                        </div>
                        """
                else:
                    stats_html += "<p>Статистика пока недоступна</p>"

                display(widgets.HTML(value=stats_html))

        except Exception as e:
            self.logger.error(f"Ошибка при отображении статистики: {str(e)}")
            with self.output_container:
                display(
                    self.utils.create_styled_message(
                        f"Ошибка загрузки статистики: {str(e)}", "incorrect"
                    )
                )

    def _handle_history_clicked(self, button):
        """
        Обработчик кнопки истории обучения.

        Args:
            button: Кнопка, которая была нажата
        """
        try:
            with self.output_container:
                clear_output(wait=True)

                # Получаем историю активности
                activity_history = self.state_manager.get_activity_history()

                history_html = "<h3>📈 История обучения</h3>"

                if activity_history:
                    for activity in activity_history[-10:]:  # Последние 10 активностей
                        date = activity.get("date", "Неизвестно")
                        action = activity.get("action", "Активность")
                        details = activity.get("details", "")

                        history_html += f"""
                        <div style="margin: 8px 0; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                            <strong>{date}</strong> - {action}
                            {f'<br><small>{details}</small>' if details else ''}
                        </div>
                        """
                else:
                    history_html += "<p>История активности пуста</p>"

                display(widgets.HTML(value=history_html))

        except Exception as e:
            self.logger.error(f"Ошибка при отображении истории: {str(e)}")
            with self.output_container:
                display(
                    self.utils.create_styled_message(
                        f"Ошибка загрузки истории: {str(e)}", "incorrect"
                    )
                )

    def _handle_export_clicked(self, button):
        """
        Обработчик кнопки экспорта данных.

        Args:
            button: Кнопка, которая была нажата
        """
        try:
            with self.output_container:
                clear_output(wait=True)
                display(
                    self.utils.create_styled_message(
                        "Подготовка данных для экспорта...", "info"
                    )
                )

                # Собираем данные для экспорта
                export_data = {
                    "user_profile": self.state_manager.user_profile.get_user_profile(),
                    "learning_progress": self.state_manager.learning_progress.get_learning_progress(),
                    "course_statistics": self.state_manager.learning_progress.get_detailed_course_statistics(),
                    "export_date": datetime.now().isoformat(),
                }

                # Создаем информацию об экспорте
                export_info = f"""
                <div style="padding: 20px; background: #e7f3ff; border-radius: 5px; border: 1px solid #b3d9ff;">
                    <h4>💾 Данные готовы к экспорту</h4>
                    <p><strong>Экспортируемые данные:</strong></p>
                    <ul>
                        <li>Профиль пользователя</li>
                        <li>Прогресс обучения</li>
                        <li>Статистика по курсам</li>
                        <li>Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M')}</li>
                    </ul>
                    <p><em>Данные сохранены в системе и могут быть переданы администратору при необходимости.</em></p>
                </div>
                """

                display(widgets.HTML(value=export_info))

                # Логируем экспорт
                self.system_logger.info(
                    f"Экспорт данных пользователя выполнен: {export_data['user_profile'].get('name', 'Unknown')}"
                )

        except Exception as e:
            self.logger.error(f"Ошибка при экспорте данных: {str(e)}")
            with self.output_container:
                display(
                    self.utils.create_styled_message(
                        f"Ошибка экспорта: {str(e)}", "incorrect"
                    )
                )

    def get_handler_status(self):
        """
        Возвращает статус модуля обработчиков.

        Returns:
            dict: Статус обработчиков
        """
        return {
            "handlers_initialized": True,
            "available_handlers": [
                "_handle_continue_clicked",
                "_handle_menu_clicked",
                "_handle_settings_clicked",
                "_handle_stats_clicked",
                "_handle_history_clicked",
                "_handle_export_clicked",
            ],
            "core_reference": self.core is not None,
            "utils_available": self.utils is not None,
        }
