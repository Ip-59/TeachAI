"""
Интерфейс для отображения экрана завершения курса.
Отвечает за показ результатов обучения, сертификата и рекомендаций.
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
from datetime import datetime
from interface_utils import InterfaceUtils, InterfaceState


class CompletionInterface:
    """Интерфейс для экрана завершения курса."""

    def __init__(
        self, state_manager, system_logger, content_generator=None, assessment=None
    ):
        """
        Инициализация интерфейса завершения курса.

        Args:
            state_manager: Менеджер состояния
            system_logger: Системный логгер
            content_generator: Генератор контента (опционально)
            assessment: Модуль оценивания (опционально)
        """
        self.state_manager = state_manager
        self.system_logger = system_logger
        self.logger = logging.getLogger(__name__)

        # Создаем content_generator если не передан (для навигации)
        if content_generator is None:
            from content_generator import ContentGenerator
            from config import ConfigManager

            config_manager = ConfigManager()
            config_manager.load_config()
            api_key = config_manager.get_api_key()
            self.content_generator = ContentGenerator(api_key)
        else:
            self.content_generator = content_generator

        # Создаем assessment если не передан (для навигации)
        if assessment is None:
            from assessment import Assessment

            self.assessment = Assessment(self.content_generator, system_logger)
        else:
            self.assessment = assessment

        # Утилиты интерфейса
        self.utils = InterfaceUtils()

    def show_course_completion(self):
        """
        Отображает экран завершения курса.

        Returns:
            widgets.VBox: Виджет с экраном завершения курса
        """
        try:
            # Получаем данные о курсе и прогрессе обучения
            course_plan = self.state_manager.get_course_plan()
            learning_progress = self.state_manager.get_learning_progress()
            progress_data = self.state_manager.calculate_course_progress()

            # Получаем название курса безопасно
            course_title = self._get_course_title(course_plan, learning_progress)
            course_id = self._get_course_id(course_plan, learning_progress)

            if hasattr(self.state_manager, "mark_active_course_completed"):
                self.state_manager.mark_active_course_completed()

            # Создаем интерфейс завершения курса
            completion_header = self.utils.create_header("Поздравляем! Курс завершен!")
            completion_description = widgets.HTML(
                value=f"<p>Вы успешно завершили курс <strong>{course_title}</strong>. Вот ваши результаты:</p>"
            )

            # Статистика курса
            stats_widget = self._create_statistics_widget(
                learning_progress, progress_data, course_plan
            )

            # Сертификат о завершении
            certificate_widget = self._create_certificate_widget(
                learning_progress, course_title
            )

            # Рекомендации по дальнейшему обучению
            recommendations_widget = self._create_recommendations_widget(course_id)

            # Кнопка для возвращения к портфелю курсов
            back_button = widgets.Button(
                description="К моим курсам",
                button_style="primary",
                tooltip="Вернуться к списку курсов",
                icon="list",
                layout=widgets.Layout(width="200px", height="40px"),
            )

            def on_back_button_clicked(b):
                from course_portfolio_ui import show_courses_home

                show_courses_home(self)

            back_button.on_click(on_back_button_clicked)

            # Собираем все в один контейнер
            form = widgets.VBox(
                [
                    completion_header,
                    completion_description,
                    stats_widget,
                    certificate_widget,
                    recommendations_widget,
                    back_button,
                ],
                layout=widgets.Layout(gap="20px"),
            )

            # Логируем завершение курса
            self.system_logger.log_activity(
                action_type="course_completed",
                details={
                    "course": course_id,
                    "course_title": course_title,
                    "average_score": learning_progress["average_score"],
                    "completed_lessons": progress_data["completed"],
                    "total_lessons": progress_data["total"],
                    "total_assessments": learning_progress["total_assessments"],
                },
            )

            return form

        except Exception as e:
            self.logger.error(
                f"Ошибка при отображении экрана завершения курса: {str(e)}"
            )

            # Логируем ошибку
            self.system_logger.log_activity(
                action_type="course_completion_display_error",
                status="error",
                error=str(e),
            )

            return self._create_completion_error_interface(str(e))

    def _create_statistics_widget(self, learning_progress, progress_data, course_plan):
        """
        Создает виджет со статистикой курса.

        Args:
            learning_progress (dict): Прогресс обучения
            progress_data (dict): Данные о прогрессе
            course_plan (dict): План курса

        Returns:
            widgets.HTML: Виджет со статистикой
        """
        # Рассчитываем общее время обучения
        total_duration = course_plan.get("total_duration_minutes", 0)
        hours = total_duration // 60
        minutes = total_duration % 60

        stats_html = f"""
        <div style="padding: 20px; background-color: #f8f9fa; border-radius: 8px; margin: 15px 0; border: 1px solid #dee2e6;">
            <h3 style="margin-top: 0; color: #495057; font-size: 20px;">📊 Статистика курса</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px;">
                <div style="background-color: #ffffff; padding: 15px; border-radius: 6px; border: 1px solid #e9ecef;">
                    <h4 style="margin: 0 0 10px 0; color: #28a745;">🎯 Успеваемость</h4>
                    <p style="margin: 5px 0; font-size: 16px;"><strong>Средний балл:</strong> {learning_progress['average_score']:.1f}%</p>
                    <p style="margin: 5px 0; font-size: 16px;"><strong>Пройдено тестов:</strong> {learning_progress['total_assessments']}</p>
                </div>
                <div style="background-color: #ffffff; padding: 15px; border-radius: 6px; border: 1px solid #e9ecef;">
                    <h4 style="margin: 0 0 10px 0; color: #007bff;">📚 Прогресс</h4>
                    <p style="margin: 5px 0; font-size: 16px;"><strong>Пройдено уроков:</strong> {progress_data['completed']} из {progress_data['total']}</p>
                    <p style="margin: 5px 0; font-size: 16px;"><strong>Общее время:</strong> примерно {hours} ч. {minutes} мин.</p>
                </div>
            </div>
        </div>
        """

        return widgets.HTML(value=stats_html)

    def _create_certificate_widget(self, learning_progress, course_title):
        """
        Создает виджет с сертификатом о завершении.

        Args:
            learning_progress (dict): Прогресс обучения
            course_title (str): Название курса

        Returns:
            widgets.HTML: Виджет с сертификатом
        """
        user_name = (
            learning_progress.get("user_name")
            or self.state_manager.get_user_profile()["name"]
        )
        current_date = datetime.now().strftime("%d.%m.%Y")

        certificate_html = f"""
        <div style="padding: 30px; border: 3px solid #007bff; border-radius: 12px; text-align: center; margin: 20px 0; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #007bff; margin: 0 0 20px 0; font-size: 28px;">🏆 Сертификат о завершении курса</h2>

            <div style="margin: 20px 0;">
                <p style="font-size: 18px; margin: 10px 0;">Этот сертификат подтверждает, что</p>
                <p style="font-size: 26px; font-weight: bold; margin: 15px 0; color: #495057; background-color: #ffffff; padding: 10px; border-radius: 6px; display: inline-block; min-width: 300px;">{user_name}</p>
                <p style="font-size: 18px; margin: 10px 0;">успешно завершил(а) курс</p>
                <p style="font-size: 24px; font-weight: bold; margin: 15px 0; color: #007bff;">{course_title}</p>
                <p style="font-size: 16px; margin: 15px 0;">со средним баллом <span style="font-weight: bold; color: #28a745;">{learning_progress['average_score']:.1f}%</span></p>
            </div>

            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                <p style="font-size: 14px; margin: 5px 0; color: #6c757d;">Дата завершения: {current_date}</p>
                <p style="font-size: 14px; margin: 5px 0; color: #6c757d;">TeachAI - персонализированное обучение с ИИ</p>
            </div>
        </div>
        """

        return widgets.HTML(value=certificate_html)

    def _create_recommendations_widget(self, current_course_id):
        """
        Создает виджет с рекомендациями по дальнейшему обучению.

        Args:
            current_course_id (str): ID текущего курса

        Returns:
            widgets.HTML: Виджет с рекомендациями
        """
        # Получаем все доступные курсы
        courses = self.state_manager.get_all_courses()

        # Исключаем текущий курс
        recommended_courses = [
            course for course in courses if course["id"] != current_course_id
        ]

        recommendations_html = f"""
        <div style="padding: 20px; background-color: #e7f3ff; border-radius: 8px; margin: 15px 0; border: 1px solid #b3d9ff;">
            <h3 style="margin-top: 0; color: #0066cc; font-size: 20px;">🚀 Рекомендации по дальнейшему обучению</h3>
            <p style="font-size: 16px; margin-bottom: 15px;">На основе вашего прогресса и результатов, вам могут быть интересны следующие курсы:</p>
        """

        if recommended_courses:
            recommendations_html += "<div style='margin-top: 15px;'>"
            for course in recommended_courses[:3]:  # Максимум 3 рекомендации
                # Определяем иконку по сложности
                difficulty = course.get("difficulty", "Не указана")
                if difficulty == "Начальный":
                    icon = "🟢"
                elif difficulty == "Средний":
                    icon = "🟡"
                elif difficulty == "Продвинутый":
                    icon = "🔴"
                else:
                    icon = "📚"

                recommendations_html += f"""
                <div style="background-color: #ffffff; padding: 15px; margin: 10px 0; border-radius: 6px; border: 1px solid #cce7ff;">
                    <h4 style="margin: 0 0 8px 0; color: #0066cc;">{icon} {course['title']}</h4>
                    <p style="margin: 5px 0; font-size: 14px; color: #666;"><strong>Сложность:</strong> {difficulty}</p>
                    <p style="margin: 5px 0; font-size: 15px; line-height: 1.4;">{course['description'][:150]}{'...' if len(course['description']) > 150 else ''}</p>
                </div>
                """
            recommendations_html += "</div>"
        else:
            recommendations_html += """
            <div style="background-color: #ffffff; padding: 15px; margin: 10px 0; border-radius: 6px; border: 1px solid #cce7ff;">
                <p style="font-style: italic; color: #666;">В настоящее время нет дополнительных рекомендаций. Пожалуйста, проверьте позже для новых курсов.</p>
            </div>
            """

        recommendations_html += """
            <div style="margin-top: 20px; padding: 15px; background-color: #f0f8ff; border-radius: 6px; border: 1px solid #cce7ff;">
                <p style="margin: 0; font-size: 14px; color: #0066cc;"><strong>💡 Совет:</strong> Для лучшего усвоения материала рекомендуется повторить ключевые концепции изученного курса и применить их на практике перед переходом к новому материалу.</p>
            </div>
        </div>
        """

        return widgets.HTML(value=recommendations_html)

    def _get_course_title(self, course_plan, learning_progress):
        """
        Безопасно получает название курса.

        Returns:
            str: Название курса
        """
        course_title = self.utils.get_safe_title(course_plan, "Курс")
        if not course_title or course_title == "Курс":
            course_title = learning_progress.get("current_course", "Курс Python")
        return course_title

    def _get_course_id(self, course_plan, learning_progress):
        """
        Безопасно получает ID курса.

        Returns:
            str: ID курса
        """
        course_id = course_plan.get("id", "unknown-course")
        if not course_id or course_id == "unknown-course":
            course_id = learning_progress.get("current_course", "python-basics")
        return course_id

    def _create_completion_error_interface(self, error_message):
        """
        Создает интерфейс ошибки для экрана завершения курса.

        Args:
            error_message (str): Сообщение об ошибке

        Returns:
            widgets.VBox: Интерфейс ошибки
        """
        error_header = self.utils.create_header(
            "Ошибка при загрузке экрана завершения курса"
        )
        error_message_widget = self.utils.create_styled_message(
            f"Произошла ошибка: {error_message}", "incorrect"
        )

        back_to_courses_button = widgets.Button(
            description="К моим курсам", button_style="primary", icon="list"
        )

        def go_back_to_courses(b):
            from course_portfolio_ui import show_courses_home

            show_courses_home(self)

        back_to_courses_button.on_click(go_back_to_courses)

        return widgets.VBox(
            [error_header, error_message_widget, back_to_courses_button]
        )
