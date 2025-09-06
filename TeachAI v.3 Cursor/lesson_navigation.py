"""
Навигация по урокам.
Вынесена из lesson_interface.py для улучшения модульности.
"""

import ipywidgets as widgets
import logging
from lesson_utils import LessonUtils
import re
from cell_integration import cell_adapter


class LessonNavigation:
    """Навигация по урокам."""

    def __init__(self, lesson_interface):
        """
        Инициализация навигации.

        Args:
            lesson_interface: Экземпляр LessonInterface
        """
        self.lesson_interface = lesson_interface
        self.logger = logging.getLogger(__name__)
        self.utils = LessonUtils()

    def create_enhanced_navigation_buttons(self, section_id, topic_id, lesson_id):
        """
        Создает улучшенные кнопки навигации для урока.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            widgets.HBox: Контейнер с кнопками навигации
        """
        try:
            # Кнопка "Назад к курсам"
            back_button = widgets.Button(
                description="← Назад к курсам",
                button_style="warning",
                layout=widgets.Layout(width="auto", margin="5px"),
            )

            # Кнопка "Пройти тест"
            test_button = widgets.Button(
                description="📝 Пройти тест",
                button_style="info",
                layout=widgets.Layout(width="auto", margin="5px"),
            )

            # Кнопка "Задать вопрос"
            ask_button = widgets.Button(
                description="❓ Задать вопрос",
                button_style="success",
                layout=widgets.Layout(width="auto", margin="5px"),
            )

            # Кнопка "Объяснить подробнее"
            explain_button = widgets.Button(
                description="📚 Объяснить подробнее",
                button_style="primary",
                layout=widgets.Layout(width="auto", margin="5px"),
            )

            # Кнопка "Показать примеры"
            examples_button = widgets.Button(
                description="💡 Показать примеры",
                button_style="info",
                layout=widgets.Layout(width="auto", margin="5px"),
            )

            # Кнопка "Контрольные задания"
            # ИСПРАВЛЕНО: Проверяем, пройден ли тест для активации кнопки
            lesson_full_id = f"{section_id}:{topic_id}:{lesson_id}"
            test_passed = self.lesson_interface.state_manager.is_test_passed(
                lesson_full_id
            )

            control_tasks_button = widgets.Button(
                description="🛠️ Контрольные задания",
                button_style="danger",
                layout=widgets.Layout(width="auto", margin="5px"),
                disabled=not test_passed,  # Активна если тест пройден
                tooltip="Доступно после прохождения теста"
                if not test_passed
                else "Выполнить контрольные задания",
            )

            # Сохраняем ссылку на кнопку для доступа извне
            self.control_tasks_button = control_tasks_button

            # Логируем статус кнопки
            self.logger.info(
                f"Кнопка 'Контрольные задания' создана. Тест пройден: {test_passed}, кнопка активна: {not control_tasks_button.disabled}"
            )

            # Привязываем обработчики событий
            self._setup_button_handlers(
                back_button,
                test_button,
                ask_button,
                explain_button,
                examples_button,
                control_tasks_button,
                section_id,
                topic_id,
                lesson_id,
            )

            # Создаем контейнер с кнопками
            navigation_container = widgets.HBox(
                [
                    examples_button,
                    explain_button,
                    ask_button,
                    test_button,
                    control_tasks_button,
                    back_button,
                ],
                layout=widgets.Layout(
                    width="100%",
                    justify_content="space-between",
                    padding="10px",
                    border="1px solid #ddd",
                    border_radius="5px",
                    margin="10px 0",
                ),
            )

            return navigation_container

        except Exception as e:
            self.logger.error(f"Ошибка при создании кнопок навигации: {str(e)}")
            # Возвращаем простую кнопку "Назад"
            back_button = widgets.Button(
                description="← Назад к курсам", button_style="warning"
            )
            back_button.on_click(lambda b: self._handle_back_button_clicked(b))
            return widgets.HBox([back_button])

    def _setup_button_handlers(
        self,
        back_button,
        test_button,
        ask_button,
        explain_button,
        examples_button,
        control_tasks_button,
        section_id,
        topic_id,
        lesson_id,
    ):
        """
        Настраивает обработчики событий для кнопок навигации.

        Args:
            back_button: Кнопка "Назад"
            test_button: Кнопка "Тест"
            ask_button: Кнопка "Вопрос"
            explain_button: Кнопка "Объяснить"
            examples_button: Кнопка "Примеры"
            control_tasks_button: Кнопка "Контрольные задания"
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока
        """

        def on_back_button_clicked(b):
            # ИСПРАВЛЕНО: Очищаем кэш при переходе к выбору курса
            self.utils.clear_lesson_cache(self.lesson_interface)

            # Возвращаемся к выбору курса
            from interface import InterfaceState

            self.lesson_interface.interface.current_state = (
                InterfaceState.COURSE_SELECTION
            )
            self.lesson_interface.interface.show_course_selection()

        def on_test_button_clicked(b):
            from IPython.display import display

            # Переходим к тестированию
            if (
                hasattr(self.lesson_interface, "assessment_interface")
                and self.lesson_interface.assessment_interface
            ):
                # Используем AssessmentInterface для показа теста
                # Получаем course_id безопасно
                course_id = self.lesson_interface.current_course_info.get(
                    "course_plan", {}
                ).get("course_id", "default")

                display(
                    self.lesson_interface.assessment_interface.show_assessment(
                        current_course=course_id,
                        current_section=self.lesson_interface.current_course_info[
                            "section_id"
                        ],
                        current_topic=self.lesson_interface.current_course_info[
                            "topic_id"
                        ],
                        current_lesson=self.lesson_interface.current_course_info[
                            "lesson_id"
                        ],
                        current_lesson_content=self.lesson_interface.current_lesson_content,
                    )
                )
            elif self.lesson_interface.assessment:
                # Fallback: используем старый метод если assessment_interface недоступен
                self.logger.warning(
                    "Используется fallback для тестирования - assessment_interface недоступен"
                )
                # Здесь можно добавить fallback логику или показать сообщение об ошибке
                from IPython.display import display, HTML

                display(
                    HTML(
                        "<p style='color: orange;'>Функция тестирования временно недоступна. Пожалуйста, попробуйте позже.</p>"
                    )
                )
            else:
                self.logger.warning("Модуль оценивания недоступен")
                from IPython.display import display, HTML

                display(HTML("<p style='color: red;'>Модуль оценивания недоступен</p>"))

        def on_ask_button_clicked(b):
            # Скрываем другие контейнеры
            self.logger.info(
                "Кнопка 'Задать вопрос' нажата - скрываем другие контейнеры"
            )
            self.lesson_interface._hide_other_containers()

            # Показываем интерфейс вопросов
            if self.lesson_interface.qa_container:
                self.logger.info("qa_container найден - показываем")
                self.lesson_interface.qa_container.layout.display = "block"
                self.logger.info("qa_container отображен")
            else:
                self.logger.error("qa_container НЕ НАЙДЕН в lesson_interface")
                # Показываем сообщение об ошибке
                from IPython.display import display, HTML

                display(
                    HTML(
                        "<p style='color: red;'>Ошибка: контейнер для вопросов не найден</p>"
                    )
                )

        def on_explain_button_clicked(b):
            # НОВАЯ ЛОГИКА: Показываем выбор типа объяснения
            # Скрываем другие контейнеры
            self.lesson_interface._hide_other_containers()

            # Показываем выбор типа объяснения
            self.lesson_interface._show_explanation_choice()

        def extract_code_blocks_from_html(html: str) -> list:
            """
            Рекурсивно ищет все <pre><code>...</code></pre> в HTML и возвращает список кусков кода.
            """
            code_blocks = []
            for match in re.finditer(r"<pre><code>([\s\S]*?)</code></pre>", html):
                code = match.group(1)
                code = re.sub(r"<.*?>", "", code)  # Удаляем все HTML-теги внутри кода
                code_blocks.append(code.strip())
            return code_blocks

        def extract_titles_and_texts(html: str) -> list:
            """
            Извлекает заголовки (<h3>) и пояснения (<p>) из HTML, возвращает список (заголовок, текст).
            ИСПРАВЛЕНО: Убрано дублирование блоков.
            """
            blocks = []
            # Ищем <h3> и <p> в порядке следования
            pattern = re.compile(r"(<h3>.*?</h3>|<p>.*?</p>)", re.DOTALL)
            matches = list(pattern.finditer(html))

            i = 0
            while i < len(matches):
                current_block = matches[i].group(0)

                if current_block.startswith("<h3>"):
                    title = re.sub("<.*?>", "", current_block).strip()
                    text = None

                    # Ищем следующий <p> после заголовка
                    if i + 1 < len(matches) and matches[i + 1].group(0).startswith(
                        "<p>"
                    ):
                        text = re.sub("<.*?>", "", matches[i + 1].group(0)).strip()
                        i += 2  # Пропускаем и заголовок, и текст
                    else:
                        i += 1  # Только заголовок

                    blocks.append((title, text))

                elif current_block.startswith("<p>"):
                    # Если встретили <p> без заголовка, добавляем как отдельный блок
                    text = re.sub("<.*?>", "", current_block).strip()
                    blocks.append((None, text))
                    i += 1

                else:
                    i += 1

            return blocks

        def on_examples_button_clicked(b):
            # Скрываем другие контейнеры
            self.lesson_interface._hide_other_containers()
            # Показываем загрузку примеров
            if self.lesson_interface.examples_container:
                self.lesson_interface.examples_container.layout.display = "block"
                loading_html = widgets.HTML(
                    value="<p><strong>Генерация примеров...</strong></p>"
                )
                self.lesson_interface.examples_container.children = [loading_html]
                try:
                    from examples_generator import ExamplesGenerator

                    examples_generator = ExamplesGenerator(
                        self.lesson_interface.content_generator.api_key
                    )
                    examples = examples_generator.generate_examples(
                        lesson_data=self.lesson_interface.current_lesson_data,
                        lesson_content=self.lesson_interface.current_lesson_content,
                        communication_style=self.lesson_interface.current_course_info[
                            "user_profile"
                        ]["communication_style"],
                        course_context=self.lesson_interface.current_course_info,
                    )
                    # --- Новый парсер: только один заголовок, все коды — отдельные ячейки ---
                    widgets_to_display = []

                    # Добавляем только один заголовок "Примеры:" (если есть в ответе)
                    if "Примеры" in examples:
                        widgets_to_display.append(
                            widgets.HTML(value="<h3>Примеры</h3>")
                        )

                    # Извлекаем все блоки кода
                    code_blocks = extract_code_blocks_from_html(examples)

                    # Извлекаем заголовки и пояснения (если есть)
                    titles_and_texts = extract_titles_and_texts(examples)

                    # ИСПРАВЛЕНО: Убираем дублирование и улучшаем структуру
                    processed_blocks = set()  # Для отслеживания уже обработанных блоков

                    # Для каждого кода — отдельная ячейка, перед ней (если есть) — заголовок/пояснение
                    for i, code in enumerate(code_blocks):
                        # Создаем уникальный идентификатор для блока
                        block_id = f"code_{i}_{hash(code)}"

                        if block_id in processed_blocks:
                            continue  # Пропускаем дублирующиеся блоки

                        processed_blocks.add(block_id)

                        # Добавляем заголовок и пояснение, если они есть
                        if i < len(titles_and_texts):
                            title, text = titles_and_texts[i]
                            if title and title.strip():
                                widgets_to_display.append(
                                    widgets.HTML(value=f"<h4>{title}</h4>")
                                )
                            if text and text.strip():
                                widgets_to_display.append(
                                    widgets.HTML(value=f"<p>{text}</p>")
                                )

                        # Создаем демо-ячейки для кода
                        try:
                            demo_cells = cell_adapter.create_demo_cells(
                                [{"code": code}]
                            )
                            widgets_to_display.extend(demo_cells)
                        except Exception as e:
                            # Fallback: если не удалось создать демо-ячейки
                            self.logger.warning(f"Не удалось создать демо-ячейки: {e}")
                            # Создаем простой виджет с кодом
                            code_widget = widgets.HTML(
                                value=f"<pre><code>{code}</code></pre>",
                                layout=widgets.Layout(
                                    margin="10px 0",
                                    padding="10px",
                                    border="1px solid #ddd",
                                    border_radius="5px",
                                    background_color="#f8f8f8",
                                ),
                            )
                            widgets_to_display.append(code_widget)

                    # Если не найдено ни одного кода — fallback: просто текст
                    if not code_blocks:
                        widgets_to_display.append(widgets.HTML(value=examples))

                    # Кнопка закрытия
                    close_button = widgets.Button(
                        description="✕ Закрыть",
                        button_style="danger",
                        layout=widgets.Layout(width="auto", margin="10px 0"),
                    )

                    def on_close_button_clicked(b):
                        self.lesson_interface.examples_container.layout.display = "none"

                    close_button.on_click(on_close_button_clicked)
                    widgets_to_display.append(close_button)

                    # ИСПРАВЛЕНО: Очищаем контейнер перед добавлением новых виджетов
                    self.lesson_interface.examples_container.children = []
                    self.lesson_interface.examples_container.children = (
                        widgets_to_display
                    )
                except Exception as e:
                    self.logger.error(f"Ошибка при генерации примеров: {str(e)}")

                    # ИСПРАВЛЕНО: Очищаем контейнер перед добавлением сообщения об ошибке
                    self.lesson_interface.examples_container.children = []

                    error_html = widgets.HTML(
                        value=f"<p style='color: red;'>Ошибка при генерации примеров: {str(e)}</p>"
                    )
                    close_button = widgets.Button(
                        description="✕ Закрыть",
                        button_style="danger",
                        layout=widgets.Layout(width="auto", margin="10px 0"),
                    )

                    def on_close_button_clicked(b):
                        self.lesson_interface.examples_container.layout.display = "none"

                    close_button.on_click(on_close_button_clicked)
                    self.lesson_interface.examples_container.children = [
                        error_html,
                        close_button,
                    ]

        def on_control_tasks_button_clicked(b):
            # Скрываем другие контейнеры
            self.lesson_interface._hide_other_containers()
            # Показываем панель контрольных заданий
            if self.lesson_interface.control_tasks_container:
                self.lesson_interface.control_tasks_container.layout.display = "block"

                # ИСПРАВЛЕНО: Очищаем контейнер перед добавлением загрузки
                self.lesson_interface.control_tasks_container.children = []

                # Показываем загрузку
                loading_html = widgets.HTML(
                    value="<p><strong>Генерация контрольного задания...</strong></p>"
                )
                self.lesson_interface.control_tasks_container.children = [loading_html]

                try:
                    # Генерируем и показываем контрольное задание
                    task_interface = (
                        self.lesson_interface.control_tasks_interface.show_control_task(
                            lesson_data=self.lesson_interface.current_lesson_data,
                            lesson_content=self.lesson_interface.current_lesson_content,
                        )
                    )

                    # ИСПРАВЛЕНО: Очищаем контейнер перед добавлением задания
                    self.lesson_interface.control_tasks_container.children = []

                    # Добавляем задание
                    if task_interface:
                        self.lesson_interface.control_tasks_container.children = [
                            task_interface
                        ]

                    # Добавляем кнопку закрытия
                    close_button = widgets.Button(
                        description="✕ Закрыть",
                        button_style="danger",
                        layout=widgets.Layout(width="auto", margin="10px 0"),
                    )

                    def on_close_button_clicked(b):
                        self.lesson_interface.control_tasks_container.layout.display = (
                            "none"
                        )

                    close_button.on_click(on_close_button_clicked)

                    # Добавляем кнопку закрытия к существующим детям
                    if self.lesson_interface.control_tasks_container.children:
                        current_children = list(
                            self.lesson_interface.control_tasks_container.children
                        )
                        current_children.append(close_button)
                        self.lesson_interface.control_tasks_container.children = (
                            current_children
                        )
                    else:
                        self.lesson_interface.control_tasks_container.children = [
                            close_button
                        ]

                except Exception as e:
                    self.logger.error(
                        f"Ошибка при генерации контрольного задания: {str(e)}"
                    )

                    # ИСПРАВЛЕНО: Очищаем контейнер перед добавлением сообщения об ошибке
                    self.lesson_interface.control_tasks_container.children = []

                    error_html = widgets.HTML(
                        value=f"<p style='color: red;'>Ошибка при генерации контрольного задания: {str(e)}</p>"
                    )
                    close_button = widgets.Button(
                        description="✕ Закрыть",
                        button_style="danger",
                        layout=widgets.Layout(width="auto", margin="10px 0"),
                    )

                    def on_close_button_clicked(b):
                        self.lesson_interface.control_tasks_container.layout.display = (
                            "none"
                        )

                    close_button.on_click(on_close_button_clicked)
                    self.lesson_interface.control_tasks_container.children = [
                        error_html,
                        close_button,
                    ]

        # Привязываем обработчики
        back_button.on_click(on_back_button_clicked)
        test_button.on_click(on_test_button_clicked)
        ask_button.on_click(on_ask_button_clicked)
        explain_button.on_click(on_explain_button_clicked)
        examples_button.on_click(on_examples_button_clicked)
        control_tasks_button.on_click(on_control_tasks_button_clicked)

    def _handle_back_button_clicked(self, b):
        """Обработчик для кнопки "Назад" (fallback)."""
        try:
            self.utils.clear_lesson_cache(self.lesson_interface)
            from interface import InterfaceState

            self.lesson_interface.interface.current_state = (
                InterfaceState.COURSE_SELECTION
            )
            self.lesson_interface.interface.show_course_selection()
        except Exception as e:
            self.logger.error(f"Ошибка при обработке кнопки 'Назад': {str(e)}")
