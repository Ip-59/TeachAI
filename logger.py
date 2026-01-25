"""
Модуль для логирования действий и ошибок системы.
Отвечает за запись логов в файлы разных типов для различных аспектов работы системы.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime


class Logger:
    """Логгер для записи действий и ошибок системы в различные файлы."""

    def __init__(self, log_dir="logs"):
        """
        Инициализация логгера.

        Args:
            log_dir (str): Директория для хранения логов
        """
        self.log_dir = log_dir
        self.lesson_history_file = os.path.join(log_dir, "lesson_history.md")
        self.questions_log_file = os.path.join(log_dir, "questions_log.json")
        self.assessment_log_file = os.path.join(log_dir, "assessment_log.json")
        self.activity_log_file = os.path.join(log_dir, "activity_log.json")

        # Настраиваем логгер Python
        self.logger = logging.getLogger(__name__)

        # Создаем директорию для логов, если она не существует
        os.makedirs(log_dir, exist_ok=True)

        # Инициализируем файлы логов, если они не существуют
        self._initialize_log_files()

    def _initialize_log_files(self):
        """Инициализирует файлы логов, если они не существуют."""
        try:
            # Инициализация lesson_history.md
            if not os.path.exists(self.lesson_history_file):
                with open(self.lesson_history_file, "w", encoding="utf-8") as f:
                    f.write("# История уроков\n\n")

            # Инициализация JSON логов
            for log_file in [
                self.questions_log_file,
                self.assessment_log_file,
                self.activity_log_file,
            ]:
                if not os.path.exists(log_file):
                    with open(log_file, "w", encoding="utf-8") as f:
                        json.dump([], f, ensure_ascii=False, indent=2)

            self.logger.debug("Файлы логов успешно инициализированы")
        except Exception as e:
            self.logger.error(f"Ошибка при инициализации файлов логов: {str(e)}")

    def _load_json_log(self, log_file):
        """
        Загружает JSON лог из файла.

        Args:
            log_file (str): Путь к файлу лога

        Returns:
            list: Список записей лога или пустой список в случае ошибки
        """
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.error(f"Ошибка при загрузке лога {log_file}: {str(e)}")
            return []

    def _save_json_log(self, log_file, log_data):
        """
        Сохраняет данные лога в JSON файл.

        Args:
            log_file (str): Путь к файлу лога
            log_data (list): Данные для сохранения

        Returns:
            bool: True если сохранение прошло успешно, иначе False
        """
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении лога {log_file}: {str(e)}")
            return False

    def log_lesson(self, course, section, topic, lesson_title, lesson_content):
        """
        Записывает информацию об уроке в историю уроков.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson_title (str): Заголовок урока
            lesson_content (str): Содержание урока

        Returns:
            bool: True если запись прошла успешно, иначе False
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(self.lesson_history_file, "a", encoding="utf-8") as f:
                f.write(f"## {lesson_title}\n")
                f.write(
                    f"**Курс:** {course} | **Раздел:** {section} | **Тема:** {topic}\n"
                )
                f.write(f"**Дата:** {timestamp}\n\n")
                # Сохраняем только первые 1000 символов контента для экономии места
                content_preview = lesson_content[:1000]
                if len(lesson_content) > 1000:
                    content_preview += "... (содержание сокращено)"
                f.write(f"{content_preview}\n\n")
                f.write("---\n\n")

            # Логируем действие
            self.log_activity(
                action_type="lesson_viewed",
                details={
                    "course": course,
                    "section": section,
                    "topic": topic,
                    "lesson_title": lesson_title,
                },
            )

            return True
        except Exception as e:
            self.logger.error(f"Ошибка при записи урока в историю: {str(e)}")
            return False

    def log_question(self, question, answer=None):
        """
        Записывает вопрос пользователя и ответ системы.

        Args:
            question (str): Вопрос пользователя
            answer (str, optional): Ответ системы

        Returns:
            bool: True если запись прошла успешно, иначе False
        """
        try:
            timestamp = datetime.now().isoformat()

            # Загружаем текущий лог вопросов
            questions_log = self._load_json_log(self.questions_log_file)

            # Добавляем новую запись
            questions_log.append(
                {"timestamp": timestamp, "question": question, "answer": answer}
            )

            # Сохраняем обновленный лог
            return self._save_json_log(self.questions_log_file, questions_log)
        except Exception as e:
            self.logger.error(f"Ошибка при записи вопроса в лог: {str(e)}")
            return False

    def log_assessment(
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
        Записывает результаты тестирования.

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
            timestamp = datetime.now().isoformat()

            # Загружаем текущий лог тестирования
            assessment_log = self._load_json_log(self.assessment_log_file)

            # Формируем массив вопросов с ответами
            question_details = []
            for i, question in enumerate(questions):
                question_details.append(
                    {
                        "question": question["text"],
                        "options": question["options"],
                        "user_answer": user_answers[i],
                        "correct_answer": correct_answers[i],
                        "is_correct": user_answers[i] == correct_answers[i],
                    }
                )

            # Добавляем новую запись
            assessment_log.append(
                {
                    "timestamp": timestamp,
                    "course": course,
                    "section": section,
                    "topic": topic,
                    "lesson": lesson,
                    "questions": question_details,
                    "score": score,
                }
            )

            # Сохраняем обновленный лог
            return self._save_json_log(self.assessment_log_file, assessment_log)
        except Exception as e:
            self.logger.error(f"Ошибка при записи результатов тестирования: {str(e)}")
            return False

    def log_activity(self, action_type, details=None, status="success", error=None):
        """
        Записывает действие пользователя или системы.

        Args:
            action_type (str): Тип действия
            details (dict, optional): Дополнительные данные о действии
            status (str): Статус действия ("success" или "error")
            error (str, optional): Описание ошибки, если status="error"

        Returns:
            bool: True если запись прошла успешно, иначе False
        """
        try:
            timestamp = datetime.now().isoformat()

            # Загружаем текущий лог активности
            activity_log = self._load_json_log(self.activity_log_file)

            # Формируем запись
            log_entry = {
                "timestamp": timestamp,
                "action_type": action_type,
                "status": status,
            }

            if details:
                log_entry["details"] = details

            if status == "error" and error:
                log_entry["error"] = error

            # Добавляем новую запись
            activity_log.append(log_entry)

            # Сохраняем обновленный лог
            return self._save_json_log(self.activity_log_file, activity_log)
        except Exception as e:
            self.logger.error(f"Ошибка при записи действия в лог: {str(e)}")
            return False
