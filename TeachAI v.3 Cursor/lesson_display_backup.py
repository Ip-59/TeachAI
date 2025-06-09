"""
Отображение уроков.
Вынесено из lesson_interface.py для улучшения модульности.
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
from lesson_utils import LessonUtils


class LessonDisplay:
    """Отображение уроков."""

    def __init__(self, lesson_interface):
        """
        Инициализация отображения уроков.

        Args:
            lesson_interface: Экземпляр LessonInterface
        """
        self.lesson_interface = lesson_interface
        self.logger = logging.getLogger(__name__)
        self.utils = LessonUtils()

    def show_lesson(self, section_id, topic_id, lesson_id):
        """
        Отображает урок пользователю с кэшированием содержания.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            widgets.VBox: Виджет с уроком
        """
        try:
            # Создаем ключ кэша для текущего урока
            cache_key = f"{section_id}:{topic_id}:{lesson_id}"

            # Получаем данные о курсе и уроке из учебного плана
            course_plan = self.lesson_interface.state_manager.get_course_plan()
            lesson_data = self.lesson_interface.state_manager.get_lesson_data(
                section_id, topic_id, lesson_id
            )

            if not lesson_data:
                raise ValueError(f"Урок с ID {lesson_id} не найден в учебном плане")

            # Получаем названия элементов
            (
                course_title,
                section_title,
                topic_title,
                lesson_title,
            ) = self.utils.get_element_titles(
                course_plan, section_id, topic_id, lesson_id
            )

            # Получаем профиль пользователя для генерации урока
            user_profile = self.lesson_interface.state_manager.get_user_profile()

            # Проверяем кэш содержания урока
            if (
                self.lesson_interface.current_lesson_cache_key == cache_key
                and self.lesson_interface.cached_lesson_content is not None
                and self.lesson_interface.cached_lesson_title is not None
            ):
                self.logger.info(
                    f"Используется кэшированное содержание урока '{lesson_title}'"
                )
                lesson_content_data = {
                    "title": self.lesson_interface.cached_lesson_title,
                    "content": self.lesson_interface.cached_lesson_content,
                }
            else:
                # Показываем сообщение о загрузке только при первой генерации
                loading_display = widgets.HTML(
                    value=f"<h1>{lesson_title}</h1><p><strong>Загрузка содержания урока...</strong></p>"
                )
                display(loading_display)

                # Генерируем содержание урока
                try:
                    self.logger.info(
                        f"Генерация нового содержания урока '{lesson_title}'"
                    )

                    lesson_content_data = (
                        self.lesson_interface.content_generator.generate_lesson(
                            course=course_title,
                            section=section_title,
                            topic=topic_title,
                            lesson=lesson_title,
                            user_name=user_profile["name"],
                            communication_style=user_profile["communication_style"],
                        )
                    )

                    # Кэшируем сгенерированное содержание
                    self.lesson_interface.cached_lesson_content = lesson_content_data[
                        "content"
                    ]
                    self.lesson_interface.cached_lesson_title = lesson_content_data[
                        "title"
                    ]
                    self.lesson_interface.current_lesson_cache_key = cache_key

                    self.logger.info("Урок успешно сгенерирован и закэширован")

                except Exception as e:
                    self.logger.error(f"Ошибка при генерации урока: {str(e)}")
                    clear_output(wait=True)
                    return self.utils.create_lesson_error_interface(
                        "Ошибка при генерации урока",
                        f"Не удалось сгенерировать содержание урока '{lesson_title}': {str(e)}",
                        self.lesson_interface,
                    )

                # Очищаем сообщение о загрузке
                clear_output(wait=True)

            # Сохраняем данные для интерактивных функций
            self.lesson_interface.current_lesson_data = lesson_data
            self.lesson_interface.current_lesson_content = lesson_content_data[
                "content"
            ]
            self.lesson_interface.current_lesson_id = (
                f"{section_id}:{topic_id}:{lesson_id}"  # Полный ID урока
            )
            self.lesson_interface.current_course_info = {
                "course_title": course_title,
                "section_title": section_title,
                "topic_title": topic_title,
                "lesson_title": lesson_title,
                "section_id": section_id,
                "topic_id": topic_id,
                "lesson_id": lesson_id,
                "user_profile": user_profile,
                "course_plan": course_plan,
            }

            # Получаем ID курса безопасно
            course_id = self.utils.get_course_id(course_plan)

            # Обновляем прогресс обучения
            self.lesson_interface.state_manager.update_learning_progress(
                course=course_id, section=section_id, topic=topic_id, lesson=lesson_id
            )

            # Логируем урок
            self.lesson_interface.system_logger.log_lesson(
                course=course_title,
                section=section_title,
                topic=topic_title,
                lesson_title=lesson_content_data["title"],
                lesson_content=lesson_content_data["content"],
            )

            # Создаем интерфейс урока
            return self.create_lesson_interface(
                lesson_content_data,
                lesson_data,
                course_title,
                section_title,
                topic_title,
                lesson_title,
                section_id,
                topic_id,
                lesson_id,
                user_profile,
            )

        except Exception as e:
            self.logger.error(f"Ошибка при отображении урока: {str(e)}")

            # Логируем ошибку
            self.lesson_interface.system_logger.log_activity(
                action_type="lesson_display_error",
                status="error",
                error=str(e),
                details={
                    "section_id": section_id,
                    "topic_id": topic_id,
                    "lesson_id": lesson_id,
                },
            )

            return self.utils.create_lesson_error_interface(
                "Ошибка при отображении урока",
                f"Не удалось отобразить урок: {str(e)}",
                self.lesson_interface,
            )

    def create_lesson_interface(
        self,
        lesson_content_data,
        lesson_data,
        course_title,
        section_title,
        topic_title,
        lesson_title,
        section_id,
        topic_id,
        lesson_id,
        user_profile,
    ):
        """
        Создает интерфейс урока.

        Args:
            lesson_content_data (dict): Данные содержания урока
            lesson_data (dict): Данные урока
            course_title (str): Название курса
            section_title (str): Название раздела
            topic_title (str): Название темы
            lesson_title (str): Название урока
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока
            user_profile (dict): Профиль пользователя

        Returns:
            widgets.VBox: Виджет с интерфейсом урока
        """
        try:
            # Создаем заголовок урока
            header_html = widgets.HTML(
                value=f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                           color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h1 style="margin: 0; font-size: 24px;">{lesson_content_data['title']}</h1>
                    <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 14px;">
                        {course_title} → {section_title} → {topic_title}
                    </p>
                </div>
                """
            )

            # Создаем контейнер для содержания урока
            content_html = widgets.HTML(
                value=lesson_content_data["content"],
                layout=widgets.Layout(
                    width="100%",
                    padding="20px",
                    border="1px solid #ddd",
                    border_radius="10px",
                    margin="10px 0",
                ),
            )

            # Создаем контейнеры для интерактивных функций
            self.lesson_interface.explain_container = widgets.VBox(
                layout=widgets.Layout(display="none", width="100%")
            )
            self.lesson_interface.examples_container = widgets.VBox(
                layout=widgets.Layout(display="none", width="100%")
            )
            self.lesson_interface.qa_container = widgets.VBox(
                layout=widgets.Layout(display="none", width="100%")
            )

            # Настраиваем QA контейнер
            from lesson_interaction import LessonInteraction

            interaction = LessonInteraction(self.lesson_interface)
            interaction.setup_enhanced_qa_container(self.lesson_interface.qa_container)

            # Создаем кнопки навигации
            from lesson_navigation import LessonNavigation

            navigation = LessonNavigation(self.lesson_interface)
            navigation_buttons = navigation.create_enhanced_navigation_buttons(
                section_id, topic_id, lesson_id
            )

            # Создаем основной контейнер
            lesson_container = widgets.VBox(
                [
                    header_html,
                    content_html,
                    navigation_buttons,
                    self.lesson_interface.explain_container,
                    self.lesson_interface.examples_container,
                    self.lesson_interface.qa_container,
                ],
                layout=widgets.Layout(width="100%", padding="20px"),
            )

            return lesson_container

        except Exception as e:
            self.logger.error(f"Ошибка при создании интерфейса урока: {str(e)}")
            return self.utils.create_lesson_error_interface(
                "Ошибка при создании интерфейса",
                f"Не удалось создать интерфейс урока: {str(e)}",
                self.lesson_interface,
            )
