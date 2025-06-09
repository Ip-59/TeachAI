"""
Утилиты для работы с уроками.
Вынесены из lesson_interface.py для улучшения модульности.
"""

import logging


class LessonUtils:
    """Утилиты для работы с уроками."""

    def __init__(self):
        """Инициализация утилит."""
        self.logger = logging.getLogger(__name__)

    def get_element_titles(self, course_plan, section_id, topic_id, lesson_id):
        """
        Получает названия элементов курса.

        Args:
            course_plan (dict): План курса
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            tuple: (course_title, section_title, topic_title, lesson_title)
        """
        try:
            # Получаем название курса
            course_title = course_plan.get("title", "Курс")

            # Получаем название раздела (sections - это список)
            sections = course_plan.get("sections", [])
            section = None
            for s in sections:
                if s.get("id") == section_id:
                    section = s
                    break

            section_title = (
                section.get("title", f"Раздел {section_id}")
                if section
                else f"Раздел {section_id}"
            )

            # Получаем название темы (topics - это список)
            topics = section.get("topics", []) if section else []
            topic = None
            for t in topics:
                if t.get("id") == topic_id:
                    topic = t
                    break

            topic_title = (
                topic.get("title", f"Тема {topic_id}") if topic else f"Тема {topic_id}"
            )

            # Получаем название урока (lessons - это список)
            lessons = topic.get("lessons", []) if topic else []
            lesson = None
            for l in lessons:
                if l.get("id") == lesson_id:
                    lesson = l
                    break

            lesson_title = (
                lesson.get("title", f"Урок {lesson_id}")
                if lesson
                else f"Урок {lesson_id}"
            )

            return course_title, section_title, topic_title, lesson_title

        except Exception as e:
            self.logger.error(f"Ошибка при получении названий элементов: {str(e)}")
            return (
                "Курс",
                f"Раздел {section_id}",
                f"Тема {topic_id}",
                f"Урок {lesson_id}",
            )

    def get_course_id(self, course_plan):
        """
        Получает ID курса из плана курса.

        Args:
            course_plan (dict): План курса

        Returns:
            str: ID курса или "default"
        """
        try:
            return course_plan.get("id", "default")
        except Exception as e:
            self.logger.error(f"Ошибка при получении ID курса: {str(e)}")
            return "default"

    def clear_lesson_cache(self, lesson_interface):
        """
        Очищает кэш урока в интерфейсе.

        Args:
            lesson_interface: Экземпляр LessonInterface
        """
        try:
            lesson_interface.cached_lesson_content = None
            lesson_interface.cached_lesson_title = None
            lesson_interface.current_lesson_cache_key = None
            self.logger.info("Кэш урока очищен")
        except Exception as e:
            self.logger.error(f"Ошибка при очистке кэша урока: {str(e)}")

    def create_lesson_error_interface(self, title, message, lesson_interface):
        """
        Создает интерфейс ошибки для урока.

        Args:
            title (str): Заголовок ошибки
            message (str): Сообщение об ошибке
            lesson_interface: Экземпляр LessonInterface

        Returns:
            widgets.VBox: Виджет с сообщением об ошибке
        """
        try:
            import ipywidgets as widgets

            # Логируем ошибку
            lesson_interface.system_logger.log_activity(
                action_type="lesson_error",
                status="error",
                error=message,
                details={"title": title},
            )

            # Создаем интерфейс ошибки
            error_html = widgets.HTML(
                value=f"""
                <div style="padding: 20px; border: 2px solid #ff6b6b; border-radius: 10px; background-color: #fff5f5;">
                    <h2 style="color: #d63031; margin-top: 0;">❌ {title}</h2>
                    <p style="color: #2d3436; font-size: 16px;">{message}</p>
                    <p style="color: #636e72; font-size: 14px;">
                        Пожалуйста, попробуйте еще раз или обратитесь к администратору системы.
                    </p>
                </div>
                """
            )

            # Кнопка возврата к курсам
            go_back_button = widgets.Button(
                description="← Вернуться к выбору курса",
                button_style="warning",
                layout=widgets.Layout(width="auto", margin="10px 0"),
            )

            def go_back_to_courses(b):
                # Очищаем кэш при возврате к выбору курса
                self.clear_lesson_cache(lesson_interface)

                # Возвращаемся к выбору курса
                from interface import InterfaceState

                lesson_interface.interface.current_state = (
                    InterfaceState.COURSE_SELECTION
                )
                lesson_interface.interface.show_course_selection()

            go_back_button.on_click(go_back_to_courses)

            # Создаем контейнер
            error_container = widgets.VBox(
                [error_html, go_back_button],
                layout=widgets.Layout(
                    width="100%",
                    padding="20px",
                    border="1px solid #ddd",
                    border_radius="10px",
                ),
            )

            return error_container

        except Exception as e:
            self.logger.error(f"Ошибка при создании интерфейса ошибки: {str(e)}")
            # Возвращаем простой виджет с ошибкой
            import ipywidgets as widgets

            return widgets.HTML(value=f"<p>Ошибка: {message}</p>")
