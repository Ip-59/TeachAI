"""
Интерфейс для отображения уроков и интерактивных функций.
Отвечает за показ содержания урока, примеров, объяснений и обработку вопросов пользователя.
ЗАВЕРШЕНО: Новая логика выбора типа объяснения, проверка релевантности вопросов, счетчик вопросов
ИСПРАВЛЕНО: Рабочая кнопка "Закрыть объяснение" (проблема #83)
ИСПРАВЛЕНО: Передача контекста курса в examples_generator для релевантности примеров (проблема #88)
ИСПРАВЛЕНО: Проблема #98 - правильные вызовы get_course_plan() через нужный менеджер
ИСПРАВЛЕНО: Реализованы обработчики интерактивных кнопок (была проблема с заглушками pass)
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
import traceback
from interface_utils import InterfaceUtils, InterfaceState

# Импорт demo_cells_integration с обработкой ошибок
try:
    from demo_cells_integration import DemoCellsIntegration

    DEMO_CELLS_AVAILABLE = True
except ImportError:
    logging.warning("Модуль demo_cells_integration недоступен")
    DEMO_CELLS_AVAILABLE = False

# Импорт control_tasks_generator с обработкой ошибок
try:
    from control_tasks_generator import ControlTasksGenerator

    CONTROL_TASKS_AVAILABLE = True
except ImportError:
    logging.warning("Модуль control_tasks_generator недоступен")
    CONTROL_TASKS_AVAILABLE = False


class LessonInterface:
    """Интерфейс для отображения уроков и интерактивных функций."""

    def __init__(
        self, state_manager, content_generator, system_logger, assessment=None
    ):
        """
        Инициализация интерфейса уроков.

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

        # Добавляем хранилище данных для интерактивных функций
        self.current_lesson_data = None
        self.current_lesson_content = None
        self.current_course_info = None
        self.current_lesson_id = None  # Для счетчика вопросов

        # ИСПРАВЛЕНО: Ссылки на контейнеры для правильного закрытия
        self.explain_container = None
        self.examples_container = None
        self.qa_container = None

        # НОВОЕ: Кэширование содержания урока для экономии API запросов
        self.cached_lesson_content = None
        self.cached_lesson_title = None
        self.current_lesson_cache_key = None

        # НОВОЕ: Интеграция демо-ячеек
        self.demo_cells_integration = None
        if DEMO_CELLS_AVAILABLE:
            try:
                self.demo_cells_integration = DemoCellsIntegration()
                self.logger.info("Demo cells integration инициализирован")
            except Exception as e:
                self.logger.error(f"Ошибка инициализации demo cells: {str(e)}")
                self.demo_cells_integration = None

        # НОВОЕ: Интеграция контрольных заданий
        self.control_tasks_generator = None
        self.current_control_tasks = None
        if CONTROL_TASKS_AVAILABLE:
            try:
                # Получаем API ключ из StateManager
                api_key = None
                if hasattr(state_manager, "state") and "api_key" in state_manager.state:
                    api_key = state_manager.state["api_key"]

                self.control_tasks_generator = ControlTasksGenerator(api_key)
                self.logger.info("Control tasks generator инициализирован")
            except Exception as e:
                self.logger.error(
                    f"Ошибка инициализации control tasks generator: {str(e)}"
                )
                self.control_tasks_generator = None

        self.logger.info("LessonInterface инициализирован с интеграциями")

    def show_lesson(self, section_id, topic_id, lesson_id):
        """
        Отображает урок пользователю.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            widgets.Widget: Виджет с уроком
        """
        try:
            self.logger.info(f"Отображение урока: {section_id}:{topic_id}:{lesson_id}")

            # НОВОЕ: Проверяем кэш урока
            lesson_cache_key = f"{section_id}:{topic_id}:{lesson_id}"
            if (
                self.current_lesson_cache_key == lesson_cache_key
                and self.cached_lesson_content
            ):
                self.logger.info("Урок загружается из кэша")
                return self._create_cached_lesson_interface(
                    section_id, topic_id, lesson_id
                )

            # Получаем профиль пользователя
            user_profile = self.state_manager.get_user_profile()
            if not user_profile:
                return self._create_lesson_error_interface(
                    "Профиль не найден",
                    "Профиль пользователя не найден. Пожалуйста, настройте профиль.",
                )

            # ИСПРАВЛЕНО: Правильный вызов get_course_plan()
            try:
                course_plan = self.state_manager.get_course_plan()
            except AttributeError:
                if hasattr(self.state_manager, "state_manager"):
                    course_plan = self.state_manager.state_manager.get_course_plan()
                else:
                    course_plan = {"title": "Курс", "sections": []}

            if not course_plan:
                return self._create_lesson_error_interface(
                    "План курса не найден",
                    "План курса не найден. Пожалуйста, выберите курс.",
                )

            # Получаем данные урока
            lesson_data = self.state_manager.get_lesson_data(
                section_id, topic_id, lesson_id
            )
            if not lesson_data:
                return self._create_lesson_error_interface(
                    "Урок не найден",
                    f"Урок {section_id}:{topic_id}:{lesson_id} не найден в плане курса.",
                )

            # Получаем названия элементов
            (
                course_title,
                section_title,
                topic_title,
                lesson_title,
            ) = self._get_element_titles_from_plan(
                course_plan, section_id, topic_id, lesson_id
            )

            # Генерируем содержание урока
            try:
                display(
                    self.utils.create_styled_message(
                        f"🎓 Генерируем содержание урока '{lesson_title}'...", "info"
                    )
                )

                lesson_content_data = self.content_generator.generate_lesson(
                    lesson_data=lesson_data,
                    communication_style=user_profile["communication_style"],
                )

                self.logger.info("Урок успешно сгенерирован")

            except Exception as e:
                self.logger.error(f"Ошибка при генерации урока: {str(e)}")
                clear_output(wait=True)
                return self._create_lesson_error_interface(
                    "Ошибка при генерации урока",
                    f"Не удалось сгенерировать содержание урока '{lesson_title}': {str(e)}",
                )

            # Очищаем сообщение о загрузке
            clear_output(wait=True)

            # Сохраняем данные для интерактивных функций
            self.current_lesson_data = lesson_data
            self.current_lesson_content = lesson_content_data["content"]
            self.current_lesson_id = (
                f"{section_id}:{topic_id}:{lesson_id}"  # Полный ID урока
            )
            self.current_course_info = {
                "course_title": course_title,
                "section_title": section_title,
                "topic_title": topic_title,
                "lesson_title": lesson_title,
                "section_id": section_id,
                "topic_id": topic_id,
                "lesson_id": lesson_id,
                "user_profile": user_profile,
                "course_plan": course_plan,  # НОВОЕ: Добавляем план курса для контекста
            }

            # Получаем ID курса безопасно
            course_id = self._get_course_id(course_plan)

            # Обновляем прогресс обучения
            self.state_manager.update_learning_progress(
                course=course_id, section=section_id, topic=topic_id, lesson=lesson_id
            )

            # Логируем урок
            self.system_logger.log_lesson(
                course=course_title,
                section=section_title,
                topic=topic_title,
                lesson_title=lesson_content_data["title"],
                lesson_content=lesson_content_data["content"],
            )

            # НОВОЕ: Интеграция демо-ячеек
            try:
                if self.demo_cells_integration:
                    lesson_content_data[
                        "content"
                    ] = self.demo_cells_integration.integrate_demo_cells_in_lesson(
                        lesson_content_data["content"], lesson_id
                    )
                    self.logger.debug("Демо-ячейки успешно интегрированы")
            except Exception as e:
                self.logger.warning(f"Ошибка интеграции демо-ячеек: {str(e)}")

            # НОВОЕ: Кэшируем урок
            self.cached_lesson_content = lesson_content_data
            self.cached_lesson_title = lesson_title
            self.current_lesson_cache_key = lesson_cache_key

            # Создаем интерфейс урока
            return self._create_lesson_interface(
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
            self.logger.error(f"Критическая ошибка при отображении урока: {str(e)}")
            self.logger.error(traceback.format_exc())
            return self._create_lesson_error_interface(
                "Критическая ошибка", f"Произошла критическая ошибка: {str(e)}"
            )

    def _get_element_titles_from_plan(
        self, course_plan, section_id, topic_id, lesson_id
    ):
        """
        Получает названия элементов из плана курса.

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

        return course_title, section_title, topic_title, lesson_title

    def _get_lesson_from_plan(self, course_plan, section_id, topic_id, lesson_id):
        """
        Получает данные урока из плана курса.

        Args:
            course_plan (dict): План курса
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            dict: Данные урока или None, если не найден
        """
        for section in course_plan.get("sections", []):
            if section.get("id") == section_id:
                for topic in section.get("topics", []):
                    if topic.get("id") == topic_id:
                        for lesson in topic.get("lessons", []):
                            if lesson.get("id") == lesson_id:
                                return lesson
        return None

    def _create_lesson_interface(
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
        МОДИФИЦИРОВАНО: Создает полный интерфейс урока с демо-ячейками и контрольными заданиями.

        Returns:
            widgets.VBox: Интерфейс урока
        """
        # Заголовок урока
        lesson_header = self.utils.create_header(lesson_title)

        # Навигационная информация
        nav_info = self.utils.create_navigation_info(
            course_title,
            section_title,
            topic_title,
            lesson_title,
            f"⏱️ {lesson_content_data.get('estimated_time', 30)} мин.",
        )

        # Содержание урока (с возможными демо-ячейками)
        lesson_content = widgets.HTML(
            value=f'<div style="{self.utils.STYLES["lesson_content"]}">{lesson_content_data["content"]}</div>'
        )

        # Создаем контейнеры для интерактивных функций
        self.explain_container = widgets.Output()
        self.examples_container = widgets.Output()
        self.qa_container = widgets.Output()

        # Интерактивные кнопки
        interactive_buttons = self._create_interactive_buttons()

        # НОВОЕ: Добавляем секцию контрольных заданий
        control_tasks_section = self._create_control_tasks_section(lesson_data)

        # Кнопки навигации
        navigation_buttons = self._create_navigation_buttons(
            section_id, topic_id, lesson_id
        )

        # Сборка интерфейса
        lesson_components = [
            lesson_header,
            nav_info,
            lesson_content,
            interactive_buttons,
            self.explain_container,
            self.examples_container,
            self.qa_container,
        ]

        # НОВОЕ: Добавляем контрольные задания, если доступны
        if control_tasks_section:
            lesson_components.append(control_tasks_section)

        lesson_components.append(navigation_buttons)

        return widgets.VBox(lesson_components, layout=widgets.Layout(gap="15px"))

    def _create_interactive_buttons(self):
        """
        Создает интерактивные кнопки урока.

        Returns:
            widgets.HBox: Контейнер с кнопками
        """
        # Кнопка объяснения
        explain_button = widgets.Button(
            description="💡 Объясни подробнее",
            button_style="info",
            layout=widgets.Layout(width="200px", margin="5px"),
        )

        # Кнопка примеров
        examples_button = widgets.Button(
            description="🔍 Приведи примеры",
            button_style="success",
            layout=widgets.Layout(width="200px", margin="5px"),
        )

        # Кнопка вопросов
        qa_button = widgets.Button(
            description="❓ Задать вопрос",
            button_style="warning",
            layout=widgets.Layout(width="200px", margin="5px"),
        )

        # Обработчики кнопок
        explain_button.on_click(self._handle_explain_button)
        examples_button.on_click(self._handle_examples_button)
        qa_button.on_click(self._handle_qa_button)

        return widgets.HBox(
            [explain_button, examples_button, qa_button],
            layout=widgets.Layout(justify_content="center", margin="20px 0"),
        )

    def _create_navigation_buttons(self, section_id, topic_id, lesson_id):
        """
        Создает кнопки навигации.

        Returns:
            widgets.HBox: Контейнер с кнопками навигации
        """
        # Кнопка "Назад"
        back_button = widgets.Button(
            description="⬅️ Вернуться к курсам",
            button_style="",
            layout=widgets.Layout(width="200px", margin="10px"),
        )

        # Кнопка теста
        test_button = widgets.Button(
            description="📝 Пройти тест",
            button_style="primary",
            layout=widgets.Layout(width="200px", margin="10px"),
        )

        # Кнопка "Далее"
        next_button = widgets.Button(
            description="➡️ Следующий урок",
            button_style="success",
            layout=widgets.Layout(width="200px", margin="10px"),
        )

        # Обработчики навигации
        def go_back_to_courses(b):
            clear_output(wait=True)
            from interface import UserInterface

            interface = UserInterface(
                self.state_manager,
                self.content_generator,
                self.assessment,
                self.system_logger,
            )
            display(interface.show_course_selection())

        def start_assessment(b):
            clear_output(wait=True)
            from assessment_interface import AssessmentInterface

            assessment_ui = AssessmentInterface(
                self.state_manager, self.assessment, self.system_logger
            )
            display(
                assessment_ui.start_lesson_assessment(section_id, topic_id, lesson_id)
            )

        def go_to_next_lesson(b):
            try:
                next_lesson_data = self.state_manager.get_next_lesson()
                if next_lesson_data and next_lesson_data[0]:
                    next_section, next_topic, next_lesson, _ = next_lesson_data
                    clear_output(wait=True)
                    display(self.show_lesson(next_section, next_topic, next_lesson))
                else:
                    clear_output(wait=True)
                    from completion_interface import CompletionInterface

                    completion_ui = CompletionInterface(
                        self.state_manager,
                        self.system_logger,
                        self.content_generator,
                        self.assessment,
                    )
                    display(completion_ui.show_course_completion())
            except Exception as e:
                self.logger.error(f"Ошибка при переходе к следующему уроку: {str(e)}")
                display(
                    self.utils.create_styled_message(f"Ошибка: {str(e)}", "incorrect")
                )

        back_button.on_click(go_back_to_courses)
        test_button.on_click(start_assessment)
        next_button.on_click(go_to_next_lesson)

        return widgets.HBox(
            [back_button, test_button, next_button],
            layout=widgets.Layout(justify_content="center", margin="30px 0"),
        )

    def _create_control_tasks_section(self, lesson_data):
        """
        НОВОЕ: Создает секцию с контрольными заданиями для урока.

        Args:
            lesson_data (dict): Данные урока

        Returns:
            widgets.VBox или None: Секция контрольных заданий
        """
        if not self.control_tasks_generator:
            return None

        try:
            # Генерируем контрольные задания для урока
            control_tasks = self.control_tasks_generator.generate_lesson_control_tasks(
                lesson_data=lesson_data, lesson_content=self.current_lesson_content
            )

            if not control_tasks or len(control_tasks) == 0:
                return None

            # Сохраняем задания
            self.current_control_tasks = control_tasks

            # Создаем заголовок секции
            tasks_header = widgets.HTML(
                value=f"""
            <div style="background: linear-gradient(135deg, #9C27B0, #673AB7);
                       color: white; padding: 15px; border-radius: 8px; margin: 30px 0 15px 0;">
                <h3 style="margin: 0; font-size: 18px;">🎯 Контрольные задания</h3>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Проверьте свои знания на практике</p>
            </div>
            """
            )

            # Создаем виджеты для каждого задания
            task_widgets = []
            for i, task in enumerate(control_tasks, 1):
                task_widget = self._create_control_task_widget(task, i)
                if task_widget:
                    task_widgets.append(task_widget)

            if not task_widgets:
                return None

            # Собираем секцию
            tasks_section = widgets.VBox(
                [tasks_header] + task_widgets, layout=widgets.Layout(gap="10px")
            )

            return tasks_section

        except Exception as e:
            self.logger.error(f"Ошибка при создании контрольных заданий: {str(e)}")
            return None

    def _create_control_task_widget(self, task, task_number):
        """
        НОВОЕ: Создает виджет для одного контрольного задания.

        Args:
            task (dict): Данные задания
            task_number (int): Номер задания

        Returns:
            widgets.VBox: Виджет задания
        """
        try:
            from interactive_cell_widget import create_interactive_cell

            # Создаем интерактивную ячейку для задания
            cell_widget = create_interactive_cell(
                title=f"Задание {task_number}: {task['title']}",
                description=task["description"],
                initial_code=task["initial_code"],
                expected_result=task["expected_result"],
                check_type=task["check_type"],
                cell_id=f"control_task_{self.current_lesson_id}_{task_number}",
                max_attempts=task.get("max_attempts"),
                hints=task.get("hints", []),
                show_solution=task.get("show_solution", False),
            )

            return cell_widget

        except Exception as e:
            self.logger.error(f"Ошибка при создании виджета задания: {str(e)}")
            # Возвращаем простой HTML виджет с заданием
            fallback_html = f"""
            <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; background-color: #f9f9f9;">
                <h4>{task['title']}</h4>
                <p>{task['description']}</p>
                <pre style="background-color: #f1f1f1; padding: 10px; border-radius: 4px;">{task['initial_code']}</pre>
                <p><em>Интерактивная ячейка недоступна. Выполните код в отдельной ячейке.</em></p>
            </div>
            """
            return widgets.HTML(value=fallback_html)

    def _get_safe_course_title(self, course_plan):
        """
        Безопасно получает название курса.

        Args:
            course_plan (dict): План курса

        Returns:
            str: Название курса
        """
        course_title = course_plan.get("title", "Курс")
        if not course_title or course_title == "Курс":
            learning_progress = self.state_manager.get_learning_progress()
            course_title = learning_progress.get("current_course", "Курс Python")
        return course_title

    def _get_course_id(self, course_plan):
        """
        Безопасно получает ID курса.

        Args:
            course_plan (dict): План курса

        Returns:
            str: ID курса
        """
        course_id = course_plan.get("id", course_plan.get("title", "unknown_course"))
        return course_id

    def _clear_lesson_cache(self):
        """
        НОВОЕ: Очищает кэш урока.
        """
        self.current_lesson_cache_key = None
        self.cached_lesson_content = None
        self.cached_lesson_title = None
        self.current_lesson_cache_key = None
        self.current_control_tasks = None  # НОВОЕ: Очищаем и контрольные задания
        self.logger.debug("Кэш урока очищен")

    def _create_cached_lesson_interface(self, section_id, topic_id, lesson_id):
        """
        НОВОЕ: Создает интерфейс урока из кэшированного содержания.

        Returns:
            widgets.VBox: Интерфейс урока из кэша
        """
        try:
            # Восстанавливаем данные из кэша
            lesson_content_data = self.cached_lesson_content
            lesson_title = self.cached_lesson_title

            # Получаем остальные данные (они легковесные)
            # ИСПРАВЛЕНО: Правильный вызов get_course_plan()
            try:
                course_plan = self.state_manager.get_course_plan()
            except AttributeError:
                if hasattr(self.state_manager, "state_manager"):
                    course_plan = self.state_manager.state_manager.get_course_plan()
                else:
                    course_plan = {"title": "Курс", "sections": []}

            user_profile = self.state_manager.get_user_profile()
            course_title = self._get_safe_course_title(course_plan)
            section_title, topic_title, _ = self._get_element_titles_from_plan(
                course_plan, section_id, topic_id, lesson_id
            )
            lesson_data = self.state_manager.get_lesson_data(
                section_id, topic_id, lesson_id
            )

            return self._create_lesson_interface(
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
            self.logger.error(f"Ошибка при создании интерфейса из кэша: {str(e)}")
            # Очищаем кэш и пересоздаем урок
            self._clear_lesson_cache()
            return self.show_lesson(section_id, topic_id, lesson_id)

    def _create_lesson_error_interface(self, title, message):
        """
        ИСПРАВЛЕНО: Создает интерфейс ошибки урока с правильным импортом.

        Args:
            title (str): Заголовок ошибки
            message (str): Сообщение об ошибке

        Returns:
            widgets.VBox: Интерфейс ошибки
        """
        error_header = self.utils.create_header(f"❌ {title}")
        error_message = self.utils.create_styled_message(message, "incorrect")

        back_button = widgets.Button(
            description="⬅️ Назад к курсам",
            button_style="primary",
            layout=widgets.Layout(width="200px", margin="20px 0"),
        )

        def go_back(b):
            clear_output(wait=True)
            from interface import UserInterface

            interface = UserInterface(
                self.state_manager,
                self.content_generator,
                self.assessment,
                self.system_logger,
            )
            display(interface.show_course_selection())

        back_button.on_click(go_back)

        return widgets.VBox(
            [
                error_header,
                error_message,
                widgets.HBox(
                    [back_button], layout=widgets.Layout(justify_content="center")
                ),
            ],
            layout=widgets.Layout(gap="15px"),
        )

    # ИСПРАВЛЕНО: Реализованы обработчики интерактивных кнопок вместо заглушек pass
    def _handle_explain_button(self, button):
        """Обработчик кнопки объяснения."""
        try:
            # Проверяем наличие данных
            if not self.current_lesson_content or not self.current_course_info:
                with self.explain_container:
                    clear_output(wait=True)
                    display(
                        self.utils.create_styled_message(
                            "Ошибка: данные урока не найдены. Попробуйте перезагрузить урок.",
                            "incorrect",
                        )
                    )
                return

            # Очищаем контейнер и показываем загрузку
            with self.explain_container:
                clear_output(wait=True)
                display(
                    self.utils.create_styled_message(
                        "💡 Генерируем подробное объяснение...", "info"
                    )
                )

            # Получаем данные для генерации
            course_info = self.current_course_info
            user_profile = course_info.get("user_profile", {})
            communication_style = user_profile.get("communication_style", "friendly")

            # Генерируем объяснение
            explanation = self.content_generator.get_detailed_explanation(
                course=course_info.get("course_title", "Курс"),
                section=course_info.get("section_title", "Раздел"),
                topic=course_info.get("topic_title", "Тема"),
                lesson=course_info.get("lesson_title", "Урок"),
                lesson_content=self.current_lesson_content,
                communication_style=communication_style,
            )

            # Создаем кнопку закрытия
            close_button = widgets.Button(
                description="❌ Закрыть объяснение",
                button_style="",
                layout=widgets.Layout(width="200px", margin="10px 0"),
            )

            def close_explanation(b):
                with self.explain_container:
                    clear_output(wait=True)

            close_button.on_click(close_explanation)

            # Показываем результат
            with self.explain_container:
                clear_output(wait=True)

                # Заголовок секции
                explanation_header = widgets.HTML(
                    value=f"""
                <div style="background: linear-gradient(135deg, #4CAF50, #45a049);
                           color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <h3 style="margin: 0; font-size: 18px;">💡 Подробное объяснение материала</h3>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">Детальный разбор темы урока</p>
                </div>
                """
                )

                # Содержание объяснения
                explanation_content = widgets.HTML(
                    value=f'<div style="padding: 15px; background: #f8f9fa; border-radius: 8px; line-height: 1.6;">{explanation}</div>'
                )

                display(explanation_header)
                display(explanation_content)
                display(close_button)

            self.logger.info("Объяснение успешно сгенерировано")

        except Exception as e:
            self.logger.error(f"Ошибка при генерации объяснения: {str(e)}")
            with self.explain_container:
                clear_output(wait=True)
                display(
                    self.utils.create_styled_message(
                        f"Ошибка при генерации объяснения: {str(e)}", "incorrect"
                    )
                )

    def _handle_examples_button(self, button):
        """Обработчик кнопки примеров."""
        try:
            # Проверяем наличие данных
            if (
                not self.current_lesson_content
                or not self.current_course_info
                or not self.current_lesson_data
            ):
                with self.examples_container:
                    clear_output(wait=True)
                    display(
                        self.utils.create_styled_message(
                            "Ошибка: данные урока не найдены. Попробуйте перезагрузить урок.",
                            "incorrect",
                        )
                    )
                return

            # Очищаем контейнер и показываем загрузку
            with self.examples_container:
                clear_output(wait=True)
                display(
                    self.utils.create_styled_message(
                        "🔍 Генерируем практические примеры...", "info"
                    )
                )

            # Получаем данные для генерации
            course_info = self.current_course_info
            user_profile = course_info.get("user_profile", {})
            communication_style = user_profile.get("communication_style", "friendly")

            # Подготавливаем контекст курса для examples_generator
            course_context = {
                "course_title": course_info.get("course_title", ""),
                "section_title": course_info.get("section_title", ""),
                "topic_title": course_info.get("topic_title", ""),
                "course_subject": course_info.get(
                    "course_title", ""
                ).lower(),  # Для определения предметной области
            }

            # Генерируем примеры
            examples = self.content_generator.generate_examples(
                lesson_data=self.current_lesson_data,
                lesson_content=self.current_lesson_content,
                communication_style=communication_style,
                course_context=course_context,
            )

            # Создаем кнопку закрытия
            close_button = widgets.Button(
                description="❌ Закрыть примеры",
                button_style="",
                layout=widgets.Layout(width="200px", margin="10px 0"),
            )

            def close_examples(b):
                with self.examples_container:
                    clear_output(wait=True)

            close_button.on_click(close_examples)

            # Показываем результат
            with self.examples_container:
                clear_output(wait=True)

                # Заголовок секции
                examples_header = widgets.HTML(
                    value=f"""
                <div style="background: linear-gradient(135deg, #2196F3, #1976D2);
                           color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <h3 style="margin: 0; font-size: 18px;">🔍 Практические примеры</h3>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">Примеры кода для закрепления материала</p>
                </div>
                """
                )

                # Содержание примеров
                examples_content = widgets.HTML(
                    value=f'<div style="padding: 15px; background: #f8f9fa; border-radius: 8px; line-height: 1.6;">{examples}</div>'
                )

                display(examples_header)
                display(examples_content)
                display(close_button)

            self.logger.info("Примеры успешно сгенерированы")

        except Exception as e:
            self.logger.error(f"Ошибка при генерации примеров: {str(e)}")
            with self.examples_container:
                clear_output(wait=True)
                display(
                    self.utils.create_styled_message(
                        f"Ошибка при генерации примеров: {str(e)}", "incorrect"
                    )
                )

    def _handle_qa_button(self, button):
        """Обработчик кнопки вопросов."""
        try:
            # Проверяем наличие данных
            if not self.current_lesson_content or not self.current_course_info:
                with self.qa_container:
                    clear_output(wait=True)
                    display(
                        self.utils.create_styled_message(
                            "Ошибка: данные урока не найдены. Попробуйте перезагрузить урок.",
                            "incorrect",
                        )
                    )
                return

            # Очищаем контейнер и показываем интерфейс вопросов
            with self.qa_container:
                clear_output(wait=True)

                # Заголовок секции
                qa_header = widgets.HTML(
                    value=f"""
                <div style="background: linear-gradient(135deg, #FF9800, #F57C00);
                           color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <h3 style="margin: 0; font-size: 18px;">❓ Задать вопрос</h3>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">Спросите что-то по материалу урока</p>
                </div>
                """
                )

                # Поле для ввода вопроса
                question_input = widgets.Textarea(
                    placeholder="Введите ваш вопрос по материалу урока...",
                    layout=widgets.Layout(
                        width="100%", height="100px", margin="10px 0"
                    ),
                )

                # Кнопки
                submit_button = widgets.Button(
                    description="✅ Задать вопрос",
                    button_style="primary",
                    layout=widgets.Layout(width="150px", margin="5px"),
                )

                close_button = widgets.Button(
                    description="❌ Закрыть",
                    button_style="",
                    layout=widgets.Layout(width="150px", margin="5px"),
                )

                # Контейнер для ответа
                answer_container = widgets.Output()

                def submit_question(b):
                    user_question = question_input.value.strip()

                    if not user_question:
                        with answer_container:
                            clear_output(wait=True)
                            display(
                                self.utils.create_styled_message(
                                    "Пожалуйста, введите вопрос.", "warning"
                                )
                            )
                        return

                    try:
                        # Показываем загрузку
                        with answer_container:
                            clear_output(wait=True)
                            display(
                                self.utils.create_styled_message(
                                    "🤔 Обрабатываем ваш вопрос...", "info"
                                )
                            )

                        # Получаем данные для генерации ответа
                        course_info = self.current_course_info
                        user_profile = course_info.get("user_profile", {})
                        user_name = user_profile.get("name", "Студент")
                        communication_style = user_profile.get(
                            "communication_style", "friendly"
                        )

                        # Генерируем ответ
                        answer = self.content_generator.answer_question(
                            course=course_info.get("course_title", "Курс"),
                            section=course_info.get("section_title", "Раздел"),
                            topic=course_info.get("topic_title", "Тема"),
                            lesson=course_info.get("lesson_title", "Урок"),
                            user_question=user_question,
                            lesson_content=self.current_lesson_content,
                            user_name=user_name,
                            communication_style=communication_style,
                        )

                        # Показываем ответ
                        with answer_container:
                            clear_output(wait=True)

                            question_display = widgets.HTML(
                                value=f"""
                            <div style="background: #e3f2fd; padding: 12px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #2196F3;">
                                <strong>Ваш вопрос:</strong><br>
                                <em>{user_question}</em>
                            </div>
                            """
                            )

                            answer_display = widgets.HTML(
                                value=f"""
                            <div style="background: #f3e5f5; padding: 15px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #9c27b0; line-height: 1.6;">
                                <strong>Ответ:</strong><br>
                                {answer}
                            </div>
                            """
                            )

                            display(question_display)
                            display(answer_display)

                        # Очищаем поле ввода
                        question_input.value = ""

                        self.logger.info(
                            f"Ответ на вопрос сгенерирован: {user_question[:50]}..."
                        )

                    except Exception as e:
                        self.logger.error(f"Ошибка при генерации ответа: {str(e)}")
                        with answer_container:
                            clear_output(wait=True)
                            display(
                                self.utils.create_styled_message(
                                    f"Ошибка при генерации ответа: {str(e)}",
                                    "incorrect",
                                )
                            )

                def close_qa(b):
                    with self.qa_container:
                        clear_output(wait=True)

                submit_button.on_click(submit_question)
                close_button.on_click(close_qa)

                # Показываем интерфейс
                buttons_container = widgets.HBox(
                    [submit_button, close_button],
                    layout=widgets.Layout(justify_content="flex-start"),
                )

                display(qa_header)
                display(question_input)
                display(buttons_container)
                display(answer_container)

            self.logger.info("Интерфейс вопросов отображен")

        except Exception as e:
            self.logger.error(f"Ошибка при создании интерфейса вопросов: {str(e)}")
            with self.qa_container:
                clear_output(wait=True)
                display(
                    self.utils.create_styled_message(
                        f"Ошибка при создании интерфейса вопросов: {str(e)}",
                        "incorrect",
                    )
                )
