"""
Интерфейс для отображения уроков и интерактивных функций.
Отвечает за показ содержания урока, примеров, объяснений и обработку вопросов пользователя.
ЗАВЕРШЕНО: Новая логика выбора типа объяснения, проверка релевантности вопросов, счетчик вопросов
ИСПРАВЛЕНО: Рабочая кнопка "Закрыть объяснение" (проблема #83)
ИСПРАВЛЕНО: Передача контекста курса в examples_generator для релевантности примеров (проблема #88)
НОВОЕ: Интеграция демонстрационных ячеек Jupiter Notebook в уроки
НОВОЕ: Автоматическая замена примеров кода на интерактивные демо-ячейки
НОВОЕ: Контрольные задания с интерактивными ячейками Jupiter Notebook
НОВОЕ: Логика определения практических vs теоретических уроков
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
import traceback
from interface_utils import InterfaceUtils, InterfaceState

# НОВОЕ: Импорт модулей Jupiter notebook и контрольных заданий
try:
    from demo_cells_integration import DemoCellsIntegration

    DEMO_CELLS_AVAILABLE = True
except ImportError:
    logging.warning(
        "Модуль demo_cells_integration не найден, демо-ячейки будут недоступны"
    )
    DEMO_CELLS_AVAILABLE = False

    class DemoCellsIntegration:
        def __init__(self):
            pass

        def integrate_demo_cells_in_lesson(self, content, lesson_id=None):
            return content


try:
    from control_tasks_generator import ControlTasksGenerator

    CONTROL_TASKS_AVAILABLE = True
except ImportError:
    logging.warning(
        "Модуль control_tasks_generator не найден, контрольные задания будут недоступны"
    )
    CONTROL_TASKS_AVAILABLE = False

    class ControlTasksGenerator:
        def __init__(self, api_key):
            pass

        def generate_control_tasks(self, *args, **kwargs):
            return []


try:
    from interactive_cell_widget import InteractiveCellWidget, create_interactive_cell

    INTERACTIVE_CELLS_AVAILABLE = True
except ImportError:
    logging.warning(
        "Модуль interactive_cell_widget не найден, интерактивные ячейки будут недоступны"
    )
    INTERACTIVE_CELLS_AVAILABLE = False

    def create_interactive_cell(*args, **kwargs):
        return widgets.HTML("<p>Интерактивные ячейки недоступны</p>")


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

        # НОВОЕ: Интегратор демо-ячеек
        self.demo_cells_integration = DemoCellsIntegration()

        # НОВОЕ: Генератор контрольных заданий
        if CONTROL_TASKS_AVAILABLE:
            try:
                # Пытаемся получить API ключ из content_generator
                api_key = getattr(content_generator, "api_key", None)
                if api_key:
                    self.control_tasks_generator = ControlTasksGenerator(api_key)
                else:
                    self.logger.warning(
                        "API ключ не найден, контрольные задания будут недоступны"
                    )
                    self.control_tasks_generator = None
            except Exception as e:
                self.logger.error(
                    f"Ошибка инициализации генератора контрольных заданий: {str(e)}"
                )
                self.control_tasks_generator = None
        else:
            self.control_tasks_generator = None

        # Добавляем хранилище данных для интерактивных функций
        self.current_lesson_data = None
        self.current_lesson_content = None
        self.current_course_info = None
        self.current_lesson_id = None  # Для счетчика вопросов

        # НОВОЕ: Кэширование содержания урока (из проблемы #89)
        self.cached_lesson_content = None
        self.cached_lesson_title = None
        self.current_lesson_cache_key = None

        # НОВОЕ: Данные контрольных заданий
        self.current_control_tasks = None

        # ИСПРАВЛЕНО: Ссылки на контейнеры для правильного закрытия
        self.explain_container = None
        self.examples_container = None
        self.qa_container = None
        self.control_tasks_container = None  # НОВОЕ: Контейнер для контрольных заданий

    def show_lesson(self, section_id, topic_id, lesson_id):
        """
        МОДИФИЦИРОВАНО: Отображает урок с демо-ячейками и контрольными заданиями.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            widgets.VBox: Полный интерфейс урока с демо-ячейками и контрольными заданиями
        """
        try:
            self.logger.info(f"Отображение урока: {section_id}:{topic_id}:{lesson_id}")

            # НОВОЕ: Создаем ключ кэша для урока
            lesson_cache_key = f"{section_id}:{topic_id}:{lesson_id}"

            # Проверяем кэш содержания урока
            if (
                self.current_lesson_cache_key == lesson_cache_key
                and self.cached_lesson_content is not None
            ):
                self.logger.info("Используем кэшированное содержание урока")
                return self._create_cached_lesson_interface(
                    section_id, topic_id, lesson_id
                )

            # Очищаем старый кэш
            self._clear_lesson_cache()

            # Получаем данные о курсе и пользователе
            course_plan = self.state_manager.get_course_plan()
            user_profile = self.state_manager.get_user_profile()

            if not course_plan or not user_profile:
                return self._create_lesson_error_interface(
                    "Ошибка конфигурации",
                    "Не удалось получить данные курса или пользователя",
                )

            # Получаем названия элементов курса
            course_title = self._get_safe_course_title(course_plan)
            (
                section_title,
                topic_title,
                lesson_title,
            ) = self._get_element_titles_from_plan(
                course_plan, section_id, topic_id, lesson_id
            )

            # Показываем сообщение о загрузке
            display(widgets.HTML(value="<p><strong>Загрузка урока...</strong></p>"))

            # Получаем данные урока
            lesson_data = self.state_manager.get_lesson_data(
                section_id, topic_id, lesson_id
            )
            if not lesson_data:
                clear_output(wait=True)
                return self._create_lesson_error_interface(
                    "Урок не найден", f"Урок '{lesson_id}' не найден в плане курса"
                )

            # Генерируем содержание урока
            try:
                lesson_content_data = self.content_generator.generate_lesson(
                    course=course_title,
                    section=section_title,
                    topic=topic_title,
                    lesson=lesson_title,
                    user_name=user_profile["name"],
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

            # НОВОЕ: Интегрируем демо-ячейки в содержание урока
            original_content = lesson_content_data["content"]
            if DEMO_CELLS_AVAILABLE:
                try:
                    lesson_content_data[
                        "content"
                    ] = self.demo_cells_integration.integrate_demo_cells_in_lesson(
                        original_content, lesson_cache_key
                    )
                    self.logger.info("Демо-ячейки успешно интегрированы в урок")
                except Exception as e:
                    self.logger.error(f"Ошибка интеграции демо-ячеек: {str(e)}")
                    # Продолжаем с оригинальным содержанием
                    lesson_content_data["content"] = original_content

            # НОВОЕ: Генерируем контрольные задания
            self.current_control_tasks = []
            if self.control_tasks_generator:
                try:
                    course_context = {
                        "course_title": course_title,
                        "course_plan": course_plan,
                        "section_title": section_title,
                        "topic_title": topic_title,
                    }

                    self.current_control_tasks = (
                        self.control_tasks_generator.generate_control_tasks(
                            lesson_data=lesson_data,
                            lesson_content=lesson_content_data["content"],
                            communication_style=user_profile["communication_style"],
                            course_context=course_context,
                        )
                    )

                    if self.current_control_tasks:
                        self.logger.info(
                            f"Сгенерировано {len(self.current_control_tasks)} контрольных заданий"
                        )
                    else:
                        self.logger.info(
                            "Контрольные задания не требуются для этого урока"
                        )

                except Exception as e:
                    self.logger.error(f"Ошибка генерации контрольных заданий: {str(e)}")
                    self.current_control_tasks = []

            # НОВОЕ: Кэшируем содержание урока
            self.cached_lesson_content = lesson_content_data
            self.cached_lesson_title = lesson_title
            self.current_lesson_cache_key = lesson_cache_key

            # Сохраняем данные для интерактивных функций
            self.current_lesson_data = lesson_data
            self.current_lesson_content = lesson_content_data["content"]
            self.current_lesson_id = lesson_cache_key
            self.current_course_info = {
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
            self.logger.error(f"Ошибка при отображении урока: {str(e)}")

            # Логируем ошибку
            self.system_logger.log_activity(
                action_type="lesson_display_error",
                status="error",
                error=str(e),
                details={
                    "section_id": section_id,
                    "topic_id": topic_id,
                    "lesson_id": lesson_id,
                },
            )

            return self._create_lesson_error_interface(
                "Ошибка при загрузке урока",
                f"Произошла ошибка при загрузке урока: {str(e)}",
            )

    def _clear_lesson_cache(self):
        """
        НОВОЕ: Очищает кэш содержания урока и контрольных заданий.
        """
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
            course_plan = self.state_manager.get_course_plan()
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

        Args:
            lesson_content_data (dict): Данные содержания урока
            lesson_data (dict): Метаданные урока
            course_title, section_title, topic_title, lesson_title (str): Названия элементов
            section_id, topic_id, lesson_id (str): ID элементов
            user_profile (dict): Профиль пользователя

        Returns:
            widgets.VBox: Полный интерфейс урока
        """
        # Навигационная информация
        nav_info = widgets.HTML(
            value=self.utils.create_navigation_info(
                course_title, section_title, topic_title, lesson_title
            )
        )

        # Заголовок урока
        lesson_header = widgets.HTML(
            value=f"<h1 style='font-size: 24px; font-weight: bold; color: #495057; margin: 20px 0 10px 0;'>{lesson_content_data['title']}</h1>"
        )

        # Информация о времени изучения
        duration_minutes = lesson_data.get("duration_minutes")
        if duration_minutes:
            time_info = widgets.HTML(
                value=f"<p><i>Примерное время изучения: {duration_minutes} минут</i></p>"
            )
        else:
            time_info = widgets.HTML(
                value="<p><i>Примерное время изучения: не указано</i></p>"
            )

        # Прогресс обучения
        progress_data = self.state_manager.calculate_course_progress()
        progress_bar, progress_text = self.utils.create_progress_info(progress_data)
        progress_container = widgets.VBox([progress_bar, progress_text])

        # МОДИФИЦИРОВАНО: Содержание урока с интегрированными демо-ячейками
        lesson_content = widgets.HTML(
            value=f"<div>{lesson_content_data['content']}</div>"
        )

        # НОВОЕ: Добавляем информацию о доступных интерактивных возможностях
        features_info = self._create_features_info()

        # ИСПРАВЛЕНО: Создаем контейнеры и сохраняем ссылки на них
        self.qa_container = widgets.VBox([])
        self.qa_container.layout.display = "none"

        self.explain_container = widgets.Output()
        self.explain_container.layout.display = "none"

        self.examples_container = widgets.Output()
        self.examples_container.layout.display = "none"

        # НОВОЕ: Контейнер для контрольных заданий
        self.control_tasks_container = widgets.Output()
        self.control_tasks_container.layout.display = "none"

        # Создаем кнопки навигации с НОВЫМИ обработчиками
        navigation_buttons = self._create_enhanced_navigation_buttons(
            section_id, topic_id, lesson_id
        )

        # Создаем улучшенную форму для вопросов
        self._setup_enhanced_qa_container(self.qa_container)

        # Собираем весь интерфейс
        form = widgets.VBox(
            [
                nav_info,
                lesson_header,
                time_info,
                features_info,  # НОВОЕ: Информация о возможностях
                progress_container,
                lesson_content,
                navigation_buttons,
                self.qa_container,
                self.explain_container,
                self.examples_container,
                self.control_tasks_container,  # НОВОЕ: Контейнер контрольных заданий
            ]
        )

        return form

    def _create_features_info(self):
        """
        НОВОЕ: Создает информационный блок о доступных интерактивных возможностях.

        Returns:
            widgets.HTML: Информационный блок
        """
        features = []

        if DEMO_CELLS_AVAILABLE:
            features.append(
                "🚀 <strong>Интерактивные примеры:</strong> Примеры кода можно выполнять"
            )

        if self.current_control_tasks:
            features.append(
                f"📝 <strong>Контрольные задания:</strong> {len(self.current_control_tasks)} заданий для проверки знаний"
            )

        if not features:
            return widgets.HTML(value="")

        features_html = "<br>".join(features)

        return widgets.HTML(
            value=f"""
            <div style="background-color: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 6px; padding: 10px; margin: 10px 0;">
                {features_html}
            </div>
            """
        )

    def _create_enhanced_navigation_buttons(self, section_id, topic_id, lesson_id):
        """
        МОДИФИЦИРОВАНО: Создает кнопки навигации с контрольными заданиями.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            widgets.HBox: Контейнер с кнопками навигации
        """
        # Создаем основные кнопки
        back_button = widgets.Button(
            description="Назад",
            button_style="info",
            icon="arrow-left",
            tooltip="Вернуться к выбору курса",
        )

        ask_button = widgets.Button(
            description="Задать вопрос",
            button_style="warning",
            icon="question",
            tooltip="Задать вопрос по материалу урока",
        )

        explain_button = widgets.Button(
            description="Объясни подробнее",
            button_style="success",
            icon="info",
            tooltip="Получить подробное объяснение",
        )

        examples_button = widgets.Button(
            description="Дополнительные примеры",
            button_style="primary",
            icon="code",
            tooltip="Получить дополнительные интерактивные примеры",
        )

        # НОВОЕ: Кнопка контрольных заданий (показывается только если есть задания)
        control_tasks_button = None
        if self.current_control_tasks and len(self.current_control_tasks) > 0:
            control_tasks_button = widgets.Button(
                description="Выполнить контрольное задание",
                button_style="danger",
                icon="pencil",
                tooltip=f"Выполнить {len(self.current_control_tasks)} контрольных заданий",
            )

        test_button = widgets.Button(
            description="Пройти тест",
            button_style="danger",
            icon="check",
            tooltip="Проверить знания по уроку",
        )

        # ОБРАБОТЧИКИ КНОПОК
        def on_back_button_clicked(b):
            self._clear_lesson_cache()  # НОВОЕ: Очищаем кэш при выходе
            clear_output(wait=True)
            from interface import Interface

            interface = Interface(
                self.state_manager,
                self.content_generator,
                self.system_logger,
                self.assessment,
            )
            display(interface.show_course_selection())

        def on_test_button_clicked(b):
            clear_output(wait=True)
            from interface import Interface

            interface = Interface(
                self.state_manager,
                self.content_generator,
                self.system_logger,
                self.assessment,
            )
            display(interface.show_assessment())

        def on_ask_button_clicked(b):
            # Скрываем другие контейнеры
            self.explain_container.layout.display = "none"
            self.examples_container.layout.display = "none"
            self.control_tasks_container.layout.display = "none"  # НОВОЕ

            # Показываем форму вопроса
            self.qa_container.layout.display = "block"

        def on_explain_button_clicked(b):
            # Скрываем другие контейнеры
            self.qa_container.layout.display = "none"
            self.examples_container.layout.display = "none"
            self.control_tasks_container.layout.display = "none"  # НОВОЕ

            # Показываем объяснение
            self.explain_container.layout.display = "block"
            self._show_explanation_choice()

        def on_examples_button_clicked(b):
            # Скрываем другие контейнеры
            self.qa_container.layout.display = "none"
            self.explain_container.layout.display = "none"
            self.control_tasks_container.layout.display = "none"  # НОВОЕ

            # Показываем дополнительные примеры
            self.examples_container.layout.display = "block"

            with self.examples_container:
                clear_output(wait=True)
                display(
                    widgets.HTML(value="<h3>Дополнительные интерактивные примеры</h3>")
                )
                display(
                    widgets.HTML(
                        value="<p><strong>Загрузка дополнительных примеров...</strong></p>"
                    )
                )

                try:
                    # МОДИФИЦИРОВАНО: Генерируем дополнительные примеры с улучшенными промптами
                    course_context = {
                        "course_title": self.current_course_info["course_title"],
                        "course_plan": self.current_course_info["course_plan"],
                        "section_title": self.current_course_info["section_title"],
                        "topic_title": self.current_course_info["topic_title"],
                    }

                    examples = self.content_generator.generate_examples(
                        lesson_data=self.current_lesson_data,
                        lesson_content=self.current_lesson_content,
                        communication_style=self.current_course_info["user_profile"][
                            "communication_style"
                        ],
                        course_context=course_context,
                    )

                    clear_output(wait=True)
                    display(
                        widgets.HTML(
                            value="<h3>Дополнительные интерактивные примеры</h3>"
                        )
                    )

                    # НОВОЕ: Интегрируем демо-ячейки и в дополнительные примеры
                    if DEMO_CELLS_AVAILABLE:
                        try:
                            examples = self.demo_cells_integration.integrate_demo_cells_in_lesson(
                                examples, f"{self.current_lesson_id}_additional"
                            )
                        except Exception as demo_error:
                            self.logger.error(
                                f"Ошибка интеграции демо-ячеек в примеры: {str(demo_error)}"
                            )

                    display(widgets.HTML(value=f"<div>{examples}</div>"))

                    # Кнопка закрытия примеров
                    close_button = widgets.Button(
                        description="Закрыть примеры", button_style="primary"
                    )

                    def on_close_button_clicked(b):
                        self.examples_container.layout.display = "none"

                    close_button.on_click(on_close_button_clicked)
                    display(close_button)

                except Exception as e:
                    clear_output(wait=True)
                    display(widgets.HTML(value="<h3>Ошибка при загрузке примеров</h3>"))
                    display(
                        widgets.HTML(
                            value=f"<p style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px;'>Не удалось сгенерировать примеры: {str(e)}</p>"
                        )
                    )

                    close_button = widgets.Button(
                        description="Закрыть", button_style="primary"
                    )

                    def on_close_button_clicked(b):
                        self.examples_container.layout.display = "none"

                    close_button.on_click(on_close_button_clicked)
                    display(close_button)

        # НОВОЕ: Обработчик кнопки контрольных заданий
        def on_control_tasks_button_clicked(b):
            # Скрываем другие контейнеры
            self.qa_container.layout.display = "none"
            self.explain_container.layout.display = "none"
            self.examples_container.layout.display = "none"

            # Показываем контрольные задания
            self.control_tasks_container.layout.display = "block"
            self._show_control_tasks()

        # Привязываем обработчики к кнопкам
        back_button.on_click(on_back_button_clicked)
        test_button.on_click(on_test_button_clicked)
        ask_button.on_click(on_ask_button_clicked)
        explain_button.on_click(on_explain_button_clicked)
        examples_button.on_click(on_examples_button_clicked)

        if control_tasks_button:
            control_tasks_button.on_click(on_control_tasks_button_clicked)

        # НОВОЕ: Создаем контейнер кнопок с учетом контрольных заданий
        if control_tasks_button:
            # Если есть контрольные задания - две строки кнопок
            return widgets.VBox(
                [
                    widgets.HBox([back_button, ask_button, explain_button]),
                    widgets.HBox([examples_button, control_tasks_button, test_button]),
                ]
            )
        else:
            # Если нет контрольных заданий - одна строка
            return widgets.HBox(
                [back_button, ask_button, explain_button, examples_button, test_button]
            )

    def _show_control_tasks(self):
        """
        НОВОЕ: Показывает интерфейс контрольных заданий.
        """
        with self.control_tasks_container:
            clear_output(wait=True)

            if not self.current_control_tasks:
                display(widgets.HTML(value="<h3>Контрольные задания</h3>"))
                display(
                    widgets.HTML(
                        value="<p>Контрольные задания для этого урока недоступны.</p>"
                    )
                )

                close_button = widgets.Button(
                    description="Закрыть", button_style="primary"
                )

                def on_close(b):
                    self.control_tasks_container.layout.display = "none"

                close_button.on_click(on_close)
                display(close_button)
                return

            # Заголовок
            display(widgets.HTML(value="<h3>📝 Контрольные задания</h3>"))
            display(
                widgets.HTML(
                    value=f"<p>Выполните {len(self.current_control_tasks)} контрольных заданий для закрепления изученного материала.</p>"
                )
            )

            # Создаем интерактивные ячейки для каждого задания
            for i, task in enumerate(self.current_control_tasks):
                try:
                    if INTERACTIVE_CELLS_AVAILABLE:
                        # Создаем интерактивную ячейку
                        interactive_cell = create_interactive_cell(
                            task_description=task["description"],
                            expected_result=task.get("expected_result"),
                            check_type=task.get("check_type", "exact"),
                            initial_code=task.get("initial_code", "# Ваш код здесь\n"),
                            cell_id=f"{self.current_lesson_id}_task_{i+1}",
                            title=task["title"],
                            description=f"Контрольное задание #{i+1}",
                            max_attempts=task.get("max_attempts"),
                            show_solution=task.get("show_solution", False),
                            solution_code=task.get("solution_code", ""),
                        )

                        display(interactive_cell)

                    else:
                        # Fallback - показываем задание как HTML
                        task_html = f"""
                        <div style="border: 2px solid #dc3545; border-radius: 8px; margin: 15px 0; padding: 15px; background-color: #fff5f5;">
                            <h4 style="color: #dc3545; margin-top: 0;">📝 {task['title']}</h4>
                            <p><strong>Описание:</strong> {task['description']}</p>
                            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0;">
                                <strong>Начальный код:</strong>
                                <pre style="margin: 5px 0;"><code>{task.get('initial_code', '# Ваш код здесь')}</code></pre>
                            </div>
                            <p><em>Интерактивные ячейки недоступны. Скопируйте код в Jupyter Notebook для выполнения.</em></p>
                        </div>
                        """
                        display(widgets.HTML(value=task_html))

                except Exception as cell_error:
                    self.logger.error(
                        f"Ошибка создания ячейки для задания {i+1}: {str(cell_error)}"
                    )
                    # Показываем ошибку пользователю
                    error_html = f"""
                    <div style="border: 1px solid #dc3545; border-radius: 4px; padding: 10px; margin: 10px 0; background-color: #f8d7da;">
                        <strong>Ошибка задания #{i+1}:</strong> {task.get('title', 'Контрольное задание')}<br>
                        <em>Не удалось создать интерактивную ячейку: {str(cell_error)}</em>
                    </div>
                    """
                    display(widgets.HTML(value=error_html))

            # Кнопки управления
            buttons_container = widgets.HBox([])

            # Кнопка проверки общего результата (будет добавлена в следующем этапе)
            check_progress_button = widgets.Button(
                description="Проверить прогресс",
                button_style="success",
                icon="check",
                tooltip="Проверить выполнение всех заданий",
            )

            close_tasks_button = widgets.Button(
                description="Закрыть задания", button_style="primary", icon="times"
            )

            def on_check_progress(b):
                # TODO: Будет реализовано в следующем этапе
                # Проверка выполнения всех контрольных заданий
                display(
                    widgets.HTML(
                        value="<p style='color: #0c5460; background-color: #d1ecf1; padding: 10px; border-radius: 5px; margin: 10px 0;'>Функция проверки прогресса будет доступна в следующем обновлении.</p>"
                    )
                )

            def on_close_tasks(b):
                self.control_tasks_container.layout.display = "none"

            check_progress_button.on_click(on_check_progress)
            close_tasks_button.on_click(on_close_tasks)

            buttons_container.children = [check_progress_button, close_tasks_button]
            display(buttons_container)

    # ========================================
    # ОСТАЛЬНЫЕ МЕТОДЫ (без изменений)
    # ========================================

    def _show_explanation_choice(self):
        """
        Показывает выбор типа объяснения.
        """
        with self.explain_container:
            clear_output(wait=True)

            # Заголовок
            display(widgets.HTML(value="<h3>Выберите тип объяснения</h3>"))

            # Кнопки выбора
            simple_button = widgets.Button(
                description="Простое объяснение",
                button_style="success",
                icon="lightbulb-o",
                layout=widgets.Layout(width="200px", margin="5px"),
            )

            detailed_button = widgets.Button(
                description="Подробное объяснение",
                button_style="info",
                icon="book",
                layout=widgets.Layout(width="200px", margin="5px"),
            )

            analogy_button = widgets.Button(
                description="Объяснение с примерами",
                button_style="warning",
                icon="puzzle-piece",
                layout=widgets.Layout(width="200px", margin="5px"),
            )

            close_button = widgets.Button(
                description="Закрыть",
                button_style="primary",
                icon="times",
                layout=widgets.Layout(width="200px", margin="5px"),
            )

            def on_explanation_type_selected(explanation_type):
                """Обработчик выбора типа объяснения."""
                with self.explain_container:
                    clear_output(wait=True)
                    display(widgets.HTML(value=f"<h3>{explanation_type}</h3>"))
                    display(
                        widgets.HTML(
                            value="<p><strong>Генерация объяснения...</strong></p>"
                        )
                    )

                    try:
                        explanation = self.content_generator.generate_explanation(
                            lesson_data=self.current_lesson_data,
                            lesson_content=self.current_lesson_content,
                            explanation_type=explanation_type.lower().replace(" ", "_"),
                            communication_style=self.current_course_info[
                                "user_profile"
                            ]["communication_style"],
                        )

                        clear_output(wait=True)
                        display(widgets.HTML(value=f"<h3>{explanation_type}</h3>"))
                        display(widgets.HTML(value=f"<div>{explanation}</div>"))

                        # Кнопка закрытия
                        close_button_final = widgets.Button(
                            description="Закрыть объяснение", button_style="primary"
                        )

                        def on_close_final(b):
                            self.explain_container.layout.display = "none"

                        close_button_final.on_click(on_close_final)
                        display(close_button_final)

                    except Exception as e:
                        clear_output(wait=True)
                        display(
                            widgets.HTML(
                                value="<h3>Ошибка при генерации объяснения</h3>"
                            )
                        )
                        display(
                            widgets.HTML(
                                value=f"<p style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px;'>Не удалось сгенерировать объяснение: {str(e)}</p>"
                            )
                        )

                        error_close_button = widgets.Button(
                            description="Закрыть", button_style="primary"
                        )

                        def on_error_close(b):
                            self.explain_container.layout.display = "none"

                        error_close_button.on_click(on_error_close)
                        display(error_close_button)

            # Обработчики кнопок
            simple_button.on_click(
                lambda b: on_explanation_type_selected("Простое объяснение")
            )
            detailed_button.on_click(
                lambda b: on_explanation_type_selected("Подробное объяснение")
            )
            analogy_button.on_click(
                lambda b: on_explanation_type_selected("Объяснение с примерами")
            )

            def on_close(b):
                self.explain_container.layout.display = "none"

            close_button.on_click(on_close)

            # Отображаем кнопки
            buttons_container = widgets.VBox(
                [
                    widgets.HBox([simple_button, detailed_button]),
                    widgets.HBox([analogy_button, close_button]),
                ]
            )

            display(buttons_container)

    def _setup_enhanced_qa_container(self, qa_container):
        """
        Настраивает улучшенный контейнер для вопросов и ответов.

        Args:
            qa_container: Контейнер для Q&A интерфейса
        """
        # Заголовок
        header = widgets.HTML(value="<h3>Задать вопрос по уроку</h3>")

        # Поле для ввода вопроса
        question_input = widgets.Textarea(
            placeholder="Введите ваш вопрос по материалу урока...",
            description="Вопрос:",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="100%", height="100px"),
        )

        # Кнопки
        submit_button = widgets.Button(
            description="Отправить вопрос", button_style="success", icon="paper-plane"
        )

        close_qa_button = widgets.Button(
            description="Закрыть", button_style="primary", icon="times"
        )

        # Контейнер для ответа
        answer_container = widgets.Output()

        def on_submit_question(b):
            """Обработчик отправки вопроса."""
            question = question_input.value.strip()

            if not question:
                with answer_container:
                    clear_output(wait=True)
                    display(
                        widgets.HTML(
                            value="<p style='color: #856404; background-color: #fff3cd; padding: 10px; border-radius: 5px;'>Пожалуйста, введите вопрос.</p>"
                        )
                    )
                return

            with answer_container:
                clear_output(wait=True)
                display(
                    widgets.HTML(
                        value="<p><strong>Поиск ответа на ваш вопрос...</strong></p>"
                    )
                )

            try:
                answer = self.content_generator.generate_qa_response(
                    lesson_data=self.current_lesson_data,
                    lesson_content=self.current_lesson_content,
                    question=question,
                    communication_style=self.current_course_info["user_profile"][
                        "communication_style"
                    ],
                )

                with answer_container:
                    clear_output(wait=True)
                    display(widgets.HTML(value="<h4>Ответ:</h4>"))
                    display(widgets.HTML(value=f"<div>{answer}</div>"))

                # Очищаем поле вопроса после успешного ответа
                question_input.value = ""

            except Exception as e:
                with answer_container:
                    clear_output(wait=True)
                    display(
                        widgets.HTML(
                            value=f"<p style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px;'>Ошибка при генерации ответа: {str(e)}</p>"
                        )
                    )

        def on_close_qa(b):
            """Обработчик закрытия Q&A."""
            qa_container.layout.display = "none"
            # Очищаем содержимое при закрытии
            question_input.value = ""
            with answer_container:
                clear_output(wait=True)

        # Привязка обработчиков
        submit_button.on_click(on_submit_question)
        close_qa_button.on_click(on_close_qa)

        # Заполняем контейнер
        qa_container.children = [
            header,
            question_input,
            widgets.HBox([submit_button, close_qa_button]),
            answer_container,
        ]

    def _create_lesson_error_interface(self, title, message):
        """
        Создает интерфейс ошибки урока.

        Args:
            title (str): Заголовок ошибки
            message (str): Сообщение об ошибке

        Returns:
            widgets.VBox: Интерфейс ошибки
        """
        error_header = self.utils.create_header(title)
        error_message = self.utils.create_styled_message(message, "incorrect")

        back_button = widgets.Button(
            description="Вернуться к выбору курса",
            button_style="primary",
            icon="arrow-left",
        )

        def go_back_to_courses(b):
            self._clear_lesson_cache()  # НОВОЕ: Очищаем кэш при ошибке
            clear_output(wait=True)
            from interface import Interface

            interface = Interface(
                self.state_manager,
                self.content_generator,
                self.system_logger,
                self.assessment,
            )
            display(interface.show_course_selection())

        back_button.on_click(go_back_to_courses)

        return widgets.VBox([error_header, error_message, back_button])

    # ========================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ========================================

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

    def _get_element_titles_from_plan(
        self, course_plan, section_id, topic_id, lesson_id
    ):
        """
        Получает названия элементов из плана курса.

        Returns:
            tuple: (section_title, topic_title, lesson_title)
        """
        section_title = "Раздел"
        topic_title = "Тема"
        lesson_title = "Урок"

        for section in course_plan.get("sections", []):
            if section.get("id") == section_id:
                section_title = (
                    section.get("title")
                    or section.get("name")
                    or section.get("id")
                    or "Раздел"
                )
                for topic in section.get("topics", []):
                    if topic.get("id") == topic_id:
                        topic_title = (
                            topic.get("title")
                            or topic.get("name")
                            or topic.get("id")
                            or "Тема"
                        )
                        for lesson in topic.get("lessons", []):
                            if lesson.get("id") == lesson_id:
                                lesson_title = (
                                    lesson.get("title")
                                    or lesson.get("name")
                                    or lesson.get("id")
                                    or "Урок"
                                )
                                break
                        break
                break

        return section_title, topic_title, lesson_title

    def _get_course_id(self, course_plan):
        """
        Получает ID курса из плана курса.

        Args:
            course_plan (dict): План курса

        Returns:
            str: ID курса
        """
        return course_plan.get("id", course_plan.get("title", "default_course"))
