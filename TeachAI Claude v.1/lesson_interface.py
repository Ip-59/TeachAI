"""
Интерфейс для отображения уроков и интерактивных функций.
Отвечает за показ содержания урока, примеров, объяснений и обработку вопросов пользователя.
ИСПРАВЛЕНО: Проблема #89 - добавлено кэширование содержания урока
ИСПРАВЛЕНО: Проблема #90 - убран course_context из generate_examples()
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
import traceback
from interface_utils import InterfaceUtils, InterfaceState


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

        # ИСПРАВЛЕНО: Добавлено кэширование содержания урока (проблема #89)
        self.cached_lesson_content = None
        self.cached_lesson_title = None
        self.current_lesson_cache_key = None  # Для идентификации текущего урока

        # ИСПРАВЛЕНО: Ссылки на контейнеры для правильного закрытия
        self.explain_container = None
        self.examples_container = None
        self.qa_container = None

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
            # ИСПРАВЛЕНО: Создаем ключ кэша для текущего урока
            cache_key = f"{section_id}:{topic_id}:{lesson_id}"

            # Получаем данные о курсе и уроке из учебного плана
            course_plan = self.state_manager.get_course_plan()
            lesson_data = self.state_manager.get_lesson_data(
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
            ) = self._get_element_titles(course_plan, section_id, topic_id, lesson_id)

            # Получаем профиль пользователя для генерации урока
            user_profile = self.state_manager.get_user_profile()

            # ИСПРАВЛЕНО: Проверяем кэш содержания урока
            if (
                self.current_lesson_cache_key == cache_key
                and self.cached_lesson_content is not None
                and self.cached_lesson_title is not None
            ):
                self.logger.info(
                    f"Используется кэшированное содержание урока '{lesson_title}'"
                )
                lesson_content_data = {
                    "title": self.cached_lesson_title,
                    "content": self.cached_lesson_content,
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

                    lesson_content_data = self.content_generator.generate_lesson(
                        course=course_title,
                        section=section_title,
                        topic=topic_title,
                        lesson=lesson_title,
                        user_name=user_profile["name"],
                        communication_style=user_profile["communication_style"],
                    )

                    # ИСПРАВЛЕНО: Кэшируем сгенерированное содержание
                    self.cached_lesson_content = lesson_content_data["content"]
                    self.cached_lesson_title = lesson_content_data["title"]
                    self.current_lesson_cache_key = cache_key

                    self.logger.info("Урок успешно сгенерирован и закэширован")

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
        Создает полный интерфейс урока.

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

        # Содержание урока
        lesson_content = widgets.HTML(
            value=f"<div>{lesson_content_data['content']}</div>"
        )

        # ИСПРАВЛЕНО: Создаем контейнеры и сохраняем ссылки на них
        self.qa_container = widgets.VBox([])
        self.qa_container.layout.display = "none"

        self.explain_container = widgets.Output()
        self.explain_container.layout.display = "none"

        self.examples_container = widgets.Output()
        self.examples_container.layout.display = "none"

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
                progress_container,
                lesson_content,
                navigation_buttons,
                self.qa_container,
                self.explain_container,
                self.examples_container,
            ]
        )

        return form

    def _create_enhanced_navigation_buttons(self, section_id, topic_id, lesson_id):
        """
        Создает кнопки навигации с улучшенными обработчиками.

        Args:
            section_id, topic_id, lesson_id (str): ID элементов

        Returns:
            widgets.HBox: Контейнер с кнопками
        """
        # Основные кнопки навигации
        back_button = widgets.Button(
            description="Назад",
            button_style="info",
            tooltip="Вернуться к выбору курса",
            icon="arrow-left",
        )

        test_button = widgets.Button(
            description="Пройти тест",
            button_style="success",
            tooltip="Проверить знания по этому уроку",
            icon="check",
        )

        # Интерактивные кнопки
        ask_button = widgets.Button(
            description="Задать вопрос",
            button_style="warning",
            tooltip="Задать вопрос по уроку",
            icon="question",
        )

        explain_button = widgets.Button(
            description="Объясни подробнее",
            button_style="info",
            tooltip="Получить более подробное объяснение материала",
            icon="info",
        )

        examples_button = widgets.Button(
            description="Приведи примеры",
            button_style="info",
            tooltip="Показать практические примеры по материалу",
            icon="file-code",
        )

        # Привязываем обработчики событий
        def on_back_button_clicked(b):
            # ИСПРАВЛЕНО: Очищаем кэш при переходе к выбору курса
            self._clear_lesson_cache()
            clear_output(wait=True)
            from setup_interface import SetupInterface

            setup_ui = SetupInterface(
                self.state_manager,
                self.content_generator,
                self.system_logger,
                self.assessment,
            )
            display(setup_ui.show_course_selection())

        def on_test_button_clicked(b):
            clear_output(wait=True)
            from assessment_interface import AssessmentInterface

            assessment_ui = AssessmentInterface(
                self.state_manager, self.assessment, self.system_logger
            )

            # Получаем текущие данные
            course_plan = self.state_manager.get_course_plan()
            course_id = course_plan.get("id", "unknown-course")

            display(
                assessment_ui.show_assessment(
                    course_id,
                    section_id,
                    topic_id,
                    lesson_id,
                    self.current_lesson_content,
                )
            )

        def on_ask_button_clicked(b):
            # Скрываем другие контейнеры
            self.explain_container.layout.display = "none"
            self.examples_container.layout.display = "none"
            # Показываем контейнер вопросов
            self.qa_container.layout.display = "flex"

        def on_explain_button_clicked(b):
            # НОВАЯ ЛОГИКА: Показываем выбор типа объяснения
            # Скрываем другие контейнеры
            self.qa_container.layout.display = "none"
            self.examples_container.layout.display = "none"

            # Показываем контейнер выбора типа объяснения
            self.explain_container.layout.display = "block"

            with self.explain_container:
                clear_output(wait=True)
                self._show_explanation_choice()

        def on_examples_button_clicked(b):
            # Скрываем другие контейнеры
            self.qa_container.layout.display = "none"
            self.explain_container.layout.display = "none"

            # Показываем примеры
            self.examples_container.layout.display = "block"

            with self.examples_container:
                clear_output(wait=True)
                display(widgets.HTML(value="<h3>Практические примеры</h3>"))
                display(
                    widgets.HTML(
                        value="<p><strong>Загрузка практических примеров...</strong></p>"
                    )
                )

                try:
                    # ИСПРАВЛЕНО: Убран course_context из вызова generate_examples (проблема #90)
                    examples = self.content_generator.generate_examples(
                        lesson_data=self.current_lesson_data,
                        lesson_content=self.current_lesson_content,
                        communication_style=self.current_course_info["user_profile"][
                            "communication_style"
                        ],
                    )

                    clear_output(wait=True)
                    display(widgets.HTML(value="<h3>Практические примеры</h3>"))
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

        # Привязываем обработчики к кнопкам
        back_button.on_click(on_back_button_clicked)
        test_button.on_click(on_test_button_clicked)
        ask_button.on_click(on_ask_button_clicked)
        explain_button.on_click(on_explain_button_clicked)
        examples_button.on_click(on_examples_button_clicked)

        return widgets.HBox(
            [back_button, ask_button, explain_button, examples_button, test_button]
        )

    def _show_explanation_choice(self):
        """
        НОВАЯ ЛОГИКА: Показывает выбор типа объяснения.
        """
        display(widgets.HTML(value="<h3>Подробное объяснение</h3>"))
        display(widgets.HTML(value="<p>Выберите тип объяснения:</p>"))

        # Кнопки выбора
        full_explanation_button = widgets.Button(
            description="Подробное пояснение всего урока",
            button_style="primary",
            layout=widgets.Layout(width="300px", margin="5px"),
        )

        concepts_explanation_button = widgets.Button(
            description="Пояснение отдельных понятий",
            button_style="info",
            layout=widgets.Layout(width="300px", margin="5px"),
        )

        close_button = widgets.Button(
            description="Закрыть",
            button_style="info",
            layout=widgets.Layout(width="100px", margin="5px"),
        )

        def on_full_explanation_clicked(b):
            clear_output(wait=True)
            display(widgets.HTML(value="<h3>Подробное объяснение урока</h3>"))
            display(
                widgets.HTML(
                    value="<p><strong>Генерация подробного объяснения урока (в 2 раза объемнее)...</strong></p>"
                )
            )

            try:
                # Генерируем подробное объяснение всего урока
                explanation = self.content_generator.get_detailed_explanation(
                    course=self.current_course_info["course_title"],
                    section=self.current_course_info["section_title"],
                    topic=self.current_course_info["topic_title"],
                    lesson=self.current_course_info["lesson_title"],
                    lesson_content=self.current_lesson_content,
                    communication_style=self.current_course_info["user_profile"][
                        "communication_style"
                    ],
                )

                clear_output(wait=True)
                display(widgets.HTML(value="<h3>Подробное объяснение урока</h3>"))
                display(widgets.HTML(value=f"<div>{explanation}</div>"))

                # ИСПРАВЛЕНО: Рабочая кнопка закрытия - использует кэшированное содержание
                close_button = widgets.Button(
                    description="Закрыть объяснение", button_style="primary"
                )

                def on_close_clicked(b):
                    # ИСПРАВЛЕНО: Используем кэшированное содержание вместо повторной генерации
                    clear_output(wait=True)
                    lesson_widget = self.show_lesson(
                        self.current_course_info["section_id"],
                        self.current_course_info["topic_id"],
                        self.current_course_info["lesson_id"],
                    )
                    display(lesson_widget)

                close_button.on_click(on_close_clicked)
                display(close_button)

            except Exception as e:
                clear_output(wait=True)
                display(widgets.HTML(value="<h3>Ошибка при генерации объяснения</h3>"))
                display(
                    widgets.HTML(
                        value=f"<p style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px;'>Ошибка: {str(e)}</p>"
                    )
                )

        def on_concepts_explanation_clicked(b):
            clear_output(wait=True)
            display(widgets.HTML(value="<h3>Ключевые понятия урока</h3>"))
            display(
                widgets.HTML(
                    value="<p><strong>Извлечение ключевых понятий...</strong></p>"
                )
            )

            try:
                # Извлекаем ключевые понятия
                concepts = self.content_generator.extract_key_concepts(
                    self.current_lesson_content, self.current_lesson_data
                )

                clear_output(wait=True)
                display(
                    widgets.HTML(
                        value="<h3>Выберите понятие для подробного изучения</h3>"
                    )
                )

                # Создаем кнопки для каждого понятия
                for concept in concepts:
                    concept_button = widgets.Button(
                        description=concept["name"],
                        button_style="info",
                        tooltip=concept["brief_description"],
                        layout=widgets.Layout(width="400px", margin="3px"),
                    )

                    def create_concept_handler(concept_data):
                        def handle_concept_click(b):
                            self._show_concept_explanation(concept_data)

                        return handle_concept_click

                    concept_button.on_click(create_concept_handler(concept))
                    display(concept_button)

                # Кнопка назад
                back_button = widgets.Button(
                    description="Назад к выбору", button_style="info"
                )

                def on_back_clicked(b):
                    clear_output(wait=True)
                    self._show_explanation_choice()

                back_button.on_click(on_back_clicked)
                display(back_button)

            except Exception as e:
                clear_output(wait=True)
                display(widgets.HTML(value="<h3>Ошибка при извлечении понятий</h3>"))
                display(
                    widgets.HTML(
                        value=f"<p style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px;'>Ошибка: {str(e)}</p>"
                    )
                )

        def on_close_clicked(b):
            # ИСПРАВЛЕНО: Используем кэшированное содержание
            clear_output(wait=True)
            lesson_widget = self.show_lesson(
                self.current_course_info["section_id"],
                self.current_course_info["topic_id"],
                self.current_course_info["lesson_id"],
            )
            display(lesson_widget)

        full_explanation_button.on_click(on_full_explanation_clicked)
        concepts_explanation_button.on_click(on_concepts_explanation_clicked)
        close_button.on_click(on_close_clicked)

        display(
            widgets.VBox(
                [full_explanation_button, concepts_explanation_button, close_button]
            )
        )

    def _show_concept_explanation(self, concept):
        """
        НОВАЯ ЛОГИКА: Показывает объяснение выбранного понятия.

        Args:
            concept (dict): Данные о понятии
        """
        clear_output(wait=True)
        display(widgets.HTML(value=f"<h3>Понятие: {concept['name']}</h3>"))
        display(
            widgets.HTML(
                value="<p><strong>Генерация подробного объяснения понятия...</strong></p>"
            )
        )

        try:
            # Генерируем объяснение понятия
            explanation = self.content_generator.explain_concept(
                concept,
                self.current_lesson_content,
                self.current_course_info["user_profile"]["communication_style"],
            )

            clear_output(wait=True)
            display(widgets.HTML(value=f"<h3>Понятие: {concept['name']}</h3>"))
            display(widgets.HTML(value=f"<div>{explanation}</div>"))

            # Кнопки навигации
            back_button = widgets.Button(
                description="Назад к понятиям", button_style="info"
            )
            close_button = widgets.Button(description="Закрыть", button_style="primary")

            def on_back_clicked(b):
                # Возвращаемся к списку понятий
                clear_output(wait=True)
                display(widgets.HTML(value="<h3>Ключевые понятия урока</h3>"))
                display(
                    widgets.HTML(
                        value="<p><strong>Загрузка списка понятий...</strong></p>"
                    )
                )

                # Повторно загружаем понятия
                try:
                    concepts = self.content_generator.extract_key_concepts(
                        self.current_lesson_content, self.current_lesson_data
                    )

                    clear_output(wait=True)
                    display(
                        widgets.HTML(
                            value="<h3>Выберите понятие для подробного изучения</h3>"
                        )
                    )

                    for concept in concepts:
                        concept_button = widgets.Button(
                            description=concept["name"],
                            button_style="info",
                            tooltip=concept["brief_description"],
                            layout=widgets.Layout(width="400px", margin="3px"),
                        )

                        def create_concept_handler(concept_data):
                            def handle_concept_click(b):
                                self._show_concept_explanation(concept_data)

                            return handle_concept_click

                        concept_button.on_click(create_concept_handler(concept))
                        display(concept_button)

                    # Кнопка назад к выбору типа
                    back_to_choice_button = widgets.Button(
                        description="Назад к выбору", button_style="info"
                    )

                    def on_back_to_choice_clicked(b):
                        clear_output(wait=True)
                        self._show_explanation_choice()

                    back_to_choice_button.on_click(on_back_to_choice_clicked)
                    display(back_to_choice_button)

                except Exception as e:
                    clear_output(wait=True)
                    display(widgets.HTML(value="<h3>Ошибка при загрузке понятий</h3>"))
                    display(
                        widgets.HTML(
                            value=f"<p style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px;'>Ошибка: {str(e)}</p>"
                        )
                    )

            def on_close_clicked(b):
                # ИСПРАВЛЕНО: Используем кэшированное содержание
                clear_output(wait=True)
                lesson_widget = self.show_lesson(
                    self.current_course_info["section_id"],
                    self.current_course_info["topic_id"],
                    self.current_course_info["lesson_id"],
                )
                display(lesson_widget)

            back_button.on_click(on_back_clicked)
            close_button.on_click(on_close_clicked)
            display(widgets.HBox([back_button, close_button]))

        except Exception as e:
            clear_output(wait=True)
            display(
                widgets.HTML(
                    value=f"<h3>Ошибка при объяснении понятия: {concept['name']}</h3>"
                )
            )
            display(
                widgets.HTML(
                    value=f"<p style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px;'>Ошибка: {str(e)}</p>"
                )
            )

    def _clear_lesson_cache(self):
        """
        НОВОЕ: Очищает кэш содержания урока.
        """
        self.cached_lesson_content = None
        self.cached_lesson_title = None
        self.current_lesson_cache_key = None
        self.logger.info("Кэш содержания урока очищен")

    def _setup_enhanced_qa_container(self, qa_container):
        """
        НОВАЯ ЛОГИКА: Настраивает улучшенный контейнер для вопросов и ответов с проверкой релевантности.

        Args:
            qa_container (widgets.VBox): Контейнер для Q&A
        """
        # Текстовое поле для вопроса
        question_input = widgets.Text(
            placeholder="Введите ваш вопрос здесь", layout=widgets.Layout(width="80%")
        )

        # Кнопка отправки вопроса
        send_question_button = widgets.Button(
            description="Отправить",
            button_style="primary",
            tooltip="Отправить вопрос",
            icon="paper-plane",
        )

        # Контейнер для вопроса
        question_container = widgets.HBox([question_input, send_question_button])

        # Контейнер для ответа
        answer_output = widgets.Output()

        # НОВАЯ ЛОГИКА: Улучшенный обработчик отправки вопроса с проверкой релевантности
        def on_send_question_button_clicked(b):
            question = question_input.value.strip()
            if not question:
                return

            with answer_output:
                clear_output(wait=True)
                display(
                    widgets.HTML(
                        value=f"<p><strong>Ваш вопрос:</strong> {question}</p>"
                    )
                )
                display(
                    widgets.HTML(
                        value=f"<p><strong>Анализ вопроса и подготовка ответа...</strong></p>"
                    )
                )

            try:
                # НОВОЕ: Увеличиваем счетчик вопросов
                questions_count = self.state_manager.increment_questions_count(
                    self.current_lesson_id
                )

                # НОВОЕ: Проверяем релевантность вопроса
                relevance_result = self.content_generator.check_question_relevance(
                    question, self.current_lesson_content, self.current_lesson_data
                )

                with answer_output:
                    clear_output(wait=True)
                    display(
                        widgets.HTML(
                            value=f"<p><strong>Ваш вопрос:</strong> {question}</p>"
                        )
                    )

                    # НОВОЕ: Если вопрос нерелевантен
                    if not relevance_result["is_relevant"]:
                        non_relevant_response = (
                            self.content_generator.generate_non_relevant_response(
                                question, relevance_result["suggestions"]
                            )
                        )
                        display(widgets.HTML(value=non_relevant_response))
                    else:
                        # Вопрос релевантен - генерируем ответ
                        display(
                            widgets.HTML(
                                value=f"<p><strong>Генерация ответа...</strong></p>"
                            )
                        )

                        answer = self.content_generator.answer_question(
                            course=self.current_course_info["course_title"],
                            section=self.current_course_info["section_title"],
                            topic=self.current_course_info["topic_title"],
                            lesson=self.current_course_info["lesson_title"],
                            user_question=question,
                            lesson_content=self.current_lesson_content,
                            user_name=self.current_course_info["user_profile"]["name"],
                            communication_style=self.current_course_info[
                                "user_profile"
                            ]["communication_style"],
                        )

                        # Логируем вопрос и ответ
                        self.system_logger.log_question(question, answer)

                        clear_output(wait=True)
                        display(
                            widgets.HTML(
                                value=f"<p><strong>Ваш вопрос:</strong> {question}</p>"
                            )
                        )
                        display(
                            widgets.HTML(
                                value=f"<div><strong>Ответ:</strong><br/>{answer}</div>"
                            )
                        )

                        # НОВОЕ: Проверяем количество вопросов и показываем предупреждение
                        if questions_count > 3:
                            warning = self.content_generator.generate_multiple_questions_warning(
                                questions_count
                            )
                            display(widgets.HTML(value=warning))

                # Очищаем поле ввода
                question_input.value = ""

            except Exception as e:
                with answer_output:
                    clear_output(wait=True)
                    display(
                        widgets.HTML(
                            value=f"<p><strong>Ваш вопрос:</strong> {question}</p>"
                        )
                    )
                    display(
                        widgets.HTML(
                            value=f"<p style='color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 5px;'>Не удалось обработать вопрос: {str(e)}</p>"
                        )
                    )

        # Привязываем обработчик к кнопке
        send_question_button.on_click(on_send_question_button_clicked)

        # Настройка qa_container
        qa_container.children = [question_container, answer_output]

    def _get_element_titles(self, course_plan, section_id, topic_id, lesson_id):
        """
        Получает названия элементов курса.

        Returns:
            tuple: (course_title, section_title, topic_title, lesson_title)
        """
        # Получаем название курса безопасно
        course_title = self.utils.get_safe_title(course_plan, "Курс")
        if not course_title or course_title == "Курс":
            learning_progress = self.state_manager.get_learning_progress()
            course_title = learning_progress.get("current_course", "Курс Python")

        # Находим названия раздела и темы
        section_title = "Раздел"
        topic_title = "Тема"
        lesson_title = "Урок"

        for section in course_plan.get("sections", []):
            if section.get("id") == section_id:
                section_title = self.utils.get_safe_title(section, "Раздел")
                for topic in section.get("topics", []):
                    if topic.get("id") == topic_id:
                        topic_title = self.utils.get_safe_title(topic, "Тема")
                        for lesson in topic.get("lessons", []):
                            if lesson.get("id") == lesson_id:
                                lesson_title = self.utils.get_safe_title(lesson, "Урок")
                                break
                        break
                break

        return course_title, section_title, topic_title, lesson_title

    def _get_course_id(self, course_plan):
        """
        Безопасно получает ID курса.

        Returns:
            str: ID курса
        """
        course_id = course_plan.get("id", "unknown-course")
        if not course_id or course_id == "unknown-course":
            learning_progress = self.state_manager.get_learning_progress()
            course_id = learning_progress.get("current_course", "python-basics")
        return course_id

    def _create_lesson_error_interface(self, title, message):
        """
        Создает интерфейс ошибки для урока.

        Returns:
            widgets.VBox: Интерфейс ошибки
        """
        error_header = self.utils.create_header(title)
        error_message = self.utils.create_styled_message(message, "incorrect")

        back_to_courses_button = widgets.Button(
            description="Вернуться к выбору курса",
            button_style="primary",
            icon="arrow-left",
        )

        def go_back_to_courses(b):
            # ИСПРАВЛЕНО: Очищаем кэш при возврате к выбору курса
            self._clear_lesson_cache()
            clear_output(wait=True)
            from setup_interface import SetupInterface

            setup_ui = SetupInterface(
                self.state_manager,
                self.content_generator,
                self.system_logger,
                self.assessment,
            )
            display(setup_ui.show_course_selection())

        back_to_courses_button.on_click(go_back_to_courses)

        return widgets.VBox([error_header, error_message, back_to_courses_button])
