"""
Интерфейс для тестирования знаний учащихся.
Отвечает за отображение тестов, обработку ответов и показ результатов.

ИСПРАВЛЕНО: Улучшена диагностика ошибок вместо простого "Интерфейс тестирования недоступен"
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
import html
import traceback
from interface_utils import InterfaceUtils


class AssessmentInterface:
    """Интерфейс для тестирования знаний учащихся."""

    def __init__(self, state_manager, assessment, system_logger, parent_facade=None):
        """
        Инициализация интерфейса тестирования.

        Args:
            state_manager: Менеджер состояния
            assessment: Модуль оценивания
            system_logger: Системный логгер
            parent_facade: Ссылка на родительский фасад
        """
        self.state_manager = state_manager
        self.assessment = assessment
        self.system_logger = system_logger
        self.parent_facade = parent_facade
        self.logger = logging.getLogger(__name__)

        # Утилиты интерфейса
        self.utils = InterfaceUtils()

        # Состояние тестирования
        self.current_questions = []
        self.current_answers = {}
        self.results_container = None

        # Получаем доступ к content_generator
        if parent_facade and hasattr(parent_facade, "content_generator"):
            self.content_generator = parent_facade.content_generator
            self.logger.info(
                "AssessmentInterface инициализирован с доступом к content_generator"
            )
        else:
            self.content_generator = None
            self.logger.warning(
                "AssessmentInterface инициализирован БЕЗ доступа к content_generator"
            )

    def _diagnose_assessment_issue(self, current_lesson_content):
        """
        НОВОЕ: Диагностирует проблемы с тестированием.

        Args:
            current_lesson_content: Содержание урока

        Returns:
            str: Детальное описание проблемы
        """
        issues = []

        # Проверяем content_generator
        if not self.content_generator:
            issues.append("content_generator = None (генератор контента недоступен)")

        # Проверяем assessment модуль
        if not self.assessment:
            issues.append("assessment = None (модуль оценивания недоступен)")

        # Проверяем содержание урока
        if not current_lesson_content:
            issues.append(f"current_lesson_content пустой: {current_lesson_content}")

        # Проверяем state_manager
        if not self.state_manager:
            issues.append("state_manager = None (менеджер состояния недоступен)")

        # Проверяем parent_facade
        if not self.parent_facade:
            issues.append("parent_facade = None (фасад не передан)")

        if issues:
            detailed_message = "ПРОБЛЕМЫ С ТЕСТИРОВАНИЕМ:\n" + "\n".join(
                f"• {issue}" for issue in issues
            )
            detailed_message += "\n\nВОЗМОЖНЫЕ ПРИЧИНЫ:"
            detailed_message += "\n• Ошибка инициализации системы (проверьте engine.py)"
            detailed_message += "\n• Урок не сгенерировался (проверьте API ключ)"
            detailed_message += "\n• Проблема с передачей facade в lesson_interface.py"
            detailed_message += "\n• Ошибка в content_generator (проверьте OpenAI API)"
            return detailed_message

        return "Компоненты тестирования корректны, проблема в другом месте"

    def show_assessment(
        self,
        current_course,
        current_section,
        current_topic,
        current_lesson,
        current_lesson_content,
    ):
        """
        Отображает интерфейс тестирования.

        Args:
            current_course (str): Текущий курс
            current_section (str): Текущий раздел
            current_topic (str): Текущая тема
            current_lesson (str): Текущий урок
            current_lesson_content (str): Содержание урока

        Returns:
            widgets.VBox: Интерфейс тестирования
        """
        try:
            self.logger.info(
                f"Начало создания интерфейса тестирования для урока: {current_lesson}"
            )

            # ИСПРАВЛЕНО: Детальная диагностика проблем вместо простого сообщения
            if not self.content_generator or not self.assessment:
                error_details = self._diagnose_assessment_issue(current_lesson_content)
                self.logger.error(f"Диагностика проблем тестирования: {error_details}")
                return self._create_error_widget(
                    "Ошибка инициализации тестирования", error_details
                )

            # Сохраняем информацию о текущем уроке
            self.current_lesson_info = {
                "course": current_course,
                "section": current_section,
                "topic": current_topic,
                "lesson": current_lesson,
            }

            # Создаем навигационную информацию
            nav_info = widgets.HTML(
                value=f"""
                <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #3b82f6;">
                    <h4 style="margin: 0 0 10px 0; color: #1e40af;">📍 Навигация</h4>
                    <p style="margin: 5px 0; color: #64748b;"><strong>Курс:</strong> {html.escape(str(current_course))}</p>
                    <p style="margin: 5px 0; color: #64748b;"><strong>Раздел:</strong> {html.escape(str(current_section))}</p>
                    <p style="margin: 5px 0; color: #64748b;"><strong>Тема:</strong> {html.escape(str(current_topic))}</p>
                    <p style="margin: 5px 0; color: #64748b;"><strong>Урок:</strong> {html.escape(str(current_lesson))}</p>
                </div>
                """
            )

            # Отладочная информация о содержании урока
            content_debug = ""
            if self.logger.isEnabledFor(logging.DEBUG):
                content_type = type(current_lesson_content).__name__
                content_length = (
                    len(str(current_lesson_content)) if current_lesson_content else 0
                )
                content_debug = f"""
                <div style="background: #fef3c7; padding: 10px; border-radius: 5px; margin-bottom: 15px; font-size: 12px;">
                    <strong>DEBUG:</strong> Содержание урока - тип: {content_type}, длина: {content_length}
                </div>
                """

            # Заголовок тестирования
            test_header = widgets.HTML(
                value=f"""
                {content_debug}
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #4CAF50, #45a049);
                           color: white; border-radius: 10px; margin: 20px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <h2 style="margin: 0; font-size: 24px;">📝 Проверка знаний</h2>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">Ответьте на следующие вопросы по теме <strong>{html.escape(current_lesson)}</strong>, чтобы проверить свои знания.</p>
                </div>
                """
            )

            # Генерируем вопросы для тестирования
            self.logger.info("Генерация вопросов для тестирования...")
            self.current_questions = self._generate_questions(current_lesson_content)

            if not self.current_questions:
                error_msg = "Не удалось сгенерировать вопросы для тестирования"
                self.logger.error(error_msg)
                return self._create_error_widget("Ошибка генерации вопросов", error_msg)

            self.logger.info(
                f"Успешно сгенерировано {len(self.current_questions)} вопросов"
            )

            # Создаем интерфейс вопросов
            questions_interface = self._create_questions_interface()

            # Кнопка завершения теста
            submit_button = widgets.Button(
                description="Завершить тест",
                button_style="primary",
                layout=widgets.Layout(
                    width="200px",
                    height="50px",
                    margin="30px auto 20px auto",
                    display="block",
                ),
            )

            # Контейнер для результатов
            self.results_container = widgets.Output()

            # Обработчик кнопки завершения теста
            def handle_test_submission(b):
                self._handle_test_submission()

            submit_button.on_click(handle_test_submission)

            # Собираем весь интерфейс
            assessment_widget = widgets.VBox(
                [
                    nav_info,
                    test_header,
                    questions_interface,
                    submit_button,
                    self.results_container,
                ]
            )

            self.logger.info("Интерфейс тестирования успешно создан")
            return assessment_widget

        except Exception as e:
            error_msg = f"Критическая ошибка создания интерфейса тестирования: {str(e)}"
            self.logger.error(f"{error_msg}\nTraceback: {traceback.format_exc()}")
            return self._create_error_widget("Критическая ошибка", error_msg)

    def _generate_questions(self, lesson_content):
        """
        Генерирует вопросы для тестирования на основе содержания урока.

        Args:
            lesson_content: Содержание урока

        Returns:
            list: Список вопросов
        """
        try:
            self.logger.info("Попытка генерации вопросов через assessment модуль")

            if not self.assessment:
                self.logger.error("Assessment модуль недоступен")
                return []

            if not hasattr(self.assessment, "generate_questions"):
                self.logger.error(
                    "Assessment модуль не имеет метода generate_questions"
                )
                return []

            # Генерируем вопросы через assessment модуль
            questions = self.assessment.generate_questions(
                course=self.current_lesson_info["course"],
                section=self.current_lesson_info["section"],
                topic=self.current_lesson_info["topic"],
                lesson=self.current_lesson_info["lesson"],
                lesson_content=lesson_content,
            )

            if questions:
                self.logger.info(
                    f"Assessment модуль сгенерировал {len(questions)} вопросов"
                )
                return questions
            else:
                self.logger.warning("Assessment модуль вернул пустой список вопросов")
                return []

        except Exception as e:
            error_msg = f"Ошибка генерации вопросов через assessment: {str(e)}"
            self.logger.error(f"{error_msg}\nTraceback: {traceback.format_exc()}")

            # Дополнительная диагностика
            if "Connection error" in str(e) or "connection" in str(e).lower():
                self.logger.error(
                    "ДИАГНОСТИКА: Ошибка подключения к OpenAI API при генерации вопросов"
                )
            elif "timeout" in str(e).lower():
                self.logger.error(
                    "ДИАГНОСТИКА: Превышено время ожидания при генерации вопросов"
                )
            elif "rate limit" in str(e).lower():
                self.logger.error(
                    "ДИАГНОСТИКА: Превышен лимит запросов при генерации вопросов"
                )

            return []

    def _create_questions_interface(self):
        """Создает интерфейс для отображения вопросов."""
        if not self.current_questions:
            return widgets.HTML(
                value="""
                <div style="background: #fef2f2; padding: 20px; border-radius: 8px; border-left: 4px solid #ef4444; text-align: center;">
                    <h4 style="color: #dc2626; margin-top: 0;">Вопросы недоступны</h4>
                    <p style="color: #991b1b;">Не удалось сгенерировать вопросы для тестирования.</p>
                </div>
                """
            )

        questions_widgets = []
        self.current_answers = {}

        for i, question in enumerate(self.current_questions):
            # Заголовок вопроса
            question_title = widgets.HTML(
                value=f"<h4 style='margin: 15px 0 10px 0; color: #2c3e50; line-height: 1.4;'>Вопрос {i+1}: {html.escape(question.get('text', question.get('question', '')))}</h4>"
            )

            # Варианты ответов
            options = question.get("options", [])
            if not options:
                self.logger.warning(f"Вопрос {i+1} не имеет вариантов ответов")
                continue

            # Очищаем варианты ответов от лишних префиксов
            clean_options = []
            for j, option in enumerate(options):
                clean_option = str(option).strip()

                # Удаляем префиксы вида A., B., etc.
                prefixes_to_remove = [
                    f"{chr(65+j)}. ",
                    f"{chr(65+j)}.",
                    "A. ",
                    "B. ",
                    "C. ",
                    "D. ",
                    "E. ",
                    "A.",
                    "B.",
                    "C.",
                    "D.",
                    "E.",
                ]

                for prefix in prefixes_to_remove:
                    if clean_option.startswith(prefix):
                        clean_option = clean_option[len(prefix) :].strip()
                        break

                clean_options.append(clean_option)

            # Создаем RadioButtons для вариантов ответов
            radio_buttons = widgets.RadioButtons(
                options=clean_options, layout=widgets.Layout(margin="10px 0 20px 20px")
            )

            # Сохраняем ссылку на RadioButtons для получения ответов
            self.current_answers[i] = radio_buttons

            questions_widgets.extend([question_title, radio_buttons])

        return widgets.VBox(questions_widgets)

    def _handle_test_submission(self):
        """Обрабатывает отправку теста."""
        try:
            self.logger.info("Обработка отправки теста")

            # Собираем ответы пользователя
            user_answers = []
            for i, radio_buttons in self.current_answers.items():
                selected_value = radio_buttons.value
                if selected_value:
                    user_answers.append(selected_value)
                else:
                    user_answers.append(None)  # Нет ответа

            self.logger.info(f"Собрано {len(user_answers)} ответов пользователя")

            # Проверяем ответы
            if not self.assessment:
                error_msg = "Assessment модуль недоступен для проверки ответов"
                self.logger.error(error_msg)
                with self.results_container:
                    clear_output()
                    display(
                        widgets.HTML(
                            value=f"""
                        <div style="background: #fef2f2; padding: 15px; border-radius: 8px; border-left: 4px solid #ef4444;">
                            <h4 style="color: #dc2626; margin-top: 0;">Ошибка проверки ответов</h4>
                            <div style="color: #991b1b;">{error_msg}</div>
                        </div>
                        """
                        )
                    )
                return

            # Получаем результат проверки
            results = self.assessment.check_answers(
                self.current_questions, user_answers
            )
            self._display_results(results, user_answers)

        except Exception as e:
            error_msg = f"Ошибка при обработке теста: {str(e)}"
            self.logger.error(f"{error_msg}\nTraceback: {traceback.format_exc()}")

            with self.results_container:
                clear_output()
                display(
                    widgets.HTML(
                        value=f"""
                    <div style="background: #fef2f2; padding: 15px; border-radius: 8px; border-left: 4px solid #ef4444;">
                        <h4 style="color: #dc2626; margin-top: 0;">Ошибка обработки теста</h4>
                        <div style="color: #991b1b;">{error_msg}</div>
                    </div>
                    """
                    )
                )

    def _display_results(self, results, user_answers):
        """Отображает результаты тестирования."""
        try:
            score = results.get("score", 0)
            total = results.get("total", len(self.current_questions))
            percentage = (score / total * 100) if total > 0 else 0

            # Определяем цвет результата
            if percentage >= 80:
                color = "#22c55e"  # Зеленый
                status = "Отлично!"
            elif percentage >= 60:
                color = "#f59e0b"  # Желтый
                status = "Хорошо!"
            else:
                color = "#ef4444"  # Красный
                status = "Нужно повторить материал"

            results_html = f"""
            <div style="background: white; padding: 20px; border-radius: 10px; margin-top: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <h3 style="text-align: center; color: {color}; margin-top: 0;">Результаты тестирования</h3>
                <div style="text-align: center; font-size: 24px; margin: 20px 0;">
                    <span style="color: {color}; font-weight: bold;">{score}/{total}</span>
                    <span style="color: #64748b;"> ({percentage:.1f}%)</span>
                </div>
                <div style="text-align: center; color: {color}; font-size: 18px; font-weight: bold; margin-bottom: 20px;">
                    {status}
                </div>
            </div>
            """

            with self.results_container:
                clear_output()
                display(widgets.HTML(value=results_html))

            # Логируем результат
            self.logger.info(
                f"Результат тестирования: {score}/{total} ({percentage:.1f}%)"
            )

        except Exception as e:
            error_msg = f"Ошибка отображения результатов: {str(e)}"
            self.logger.error(error_msg)

            with self.results_container:
                clear_output()
                display(
                    widgets.HTML(
                        value=f"""
                    <div style="background: #fef2f2; padding: 15px; border-radius: 8px; border-left: 4px solid #ef4444;">
                        <h4 style="color: #dc2626; margin-top: 0;">Ошибка отображения результатов</h4>
                        <div style="color: #991b1b;">{error_msg}</div>
                    </div>
                    """
                    )
                )

    def _create_error_widget(self, title, message):
        """Создает виджет для отображения ошибки."""
        return widgets.HTML(
            value=f"""
            <div style="background: #fef2f2; padding: 20px; border-radius: 10px; border-left: 4px solid #ef4444; margin: 20px 0;">
                <h3 style="color: #dc2626; margin-top: 0;">{html.escape(title)}</h3>
                <div style="color: #991b1b; white-space: pre-line; line-height: 1.5;">
                    {html.escape(message)}
                </div>
            </div>
            """
        )
