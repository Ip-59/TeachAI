"""
Интерфейс для объяснений и ключевых понятий урока.
Отвечает за выбор типа объяснения, извлечение понятий и их детальное объяснение.
РЕФАКТОРИНГ: Выделен из lesson_interface.py для лучшей модульности (часть 1/3)
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging


class LessonExplanationInterface:
    """Интерфейс для объяснений и ключевых понятий урока."""

    def __init__(
        self, state_manager, content_generator, system_logger, current_course_info
    ):
        """
        Инициализация интерфейса объяснений.

        Args:
            state_manager: Менеджер состояния
            content_generator: Генератор контента
            system_logger: Системный логгер
            current_course_info: Информация о текущем курсе и уроке
        """
        self.state_manager = state_manager
        self.content_generator = content_generator
        self.system_logger = system_logger
        self.logger = logging.getLogger(__name__)

        # Данные текущего урока
        self.current_course_info = current_course_info
        self.current_lesson_data = None
        self.current_lesson_content = None

        # Устанавливаем данные урока из course_info если доступны
        if hasattr(current_course_info, "get"):
            self.current_lesson_data = current_course_info.get("lesson_data")
            self.current_lesson_content = current_course_info.get("lesson_content")

    def update_lesson_data(self, lesson_data, lesson_content):
        """
        Обновляет данные урока для объяснений.

        Args:
            lesson_data (dict): Метаданные урока
            lesson_content (str): Содержание урока
        """
        self.current_lesson_data = lesson_data
        self.current_lesson_content = lesson_content

    def show_explanation_choice(self):
        """
        Показывает выбор типа объяснения.
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

                # Рабочая кнопка закрытия - полная перерисовка урока
                close_button = widgets.Button(
                    description="Закрыть объяснение", button_style="primary"
                )

                def on_close_clicked(b):
                    self._return_to_lesson()

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
                            self.show_concept_explanation(concept_data)

                        return handle_concept_click

                    concept_button.on_click(create_concept_handler(concept))
                    display(concept_button)

                # Кнопка назад
                back_button = widgets.Button(
                    description="Назад к выбору", button_style="info"
                )

                def on_back_clicked(b):
                    clear_output(wait=True)
                    self.show_explanation_choice()

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
            self._return_to_lesson()

        full_explanation_button.on_click(on_full_explanation_clicked)
        concepts_explanation_button.on_click(on_concepts_explanation_clicked)
        close_button.on_click(on_close_clicked)

        display(
            widgets.VBox(
                [full_explanation_button, concepts_explanation_button, close_button]
            )
        )

    def show_concept_explanation(self, concept):
        """
        Показывает объяснение выбранного понятия.

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
                                self.show_concept_explanation(concept_data)

                            return handle_concept_click

                        concept_button.on_click(create_concept_handler(concept))
                        display(concept_button)

                    # Кнопка назад к выбору типа
                    back_to_choice_button = widgets.Button(
                        description="Назад к выбору", button_style="info"
                    )

                    def on_back_to_choice_clicked(b):
                        clear_output(wait=True)
                        self.show_explanation_choice()

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
                self._return_to_lesson()

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

    def _return_to_lesson(self):
        """
        Возвращается к отображению урока через полную перерисовку.
        """
        clear_output(wait=True)

        # Импортируем lesson_interface для перерисовки урока
        from lesson_interface import LessonInterface

        lesson_ui = LessonInterface(
            self.state_manager,
            self.content_generator,
            self.system_logger,
            None,  # assessment будет создан внутри, если нужен
        )

        lesson_widget = lesson_ui.show_lesson(
            self.current_course_info["section_id"],
            self.current_course_info["topic_id"],
            self.current_course_info["lesson_id"],
        )
        display(lesson_widget)
