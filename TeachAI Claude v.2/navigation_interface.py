"""
Интерфейс навигации между уроками TeachAI.
Отвечает за переходы между уроками, разделами и темами курса.
Обеспечивает удобную навигацию и отображение текущего местоположения в курсе.
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
from interface_utils import InterfaceUtils, InterfaceState


class NavigationInterface:
    """Интерфейс навигации между уроками."""

    def __init__(
        self, state_manager, content_generator, system_logger, assessment=None
    ):
        """
        Инициализация интерфейса навигации.

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

    def show_lesson_navigation(
        self, current_section_id, current_topic_id, current_lesson_id
    ):
        """
        Отображает навигационный интерфейс для текущего урока.

        Args:
            current_section_id (str): ID текущего раздела
            current_topic_id (str): ID текущей темы
            current_lesson_id (str): ID текущего урока

        Returns:
            widgets.VBox: Виджет с навигацией
        """
        try:
            # Получаем информацию о навигации
            nav_info = self._get_navigation_info(
                current_section_id, current_topic_id, current_lesson_id
            )

            if not nav_info:
                return self._create_error_navigation()

            # Создаем элементы навигации
            breadcrumb = self._create_breadcrumb(nav_info)
            navigation_buttons = self._create_navigation_buttons(nav_info)
            progress_info = self._create_progress_info(nav_info)

            # Контейнер навигации
            navigation_container = widgets.VBox(
                [breadcrumb, progress_info, navigation_buttons]
            )

            return navigation_container

        except Exception as e:
            self.logger.error(f"Ошибка создания навигации: {str(e)}")
            return self._create_error_navigation()

    def _get_navigation_info(self, section_id, topic_id, lesson_id):
        """
        Получает информацию для навигации.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            dict: Информация о навигации или None
        """
        try:
            # Получаем план курса
            course_plan = self.state_manager.get_course_plan()
            if not course_plan:
                return None

            # Получаем прогресс обучения
            learning_progress = self.state_manager.get_learning_progress()

            # Находим текущий урок и соседние
            current_lesson = self._find_lesson_in_plan(
                course_plan, section_id, topic_id, lesson_id
            )
            prev_lesson = self._find_previous_lesson(
                course_plan, section_id, topic_id, lesson_id
            )
            next_lesson = self._find_next_lesson(
                course_plan, section_id, topic_id, lesson_id
            )

            # Получаем названия элементов
            course_title = course_plan.get("title", "Курс")
            section_title, topic_title = self._get_element_titles(
                course_plan, section_id, topic_id
            )
            lesson_title = (
                current_lesson.get("title", f"Урок {lesson_id}")
                if current_lesson
                else f"Урок {lesson_id}"
            )

            return {
                "course_title": course_title,
                "section_title": section_title,
                "topic_title": topic_title,
                "lesson_title": lesson_title,
                "current_lesson": {
                    "section_id": section_id,
                    "topic_id": topic_id,
                    "lesson_id": lesson_id,
                },
                "prev_lesson": prev_lesson,
                "next_lesson": next_lesson,
                "progress": self._calculate_lesson_progress(
                    course_plan, section_id, topic_id, lesson_id
                ),
            }

        except Exception as e:
            self.logger.error(f"Ошибка получения информации навигации: {str(e)}")
            return None

    def _create_breadcrumb(self, nav_info):
        """Создает хлебные крошки навигации."""
        breadcrumb_html = f"""
        <div style="
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            padding: 12px 20px;
            border-radius: 8px;
            margin: 10px 0;
            border: 1px solid #dee2e6;
            font-size: 14px;
            color: #495057;
        ">
            📚 <strong>{nav_info['course_title']}</strong> →
            📖 {nav_info['section_title']} →
            📝 {nav_info['topic_title']} →
            🎯 <strong style="color: #007bff;">{nav_info['lesson_title']}</strong>
        </div>
        """
        return widgets.HTML(value=breadcrumb_html)

    def _create_progress_info(self, nav_info):
        """Создает информацию о прогрессе."""
        progress = nav_info["progress"]
        progress_html = f"""
        <div style="text-align: center; margin: 15px 0; color: #6c757d;">
            📊 Урок {progress['current']} из {progress['total']}
            ({progress['percentage']:.1f}% курса завершено)
        </div>
        """
        return widgets.HTML(value=progress_html)

    def _create_navigation_buttons(self, nav_info):
        """Создает кнопки навигации."""
        # Кнопка "Предыдущий урок"
        prev_button = widgets.Button(
            description="← Предыдущий",
            disabled=not nav_info["prev_lesson"],
            button_style="info",
            layout=widgets.Layout(width="120px"),
        )

        # Кнопка "Главное меню"
        menu_button = widgets.Button(
            description="🏠 Меню",
            button_style="warning",
            layout=widgets.Layout(width="120px"),
        )

        # Кнопка "Следующий урок"
        next_button = widgets.Button(
            description="Следующий →",
            disabled=not nav_info["next_lesson"],
            button_style="success",
            layout=widgets.Layout(width="120px"),
        )

        # Обработчики событий
        def on_prev_clicked(b):
            if nav_info["prev_lesson"]:
                self._navigate_to_lesson(nav_info["prev_lesson"])

        def on_menu_clicked(b):
            self._navigate_to_main_menu()

        def on_next_clicked(b):
            if nav_info["next_lesson"]:
                self._navigate_to_lesson(nav_info["next_lesson"])

        prev_button.on_click(on_prev_clicked)
        menu_button.on_click(on_menu_clicked)
        next_button.on_click(on_next_clicked)

        # Контейнер с кнопками
        return widgets.HBox(
            [prev_button, menu_button, next_button],
            layout=widgets.Layout(
                justify_content="center",
                margin="20px 0",
                padding="15px",
                border_top="1px solid #dee2e6",
            ),
        )

    def _navigate_to_lesson(self, lesson_info):
        """Переходит к указанному уроку."""
        try:
            clear_output(wait=True)

            # Импортируем LessonInterface для перехода
            from lesson_interface import LessonInterface

            lesson_interface = LessonInterface(
                self.state_manager,
                self.content_generator,
                self.system_logger,
                self.assessment,
            )

            display(
                lesson_interface.show_lesson(
                    lesson_info["section_id"],
                    lesson_info["topic_id"],
                    lesson_info["lesson_id"],
                )
            )

        except Exception as e:
            self.logger.error(f"Ошибка перехода к уроку: {str(e)}")
            display(
                self.utils.create_styled_message(
                    f"Ошибка перехода к уроку: {str(e)}", "incorrect"
                )
            )

    def _navigate_to_main_menu(self):
        """Переходит к главному меню."""
        try:
            clear_output(wait=True)

            from interface import UserInterface

            interface = UserInterface(
                self.state_manager,
                self.content_generator,
                self.assessment,
                self.system_logger,
            )

            display(interface.show_main_menu())

        except Exception as e:
            self.logger.error(f"Ошибка перехода к главному меню: {str(e)}")
            display(
                self.utils.create_styled_message(
                    f"Ошибка перехода к главному меню: {str(e)}", "incorrect"
                )
            )

    def _find_lesson_in_plan(self, course_plan, section_id, topic_id, lesson_id):
        """Находит урок в плане курса."""
        try:
            sections = course_plan.get("sections", [])
            for section in sections:
                if section.get("id") == section_id:
                    for topic in section.get("topics", []):
                        if topic.get("id") == topic_id:
                            for lesson in topic.get("lessons", []):
                                if lesson.get("id") == lesson_id:
                                    return lesson
            return None
        except Exception:
            return None

    def _find_previous_lesson(self, course_plan, section_id, topic_id, lesson_id):
        """Находит предыдущий урок."""
        return self.state_manager.get_previous_lesson(lesson_id)

    def _find_next_lesson(self, course_plan, section_id, topic_id, lesson_id):
        """Находит следующий урок."""
        return self.state_manager.get_next_lesson(lesson_id)

    def _get_element_titles(self, course_plan, section_id, topic_id):
        """Получает названия раздела и темы."""
        section_title = f"Раздел {section_id}"
        topic_title = f"Тема {topic_id}"

        try:
            sections = course_plan.get("sections", [])
            for section in sections:
                if section.get("id") == section_id:
                    section_title = section.get("title", section_title)
                    for topic in section.get("topics", []):
                        if topic.get("id") == topic_id:
                            topic_title = topic.get("title", topic_title)
                            break
                    break
        except Exception:
            pass

        return section_title, topic_title

    def _calculate_lesson_progress(self, course_plan, section_id, topic_id, lesson_id):
        """Рассчитывает прогресс по урокам."""
        try:
            total_lessons = 0
            current_lesson_num = 0

            sections = course_plan.get("sections", [])
            for section in sections:
                for topic in section.get("topics", []):
                    for lesson in topic.get("lessons", []):
                        total_lessons += 1
                        if (
                            section.get("id") == section_id
                            and topic.get("id") == topic_id
                            and lesson.get("id") == lesson_id
                        ):
                            current_lesson_num = total_lessons

            percentage = (
                (current_lesson_num / total_lessons * 100) if total_lessons > 0 else 0
            )

            return {
                "current": current_lesson_num,
                "total": total_lessons,
                "percentage": percentage,
            }

        except Exception:
            return {"current": 1, "total": 1, "percentage": 100}

    def _create_error_navigation(self):
        """Создает навигацию при ошибке."""
        error_html = """
        <div style="text-align: center; padding: 20px; color: #dc3545;">
            ⚠️ Ошибка загрузки навигации
        </div>
        """

        menu_button = widgets.Button(
            description="🏠 Главное меню", button_style="primary"
        )

        def on_menu_clicked(b):
            self._navigate_to_main_menu()

        menu_button.on_click(on_menu_clicked)

        return widgets.VBox(
            [
                widgets.HTML(value=error_html),
                widgets.HBox(
                    [menu_button], layout=widgets.Layout(justify_content="center")
                ),
            ]
        )
