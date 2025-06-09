"""
Интерфейс для тестирования знаний учащихся.
Отвечает за отображение тестов, обработку ответов и показ результатов.

ИСПРАВЛЕНО ЭТАП 40: Восстановлена правильная архитектура автоматического перехода к урокам (проблема #171)
ОСНОВАНО НА: project knowledge - lesson_interface.py, main_menu_interface.py
ПРОБЛЕМЫ РЕШЕНЫ: #165, #166, #167, #168, #169, #170 (сохранены все исправления)
ВОССТАНОВЛЕНО: автоматический переход к следующему уроку через lesson_interface.show_lesson()
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
            parent_facade: Ссылка на родительский фасад (опционально)
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

        self.logger.info("AssessmentInterface инициализирован")

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
            current_course (str): ID текущего курса
            current_section (str): ID текущего раздела
            current_topic (str): ID текущей темы
            current_lesson (str): ID текущего урока
            current_lesson_content (str): Содержание урока для генерации тестов

        Returns:
            widgets.VBox: Интерфейс тестирования
        """
        try:
            self.logger.info("Создание интерфейса тестирования")

            # Получаем названия элементов
            course_plan = self._get_course_plan()
            (
                course_title,
                section_title,
                topic_title,
                lesson_title,
            ) = self._get_element_titles(course_plan)

            if not lesson_title or lesson_title == "Урок":
                lesson_title = current_lesson or "Урок"

            # Создаем навигационную информацию
            nav_info = self.utils.create_navigation_info(
                course_title, section_title, topic_title, lesson_title
            )

            # Заголовок тестирования
            test_header = widgets.HTML(
                value="""
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #4CAF50, #45a049);
                           color: white; border-radius: 10px; margin: 20px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <h2 style="margin: 0; font-size: 24px;">📝 Проверка знаний</h2>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">Ответьте на следующие вопросы по теме <strong>{}</strong>, чтобы проверить свои знания.</p>
                </div>
                """.format(
                    html.escape(lesson_title)
                )
            )

            # Генерируем вопросы для тестирования
            self.current_questions = self._generate_questions(
                current_lesson_content,
                {
                    "course": course_title,
                    "section": section_title,
                    "topic": topic_title,
                    "lesson": lesson_title,
                },
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
            self.results_container = widgets.VBox()

            # Обработчик кнопки завершения теста
            submit_button.on_click(
                lambda b: self._handle_test_submission(
                    b, course_title, section_title, topic_title, lesson_title
                )
            )

            # Создаем стабильный main_container (ИСПРАВЛЕНО ЭТАП 40: проблема #165)
            main_container = widgets.VBox(
                [
                    nav_info,
                    test_header,
                    questions_interface,
                    submit_button,
                    self.results_container,
                ],
                layout=widgets.Layout(
                    margin="0 auto", max_width="900px", padding="0 20px"
                ),
            )

            return main_container

        except Exception as e:
            self.logger.error(f"Ошибка создания интерфейса тестирования: {str(e)}")
            return self.utils.create_styled_message(
                f"Ошибка создания тестирования: {str(e)}", "incorrect"
            )

    def _generate_questions(self, lesson_content, course_info):
        """
        Генерирует вопросы для тестирования.

        Args:
            lesson_content (str): Содержание урока
            course_info (dict): Информация о курсе

        Returns:
            list: Список вопросов
        """
        try:
            self.logger.info("Генерация вопросов для тестирования")

            # Извлекаем параметры для assessment.generate_questions
            course_title = course_info.get("course", "Курс")
            section_title = course_info.get("section", "Раздел")
            topic_title = course_info.get("topic", "Тема")
            lesson_title = course_info.get("lesson", "Урок")

            self.logger.info(
                f"Генерация вопросов для: {course_title} → {section_title} → {topic_title} → {lesson_title}"
            )
            self.logger.info(
                f"Размер контента урока: {len(lesson_content) if lesson_content else 0} символов"
            )

            # Генерируем вопросы через assessment с правильными параметрами
            questions = self.assessment.generate_questions(
                course=course_title,
                section=section_title,
                topic=topic_title,
                lesson=lesson_title,
                lesson_content=lesson_content,
                num_questions=5,
            )

            if not questions:
                self.logger.warning("Не удалось сгенерировать вопросы")
                return []

            self.logger.info(f"Сгенерировано {len(questions)} вопросов")
            return questions

        except Exception as e:
            self.logger.error(f"Ошибка генерации вопросов: {str(e)}")
            return []

    def _create_questions_interface(self):
        """
        Создает интерфейс вопросов.

        Returns:
            widgets.VBox: Интерфейс вопросов
        """
        if not self.current_questions:
            return widgets.HTML(
                value="<div style='text-align: center; color: #666; padding: 20px;'>Вопросы недоступны</div>"
            )

        questions_widgets = []

        for i, question in enumerate(self.current_questions):
            # Заголовок вопроса
            question_title = widgets.HTML(
                value=f"<h3 style='margin: 20px 0 10px 0; color: #333;'>Вопрос {i + 1}: {html.escape(question['text'])}</h3>"
            )

            # Варианты ответов
            options = question.get("options", [])
            if not options:
                continue

            self.logger.info(f"Вопрос {i + 1}: варианты = {options}")

            # Обычные RadioButtons (проверенно работающие)
            radio_group = widgets.RadioButtons(
                options=options,
                value=None,
                disabled=False,
                layout=widgets.Layout(margin="0 0 0 20px", width="100%"),
            )

            # Обработчик выбора ответа (ПРОВЕРЕННЫЙ РАБОЧИЙ КОД)
            def make_answer_handler(question_index, opts=options):
                def answer_handler(change):
                    if change["new"] is not None:
                        selected_option = change["new"]
                        self.logger.info(
                            f"Вопрос {question_index + 1}: выбран '{selected_option}' = вариант {opts.index(selected_option) + 1}"
                        )
                        answer_letter = opts.index(selected_option) + 1
                        self.current_answers[question_index] = answer_letter
                        self.logger.info(f"Текущие ответы: {self.current_answers}")

                return answer_handler

            radio_group.observe(make_answer_handler(i), names="value")

            # Контейнер вопроса
            question_container = widgets.VBox(
                [question_title, radio_group],
                layout=widgets.Layout(
                    margin="10px 0",
                    padding="15px",
                    border="1px solid #ddd",
                    border_radius="8px",
                ),
            )

            questions_widgets.append(question_container)

        return widgets.VBox(questions_widgets)

    def _handle_test_submission(
        self, button, course_title, section_title, topic_title, lesson_title
    ):
        """
        Обрабатывает отправку теста.

        Args:
            button: Кнопка, которая была нажата
            course_title (str): Название курса
            section_title (str): Название раздела
            topic_title (str): Название темы
            lesson_title (str): Название урока
        """
        try:
            self.logger.info("Обработка результатов теста")

            # Преобразуем ответы в список (ПРОСТОЙ РАБОЧИЙ КОД)
            user_answers = []
            for i in range(len(self.current_questions)):
                answer = self.current_answers.get(i, 0)
                user_answers.append(answer)

            # ИСПРАВЛЕНО ЭТАП 40: отладочное логирование (проблема #170)
            self.logger.info("=== ОТЛАДКА РЕЗУЛЬТАТОВ ТЕСТА ===")
            self.logger.info(f"Количество вопросов: {len(self.current_questions)}")
            self.logger.info(f"Ответы пользователя: {user_answers}")

            # Вычисляем результаты
            score, correct_answers, score_count = self.assessment.calculate_score(
                self.current_questions, user_answers
            )

            self.logger.info(
                f"Результат calculate_score: score={score}, correct_answers={correct_answers}, score_count={score_count}"
            )

            # ИСПРАВЛЕНО ЭТАП 40: проблема #170 - преобразование букв в цифры
            if correct_answers and isinstance(correct_answers[0], str):
                # Преобразуем буквы в цифры: A=1, B=2, C=3
                letter_to_number = {"A": 1, "B": 2, "C": 3}
                correct_answers_numbers = [
                    letter_to_number.get(answer, 1) for answer in correct_answers
                ]

                self.logger.info(
                    f"ИСПРАВЛЕНО: Буквы {correct_answers} -> Цифры {correct_answers_numbers}"
                )

                # Пересчитываем результат с правильными форматами
                score_count = sum(
                    1
                    for i in range(len(user_answers))
                    if i < len(correct_answers_numbers)
                    and user_answers[i] == correct_answers_numbers[i]
                )
                score = (score_count / len(self.current_questions)) * 100

                self.logger.info(
                    f"ПЕРЕСЧИТАНО: score={score}%, score_count={score_count}"
                )

            self.logger.info(
                f"Результат теста: {score_count}/{len(self.current_questions)} ({score:.1f}%)"
            )

            # Сохраняем результаты
            self._save_assessment_results(
                course_title,
                section_title,
                topic_title,
                lesson_title,
                self.current_questions,
                user_answers,
                correct_answers,
                score,
            )

            # Определяем статус прохождения
            is_passed = score >= 70

            # Отмечаем урок как завершенный
            lesson_key = f"{section_title}:{topic_title}:{lesson_title}"
            self.state_manager.mark_lesson_completed(lesson_key)
            self.logger.info(
                f"Урок {lesson_key} отмечен как завершенный с оценкой {score:.1f}%"
            )

            # Отображаем результаты (ИСПРАВЛЕНО ЭТАП 40: проблема #165 - без сдвига интерфейса)
            results_widget = self._create_results_widget(
                score, score_count, len(self.current_questions), is_passed, lesson_title
            )

            self.results_container.children = [results_widget]

            # Детальное логирование результатов (ИСПРАВЛЕНО ЭТАП 40: проблема #168)
            self.logger.info(f"=== РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ ===")
            self.logger.info(f"Курс: {course_title}")
            self.logger.info(f"Раздел: {section_title}")
            self.logger.info(f"Тема: {topic_title}")
            self.logger.info(f"Урок: {lesson_title}")
            self.logger.info(f"Оценка: {score:.1f}%")
            self.logger.info(
                f"Правильных ответов: {score_count} из {len(self.current_questions)}"
            )
            self.logger.info(f"Статус: {'ПРОЙДЕН' if is_passed else 'НЕ ПРОЙДЕН'}")

            # Безопасное использование system_logger если метод существует
            if hasattr(self.system_logger, "log_lesson"):
                try:
                    self.system_logger.log_lesson(
                        course=course_title,
                        section=section_title,
                        topic=topic_title,
                        lesson=lesson_title,
                        score=score,
                        passed=is_passed,
                    )
                except Exception as log_error:
                    self.logger.warning(
                        f"Ошибка логирования в system_logger: {log_error}"
                    )

        except Exception as e:
            self.logger.error(f"Ошибка при обработке результатов теста: {str(e)}")
            error_widget = widgets.HTML(
                value=f"<div style='color: red; padding: 20px;'>Ошибка при обработке результатов: {html.escape(str(e))}</div>"
            )
            self.results_container.children = [error_widget]

    def _create_results_widget(
        self, score, score_count, total_questions, is_passed, lesson_title
    ):
        """
        Создает виджет результатов теста.

        Args:
            score (float): Оценка в процентах
            score_count (int): Количество правильных ответов
            total_questions (int): Общее количество вопросов
            is_passed (bool): Пройден ли тест
            lesson_title (str): Название урока

        Returns:
            widgets.VBox: Виджет результатов
        """
        # Цвет результата
        color = "#4CAF50" if is_passed else "#f44336"
        status_icon = "✅" if is_passed else "❌"
        status_text = "Тест пройден" if is_passed else "Тест не пройден"

        # HTML результатов
        results_html = f"""
        <div style="text-align: center; padding: 30px; border: 2px solid {color};
                   border-radius: 15px; margin: 20px 0; background: linear-gradient(135deg, {color}20, {color}10);">
            <h2 style="color: {color}; margin: 0 0 20px 0; font-size: 28px;">📊 Результаты теста</h2>
            <div style="font-size: 20px; margin: 15px 0;">
                <strong>Ваш результат: {score:.1f}%</strong>
            </div>
            <div style="font-size: 18px; margin: 10px 0;">
                Правильных ответов: <strong>{score_count} из {total_questions}</strong>
            </div>
            <div style="font-size: 18px; margin: 15px 0; color: {color};">
                Статус: <strong>{status_icon} {status_text}</strong>
            </div>
            <div style="font-size: 16px; margin: 10px 0; color: #666;">
                Урок: <strong>{html.escape(lesson_title)}</strong>
            </div>
        </div>
        """

        results_widget = widgets.HTML(value=results_html)

        # Кнопка продолжения обучения
        continue_button = widgets.Button(
            description="Продолжить обучение",
            button_style="success",
            layout=widgets.Layout(
                width="200px",
                height="40px",
                margin="20px auto 10px auto",
                display="block",
            ),
        )

        # ИСПРАВЛЕНО ЭТАП 40: Восстановлена правильная архитектура перехода к урокам (проблема #171)
        def on_continue_clicked(b):
            """Обработчик кнопки продолжения обучения - ПРАВИЛЬНАЯ АРХИТЕКТУРА."""
            try:
                self.logger.info("Переход к следующему уроку")

                # Получаем следующий урок
                next_lesson = self.state_manager.get_next_lesson()

                if next_lesson and len(next_lesson) >= 3:
                    section_id, topic_id, lesson_id = next_lesson[:3]
                    self.logger.info(
                        f"Найден следующий урок: {section_id}:{topic_id}:{lesson_id}"
                    )

                    # ИСПРАВЛЕНО: Получаем content_generator правильно
                    content_generator = None
                    if self.parent_facade and hasattr(
                        self.parent_facade, "content_generator"
                    ):
                        content_generator = self.parent_facade.content_generator
                    elif hasattr(self, "content_generator"):
                        content_generator = self.content_generator

                    if not content_generator:
                        # Показываем ошибку, но не ломаем интерфейс
                        error_widget = widgets.HTML(
                            value="""
                            <div style='color: red; padding: 20px; text-align: center; border: 1px solid red; border-radius: 8px; margin: 20px;'>
                                <h3>Ошибка перехода к уроку</h3>
                                <p>Генератор контента недоступен. Перезапустите систему для продолжения обучения.</p>
                            </div>
                            """
                        )
                        clear_output(wait=True)
                        display(error_widget)
                        self.logger.error(
                            "content_generator недоступен для создания следующего урока"
                        )
                        return

                    # ПРАВИЛЬНЫЙ ПАТТЕРН ИЗ PROJECT KNOWLEDGE:
                    from lesson_interface import LessonInterface

                    lesson_ui = LessonInterface(
                        state_manager=self.state_manager,
                        content_generator=content_generator,
                        system_logger=self.system_logger,
                        assessment=self.assessment,
                        parent_facade=self.parent_facade,
                    )

                    # Очищаем экран и отображаем новый урок
                    clear_output(wait=True)

                    # Генерируем и отображаем следующий урок
                    lesson_widget = lesson_ui.show_lesson(
                        section_id, topic_id, lesson_id
                    )
                    display(lesson_widget)

                    self.logger.info(
                        f"Успешный переход к уроку {section_id}:{topic_id}:{lesson_id}"
                    )

                else:
                    # Курс завершен
                    clear_output(wait=True)
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
                    display(completion_message)
                    self.logger.info(
                        "Курс завершен - отображено сообщение о завершении"
                    )

            except Exception as e:
                self.logger.error(f"Ошибка при переходе к следующему уроку: {str(e)}")
                # Показываем ошибку, но не ломаем интерфейс
                error_widget = widgets.HTML(
                    value=f"""
                    <div style='color: red; padding: 20px; text-align: center; border: 1px solid red; border-radius: 8px; margin: 20px;'>
                        <h3>Критическая ошибка</h3>
                        <p><strong>Ошибка:</strong> {html.escape(str(e))}</p>
                        <p>Перезапустите систему для продолжения обучения.</p>
                    </div>
                    """
                )
                clear_output(wait=True)
                display(error_widget)

        continue_button.on_click(on_continue_clicked)

        return widgets.VBox([results_widget, continue_button])

    def _save_assessment_results(
        self,
        course_title,
        section_title,
        topic_title,
        lesson_title,
        questions,
        user_answers,
        correct_answers,
        score,
    ):
        """
        Сохраняет результаты тестирования.

        Args:
            course_title (str): Название курса
            section_title (str): Название раздела
            topic_title (str): Название темы
            lesson_title (str): Название урока
            questions (list): Список вопросов
            user_answers (list): Ответы пользователя
            correct_answers (list): Правильные ответы
            score (float): Оценка
        """
        try:
            # Сохраняем результаты через state_manager
            assessment_data = {
                "course": course_title,
                "section": section_title,
                "topic": topic_title,
                "lesson": lesson_title,
                "questions": questions,
                "user_answers": user_answers,
                "correct_answers": correct_answers,
                "score": score,
                "passed": score >= 70,
            }

            # Используем безопасное сохранение
            if hasattr(self.state_manager, "save_assessment_result"):
                self.state_manager.save_assessment_result(assessment_data)
            elif hasattr(self.state_manager, "save_assessment"):
                self.state_manager.save_assessment(assessment_data)
            else:
                self.logger.warning(
                    "Метод сохранения результатов не найден в state_manager"
                )

            self.logger.info("Результаты тестирования сохранены")

        except Exception as e:
            self.logger.error(f"Ошибка сохранения результатов: {str(e)}")

    def _get_course_plan(self):
        """
        Получает план курса из state_manager.

        Returns:
            dict: План курса или None
        """
        try:
            # Попробуем несколько способов получения плана курса
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
        except Exception:
            return None

    def _get_element_titles(self, course_plan):
        """
        Извлекает названия элементов из плана курса.

        ИСПРАВЛЕНО ЭТАП 40: Поддержка разных структур course_plan (проблема #167)

        Args:
            course_plan (dict): План курса

        Returns:
            tuple: (course_title, section_title, topic_title, lesson_title)
        """
        try:
            # Поддерживаем разные структуры course_plan
            if isinstance(course_plan, dict):
                course_title = course_plan.get("title", "Курс")

                if "sections" in course_plan:
                    sections = course_plan["sections"]

                    # Структура 1: sections как список
                    if isinstance(sections, list) and sections:
                        first_section = sections[0]
                        section_title = first_section.get("title", "Раздел")

                        topics = first_section.get("topics", [])
                        if isinstance(topics, list) and topics:
                            first_topic = topics[0]
                            topic_title = first_topic.get("title", "Тема")

                            lessons = first_topic.get("lessons", [])
                            if isinstance(lessons, list) and lessons:
                                first_lesson = lessons[0]
                                lesson_title = first_lesson.get("title", "Урок")
                                return (
                                    course_title,
                                    section_title,
                                    topic_title,
                                    lesson_title,
                                )

                    # Структура 2: sections как словарь
                    elif isinstance(sections, dict):
                        for section_id, section_data in sections.items():
                            section_title = section_data.get("title", "Раздел")

                            topics = section_data.get("topics", {})
                            if isinstance(topics, dict):
                                for topic_id, topic_data in topics.items():
                                    topic_title = topic_data.get("title", "Тема")

                                    lessons = topic_data.get("lessons", {})
                                    if isinstance(lessons, dict):
                                        for lesson_id, lesson_data in lessons.items():
                                            lesson_title = lesson_data.get(
                                                "title", "Урок"
                                            )
                                            return (
                                                course_title,
                                                section_title,
                                                topic_title,
                                                lesson_title,
                                            )

            # Fallback значения
            return ("Курс", "Раздел", "Тема", "Урок")

        except Exception as e:
            self.logger.error(f"Ошибка извлечения названий элементов: {str(e)}")
            return ("Курс", "Раздел", "Тема", "Урок")
