"""
Обработчики интерактивных кнопок для уроков.
Отвечает за обработку действий "Объясни подробнее", "Приведи примеры", "Задать вопрос".

ИСПРАВЛЕНО ЭТАП 30: Устранены ошибки 'str' object has no attribute 'get' в API вызовах
ИСПРАВЛЕНО ЭТАП 34: Добавлен alias handle_question_button для совместимости (проблема #141)
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
import traceback


class LessonInteractiveHandlers:
    """Обработчики интерактивных функций урока."""

    def __init__(self, content_generator, state_manager, utils, logger):
        """
        Инициализация обработчиков.

        Args:
            content_generator: Генератор контента
            state_manager: Менеджер состояния
            utils: Утилиты интерфейса
            logger: Логгер
        """
        self.content_generator = content_generator
        self.state_manager = state_manager
        self.utils = utils
        self.logger = logger

        # Контейнеры для правильного закрытия
        self.explain_container = None
        self.examples_container = None
        self.qa_container = None

        # Данные текущего урока
        self.current_lesson_content = None
        self.current_course_info = None
        self.current_lesson_id = None

    def set_lesson_data(self, lesson_content, course_info, lesson_id):
        """
        Устанавливает данные текущего урока.

        Args:
            lesson_content: Содержание урока
            course_info: Информация о курсе
            lesson_id: ID урока
        """
        self.current_lesson_content = lesson_content
        self.current_course_info = course_info
        self.current_lesson_id = lesson_id

    def handle_explain_button(self, button):
        """
        Обработчик кнопки "Объясни подробнее".
        Генерирует подробное объяснение материала урока.
        """
        try:
            # Проверка данных урока
            if not self.current_lesson_content or not self.current_course_info:
                self._show_error("Данные урока недоступны")
                return

            # Очищаем предыдущий контейнер если он есть
            if self.explain_container:
                self.explain_container.close()

            # Создаем контейнер для объяснения
            self.explain_container = widgets.VBox()

            # Заголовок с зеленым градиентом
            header = widgets.HTML(
                value=f"""
                <div style="background: linear-gradient(135deg, #4ade80, #22c55e);
                           padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                    <h3 style="color: white; margin: 0; font-size: 18px;">
                        📚 Подробное объяснение материала
                    </h3>
                </div>
                """
            )

            # ИСПРАВЛЕНО ЭТАП 30: Правильный вызов нового API
            # Формируем lesson_data как словарь
            lesson_data = {
                "title": self.current_course_info.get("lesson_title", "Урок"),
                "id": self.current_course_info.get("lesson_id", ""),
                "description": "",
            }

            # Получаем содержание урока
            if isinstance(self.current_lesson_content, dict):
                lesson_content = self.current_lesson_content.get(
                    "content", str(self.current_lesson_content)
                )
            else:
                lesson_content = str(self.current_lesson_content)

            # Получаем стиль общения пользователя
            user_profile = self.current_course_info.get("user_profile", {})
            communication_style = user_profile.get("communication_style", "friendly")

            # Получаем подробное объяснение через НОВЫЙ API
            explanation = self.content_generator.get_detailed_explanation(
                lesson_data=lesson_data,
                lesson_content=lesson_content,
                communication_style=communication_style,
            )

            # Контент объяснения
            content = widgets.HTML(
                value=f"""
                <div style="background: #f0f9ff; padding: 20px; border-radius: 8px;
                           border-left: 4px solid #22c55e; margin-bottom: 15px;">
                    <div style="line-height: 1.6; color: #1f2937;">
                        {explanation}
                    </div>
                </div>
                """
            )

            # Кнопка закрытия
            close_button = widgets.Button(
                description="Закрыть объяснение",
                button_style="success",
                icon="check",
                layout=widgets.Layout(width="auto", margin="10px 0"),
            )
            close_button.on_click(self._close_explain_container)

            # Собираем интерфейс
            self.explain_container.children = [header, content, close_button]
            display(self.explain_container)

            self.logger.info(
                f"Показано подробное объяснение для урока {self.current_lesson_id}"
            )

        except Exception as e:
            self.logger.error(f"Ошибка при показе объяснения: {str(e)}")
            self._show_error(f"Ошибка получения объяснения: {str(e)}")

    def handle_examples_button(self, button):
        """
        Обработчик кнопки "Приведи примеры".
        Генерирует практические примеры для урока.
        """
        try:
            # Проверка данных урока
            if not self.current_lesson_content or not self.current_course_info:
                self._show_error("Данные урока недоступны")
                return

            # Очищаем предыдущий контейнер если он есть
            if self.examples_container:
                self.examples_container.close()

            # Создаем контейнер для примеров
            self.examples_container = widgets.VBox()

            # Заголовок с синим градиентом
            header = widgets.HTML(
                value=f"""
                <div style="background: linear-gradient(135deg, #3b82f6, #1d4ed8);
                           padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                    <h3 style="color: white; margin: 0; font-size: 18px;">
                        💡 Практические примеры
                    </h3>
                </div>
                """
            )

            # ИСПРАВЛЕНО ЭТАП 30: Правильный вызов нового API
            # Формируем lesson_data как словарь
            lesson_data = {
                "title": self.current_course_info.get("lesson_title", "Урок"),
                "id": self.current_course_info.get("lesson_id", ""),
                "description": "",
            }

            # Получаем содержание урока
            if isinstance(self.current_lesson_content, dict):
                lesson_content = self.current_lesson_content.get(
                    "content", str(self.current_lesson_content)
                )
            else:
                lesson_content = str(self.current_lesson_content)

            # Получаем стиль общения пользователя
            user_profile = self.current_course_info.get("user_profile", {})
            communication_style = user_profile.get("communication_style", "friendly")

            # Формируем контекст курса
            course_context = {
                "course_title": self.current_course_info.get("course_title", ""),
                "course_plan": self.current_course_info.get("course_plan", {}),
            }

            # Генерируем примеры через НОВЫЙ API
            examples = self.content_generator.generate_examples(
                lesson_data=lesson_data,
                lesson_content=lesson_content,
                communication_style=communication_style,
                course_context=course_context,
            )

            # Контент примеров
            content = widgets.HTML(
                value=f"""
                <div style="background: #eff6ff; padding: 20px; border-radius: 8px;
                           border-left: 4px solid #3b82f6; margin-bottom: 15px;">
                    <div style="line-height: 1.6; color: #1f2937;">
                        {examples}
                    </div>
                </div>
                """
            )

            # Кнопка закрытия
            close_button = widgets.Button(
                description="Закрыть примеры",
                button_style="info",
                icon="check",
                layout=widgets.Layout(width="auto", margin="10px 0"),
            )
            close_button.on_click(self._close_examples_container)

            # Собираем интерфейс
            self.examples_container.children = [header, content, close_button]
            display(self.examples_container)

            self.logger.info(f"Показаны примеры для урока {self.current_lesson_id}")

        except Exception as e:
            self.logger.error(f"Ошибка при показе примеров: {str(e)}")
            self._show_error(f"Ошибка получения примеров: {str(e)}")

    def handle_qa_button(self, button):
        """
        Обработчик кнопки "Задать вопрос".
        Создает интерфейс для вопросов и ответов.
        """
        try:
            # Проверка данных урока
            if not self.current_lesson_content or not self.current_course_info:
                self._show_error("Данные урока недоступны")
                return

            # Очищаем предыдущий контейнер если он есть
            if self.qa_container:
                self.qa_container.close()

            # Создаем контейнер для Q&A
            self.qa_container = widgets.VBox()

            # Заголовок с фиолетовым градиентом
            header = widgets.HTML(
                value=f"""
                <div style="background: linear-gradient(135deg, #8b5cf6, #7c3aed);
                           padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                    <h3 style="color: white; margin: 0; font-size: 18px;">
                        ❓ Задайте вопрос по материалу урока
                    </h3>
                </div>
                """
            )

            # Поле ввода вопроса
            question_input = widgets.Textarea(
                placeholder="Введите ваш вопрос по материалу урока...",
                layout=widgets.Layout(width="100%", height="80px"),
                description="Вопрос:",
            )

            # Кнопка отправки
            submit_button = widgets.Button(
                description="Получить ответ",
                button_style="primary",
                icon="paper-plane",
                layout=widgets.Layout(width="auto", margin="10px 0"),
            )

            # Контейнер для ответа
            answer_output = widgets.Output()

            def on_submit_question(button):
                """Обработка отправки вопроса."""
                try:
                    user_question = question_input.value.strip()
                    if not user_question:
                        with answer_output:
                            clear_output(wait=True)
                            display(
                                widgets.HTML(
                                    value="""
                                <div style="background: #fef3c7; padding: 15px; border-radius: 8px;
                                           border-left: 4px solid #f59e0b;">
                                    <div style="color: #92400e;">
                                        Пожалуйста, введите ваш вопрос
                                    </div>
                                </div>
                                """
                                )
                            )
                        return

                    with answer_output:
                        clear_output(wait=True)
                        display(
                            widgets.HTML(
                                value="""
                            <div style="background: #dbeafe; padding: 15px; border-radius: 8px;
                                       border-left: 4px solid #3b82f6;">
                                <div style="color: #1e40af;">
                                    🤔 Обрабатываю ваш вопрос...
                                </div>
                            </div>
                            """
                            )
                        )

                    # Формируем данные для генератора Q&A
                    lesson_data = {
                        "title": self.current_course_info.get("lesson_title", "Урок"),
                        "id": self.current_course_info.get("lesson_id", ""),
                        "description": "",
                    }

                    # Получаем содержание урока
                    if isinstance(self.current_lesson_content, dict):
                        lesson_content = self.current_lesson_content.get(
                            "content", str(self.current_lesson_content)
                        )
                    else:
                        lesson_content = str(self.current_lesson_content)

                    # Получаем стиль общения пользователя
                    user_profile = self.current_course_info.get("user_profile", {})
                    communication_style = user_profile.get(
                        "communication_style", "friendly"
                    )

                    # Генерируем ответ через QA генератор
                    answer = self.content_generator.process_question_answer(
                        lesson_data=lesson_data,
                        lesson_content=lesson_content,
                        user_question=user_question,
                        communication_style=communication_style,
                    )

                    # Показываем ответ
                    with answer_output:
                        clear_output(wait=True)
                        display(
                            widgets.HTML(
                                value=f"""
                            <div style="background: #f0fdf4; padding: 20px; border-radius: 8px;
                                       border-left: 4px solid #22c55e; margin-bottom: 15px;">
                                <div style="color: #166534; font-weight: 500; margin-bottom: 10px;">
                                    💬 Ответ на ваш вопрос:
                                </div>
                                <div style="line-height: 1.6; color: #1f2937;">
                                    {answer}
                                </div>
                            </div>
                            """
                            )
                        )

                    self.logger.info(
                        f"Отвечен вопрос для урока {self.current_lesson_id}: {user_question[:50]}..."
                    )

                except Exception as e:
                    self.logger.error(f"Ошибка при обработке вопроса: {str(e)}")
                    with answer_output:
                        clear_output(wait=True)
                        display(
                            widgets.HTML(
                                value=f"""
                            <div style="background: #fee2e2; padding: 15px; border-radius: 8px;
                                       border-left: 4px solid #ef4444;">
                                <div style="color: #dc2626;">
                                    Ошибка получения ответа: {str(e)}
                                </div>
                            </div>
                            """
                            )
                        )

            submit_button.on_click(on_submit_question)

            # Кнопка закрытия
            close_button = widgets.Button(
                description="Закрыть",
                button_style="warning",
                icon="times",
                layout=widgets.Layout(width="auto", margin="10px 0"),
            )
            close_button.on_click(self._close_qa_container)

            # Собираем интерфейс
            self.qa_container.children = [
                header,
                question_input,
                submit_button,
                answer_output,
                close_button,
            ]
            display(self.qa_container)

            self.logger.info(
                f"Показан интерфейс Q&A для урока {self.current_lesson_id}"
            )

        except Exception as e:
            self.logger.error(f"Ошибка при показе Q&A интерфейса: {str(e)}")
            self._show_error(f"Ошибка создания интерфейса вопросов: {str(e)}")

    # ИСПРАВЛЕНО ЭТАП 34: Добавлен alias для совместимости с lesson_utils.py
    def handle_question_button(self, button):
        """
        Alias для handle_qa_button для совместимости с lesson_utils.py.

        Args:
            button: Кнопка, которая была нажата
        """
        return self.handle_qa_button(button)

    def _close_explain_container(self, button):
        """Закрывает контейнер объяснения."""
        if self.explain_container:
            self.explain_container.close()
            self.explain_container = None

    def _close_examples_container(self, button):
        """Закрывает контейнер примеров."""
        if self.examples_container:
            self.examples_container.close()
            self.examples_container = None

    def _close_qa_container(self, button):
        """Закрывает контейнер вопросов и ответов."""
        if self.qa_container:
            self.qa_container.close()
            self.qa_container = None

    def _show_error(self, error_message):
        """
        Показывает сообщение об ошибке.

        Args:
            error_message (str): Текст ошибки
        """
        error_widget = widgets.HTML(
            value=f"""
            <div style="background: #fee2e2; padding: 15px; border-radius: 8px;
                       border-left: 4px solid #ef4444; margin: 15px 0;">
                <div style="color: #dc2626; font-weight: 500;">
                    {error_message}
                </div>
            </div>
            """
        )
        display(error_widget)

    def get_status(self):
        """
        Возвращает статус обработчиков.

        Returns:
            dict: Статус интерактивных обработчиков
        """
        return {
            "has_lesson_data": bool(
                self.current_lesson_content and self.current_course_info
            ),
            "lesson_id": self.current_lesson_id,
            "active_containers": {
                "explain": bool(self.explain_container),
                "examples": bool(self.examples_container),
                "qa": bool(self.qa_container),
            },
        }
