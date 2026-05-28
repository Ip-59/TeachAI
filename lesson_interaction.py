"""
Интерактивные функции для уроков.
Вынесены из lesson_interface.py для улучшения модульности.
"""

import ipywidgets as widgets
import logging
from lesson_utils import LessonUtils


class LessonInteraction:
    """Интерактивные функции для уроков."""

    def __init__(self, lesson_interface):
        """
        Инициализация интерактивных функций.

        Args:
            lesson_interface: Экземпляр LessonInterface
        """
        self.lesson_interface = lesson_interface
        self.logger = logging.getLogger(__name__)
        self.utils = LessonUtils()

    def show_explanation_choice(self):
        """
        Показывает выбор типа объяснения.
        """
        try:
            # Создаем заголовок
            title_html = widgets.HTML(value="<h3>📚 Выберите тип объяснения:</h3>")

            # Кнопка "Полное объяснение"
            full_explanation_button = widgets.Button(
                description="📖 Полное объяснение урока",
                button_style="primary",
                layout=widgets.Layout(width="auto", margin="5px"),
            )

            # Кнопка "Ключевые понятия"
            concepts_button = widgets.Button(
                description="🔑 Ключевые понятия",
                button_style="info",
                layout=widgets.Layout(width="auto", margin="5px"),
            )

            # Кнопка "Назад"
            back_button = widgets.Button(
                description="← Назад",
                button_style="warning",
                layout=widgets.Layout(width="auto", margin="5px"),
            )

            # Привязываем обработчики
            def on_full_explanation_clicked(b):
                try:
                    # Получаем информацию о курсе
                    course_info = self.lesson_interface.current_course_info
                    course_title = course_info.get("course_title", "Курс")
                    section_title = course_info.get("section_title", "Раздел")
                    topic_title = course_info.get("topic_title", "Тема")
                    lesson_title = course_info.get("lesson_title", "Урок")

                    # Генерируем полное объяснение
                    explanation = self.lesson_interface.content_generator.get_detailed_explanation(
                        course=course_title,
                        section=section_title,
                        topic=topic_title,
                        lesson=lesson_title,
                        lesson_content=self.lesson_interface.current_lesson_content,
                        communication_style=self.lesson_interface.current_course_info[
                            "user_profile"
                        ]["communication_style"],
                    )

                    # Создаем виджет с объяснением (таблицы/LaTeX — на случай старого HTML)
                    from content_renderer import enhance_content

                    explanation_html = widgets.HTML(value=enhance_content(explanation))

                    # Кнопка закрытия
                    close_button = widgets.Button(
                        description="✕ Закрыть",
                        button_style="danger",
                        layout=widgets.Layout(width="auto", margin="10px 0"),
                    )

                    def on_close_clicked(b):
                        self.lesson_interface.explain_container.layout.display = "none"

                    close_button.on_click(on_close_clicked)

                    # Обновляем контейнер
                    self.lesson_interface.explain_container.children = [
                        explanation_html,
                        close_button,
                    ]

                except Exception as e:
                    self.logger.error(
                        f"Ошибка при генерации полного объяснения: {str(e)}"
                    )
                    error_html = widgets.HTML(
                        value=f"<p style='color: red;'>Ошибка при генерации объяснения: {str(e)}</p>"
                    )
                    self.lesson_interface.explain_container.children = [error_html]

            def on_concepts_explanation_clicked(b):
                try:
                    # Кэш в памяти: если понятия для этого урока уже извлекали —
                    # не дёргаем LLM повторно (это и быстрее, и стабильнее
                    # с точки зрения навигации «Назад/Вперёд»).
                    cached = self.lesson_interface.current_lesson_concepts
                    if cached:
                        concepts = cached
                    else:
                        concepts = (
                            self.lesson_interface.content_generator.generate_concepts(
                                lesson_content=self.lesson_interface.current_lesson_content,
                                communication_style=self.lesson_interface.current_course_info[
                                    "user_profile"
                                ]["communication_style"],
                                lesson_data=self.lesson_interface.current_lesson_data,
                                course_context=self.lesson_interface.current_course_info,
                            )
                        )
                        # Сохраняем результат для последующих кликов
                        self.lesson_interface.current_lesson_concepts = concepts

                    # Создаем список понятий
                    concepts_list = []
                    for concept_data in concepts:
                        concept_button = widgets.Button(
                            description=f"🔑 {concept_data['title']}",
                            button_style="info",
                            layout=widgets.Layout(width="auto", margin="2px"),
                        )

                        def create_concept_handler(concept_data):
                            def handle_concept_click(b):
                                self.show_concept_explanation(concept_data)

                            return handle_concept_click

                        concept_button.on_click(create_concept_handler(concept_data))
                        concepts_list.append(concept_button)

                    # Кнопка "Назад"
                    back_to_choice_button = widgets.Button(
                        description="← Назад к выбору",
                        button_style="warning",
                        layout=widgets.Layout(width="auto", margin="10px 0"),
                    )

                    def on_back_clicked(b):
                        self.show_explanation_choice()

                    back_to_choice_button.on_click(on_back_clicked)

                    # Обновляем контейнер
                    self.lesson_interface.explain_container.children = [
                        widgets.HTML(value="<h3>🔑 Ключевые понятия:</h3>"),
                        widgets.VBox(concepts_list),
                        back_to_choice_button,
                    ]

                except Exception as e:
                    self.logger.error(f"Ошибка при генерации понятий: {str(e)}")
                    error_html = widgets.HTML(
                        value=f"<p style='color: red;'>Ошибка при генерации понятий: {str(e)}</p>"
                    )
                    self.lesson_interface.explain_container.children = [error_html]

            def on_back_clicked(b):
                self.lesson_interface.explain_container.layout.display = "none"

            # Привязываем обработчики
            full_explanation_button.on_click(on_full_explanation_clicked)
            concepts_button.on_click(on_concepts_explanation_clicked)
            back_button.on_click(on_back_clicked)

            # Создаем контейнер
            choice_container = widgets.VBox(
                [title_html, full_explanation_button, concepts_button, back_button],
                layout=widgets.Layout(
                    width="100%",
                    padding="20px",
                    border="1px solid #ddd",
                    border_radius="10px",
                ),
            )

            # Показываем контейнер
            self.lesson_interface.explain_container.children = [choice_container]
            self.lesson_interface.explain_container.layout.display = "block"

        except Exception as e:
            self.logger.error(f"Ошибка при показе выбора объяснения: {str(e)}")

    def show_concept_explanation(self, concept):
        """
        Показывает подробное объяснение конкретного понятия.

        Запрашивает у LLM развёрнутое объяснение с привязкой к материалу
        текущего урока. Без этого пользователь видел только короткую
        аннотацию (1-2 предложения) из списка понятий, что не является
        "подробным объяснением".

        Args:
            concept (dict): Данные о понятии (title, description) либо
                (name, brief_description) — поддерживаются оба формата.
        """
        try:
            concept_title = concept.get("title") or concept.get("name") or "Понятие"
            concept_brief = (
                concept.get("description") or concept.get("brief_description") or ""
            )

            title_html = widgets.HTML(value=f"<h3>🔑 {concept_title}</h3>")
            loading_html = widgets.HTML(
                value="<p><strong>Генерация подробного объяснения понятия...</strong></p>"
            )
            # Показываем loader сразу, чтобы пользователь видел реакцию на клик
            self.lesson_interface.explain_container.children = [title_html, loading_html]

            try:
                explanation_html_value = (
                    self.lesson_interface.content_generator.explain_concept(
                        concept={
                            "name": concept_title,
                            "brief_description": concept_brief,
                        },
                        lesson_content=self.lesson_interface.current_lesson_content,
                        communication_style=self.lesson_interface.current_course_info[
                            "user_profile"
                        ]["communication_style"],
                    )
                )
                explanation_widget = widgets.HTML(value=explanation_html_value)
            except Exception as exc:
                self.logger.error(f"Ошибка при генерации объяснения понятия: {exc}")
                explanation_widget = widgets.HTML(
                    value=(
                        "<p style='color:#721c24; background-color:#f8d7da; "
                        "padding:10px; border-radius:5px;'>"
                        f"Не удалось сгенерировать подробное объяснение: {exc}<br>"
                        f"Краткое описание: {concept_brief}</p>"
                    )
                )

            back_button = widgets.Button(
                description="← Назад к понятиям",
                button_style="warning",
                layout=widgets.Layout(width="auto", margin="10px 0"),
            )

            def on_back_clicked(b):
                # Возвращаемся к списку понятий — используем кэш, чтобы не
                # тратить токены LLM и не выдавать студенту другой список
                # понятий при каждом возврате.
                try:
                    cached = self.lesson_interface.current_lesson_concepts
                    if cached:
                        concepts = cached
                    else:
                        concepts = (
                            self.lesson_interface.content_generator.generate_concepts(
                                lesson_content=self.lesson_interface.current_lesson_content,
                                communication_style=self.lesson_interface.current_course_info[
                                    "user_profile"
                                ]["communication_style"],
                                lesson_data=self.lesson_interface.current_lesson_data,
                                course_context=self.lesson_interface.current_course_info,
                            )
                        )
                        self.lesson_interface.current_lesson_concepts = concepts

                    concepts_list = []
                    for concept_data in concepts:
                        concept_button = widgets.Button(
                            description=f"🔑 {concept_data['title']}",
                            button_style="info",
                            layout=widgets.Layout(width="auto", margin="2px"),
                        )

                        def create_concept_handler(concept_data):
                            def handle_concept_click(b):
                                self.show_concept_explanation(concept_data)

                            return handle_concept_click

                        concept_button.on_click(create_concept_handler(concept_data))
                        concepts_list.append(concept_button)

                    # Кнопка "Назад к выбору"
                    back_to_choice_button = widgets.Button(
                        description="← Назад к выбору",
                        button_style="warning",
                        layout=widgets.Layout(width="auto", margin="10px 0"),
                    )

                    def on_back_to_choice_clicked(b):
                        self.show_explanation_choice()

                    back_to_choice_button.on_click(on_back_to_choice_clicked)

                    # Обновляем контейнер
                    self.lesson_interface.explain_container.children = [
                        widgets.HTML(value="<h3>🔑 Ключевые понятия:</h3>"),
                        widgets.VBox(concepts_list),
                        back_to_choice_button,
                    ]

                except Exception as e:
                    self.logger.error(f"Ошибка при возврате к понятиям: {str(e)}")

            back_button.on_click(on_back_clicked)

            # Кнопка "Закрыть"
            close_button = widgets.Button(
                description="✕ Закрыть",
                button_style="danger",
                layout=widgets.Layout(width="auto", margin="10px 0"),
            )

            def on_close_clicked(b):
                self.lesson_interface.explain_container.layout.display = "none"

            close_button.on_click(on_close_clicked)

            # Создаём контейнер с подробным LLM-объяснением (а не с краткой аннотацией)
            concept_container = widgets.VBox(
                [title_html, explanation_widget, back_button, close_button],
                layout=widgets.Layout(
                    width="100%",
                    padding="20px",
                    border="1px solid #ddd",
                    border_radius="10px",
                ),
            )

            # Обновляем контейнер
            self.lesson_interface.explain_container.children = [concept_container]

        except Exception as e:
            self.logger.error(f"Ошибка при показе объяснения понятия: {str(e)}")

    def setup_enhanced_qa_container(self, qa_container):
        """
        Настраивает улучшенный контейнер для вопросов и ответов.

        Args:
            qa_container: Контейнер для вопросов и ответов
        """
        try:
            self.logger.info("Настраиваем улучшенный QA контейнер")
            self.logger.info(f"qa_container: {qa_container}")

            # Создаем заголовок
            title_html = widgets.HTML(value="<h3>❓ Задайте вопрос по уроку:</h3>")

            # Поле ввода вопроса
            question_input = widgets.Textarea(
                placeholder="Введите ваш вопрос здесь...",
                layout=widgets.Layout(width="100%", height="100px"),
            )

            # Кнопка отправки вопроса
            send_button = widgets.Button(
                description="📤 Отправить вопрос",
                button_style="success",
                layout=widgets.Layout(width="auto", margin="10px 0"),
            )

            # Область для ответа
            answer_area = widgets.HTML(
                value="<p>Ответ появится здесь после отправки вопроса.</p>",
                layout=widgets.Layout(
                    width="100%", padding="10px", border="1px solid #ddd"
                ),
            )

            # Кнопка закрытия
            close_button = widgets.Button(
                description="✕ Закрыть",
                button_style="danger",
                layout=widgets.Layout(width="auto", margin="10px 0"),
            )

            self.logger.info("Виджеты QA контейнера созданы")

            def on_send_question_button_clicked(b):
                self.logger.info("Кнопка 'Отправить вопрос' нажата")
                try:
                    question = question_input.value.strip()
                    if not question:
                        self.logger.warning("Вопрос пустой")
                        answer_area.value = (
                            "<p style='color: orange;'>Пожалуйста, введите вопрос.</p>"
                        )
                        return

                    self.logger.info(f"Обрабатываем вопрос: {question[:50]}...")

                    # Показываем загрузку
                    answer_area.value = (
                        "<p><strong>Анализ вопроса и подготовка ответа...</strong></p>"
                    )

                    # Получаем информацию о курсе для правильного вызова методов
                    course_info = self.lesson_interface.current_course_info

                    # Увеличиваем счетчик вопросов
                    # Создаем уникальный ID урока для счетчика
                    lesson_full_id = f"{course_info.get('section_id', 'unknown')}:{course_info.get('topic_id', 'unknown')}:{course_info.get('lesson_id', 'unknown')}"
                    questions_count = (
                        self.lesson_interface.state_manager.increment_questions_count(
                            lesson_full_id
                        )
                    )

                    self.logger.info(f"Счетчик вопросов обновлен: {questions_count}")

                    # Проверяем релевантность вопроса.
                    # Передаём course_context, чтобы из тела урока была срезана
                    # breadcrumb-шапка и LLM учитывал именно материал урока
                    # (а не название курса/раздела).
                    relevance_result = self.lesson_interface.content_generator.check_question_relevance(
                        question,
                        self.lesson_interface.current_lesson_content,
                        self.lesson_interface.current_lesson_data,
                        course_context=self.lesson_interface.current_course_info,
                        lesson_raw_content=self.lesson_interface.current_lesson_raw_content,
                    )

                    self.logger.info(f"Релевантность вопроса: {relevance_result}")

                    # Если вопрос нерелевантен
                    if not relevance_result.get("is_relevant", True):
                        self.logger.warning("Вопрос нерелевантен уроку")
                        answer_area.value = f"""
                        <div style='background-color: #fff3cd; color: #856404; padding: 15px;
                                    border-radius: 8px; border: 1px solid #ffeaa7;'>
                            <h4>⚠️ Вопрос не связан с уроком</h4>
                            <p><strong>Ваш вопрос:</strong> {question}</p>
                            <p><strong>Причина:</strong> {relevance_result.get('reason', 'Вопрос не относится к теме урока')}</p>
                            <p><strong>Рекомендация:</strong> Задайте вопрос, связанный с содержанием урока.</p>
                        </div>
                        """
                        return

                    # Генерируем ответ
                    self.logger.info("Генерируем ответ на вопрос")

                    # Получаем информацию о курсе для правильного вызова answer_question
                    course_info = self.lesson_interface.current_course_info
                    course_title = course_info.get("course_title", "Курс")
                    section_title = course_info.get("section_title", "Раздел")
                    topic_title = course_info.get("topic_title", "Тема")
                    lesson_title = course_info.get("lesson_title", "Урок")
                    user_name = course_info.get("user_profile", {}).get(
                        "name", "Пользователь"
                    )

                    answer = self.lesson_interface.content_generator.answer_question(
                        course=course_title,
                        section=section_title,
                        topic=topic_title,
                        lesson=lesson_title,
                        user_question=question,
                        lesson_content=self.lesson_interface.current_lesson_content,
                        user_name=user_name,
                        communication_style=course_info["user_profile"][
                            "communication_style"
                        ],
                    )

                    self.logger.info(
                        f"Ответ сгенерирован, длина: {len(answer)} символов"
                    )

                    # Отображаем ответ
                    answer_area.value = answer

                    # Очищаем поле ввода
                    question_input.value = ""

                    self.logger.info("Вопрос успешно обработан")

                except Exception as e:
                    self.logger.error(f"Ошибка при генерации ответа: {str(e)}")
                    answer_area.value = f"<p style='color: red;'>Ошибка при генерации ответа: {str(e)}</p>"

            def on_close_button_clicked(b):
                self.logger.info("Кнопка 'Закрыть' нажата")
                qa_container.layout.display = "none"

            # Привязываем обработчики
            send_button.on_click(on_send_question_button_clicked)
            close_button.on_click(on_close_button_clicked)

            # Создаем контейнер
            qa_container.children = [
                title_html,
                question_input,
                send_button,
                answer_area,
                close_button,
            ]

            self.logger.info("QA контейнер успешно настроен")
            self.logger.info(
                f"Количество виджетов в контейнере: {len(qa_container.children)}"
            )
            self.logger.info(
                f"Виджеты: {[type(widget).__name__ for widget in qa_container.children]}"
            )

        except Exception as e:
            self.logger.error(f"Ошибка при настройке QA контейнера: {str(e)}")

    def hide_other_containers(self):
        """
        Скрывает другие контейнеры при показе интерактивных функций.
        """
        try:
            if self.lesson_interface.explain_container:
                self.lesson_interface.explain_container.layout.display = "none"
            if self.lesson_interface.examples_container:
                self.lesson_interface.examples_container.layout.display = "none"
            if self.lesson_interface.qa_container:
                self.lesson_interface.qa_container.layout.display = "none"
        except Exception as e:
            self.logger.error(f"Ошибка при скрытии контейнеров: {str(e)}")
