"""
Обработчики интерактивных кнопок для уроков.
Отвечает за обработку действий "Объясни подробнее", "Приведи примеры", "Задать вопрос".

ИСПРАВЛЕНО: Улучшена диагностика ошибок вместо простого "Данные урока недоступны"
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
        self.logger.info(f"Установка данных урока: {lesson_id}")
        self.logger.debug(
            f"lesson_content тип: {type(lesson_content)}, содержание: {lesson_content}"
        )
        self.logger.debug(
            f"course_info тип: {type(course_info)}, содержание: {course_info}"
        )

        self.current_lesson_content = lesson_content
        self.current_course_info = course_info
        self.current_lesson_id = lesson_id

        self.logger.info(f"Данные урока {lesson_id} успешно установлены")

    def _diagnose_lesson_data_issue(self):
        """
        НОВОЕ: Диагностирует проблемы с данными урока.

        Returns:
            str: Детальное описание проблемы
        """
        issues = []

        # Проверяем current_lesson_content
        if self.current_lesson_content is None:
            issues.append("current_lesson_content = None (данные урока не переданы)")
        elif not self.current_lesson_content:
            issues.append(
                f"current_lesson_content пустой: {self.current_lesson_content}"
            )
        else:
            self.logger.debug(
                f"current_lesson_content OK: тип {type(self.current_lesson_content)}"
            )

        # Проверяем current_course_info
        if self.current_course_info is None:
            issues.append("current_course_info = None (информация о курсе не передана)")
        elif not self.current_course_info:
            issues.append(f"current_course_info пустой: {self.current_course_info}")
        else:
            self.logger.debug(
                f"current_course_info OK: тип {type(self.current_course_info)}"
            )

        # Проверяем current_lesson_id
        if not self.current_lesson_id:
            issues.append(f"current_lesson_id пустой: {self.current_lesson_id}")
        else:
            self.logger.debug(f"current_lesson_id OK: {self.current_lesson_id}")

        # Проверяем content_generator
        if not self.content_generator:
            issues.append("content_generator = None (генератор контента недоступен)")
        else:
            self.logger.debug("content_generator OK")

        if issues:
            detailed_message = "ПРОБЛЕМЫ С ДАННЫМИ УРОКА:\n" + "\n".join(
                f"• {issue}" for issue in issues
            )
            detailed_message += "\n\nВОЗМОЖНЫЕ ПРИЧИНЫ:"
            detailed_message += "\n• Урок не сгенерировался из-за ошибки API"
            detailed_message += "\n• Ошибка в lesson_interface.py при сохранении данных"
            detailed_message += "\n• Проблема с инициализацией компонентов системы"
            detailed_message += "\n• Ошибка в content_generator (проверьте API ключ)"
            return detailed_message

        return "Данные урока корректны, проблема в другом месте"

    def handle_explain_button(self, button):
        """
        Обработчик кнопки "Объясни подробнее".
        Генерирует подробное объяснение материала урока.
        """
        try:
            self.logger.info(
                f"Обработка кнопки 'Объясни подробнее' для урока {self.current_lesson_id}"
            )

            # ИСПРАВЛЕНО: Детальная диагностика вместо простого сообщения
            if not self.current_lesson_content or not self.current_course_info:
                error_details = self._diagnose_lesson_data_issue()
                self.logger.error(
                    f"Диагностика проблемы с данными урока: {error_details}"
                )
                self._show_error(f"Ошибка доступа к данным урока:\n\n{error_details}")
                return

            # Проверяем content_generator
            if not self.content_generator:
                error_msg = "ContentGenerator недоступен. Проверьте инициализацию системы и API ключ."
                self.logger.error(error_msg)
                self._show_error(error_msg)
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

            self.logger.info("Вызов content_generator.get_detailed_explanation")

            # Получаем подробное объяснение через API
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
                f"Подробное объяснение успешно показано для урока {self.current_lesson_id}"
            )

        except Exception as e:
            error_msg = f"Ошибка при получении объяснения: {str(e)}"
            self.logger.error(f"{error_msg}\nTraceback: {traceback.format_exc()}")

            # Диагностируем тип ошибки
            if "Connection error" in str(e) or "connection" in str(e).lower():
                detailed_error = f"{error_msg}\n\nПРОВЕРЬТЕ:\n• API ключ OpenAI в .env файле\n• Интернет соединение\n• Статус сервиса OpenAI"
            elif "timeout" in str(e).lower():
                detailed_error = (
                    f"{error_msg}\n\nПревышено время ожидания ответа от API"
                )
            elif "rate limit" in str(e).lower():
                detailed_error = f"{error_msg}\n\nПревышен лимит запросов к API"
            else:
                detailed_error = f"{error_msg}\n\nТип ошибки: {type(e).__name__}"

            self._show_error(detailed_error)

    def handle_examples_button(self, button):
        """
        Обработчик кнопки "Приведи примеры".
        Генерирует практические примеры для урока.
        """
        try:
            self.logger.info(
                f"Обработка кнопки 'Приведи примеры' для урока {self.current_lesson_id}"
            )

            # ИСПРАВЛЕНО: Детальная диагностика вместо простого сообщения
            if not self.current_lesson_content or not self.current_course_info:
                error_details = self._diagnose_lesson_data_issue()
                self.logger.error(
                    f"Диагностика проблемы с данными урока: {error_details}"
                )
                self._show_error(f"Ошибка доступа к данным урока:\n\n{error_details}")
                return

            # Проверяем content_generator
            if not self.content_generator:
                error_msg = "ContentGenerator недоступен. Проверьте инициализацию системы и API ключ."
                self.logger.error(error_msg)
                self._show_error(error_msg)
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

            self.logger.info("Вызов content_generator.generate_examples")

            # Генерируем примеры через API
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

            self.logger.info(
                f"Примеры успешно показаны для урока {self.current_lesson_id}"
            )

        except Exception as e:
            error_msg = f"Ошибка при получении примеров: {str(e)}"
            self.logger.error(f"{error_msg}\nTraceback: {traceback.format_exc()}")

            # Диагностируем тип ошибки
            if "Connection error" in str(e) or "connection" in str(e).lower():
                detailed_error = f"{error_msg}\n\nПРОВЕРЬТЕ:\n• API ключ OpenAI в .env файле\n• Интернет соединение\n• Статус сервиса OpenAI"
            elif "timeout" in str(e).lower():
                detailed_error = (
                    f"{error_msg}\n\nПревышено время ожидания ответа от API"
                )
            elif "rate limit" in str(e).lower():
                detailed_error = f"{error_msg}\n\nПревышен лимит запросов к API"
            else:
                detailed_error = f"{error_msg}\n\nТип ошибки: {type(e).__name__}"

            self._show_error(detailed_error)

    def handle_qa_button(self, button):
        """
        Обработчик кнопки "Задать вопрос".
        Создает интерфейс для вопросов и ответов.
        """
        try:
            self.logger.info(
                f"Обработка кнопки 'Задать вопрос' для урока {self.current_lesson_id}"
            )

            # ИСПРАВЛЕНО: Детальная диагностика вместо простого сообщения
            if not self.current_lesson_content or not self.current_course_info:
                error_details = self._diagnose_lesson_data_issue()
                self.logger.error(
                    f"Диагностика проблемы с данными урока: {error_details}"
                )
                self._show_error(f"Ошибка доступа к данным урока:\n\n{error_details}")
                return

            # Проверяем content_generator
            if not self.content_generator:
                error_msg = "ContentGenerator недоступен. Проверьте инициализацию системы и API ключ."
                self.logger.error(error_msg)
                self._show_error(error_msg)
                return

            # Очищаем предыдущий контейнер если он есть
            if self.qa_container:
                self.qa_container.close()

            # Создаем контейнер для Q&A
            self.qa_container = widgets.VBox()

            # Заголовок
            header = widgets.HTML(
                value=f"""
                <div style="background: linear-gradient(135deg, #8b5cf6, #7c3aed);
                           padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                    <h3 style="color: white; margin: 0; font-size: 18px;">
                        ❓ Задать вопрос по уроку
                    </h3>
                </div>
                """
            )

            # Поле для ввода вопроса
            question_input = widgets.Textarea(
                placeholder="Введите ваш вопрос по материалу урока...",
                layout=widgets.Layout(width="100%", height="100px", margin="10px 0"),
            )

            # Кнопка отправки
            submit_button = widgets.Button(
                description="Получить ответ",
                button_style="primary",
                icon="paper-plane",
                layout=widgets.Layout(width="150px", margin="5px 0"),
            )

            # Контейнер для ответа
            answer_output = widgets.Output()

            # Кнопка закрытия
            close_button = widgets.Button(
                description="Закрыть",
                button_style="danger",
                icon="times",
                layout=widgets.Layout(width="100px", margin="5px 10px"),
            )

            def handle_question_submit(b):
                """Обработчик отправки вопроса."""
                question = question_input.value.strip()
                if not question:
                    with answer_output:
                        clear_output()
                        print("Пожалуйста, введите вопрос.")
                    return

                try:
                    with answer_output:
                        clear_output()
                        print("Обрабатываем ваш вопрос...")

                    # Формируем данные для API
                    lesson_data = {
                        "title": self.current_course_info.get("lesson_title", "Урок"),
                        "id": self.current_course_info.get("lesson_id", ""),
                        "description": "",
                    }

                    if isinstance(self.current_lesson_content, dict):
                        lesson_content = self.current_lesson_content.get(
                            "content", str(self.current_lesson_content)
                        )
                    else:
                        lesson_content = str(self.current_lesson_content)

                    user_profile = self.current_course_info.get("user_profile", {})
                    communication_style = user_profile.get(
                        "communication_style", "friendly"
                    )

                    # Получаем ответ через API
                    answer = self.content_generator.answer_question(
                        question=question,
                        lesson_data=lesson_data,
                        lesson_content=lesson_content,
                        communication_style=communication_style,
                    )

                    with answer_output:
                        clear_output()
                        display(
                            widgets.HTML(
                                value=f"""
                            <div style="background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #8b5cf6;">
                                <h4 style="color: #7c3aed; margin-top: 0;">Ответ:</h4>
                                <div style="line-height: 1.6; color: #1f2937;">{answer}</div>
                            </div>
                            """
                            )
                        )

                except Exception as e:
                    error_msg = f"Ошибка при получении ответа: {str(e)}"
                    with answer_output:
                        clear_output()
                        display(
                            widgets.HTML(
                                value=f"""
                            <div style="background: #fef2f2; padding: 15px; border-radius: 8px; border-left: 4px solid #ef4444;">
                                <h4 style="color: #dc2626; margin-top: 0;">Ошибка:</h4>
                                <div style="color: #991b1b;">{error_msg}</div>
                            </div>
                            """
                            )
                        )

            submit_button.on_click(handle_question_submit)
            close_button.on_click(self._close_qa_container)

            # Собираем интерфейс
            button_row = widgets.HBox([submit_button, close_button])
            self.qa_container.children = [
                header,
                question_input,
                button_row,
                answer_output,
            ]
            display(self.qa_container)

            self.logger.info(
                f"Интерфейс Q&A успешно показан для урока {self.current_lesson_id}"
            )

        except Exception as e:
            error_msg = f"Ошибка при создании интерфейса вопросов: {str(e)}"
            self.logger.error(f"{error_msg}\nTraceback: {traceback.format_exc()}")
            self._show_error(error_msg)

    # Alias для совместимости
    def handle_question_button(self, button):
        """Alias для handle_qa_button для обратной совместимости."""
        return self.handle_qa_button(button)

    def _show_error(self, message):
        """Показывает сообщение об ошибке."""
        error_widget = widgets.HTML(
            value=f"""
            <div style="background: #fef2f2; padding: 15px; border-radius: 8px;
                       border-left: 4px solid #ef4444; margin: 10px 0;">
                <h4 style="color: #dc2626; margin-top: 0;">Ошибка интерактивной функции</h4>
                <div style="color: #991b1b; white-space: pre-line;">{message}</div>
            </div>
            """
        )
        display(error_widget)

    def _close_explain_container(self, button):
        """Закрывает контейнер объяснения."""
        if self.explain_container:
            self.explain_container.close()

    def _close_examples_container(self, button):
        """Закрывает контейнер примеров."""
        if self.examples_container:
            self.examples_container.close()

    def _close_qa_container(self, button):
        """Закрывает контейнер Q&A."""
        if self.qa_container:
            self.qa_container.close()
