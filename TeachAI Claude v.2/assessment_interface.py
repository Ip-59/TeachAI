"""
Интерфейс для тестирования знаний учащихся.
Отвечает за отображение тестов, обработку ответов и показ результатов.

ИСПРАВЛЕНО ЭТАП 42: Восстановлена правильная логика перехода к следующему уроку (проблема #171)
ИСПРАВЛЕНО ЭТАП 42: Решены проблемы #173-#178 из предыдущей сессии
ОСНОВАНО НА: project knowledge - lesson_interface.py, state_manager.py
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
import html
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
            parent_facade: Ссылка на родительский фасад (ОБЯЗАТЕЛЬНО для доступа к content_generator)
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

        # ИСПРАВЛЕНО: Добавлен доступ к content_generator через parent_facade
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
            current_course (str): Название курса
            current_section (str): Название раздела
            current_topic (str): Название темы
            current_lesson (str): Название урока
            current_lesson_content (str): Содержание урока для генерации тестов

        Returns:
            widgets.VBox: Интерфейс тестирования
        """
        try:
            self.logger.info("=== ОТЛАДКА ASSESSMENT ===")
            self.logger.info(
                f"Создание интерфейса тестирования для урока: {current_lesson}"
            )
            self.logger.info(
                f"Размер переданного контента: {len(current_lesson_content)} символов"
            )
            self.logger.info(
                f"Первые 200 символов контента: {current_lesson_content[:200]}..."
            )

            # ОТЛАДКА: Показываем информацию о контенте прямо в интерфейсе
            content_debug = f"""
            <div style='background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 5px; font-size: 12px;'>
                <h4>📖 КОНТЕНТ ДЛЯ ТЕСТИРОВАНИЯ:</h4>
                <p><strong>Урок:</strong> {html.escape(current_lesson)}</p>
                <p><strong>Размер контента:</strong> {len(current_lesson_content)} символов</p>
                <p><strong>Начало контента:</strong> {html.escape(current_lesson_content[:150])}...</p>
            </div>
            """

            # Сохраняем данные урока для последующего использования
            self.current_lesson_info = {
                "course": current_course,
                "section": current_section,
                "topic": current_topic,
                "lesson": current_lesson,
                "content": current_lesson_content,
            }

            # Получаем план курса и проверяем структуру
            course_plan = self._get_course_plan()

            # Создаем навигационную информацию
            nav_info = self.utils.create_navigation_info(
                current_course, current_section, current_topic, current_lesson
            )

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
            self.current_questions = self._generate_questions(current_lesson_content)

            if not self.current_questions:
                return self._create_error_widget(
                    "Ошибка генерации вопросов",
                    "Не удалось сгенерировать вопросы для тестирования.",
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

            return assessment_widget

        except Exception as e:
            self.logger.error(f"Ошибка создания интерфейса тестирования: {str(e)}")
            return self._create_error_widget(
                "Критическая ошибка", f"Произошла ошибка: {str(e)}"
            )

    def _generate_questions(self, lesson_content):
        """Генерирует вопросы для тестирования на основе содержания урока."""
        try:
            self.logger.info("Генерация вопросов для тестирования")

            if not self.assessment:
                self.logger.error("Assessment модуль недоступен")
                return []

            # Генерируем вопросы через assessment модуль
            questions = self.assessment.generate_questions(
                course=self.current_lesson_info["course"],
                section=self.current_lesson_info["section"],
                topic=self.current_lesson_info["topic"],
                lesson=self.current_lesson_info["lesson"],
                lesson_content=lesson_content,
            )

            self.logger.info(f"Сгенерировано {len(questions)} вопросов")
            return questions

        except Exception as e:
            self.logger.error(f"Ошибка генерации вопросов: {str(e)}")
            return []

    def _create_questions_interface(self):
        """Создает интерфейс для отображения вопросов."""
        if not self.current_questions:
            return widgets.HTML(
                value="<p style='color: red; text-align: center;'>Вопросы недоступны</p>"
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

            # ОТЛАДКА: Проверяем исходные данные вопроса
            self.logger.info(f"=== ВОПРОС {i+1} ===")
            self.logger.info(f"Полные данные вопроса: {question}")
            self.logger.info(f"Исходные варианты: {options}")

            # ИСПРАВЛЕНО: Более агрессивная очистка + обрезание для RadioButtons
            clean_options = []
            for j, option in enumerate(options):
                clean_option = str(option).strip()

                # Удаляем все возможные префиксы в начале строки
                prefixes_to_remove = [
                    f"{chr(65+j)}. {chr(65+j)}.",  # A. A.
                    f"{chr(65+j)}.{chr(65+j)}.",  # A.A.
                    f"{chr(65+j)}. ",  # A.
                    f"{chr(65+j)}.",  # A.
                    "A. A.",
                    "B. B.",
                    "C. C.",
                    "D. D.",
                    "E. E.",  # Любые двойные
                    "A.A.",
                    "B.B.",
                    "C.C.",
                    "D.D.",
                    "E.E.",  # Без пробелов
                    "A. ",
                    "B. ",
                    "C. ",
                    "D. ",
                    "E. ",  # Одиночные с пробелом
                    "A.",
                    "B.",
                    "C.",
                    "D.",
                    "E.",  # Одиночные без пробела
                ]

                for prefix in prefixes_to_remove:
                    if clean_option.startswith(prefix):
                        clean_option = clean_option[len(prefix) :].strip()
                        break

                # ИСПРАВЛЕНО: Более агрессивное обрезание для RadioButtons (они хуже переносят)
                if len(clean_option) > 45:
                    clean_option = clean_option[:42] + "..."

                clean_options.append(clean_option)
                self.logger.info(f"  Вариант {j}: '{option}' -> '{clean_option}'")

            # ИСПРАВЛЕНО: Возвращаемся к RadioButtons, но БЕЗ обрезания текста
            clean_options = []
            for j, option in enumerate(options):
                clean_option = str(option).strip()

                # Удаляем все возможные префиксы в начале строки
                prefixes_to_remove = [
                    f"{chr(65+j)}. {chr(65+j)}.",  # A. A.
                    f"{chr(65+j)}.{chr(65+j)}.",  # A.A.
                    f"{chr(65+j)}. ",  # A.
                    f"{chr(65+j)}.",  # A.
                    "A. A.",
                    "B. B.",
                    "C. C.",
                    "D. D.",
                    "E. E.",  # Любые двойные
                    "A.A.",
                    "B.B.",
                    "C.C.",
                    "D.D.",
                    "E.E.",  # Без пробелов
                    "A. ",
                    "B. ",
                    "C. ",
                    "D. ",
                    "E. ",  # Одиночные с пробелом
                    "A.",
                    "B.",
                    "C.",
                    "D.",
                    "E.",  # Одиночные без пробела
                ]

                for prefix in prefixes_to_remove:
                    if clean_option.startswith(prefix):
                        clean_option = clean_option[len(prefix) :].strip()
                        break

                # ИСПРАВЛЕНО: НЕ обрезаем текст, пусть RadioButtons сам разбирается
                clean_options.append(clean_option)

            self.logger.info(f"Очищенные варианты: {clean_options}")

            # Создаем финальные опции с правильными маркерами
            radio_options = [
                (f"{chr(65+j)}. {clean_option}", j)
                for j, clean_option in enumerate(clean_options)
            ]

            radio_buttons = widgets.RadioButtons(
                options=radio_options,
                layout=widgets.Layout(
                    margin="10px 0 15px 20px",
                    width="100%",  # Пусть занимает всю доступную ширину
                ),
                style={"description_width": "0px"},  # Убираем отступ для description
                disabled=False,
            )

            # Сохраняем ссылку на радиокнопки для получения ответов
            self.current_answers[i] = radio_buttons

            questions_widgets.extend([question_title, radio_buttons])

            # Добавляем разделитель только между вопросами (не после последнего)
            if i < len(self.current_questions) - 1:
                separator = widgets.HTML(
                    value="<div style='height: 15px;'></div>"
                )  # Уменьшил с 25px до 15px
                questions_widgets.append(separator)

        return widgets.VBox(questions_widgets)

    def _handle_test_submission(self):
        """Обрабатывает отправку теста и показывает результаты."""
        try:
            self.logger.info("Обработка результатов теста")

            # Собираем ответы пользователя
            user_answers = []
            for i in range(len(self.current_questions)):
                if (
                    i in self.current_answers
                    and self.current_answers[i].value is not None
                ):
                    user_answers.append(self.current_answers[i].value)
                else:
                    user_answers.append(None)

            # ОТЛАДКА: Логируем собранные ответы + показываем в интерфейсе
            self.logger.info(f"Собранные ответы пользователя: {user_answers}")
            self.logger.info(f"Количество вопросов: {len(self.current_questions)}")

            # ОТЛАДКА: Показываем информацию о сборе ответов в интерфейсе
            answers_debug = []
            for i, answer in enumerate(user_answers):
                if answer is not None:
                    answers_debug.append(
                        f"Вопрос {i+1}: выбран вариант {answer} ({chr(65+answer)})"
                    )
                    self.logger.info(
                        f"Вопрос {i+1}: выбран вариант {answer} ({chr(65+answer)})"
                    )
                else:
                    answers_debug.append(f"Вопрос {i+1}: ответ НЕ выбран")
                    self.logger.info(f"Вопрос {i+1}: ответ не выбран")

            answers_debug_html = f"""
            <div style='background: #e3f2fd; padding: 10px; margin: 10px 0; border-radius: 5px; font-size: 12px;'>
                <h4>📝 СОБРАННЫЕ ОТВЕТЫ:</h4>
                {'<br>'.join(answers_debug)}
            </div>
            """

            # Проверяем, что на все вопросы даны ответы
            unanswered = [
                i + 1 for i, answer in enumerate(user_answers) if answer is None
            ]
            if unanswered:
                with self.results_container:
                    clear_output(wait=True)
                    display(
                        widgets.HTML(
                            value=f"<p style='color: #856404; background-color: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0;'>Пожалуйста, ответьте на вопросы: {', '.join(map(str, unanswered))} перед завершением теста.</p>"
                        )
                    )
                return

            # ИСПРАВЛЕНО: Преобразуем числовые ответы в буквы для сравнения
            user_answers_letters = []
            for answer in user_answers:
                if answer is not None:
                    # Преобразуем индекс в букву: 0 → 'A', 1 → 'B', и т.д.
                    user_answers_letters.append(chr(65 + answer))
                else:
                    user_answers_letters.append(None)

            self.logger.info(
                f"Преобразованные ответы пользователя: {user_answers_letters}"
            )

            # Вычисляем результат с правильным форматом ответов
            score, correct_answers, score_count = self.assessment.calculate_score(
                self.current_questions, user_answers_letters
            )

            # ОТЛАДКА: Показываем информацию прямо в интерфейсе
            debug_info = f"""
            {answers_debug_html}
            <div style='background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; font-family: monospace; font-size: 12px;'>
                <h4>🔍 РЕЗУЛЬТАТЫ ВЫЧИСЛЕНИЯ:</h4>
                <p><strong>Исходные ответы (числа):</strong> {user_answers}</p>
                <p><strong>Преобразованные ответы (буквы):</strong> {user_answers_letters}</p>
                <p><strong>Правильные ответы:</strong> {correct_answers}</p>
                <p><strong>Результат calculate_score:</strong> score={score}, score_count={score_count}</p>
                <p><strong>Количество вопросов:</strong> {len(self.current_questions)}</p>
                <p><strong>Вычисление:</strong> {score_count}/{len(self.current_questions)} = {score:.1f}%</p>
            </div>
            """

            # ОТЛАДКА: Логируем результаты вычисления
            self.logger.info(f"=== РЕЗУЛЬТАТЫ ВЫЧИСЛЕНИЯ ===")
            self.logger.info(f"Исходные ответы пользователя: {user_answers}")
            self.logger.info(f"Преобразованные ответы: {user_answers_letters}")
            self.logger.info(
                f"Результат calculate_score: score={score}, correct_answers={correct_answers}, score_count={score_count}"
            )
            self.logger.info(f"Правильные ответы: {correct_answers}")
            self.logger.info(f"Совпадения: score_count={score_count}")
            self.logger.info(f"Финальная оценка: {score:.1f}%")

            self.logger.info(
                f"Результат теста: {score_count}/{len(self.current_questions)} ({score:.1f}%)"
            )

            # Сохраняем результаты
            self._save_assessment_results(user_answers_letters, correct_answers, score)

            # Определяем статус прохождения
            is_passed = score >= 70

            # ИСПРАВЛЕНО: Правильное определение lesson_id для mark_lesson_completed
            lesson_id = self._get_current_lesson_id()
            if lesson_id and is_passed:
                self.state_manager.mark_lesson_completed(lesson_id)
                self.logger.info(
                    f"Урок {lesson_id} отмечен как завершенный с оценкой {score:.1f}%"
                )

            # Отображаем результаты
            self._show_results(
                score, score_count, len(self.current_questions), is_passed, debug_info
            )

        except Exception as e:
            self.logger.error(f"Ошибка обработки результатов теста: {str(e)}")
            with self.results_container:
                clear_output(wait=True)
                display(
                    self._create_error_widget(
                        "Ошибка обработки", f"Произошла ошибка: {str(e)}"
                    )
                )

    def _get_current_lesson_id(self):
        """Получает правильный ID текущего урока."""
        try:
            # ИСПРАВЛЕНО: Получаем lesson_id из lesson_interface если доступен
            if hasattr(self.parent_facade, "lesson_interface") and hasattr(
                self.parent_facade.lesson_interface, "current_course_info"
            ):
                course_info = self.parent_facade.lesson_interface.current_course_info
                lesson_id = course_info.get("lesson_id")
                if lesson_id:
                    self.logger.info(
                        f"Используем lesson_id из lesson_interface: {lesson_id}"
                    )
                    return lesson_id

            # Fallback: получаем из state_manager
            next_lesson = self.state_manager.get_next_lesson()
            if next_lesson and len(next_lesson) >= 3:
                lesson_id = next_lesson[2]  # lesson_id из кортежа
                self.logger.info(f"Используем lesson_id из state_manager: {lesson_id}")
                return lesson_id

            self.logger.warning("Не удалось определить lesson_id")
            return None

        except Exception as e:
            self.logger.error(f"Ошибка получения lesson_id: {str(e)}")
            return None

    def _save_assessment_results(self, user_answers_letters, correct_answers, score):
        """Сохраняет результаты тестирования."""
        try:
            assessment_data = {
                "course": self.current_lesson_info["course"],
                "section": self.current_lesson_info["section"],
                "topic": self.current_lesson_info["topic"],
                "lesson": self.current_lesson_info["lesson"],
                "questions": self.current_questions,
                "user_answers": user_answers_letters,
                "correct_answers": correct_answers,
                "score": score,
                "passed": score >= 70,
            }

            # Сохраняем через системный логгер
            if hasattr(self.system_logger, "log_assessment"):
                self.system_logger.log_assessment(assessment_data)

            self.logger.info("Результаты тестирования сохранены")

        except Exception as e:
            self.logger.error(f"Ошибка сохранения результатов: {str(e)}")

    def _show_results(
        self, score, score_count, total_questions, is_passed, debug_info=""
    ):
        """Отображает результаты тестирования."""
        with self.results_container:
            clear_output(wait=True)

            # Определяем стиль в зависимости от результата
            if is_passed:
                style = "background: linear-gradient(135deg, #4CAF50, #45a049); color: white;"
                status_icon = "✅"
                status_text = "Тест пройден"
            else:
                style = "background: linear-gradient(135deg, #f44336, #d32f2f); color: white;"
                status_icon = "❌"
                status_text = "Тест не пройден"

            # Виджет результатов
            results_widget = widgets.HTML(
                value=f"""
                <div style="text-align: center; padding: 30px; {style} border-radius: 10px;
                           margin: 20px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <h2 style="margin: 0 0 20px 0;">📊 Результаты теста</h2>
                    <div style="font-size: 18px; margin: 15px 0;">
                        <strong>Ваш результат: {score:.1f}%</strong>
                    </div>
                    <div style="font-size: 16px; margin: 10px 0;">
                        Правильных ответов: {score_count} из {total_questions}
                    </div>
                    <div style="font-size: 18px; margin: 20px 0;">
                        <strong>Статус: {status_icon} {status_text}</strong>
                    </div>
                    <div style="font-size: 14px; margin: 15px 0;">
                        Урок: {html.escape(self.current_lesson_info['lesson'])}
                    </div>
                </div>
                {debug_info}
                """
            )

            # Кнопка продолжения (только если тест пройден)
            if is_passed:
                continue_button = widgets.Button(
                    description="Продолжить обучение",
                    button_style="success",
                    layout=widgets.Layout(
                        width="250px",
                        height="50px",
                        margin="20px auto",
                        display="block",
                    ),
                )

                def handle_continue(b):
                    self._continue_to_next_lesson()

                continue_button.on_click(handle_continue)

                display(widgets.VBox([results_widget, continue_button]))
            else:
                # Кнопка повторной попытки
                retry_button = widgets.Button(
                    description="Попробовать снова",
                    button_style="info",
                    layout=widgets.Layout(
                        width="250px",
                        height="50px",
                        margin="20px auto",
                        display="block",
                    ),
                )

                def handle_retry(b):
                    # Перезагружаем интерфейс тестирования
                    assessment_widget = self.show_assessment(
                        self.current_lesson_info["course"],
                        self.current_lesson_info["section"],
                        self.current_lesson_info["topic"],
                        self.current_lesson_info["lesson"],
                        self.current_lesson_info["content"],
                    )
                    clear_output(wait=True)
                    display(assessment_widget)

                retry_button.on_click(handle_retry)

                display(widgets.VBox([results_widget, retry_button]))

    def _continue_to_next_lesson(self):
        """ИСПРАВЛЕНО: Правильная логика перехода к следующему уроку."""
        try:
            self.logger.info("=== ПЕРЕХОД К СЛЕДУЮЩЕМУ УРОКУ ===")

            # Проверяем доступность content_generator
            if not self.content_generator:
                self._show_content_generator_error()
                return

            # Получаем следующий урок
            next_lesson = self.state_manager.get_next_lesson()
            self.logger.info(f"Следующий урок из state_manager: {next_lesson}")

            if next_lesson and len(next_lesson) >= 3:
                section_id, topic_id, lesson_id = next_lesson[:3]
                self.logger.info(
                    f"Переходим к уроку: {section_id}:{topic_id}:{lesson_id}"
                )

                # ПРАВИЛЬНЫЙ ПАТТЕРН ИЗ PROJECT KNOWLEDGE:
                from lesson_interface import LessonInterface

                lesson_ui = LessonInterface(
                    state_manager=self.state_manager,
                    content_generator=self.content_generator,
                    system_logger=self.system_logger,
                    assessment=self.assessment,
                    parent_facade=self.parent_facade,
                )

                # Очищаем экран и отображаем новый урок
                clear_output(wait=True)

                # Генерируем и отображаем следующий урок
                lesson_widget = lesson_ui.show_lesson(section_id, topic_id, lesson_id)
                display(lesson_widget)

                self.logger.info(
                    f"✅ Успешный переход к уроку {section_id}:{topic_id}:{lesson_id}"
                )

            else:
                # Курс завершен
                self._show_course_completion()

        except Exception as e:
            self.logger.error(f"Ошибка перехода к следующему уроку: {str(e)}")
            self._show_transition_error(str(e))

    def _show_content_generator_error(self):
        """Показывает ошибку недоступности генератора контента."""
        error_widget = widgets.HTML(
            value="""
            <div style='color: red; padding: 20px; text-align: center; border: 1px solid red; border-radius: 8px; margin: 20px;'>
                <h3>Ошибка перехода к уроку</h3>
                <p>Генератор контента недоступен. Перезапустите систему для продолжения обучения.</p>
                <p><small>Убедитесь, что AssessmentInterface создается с parent_facade в interface_facade.py</small></p>
            </div>
            """
        )
        clear_output(wait=True)
        display(error_widget)
        self.logger.error("content_generator недоступен для создания следующего урока")

    def _show_course_completion(self):
        """Показывает сообщение о завершении курса."""
        completion_message = widgets.HTML(
            value="""
            <div style="text-align: center; padding: 50px; background: linear-gradient(135deg, #FFD700, #FFA500);
                       color: white; border-radius: 15px; margin: 20px; box-shadow: 0 8px 16px rgba(0,0,0,0.2);">
                <h1 style="margin: 0 0 20px 0; font-size: 36px;">🎉 Поздравляем!</h1>
                <h2 style="margin: 0 0 15px 0; font-size: 24px;">Курс успешно завершен!</h2>
                <p style="font-size: 18px; margin: 0;">Все уроки пройдены. Отличная работа!</p>
            </div>
            """
        )
        clear_output(wait=True)
        display(completion_message)
        self.logger.info("Курс завершен - все уроки пройдены")

    def _show_transition_error(self, error_msg):
        """Показывает ошибку перехода к следующему уроку."""
        error_widget = widgets.HTML(
            value=f"""
            <div style='color: red; padding: 20px; text-align: center; border: 1px solid red; border-radius: 8px; margin: 20px;'>
                <h3>Ошибка перехода к следующему уроку</h3>
                <p>Произошла ошибка: {html.escape(error_msg)}</p>
                <p>Попробуйте перезапустить систему.</p>
            </div>
            """
        )
        clear_output(wait=True)
        display(error_widget)

    def _create_error_widget(self, title, message):
        """Создает виджет для отображения ошибки."""
        return widgets.HTML(
            value=f"""
            <div style='color: red; padding: 20px; text-align: center; border: 1px solid red; border-radius: 8px; margin: 20px;'>
                <h3>{html.escape(title)}</h3>
                <p>{html.escape(message)}</p>
            </div>
            """
        )

    def _get_course_plan(self):
        """Получает план курса из state_manager."""
        try:
            if hasattr(self.state_manager, "get_course_plan"):
                return self.state_manager.get_course_plan()
            elif hasattr(self.state_manager, "course_data_manager"):
                return self.state_manager.course_data_manager.get_course_plan()
            elif (
                hasattr(self.state_manager, "state")
                and "course_plan" in self.state_manager.state
            ):
                return self.state_manager.state["course_plan"]
            else:
                return None
        except Exception as e:
            self.logger.error(f"Ошибка получения плана курса: {str(e)}")
            return None
