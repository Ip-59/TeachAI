"""
Модуль для контроля знаний и оценивания.
Отвечает за генерацию тестов, проверку ответов и расчет оценок.

ИСПРАВЛЕНО ЭТАП 33: Добавлен недостающий метод log_activity (проблема #138)
ИСПРАВЛЕНО ЭТАП 36: Исправлен вызов generate_assessment с правильными параметрами (проблема #149)
ИСПРАВЛЕНО ЭТАП 37: Исправлены ключи 'question' → 'text' в format_question_html и format_results_html (проблема #155)
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

    # ИСПРАВЛЕНО ЭТАП 33: Добавлен недостающий метод для совместимости
    def log_activity(self, action_type, details=None, status="success", error=None):
        """
        Делегирует логирование к system_logger.

        Args:
            action_type (str): Тип действия
            details (dict): Детали действия
            status (str): Статус выполнения
            error (str): Сообщение об ошибке (если есть)
        """
        if self.system_logger:
            self.system_logger.log_activity(action_type, details, status, error)

    def generate_questions(
        self, course, section, topic, lesson, lesson_content, num_questions=5
    ):
        """
        Генерирует вопросы для теста по содержанию урока.

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
            # ИСПРАВЛЕНО ЭТАП 36: Формируем lesson_data для правильного вызова generate_assessment (проблема #149)
            lesson_data = {
                "course_title": course,
                "section_title": section,
                "topic_title": topic,
                "title": lesson,
            }

            questions = self.content_generator.generate_assessment(
                lesson_data, lesson_content, num_questions
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
            question (dict): Словарь с данными вопроса, включая правильный ответ
            user_answer (int): Выбранный пользователем номер ответа (1, 2 или 3)

        Returns:
            AnswerResult: CORRECT или INCORRECT
        """
        try:
            correct_answer = question.get("correct_answer", 1)

            if user_answer == correct_answer:
                return AnswerResult.CORRECT
            else:
                return AnswerResult.INCORRECT

        except Exception as e:
            self.logger.error(f"Ошибка при проверке ответа: {str(e)}")
            return AnswerResult.INCORRECT

    def calculate_score(self, questions, user_answers):
        """
        Рассчитывает итоговый балл по результатам теста.

        Args:
            questions (list): Список вопросов
            user_answers (list): Список ответов пользователя

        Returns:
            tuple: (score_percentage, correct_answers_list, score_count)
        """
        try:
            if not questions or not user_answers:
                return 0.0, [], 0

            correct_answers = []
            score_count = 0

            for i, question in enumerate(questions):
                # Получаем правильный ответ для вопроса
                correct_answer = question.get(
                    "correct_option", question.get("correct_answer", 1)
                )
                correct_answers.append(correct_answer)

                # Проверяем ответ пользователя
                if i < len(user_answers) and user_answers[i] == correct_answer:
                    score_count += 1

            # Рассчитываем процент правильных ответов
            score_percentage = (score_count / len(questions)) * 100

            self.logger.info(
                f"Результат теста: {score_count}/{len(questions)} ({score_percentage:.1f}%)"
            )

            return score_percentage, correct_answers, score_count

        except Exception as e:
            self.logger.error(f"Ошибка при расчете балла: {str(e)}")
            return 0.0, [], 0

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
            score (float): Оценка за тест (0-100)

        Returns:
            bool: True если запись прошла успешно, иначе False
        """
        try:
            # Используем system_logger для записи результатов
            self.system_logger.log_assessment_results(
                course=course,
                section=section,
                topic=topic,
                lesson=lesson,
                questions=questions,
                user_answers=user_answers,
                correct_answers=correct_answers,
                score=score,
            )

            self.logger.info(f"Результаты теста успешно записаны в лог")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка при записи результатов теста: {str(e)}")
            return False

    def format_question_html(self, question, question_index):
        """
        Форматирует вопрос в HTML для отображения.

        Args:
            question (dict): Данные вопроса
            question_index (int): Номер вопроса

        Returns:
            str: HTML-код вопроса
        """
        try:
            # ИСПРАВЛЕНО ЭТАП 37: Правильный ключ 'text' вместо 'question' (проблема #155)
            question_text = question.get("text", "Вопрос не загружен")
            options = question.get("options", ["Вариант 1", "Вариант 2", "Вариант 3"])

            html = f"""
            <div style="{self.styles['question_box']}">
                <div style="{self.styles['question_title']}">
                    Вопрос {question_index + 1}: {question_text}
                </div>
                <ul style="{self.styles['options_list']}">
            """

            for i, option in enumerate(options, 1):
                html += f"""
                    <li style="{self.styles['option_item']}" data-question="{question_index}" data-answer="{i}">
                        {i}. {option}
                    </li>
                """

            html += """
                </ul>
            </div>
            """

            return html

        except Exception as e:
            self.logger.error(f"Ошибка при форматировании вопроса: {str(e)}")
            return f"""
            <div style="{self.styles['question_box']}">
                <div style="color: red;">Ошибка при загрузке вопроса {question_index + 1}</div>
            </div>
            """

    def format_results_html(self, questions, user_answers, score_data):
        """
        Форматирует результаты теста в HTML.

        Args:
            questions (list): Список вопросов
            user_answers (list): Ответы пользователя
            score_data (dict): Данные о результатах

        Returns:
            str: HTML-код с результатами
        """
        try:
            # Определяем стиль для общего результата
            percentage = score_data.get("percentage", 0)
            if percentage >= 75:
                result_style = self.styles["score_high"]
            elif percentage >= 60:
                result_style = self.styles["score_medium"]
            else:
                result_style = self.styles["score_low"]

            html = f"""
            <div style="{self.styles['result_box']}">
                <div style="{result_style}">
                    Результат: {score_data['correct_answers']}/{score_data['total_questions']}
                    ({score_data['percentage']}%) - {score_data['grade']}
                </div>
            """

            # Показываем детали по каждому вопросу
            for i, question in enumerate(questions):
                user_answer = user_answers[i] if i < len(user_answers) else None
                correct_answer = question.get("correct_answer", 1)
                options = question.get("options", [])

                is_correct = user_answer == correct_answer
                status_color = "#155724" if is_correct else "#721c24"
                status_bg = "#d4edda" if is_correct else "#f8d7da"
                status_text = "Правильно" if is_correct else "Неправильно"

                # ИСПРАВЛЕНО ЭТАП 37: Правильный ключ 'text' вместо 'question' (проблема #155)
                html += f"""
                <div style="margin: 15px 0; padding: 10px; border-radius: 5px; background-color: {status_bg}; color: {status_color};">
                    <strong>Вопрос {i + 1}:</strong> {question.get('text', 'Вопрос не загружен')}<br/>
                    <strong>Ваш ответ:</strong> {options[user_answer-1] if user_answer and user_answer <= len(options) else 'Не отвечен'}<br/>
                    <strong>Правильный ответ:</strong> {options[correct_answer-1] if correct_answer <= len(options) else 'Ошибка в данных'}<br/>
                    <strong>Результат:</strong> {status_text}
                </div>
                """

            html += "</div>"
            return html

        except Exception as e:
            self.logger.error(f"Ошибка при форматировании результатов: {str(e)}")
            return f"""
            <div style="{self.styles['result_box']}">
                <div style="color: red;">Ошибка при отображении результатов: {str(e)}</div>
            </div>
            """

    def generate_test_completion_message(
        self, score_percentage, course_title, lesson_title
    ):
        """
        Генерирует сообщение о завершении теста.

        Args:
            score_percentage (float): Процент правильных ответов
            course_title (str): Название курса
            lesson_title (str): Название урока

        Returns:
            str: HTML-сообщение о завершении
        """
        try:
            if score_percentage >= 80:
                message_style = self.styles["score_high"]
                emoji = "🎉"
                message = "Отличный результат!"
            elif score_percentage >= 60:
                message_style = self.styles["score_medium"]
                emoji = "👍"
                message = "Хороший результат!"
            else:
                message_style = self.styles["score_low"]
                emoji = "📚"
                message = "Стоит повторить материал."

            return f"""
            <div style="{message_style}">
                {emoji} {message} Тест по уроку "{lesson_title}" (курс "{course_title}") завершен.
                Ваш результат: {score_percentage:.1f}%
            </div>
            """

        except Exception as e:
            self.logger.error(f"Ошибка при генерации сообщения завершения: {str(e)}")
            return f"""
            <div style="{self.styles['result_box']}">
                <div>Тест завершен. Результат: {score_percentage:.1f}%</div>
            </div>
            """

    def get_assessment_statistics(self):
        """
        Возвращает статистику по всем пройденным тестам.

        Returns:
            dict: Статистика тестирования
        """
        try:
            # Получаем статистику от system_logger
            if hasattr(self.system_logger, "get_assessment_statistics"):
                return self.system_logger.get_assessment_statistics()
            else:
                return {
                    "total_tests": 0,
                    "average_score": 0.0,
                    "completed_lessons": [],
                    "message": "Статистика недоступна",
                }

        except Exception as e:
            self.logger.error(f"Ошибка при получении статистики: {str(e)}")
            return {
                "total_tests": 0,
                "average_score": 0.0,
                "completed_lessons": [],
                "error": str(e),
            }
