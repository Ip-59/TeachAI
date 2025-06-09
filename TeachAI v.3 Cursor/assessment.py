"""
Модуль для контроля знаний и оценивания.
Отвечает за генерацию тестов, проверку ответов и расчет оценок.
"""

import logging
from enum import Enum


class AnswerResult(Enum):
    """Перечисление для результатов ответа на вопрос."""

    CORRECT = "correct"
    INCORRECT = "incorrect"


class Assessment:
    """Класс для оценивания знаний пользователя."""

    def __init__(self, content_generator, logger):
        """
        Инициализация модуля оценивания.

        Args:
            content_generator (ContentGenerator): Объект генератора контента
            logger (Logger): Объект логгера
        """
        self.content_generator = content_generator
        self.system_logger = logger
        self.logger = logging.getLogger(__name__)

        # Стили для отображения вопросов и ответов
        self.styles = {
            "container": "font-family: Arial, sans-serif; font-size: 16px; line-height: 1.6; padding: 20px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 20px;",
            "question_box": "margin-bottom: 20px; padding: 15px; border: 1px solid #dee2e6; border-radius: 5px; background-color: #ffffff;",
            "question_title": "font-size: 18px; font-weight: bold; margin-bottom: 15px; color: #212529;",
            "options_list": "list-style-type: none; padding-left: 0;",
            "option_item": "margin-bottom: 10px; padding: 10px; border: 1px solid #ced4da; border-radius: 5px; cursor: pointer;",
            "option_selected": "background-color: #e9ecef; border-color: #adb5bd;",
            "correct": "background-color: #d4edda; color: #155724; border-color: #c3e6cb;",
            "incorrect": "background-color: #f8d7da; color: #721c24; border-color: #f5c6cb;",
            "result_box": "margin-top: 20px; padding: 15px; border-radius: 5px;",
            "button": "padding: 10px 15px; background-color: #007bff; color: #ffffff; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;",
            "button_hover": "background-color: #0069d9;",
            "score_high": "background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; font-size: 18px; font-weight: bold; text-align: center;",
            "score_medium": "background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; font-size: 18px; font-weight: bold; text-align: center;",
            "score_low": "background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; font-size: 18px; font-weight: bold; text-align: center;",
        }

    def generate_questions(
        self, course, section, topic, lesson, lesson_content, num_questions=5
    ):
        """
        Генерирует вопросы для проверки знаний.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson (str): Название урока
            lesson_content (str): Содержание урока
            num_questions (int): Количество вопросов

        Returns:
            list: Список вопросов с вариантами ответов

        Raises:
            Exception: Если не удалось сгенерировать вопросы
        """
        try:
            questions = self.content_generator.generate_assessment(
                course, section, topic, lesson, lesson_content, num_questions
            )

            # Логируем успешную генерацию вопросов
            self.system_logger.log_activity(
                action_type="questions_generated",
                details={
                    "course": course,
                    "section": section,
                    "topic": topic,
                    "lesson": lesson,
                    "num_questions": len(questions),
                },
            )

            self.logger.info(
                f"Успешно сгенерировано {len(questions)} вопросов для урока '{lesson}'"
            )
            return questions

        except Exception as e:
            # Логируем ошибку
            self.system_logger.log_activity(
                action_type="questions_generation_failed",
                status="error",
                error=str(e),
                details={
                    "course": course,
                    "section": section,
                    "topic": topic,
                    "lesson": lesson,
                },
            )

            self.logger.error(f"Критическая ошибка при генерации вопросов: {str(e)}")
            raise Exception(
                f"Не удалось сгенерировать вопросы для урока '{lesson}': {str(e)}"
            )

    def check_answer(self, question, user_answer):
        """
        Проверяет ответ пользователя.

        Args:
            question (dict): Словарь с данными вопроса
            user_answer (int): Ответ пользователя (индекс, начиная с 1)

        Returns:
            tuple: (результат, правильный ответ)
        """
        try:
            # Если в вопросе указан correct_answer, используем его
            if "correct_answer" in question:
                correct_answer = question["correct_answer"]
            # Если в вопросе указан correct_option, используем его
            elif "correct_option" in question:
                correct_answer = question["correct_option"]
            else:
                self.logger.error(
                    "В вопросе отсутствует информация о правильном ответе"
                )
                raise ValueError(
                    "Некорректный формат вопроса: отсутствует правильный ответ"
                )

            # Проверяем ответ пользователя
            if user_answer == correct_answer:
                return AnswerResult.CORRECT, correct_answer
            else:
                return AnswerResult.INCORRECT, correct_answer

        except Exception as e:
            self.logger.error(f"Ошибка при проверке ответа: {str(e)}")
            raise

    def calculate_score(self, questions, user_answers):
        """
        Рассчитывает оценку за тест.

        Args:
            questions (list): Список вопросов
            user_answers (list): Список ответов пользователя

        Returns:
            tuple: (оценка, список результатов, список правильных ответов)
        """
        try:
            if len(questions) != len(user_answers):
                self.logger.error(
                    "Количество вопросов не соответствует количеству ответов"
                )
                raise ValueError(
                    "Количество вопросов не соответствует количеству ответов"
                )

            results = []
            correct_answers = []

            # Проверяем каждый ответ
            for i, question in enumerate(questions):
                result, correct_answer = self.check_answer(question, user_answers[i])
                results.append(result)
                correct_answers.append(correct_answer)

            # Рассчитываем оценку (0-100)
            correct_count = results.count(AnswerResult.CORRECT)
            score = (correct_count / len(questions)) * 100

            self.logger.info(
                f"Оценка рассчитана: {score:.1f}% ({correct_count}/{len(questions)})"
            )
            return score, results, correct_answers

        except Exception as e:
            self.logger.error(f"Ошибка при расчете оценки: {str(e)}")
            raise

    def log_assessment_results(
        self,
        course,
        section,
        topic,
        lesson,
        questions,
        user_answers,
        correct_answers,
        score,
    ):
        """
        Записывает результаты тестирования в лог.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson (str): Название урока
            questions (list): Список вопросов
            user_answers (list): Список ответов пользователя
            correct_answers (list): Список правильных ответов
            score (float): Оценка (0-100)

        Returns:
            bool: True если запись прошла успешно, иначе False
        """
        try:
            # Записываем результаты в лог
            self.system_logger.log_assessment(
                course=course,
                section=section,
                topic=topic,
                lesson=lesson,
                questions=questions,
                user_answers=user_answers,
                correct_answers=correct_answers,
                score=score,
            )

            # Логируем действие
            self.system_logger.log_activity(
                action_type="assessment_completed",
                details={
                    "course": course,
                    "section": section,
                    "topic": topic,
                    "lesson": lesson,
                    "score": score,
                    "questions_count": len(questions),
                },
            )

            self.logger.info(f"Результаты тестирования успешно записаны: {score:.1f}%")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка при записи результатов тестирования: {str(e)}")

            # Логируем ошибку
            self.system_logger.log_activity(
                action_type="assessment_log_failed",
                status="error",
                error=str(e),
                details={
                    "course": course,
                    "section": section,
                    "topic": topic,
                    "lesson": lesson,
                },
            )

            return False

    def format_questions_html(self, questions):
        """
        Форматирует список вопросов в HTML с правильными стилями.

        Args:
            questions (list): Список вопросов

        Returns:
            str: HTML-код с отформатированными вопросами
        """
        html = f"""
        <div style="{self.styles['container']}">
            <h2 style="font-size: 24px; margin-bottom: 20px;">Проверка знаний</h2>
        """

        for i, question in enumerate(questions):
            html += f"""
            <div style="{self.styles['question_box']}" id="question-{i+1}">
                <div style="{self.styles['question_title']}">Вопрос {i+1}: {question['text']}</div>
                <div style="{self.styles['options_list']}">
            """

            for j, option in enumerate(question.get("options", [])):
                html += f"""
                <div style="{self.styles['option_item']}" onclick="selectOption({i+1}, {j+1})" id="option-{i+1}-{j+1}">
                    <label style="display: block; cursor: pointer;">
                        <input type="radio" name="question-{i+1}" value="{j+1}" style="margin-right: 10px;">
                        {option}
                    </label>
                </div>
                """

            html += """
                </div>
            </div>
            """

        html += """
        </div>
        <script>
            function selectOption(questionNumber, optionNumber) {
                // Сначала снимаем выделение со всех опций этого вопроса
                const options = document.querySelectorAll(`[id^=option-${questionNumber}-]`);
                options.forEach(option => {
                    option.style.backgroundColor = '';
                    option.style.borderColor = '#ced4da';
                });

                // Выделяем выбранную опцию
                const selectedOption = document.getElementById(`option-${questionNumber}-${optionNumber}`);
                selectedOption.style.backgroundColor = '#e9ecef';
                selectedOption.style.borderColor = '#adb5bd';

                // Устанавливаем значение радиокнопки
                const radioInput = selectedOption.querySelector('input[type="radio"]');
                radioInput.checked = true;
            }
        </script>
        """

        return html

    def format_results_html(self, questions, user_answers, correct_answers, score):
        """
        Форматирует результаты тестирования в HTML с правильными стилями.

        Args:
            questions (list): Список вопросов
            user_answers (list): Список ответов пользователя
            correct_answers (list): Список правильных ответов
            score (float): Оценка (0-100)

        Returns:
            str: HTML-код с отформатированными результатами
        """
        # Определяем стиль отображения оценки в зависимости от результата
        if score >= 80:
            score_style = self.styles["score_high"]
        elif score >= 60:
            score_style = self.styles["score_medium"]
        else:
            score_style = self.styles["score_low"]

        html = f"""
        <div style="{self.styles['container']}">
            <h2 style="font-size: 24px; margin-bottom: 20px;">Результаты тестирования</h2>
            <div style="{score_style}">Ваш результат: {score:.1f}%</div>
            <div style="margin-top: 20px;">
        """

        for i, (question, user_answer, correct_answer) in enumerate(
            zip(questions, user_answers, correct_answers)
        ):
            html += f"""
            <div style="{self.styles['question_box']}">
                <div style="{self.styles['question_title']}">Вопрос {i+1}: {question['text']}</div>
                <div style="{self.styles['options_list']}">
            """

            for j, option in enumerate(question.get("options", [])):
                option_num = j + 1
                style = self.styles["option_item"]

                if option_num == user_answer and option_num == correct_answer:
                    style += f"; {self.styles['correct']}"
                    label = f"{option} ✓ (Ваш ответ, правильно)"
                elif option_num == user_answer:
                    style += f"; {self.styles['incorrect']}"
                    label = f"{option} ✗ (Ваш ответ, неправильно)"
                elif option_num == correct_answer:
                    style += f"; {self.styles['correct']}"
                    label = f"{option} ✓ (Правильный ответ)"
                else:
                    label = option

                html += f"""
                <div style="{style}">
                    {label}
                </div>
                """

            html += """
                </div>
            </div>
            """

        html += """
            </div>
        </div>
        """

        return html
