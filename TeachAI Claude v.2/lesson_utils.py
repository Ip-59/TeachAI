"""
Утилиты для интерфейса уроков.
Отвечает за создание компонентов интерфейса урока.
РЕФАКТОРИНГ: Выделен из lesson_interface.py для соответствия лимиту размера.
ИСПРАВЛЕНО ЭТАП 34: Упрощен обработчик кнопки тестирования (проблема #145)
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import html
import logging


class LessonUtils:
    """Утилиты для создания интерфейса уроков."""

    def __init__(
        self,
        interface_utils=None,
        logger=None,
        state_manager=None,
        content_generator=None,
        assessment=None,
    ):
        """
        Инициализация утилит урока.

        Args:
            interface_utils: Утилиты интерфейса (опционально)
            logger: Логгер (опционально)
            state_manager: Менеджер состояния (опционально)
            content_generator: Генератор контента (опционально)
            assessment: Модуль оценивания (опционально)
        """
        self.interface_utils = interface_utils
        self.logger = logger or logging.getLogger(__name__)
        self.state_manager = state_manager
        self.content_generator = content_generator
        self.assessment = assessment

        self.logger.info("LessonUtils инициализирован")

    def create_lesson_header(self, lesson_title):
        """
        Создает заголовок урока.

        Args:
            lesson_title (str): Название урока

        Returns:
            widgets.HTML: Заголовок урока
        """
        safe_title = html.escape(str(lesson_title))
        return widgets.HTML(
            value=f"""
            <h1 style="margin: 10px 0; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                       color: white; border-radius: 10px; text-align: center; font-size: 24px;
                       box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                📚 {safe_title}
            </h1>
            """
        )

    def create_navigation_info(
        self,
        course_title,
        section_title,
        topic_title,
        lesson_title,
        estimated_time="⏱️ 30 мин.",
    ):
        """
        Создает навигационную информацию урока.

        Args:
            course_title (str): Название курса
            section_title (str): Название раздела
            topic_title (str): Название темы
            lesson_title (str): Название урока
            estimated_time (str): Предполагаемое время изучения

        Returns:
            widgets.HTML: Навигационная информация
        """
        safe_course = html.escape(str(course_title))
        safe_section = html.escape(str(section_title))
        safe_topic = html.escape(str(topic_title))
        safe_lesson = html.escape(str(lesson_title))
        safe_time = html.escape(str(estimated_time))

        return widgets.HTML(
            value=f"""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;
                       border-left: 4px solid #007bff;">
                <div style="display: flex; flex-wrap: wrap; gap: 15px; align-items: center;">
                    <span style="font-weight: bold; color: #495057;">📘 Курс: {safe_course}</span>
                    <span style="color: #6c757d;">📂 Раздел: {safe_section}</span>
                    <span style="color: #6c757d;">📋 Тема: {safe_topic}</span>
                    <span style="color: #6c757d;">📖 Урок: {safe_lesson}</span>
                    <span style="color: #28a745; font-weight: bold;">{safe_time}</span>
                </div>
            </div>
            """
        )

    # ИСПРАВЛЕНО ЭТАП 34: Добавлен alias для совместимости с lesson_interface.py
    def create_lesson_navigation(
        self,
        course_title,
        section_title,
        topic_title,
        lesson_title,
        estimated_time="⏱️ 30 мин.",
    ):
        """
        Alias для create_navigation_info для обратной совместимости.
        """
        return self.create_navigation_info(
            course_title, section_title, topic_title, lesson_title, estimated_time
        )

    def create_lesson_content(self, lesson_content_data):
        """
        Создает виджет содержания урока.

        ИСПРАВЛЕНО ЭТАП 33: Автоматическое определение типа HTML контента (проблема #135)

        Args:
            lesson_content_data (dict): Данные содержания урока

        Returns:
            widgets.HTML: Виджет с содержанием урока
        """
        try:
            # Извлекаем контент
            if isinstance(lesson_content_data, dict):
                content = lesson_content_data.get("content", "")
            else:
                content = str(lesson_content_data)

            if not content:
                content = "Содержание урока недоступно"

            # ИСПРАВЛЕНО ЭТАП 34: Улучшена логика определения HTML (проблема #135 fix)
            # Определяем тип контента более точно
            is_full_html = (
                "<style>" in content
                or '<div class="content-container">' in content
                or "<!DOCTYPE" in content
                or "<html>" in content
                or "<HTML>" in content
                or content.strip().startswith("<html")
            )

            if is_full_html:
                # LessonGenerator вернул полный HTML документ - возвращаем как есть
                return widgets.HTML(value=content)
            else:
                # LessonGenerator вернул обычный текст - форматируем его
                safe_content = html.escape(content)
                formatted_content = safe_content.replace("\n", "<br>")

                return widgets.HTML(
                    value=f"""
                    <div style="font-family: Arial, sans-serif; font-size: 16px; line-height: 1.6;
                               margin: 20px 0; padding: 20px; background: white; border-radius: 8px;
                               box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                        {formatted_content}
                    </div>
                    """
                )

        except Exception as e:
            self.logger.error(f"Ошибка создания содержания урока: {str(e)}")
            return widgets.HTML(
                value=f"""
                <div style="color: #dc3545; padding: 20px; background: #f8d7da; border-radius: 8px;">
                    <strong>Ошибка отображения содержания урока:</strong><br>
                    {html.escape(str(e))}
                </div>
                """
            )

    def create_interactive_buttons(self, interactive_handlers):
        """
        Создает интерактивные кнопки урока.

        Args:
            interactive_handlers: Обработчики интерактивных элементов

        Returns:
            widgets.HBox: Контейнер с кнопками
        """
        # Кнопка "Объясни подробнее"
        explain_button = widgets.Button(
            description="📚 Объясни подробнее",
            button_style="info",
            tooltip="Получить подробное объяснение материала",
            layout=widgets.Layout(width="200px", height="40px"),
        )

        # Кнопка "Приведи примеры"
        examples_button = widgets.Button(
            description="💡 Приведи примеры",
            button_style="warning",
            tooltip="Получить практические примеры",
            layout=widgets.Layout(width="200px", height="40px"),
        )

        # Кнопка "Задать вопрос"
        question_button = widgets.Button(
            description="❓ Задать вопрос",
            button_style="primary",
            tooltip="Задать вопрос по материалу урока",
            layout=widgets.Layout(width="200px", height="40px"),
        )

        # Подключаем обработчики
        if interactive_handlers:
            explain_button.on_click(interactive_handlers.handle_explain_button)
            examples_button.on_click(interactive_handlers.handle_examples_button)
            question_button.on_click(interactive_handlers.handle_question_button)

        return widgets.HBox(
            [explain_button, examples_button, question_button],
            layout=widgets.Layout(justify_content="center", margin="15px 0"),
        )

    def create_assessment_button(self, assessment_module, lesson_data, course_info):
        """
        Создает кнопку тестирования урока.

        ИСПРАВЛЕНО ЭТАП 34: Упрощен обработчик кнопки через facade.show_assessment() (проблема #145)

        Args:
            assessment_module: Модуль оценивания
            lesson_data: Данные урока
            course_info: Информация о курсе

        Returns:
            widgets.VBox: Контейнер с кнопкой тестирования
        """
        # Кнопка тестирования
        test_button = widgets.Button(
            description="🎯 Пройти тест по уроку",
            button_style="success",
            tooltip="Пройти тест для проверки знаний",
            layout=widgets.Layout(width="250px", height="45px"),
        )

        # Контейнер для вывода сообщений
        output_container = widgets.Output()

        def on_test_click(button):
            """
            ИСПРАВЛЕНО ЭТАП 34: Упрощенный обработчик кнопки тестирования.
            Использует facade.show_assessment() вместо создания нового UserInterface.
            """
            with output_container:
                output_container.clear_output()

                try:
                    self.logger.info("Начало тестирования урока")

                    # Определяем lesson_id из разных источников
                    lesson_id = None
                    if isinstance(lesson_data, dict):
                        lesson_id = lesson_data.get("id") or lesson_data.get(
                            "lesson_id"
                        )

                    if not lesson_id and isinstance(course_info, dict):
                        lesson_id = course_info.get("lesson_id")

                    if not lesson_id:
                        lesson_id = "текущий-урок"

                    self.logger.info(f"Используемый lesson_id: {lesson_id}")

                    # ИСПРАВЛЕНО ЭТАП 34: Используем facade.show_assessment() вместо создания UserInterface
                    facade = None
                    if isinstance(course_info, dict):
                        facade = course_info.get("facade")

                    if facade and hasattr(facade, "show_assessment"):
                        # Используем фасад для запуска тестирования
                        display(
                            widgets.HTML(
                                value="""
                            <div style="color: #155724; padding: 10px; background-color: #d4edda;
                                       border: 1px solid #c3e6cb; border-radius: 5px;">
                                <strong>🎯 Запуск тестирования...</strong>
                            </div>
                            """
                            )
                        )

                        # Вызываем тестирование через фасад
                        assessment_interface = facade.show_assessment(lesson_id)
                        if assessment_interface:
                            clear_output(wait=True)
                            display(assessment_interface)
                            self.logger.info(
                                f"Тестирование урока {lesson_id} успешно запущено через facade"
                            )
                        else:
                            error_msg = "Не удалось запустить тестирование через facade"
                            self.logger.error(error_msg)
                            display(
                                widgets.HTML(
                                    value=f"""
                                <div style="color: #721c24; padding: 10px; background-color: #f8d7da;
                                           border: 1px solid #f5c6cb; border-radius: 5px;">
                                    <strong>Ошибка:</strong><br>
                                    {html.escape(error_msg)}
                                </div>
                                """
                                )
                            )
                    else:
                        error_msg = "Интерфейс тестирования недоступен"
                        self.logger.error(error_msg)
                        display(
                            widgets.HTML(
                                value=f"""
                            <div style="color: #721c24; padding: 10px; background-color: #f8d7da;
                                       border: 1px solid #f5c6cb; border-radius: 5px;">
                                <strong>Ошибка:</strong><br>
                                {html.escape(error_msg)}<br>
                                <small>Убедитесь, что система правильно инициализирована.</small>
                            </div>
                            """
                            )
                        )

                except Exception as e:
                    error_msg = f"Критическая ошибка при тестировании: {str(e)}"
                    self.logger.error(error_msg)
                    display(
                        widgets.HTML(
                            value=f"""
                        <div style="color: #721c24; padding: 10px; background-color: #f8d7da;
                                   border: 1px solid #f5c6cb; border-radius: 5px;">
                            <strong>Критическая ошибка:</strong><br>
                            {html.escape(error_msg)}
                        </div>
                        """
                        )
                    )

        # Подключаем обработчик
        test_button.on_click(on_test_click)

        return widgets.VBox(
            [test_button, output_container],
            layout=widgets.Layout(align_items="center", margin="20px 0"),
        )

    def create_lesson_error_interface(self, error_title, error_message):
        """
        Создает интерфейс ошибки урока.

        Args:
            error_title (str): Заголовок ошибки
            error_message (str): Сообщение об ошибке

        Returns:
            widgets.VBox: Интерфейс ошибки
        """
        safe_title = html.escape(str(error_title))
        safe_message = html.escape(str(error_message))

        error_header = widgets.HTML(
            value=f"""
            <h2 style="color: #dc3545; margin: 10px 0; text-align: center;">
                ⚠️ {safe_title}
            </h2>
            """
        )

        error_content = widgets.HTML(
            value=f"""
            <div style="color: #721c24; padding: 20px; background-color: #f8d7da;
                       border: 1px solid #f5c6cb; border-radius: 8px; margin: 20px 0;">
                <strong>Ошибка:</strong><br>
                {safe_message}
            </div>
            """
        )

        return widgets.VBox(
            [error_header, error_content], layout=widgets.Layout(margin="20px 0")
        )

    def get_element_titles_from_plan(
        self, course_plan, section_id, topic_id, lesson_id
    ):
        """
        Извлекает названия элементов из плана курса.

        ИСПРАВЛЕНО ЭТАП 33: Правильная сигнатура метода (проблема #139)

        Args:
            course_plan (dict): План курса
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            tuple: (course_title, section_title, topic_title, lesson_title)
        """
        course_title = course_plan.get("title", "Курс")
        section_title = "Раздел"
        topic_title = "Тема"
        lesson_title = "Урок"

        try:
            for section in course_plan.get("sections", []):
                if section.get("id") == section_id:
                    section_title = section.get("title", section_title)
                    for topic in section.get("topics", []):
                        if topic.get("id") == topic_id:
                            topic_title = topic.get("title", topic_title)
                            for lesson in topic.get("lessons", []):
                                if lesson.get("id") == lesson_id:
                                    lesson_title = lesson.get("title", lesson_title)
                                    break
                            break
                    break
        except Exception as e:
            self.logger.warning(f"Ошибка извлечения названий из плана курса: {str(e)}")

        return course_title, section_title, topic_title, lesson_title

    def get_lesson_from_plan(self, course_plan, section_id, topic_id, lesson_id):
        """
        Извлекает данные урока из плана курса.

        Args:
            course_plan (dict): План курса
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            dict: Данные урока или None
        """
        try:
            if not isinstance(course_plan, dict):
                return None

            sections = course_plan.get("sections", [])
            for section in sections:
                if section.get("id") == section_id:
                    topics = section.get("topics", [])
                    for topic in topics:
                        if topic.get("id") == topic_id:
                            lessons = topic.get("lessons", [])
                            for lesson in lessons:
                                if lesson.get("id") == lesson_id:
                                    return lesson

            return None

        except Exception as e:
            self.logger.error(f"Ошибка при поиске урока {lesson_id}: {str(e)}")
            return None

    def get_course_id(self, course_plan):
        """
        Извлекает ID курса из плана курса.

        Args:
            course_plan (dict): План курса

        Returns:
            str: ID курса
        """
        if isinstance(course_plan, dict):
            return course_plan.get("id", "unknown-course")
        return "unknown-course"

    def validate_lesson_data(self, lesson_content_data, lesson_data):
        """
        Валидирует данные урока.

        Args:
            lesson_content_data: Данные содержания урока
            lesson_data: Данные урока из плана

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            if not lesson_content_data:
                return False, "Содержание урока отсутствует"

            if isinstance(lesson_content_data, dict):
                if not lesson_content_data.get("content"):
                    return False, "Содержание урока пустое"

            return True, ""

        except Exception as e:
            self.logger.error(f"Ошибка валидации данных урока: {str(e)}")
            return False, f"Ошибка валидации: {str(e)}"
