"""
Модуль для генерации учебного контента через OpenAI API.
Отвечает за создание уроков, вопросов и обработку ответов пользователя.

НОВАЯ АРХИТЕКТУРА: Этот модуль теперь служит фасадом для специализированных генераторов.
Обеспечивает полную обратную совместимость со старым интерфейсом.
ЗАВЕРШЕНО: Интеграция новых генераторов для логической модернизации.
"""

import logging
from datetime import datetime
import re
from IPython.display import display

# Импортируем все специализированные генераторы
from course_plan_generator import CoursePlanGenerator
from lesson_generator import LessonGenerator
from examples_generator import ExamplesGenerator
from explanation_generator import ExplanationGenerator
from assessment_generator import AssessmentGenerator
from qa_generator import QAGenerator
from concepts_generator import ConceptsGenerator
from relevance_checker import RelevanceChecker
from content_utils import append_question_reminder


class ContentGenerator:
    """
    Фасад для генерации учебного контента с использованием OpenAI API.

    ВАЖНО: Обеспечивает полную обратную совместимость с предыдущей версией.
    Все методы работают точно так же, как раньше!
    ЗАВЕРШЕНО: Добавлены новые методы для логической модернизации.
    """

    def __init__(self, api_key, loading_manager=None):
        """
        Инициализация генератора контента.

        Args:
            api_key (str): API ключ OpenAI
            loading_manager: Менеджер индикаторов загрузки
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.loading_manager = loading_manager

        try:
            # Инициализируем все специализированные генераторы (включая новые)
            self.course_plan_gen = CoursePlanGenerator(api_key)
            self.lesson_gen = LessonGenerator(api_key)
            self.examples_gen = ExamplesGenerator(api_key)
            self.explanation_gen = ExplanationGenerator(api_key)
            self.assessment_gen = AssessmentGenerator(api_key)
            self.qa_gen = QAGenerator(api_key)
            self.concepts_gen = ConceptsGenerator(api_key)  # НОВЫЙ
            self.relevance_checker = RelevanceChecker(api_key)  # НОВЫЙ

            self.logger.info(
                "ContentGenerator (фасад) с новыми генераторами успешно инициализирован"
            )

        except Exception as e:
            self.logger.error(f"Ошибка при инициализации ContentGenerator: {str(e)}")
            raise

        # Сохраняем старые атрибуты для совместимости
        self.communication_styles = {
            "formal": "Формальный, академический стиль общения с использованием научной терминологии.",
            "friendly": "Дружелюбный стиль общения, использующий простые объяснения и аналогии.",
            "casual": "Непринужденный, разговорный стиль с элементами юмора.",
            "brief": "Краткий и четкий стиль, фокусирующийся только на ключевой информации.",
        }

        # Создаем директорию для отладочных файлов (для совместимости)
        self.debug_dir = "debug_responses"
        import os

        os.makedirs(self.debug_dir, exist_ok=True)

    # ========================================
    # ПУБЛИЧНЫЕ МЕТОДЫ - ОБРАТНАЯ СОВМЕСТИМОСТЬ
    # ========================================

    def generate_course_plan(self, course_data, total_study_hours, lesson_duration_minutes):
        """
        Генерирует план курса с индикатором загрузки.

        Args:
            course_data (dict): Данные курса
            total_study_hours (int): Общее количество часов обучения
            lesson_duration_minutes (int): Продолжительность урока

        Returns:
            dict: План курса

        Raises:
            Exception: Если не удалось сгенерировать план
        """
        try:
            # Показываем индикатор загрузки
            if self.loading_manager:
                loading_widget = self.loading_manager.show_loading(
                    "openai", operation="generate_course_plan"
                )
                display(loading_widget)
            
            # Генерируем план курса
            result = self.course_plan_gen.generate_course_plan(
            course_data, total_study_hours, lesson_duration_minutes
        )
            
            # Скрываем индикатор загрузки
            if self.loading_manager:
                self.loading_manager.hide_loading()
            
            return result
            
        except Exception as e:
            # Скрываем индикатор загрузки в случае ошибки
            if self.loading_manager:
                self.loading_manager.hide_loading()
            raise

    def generate_lesson(
        self, course, section, topic, lesson, user_name, communication_style="friendly"
    ):
        """
        Генерирует содержание урока с индикатором загрузки.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson (str): Название урока
            user_name (str): Имя пользователя
            communication_style (str): Стиль общения

        Returns:
            dict: Словарь с заголовком и содержанием урока

        Raises:
            Exception: Если не удалось сгенерировать урок
        """
        try:
            # Показываем индикатор загрузки, если доступен
            if self.loading_manager:
                loading_widget = self.loading_manager.show_loading(
                    "lesson", lesson_title=f"{course} - {lesson}"
                )
                display(loading_widget)
            
            # Генерируем урок
            result = self.lesson_gen.generate_lesson(
            course, section, topic, lesson, user_name, communication_style
        )
            
            # Скрываем индикатор загрузки
            if self.loading_manager:
                self.loading_manager.hide_loading()
            
            return result
            
        except Exception as e:
            # Скрываем индикатор загрузки в случае ошибки
            if self.loading_manager:
                self.loading_manager.hide_loading()
            raise

    def generate_examples(
        self, lesson_data, lesson_content, communication_style="friendly"
    ):
        """
        Генерирует практические примеры по материалу урока.

        Args:
            lesson_data (dict): Данные об уроке (название, описание, ключевые слова)
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения

        Returns:
            str: Строка с практическими примерами

        Raises:
            Exception: Если не удалось сгенерировать примеры
        """
        return self.examples_gen.generate_examples(
            lesson_data, lesson_content, communication_style
        )

    def generate_assessment(
        self, course, section, topic, lesson, lesson_content, num_questions=5
    ):
        """
        Генерирует тест для урока с индикатором загрузки.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson (str): Название урока
            lesson_content (str): Содержание урока
            num_questions (int): Количество вопросов

        Returns:
            list: Список вопросов

        Raises:
            Exception: Если не удалось сгенерировать тест
        """
        try:
            # Показываем индикатор загрузки
            if self.loading_manager:
                loading_widget = self.loading_manager.show_loading(
                    "openai", operation="generate_test"
                )
                display(loading_widget)
            
            # Генерируем тест
            result = self.assessment_gen.generate_assessment(
            course, section, topic, lesson, lesson_content, num_questions
        )
            
            # Скрываем индикатор загрузки
            if self.loading_manager:
                self.loading_manager.hide_loading()
            
            return result
            
        except Exception as e:
            # Скрываем индикатор загрузки в случае ошибки
            if self.loading_manager:
                self.loading_manager.hide_loading()
            raise

    def answer_question(
        self,
        course,
        section,
        topic,
        lesson,
        user_question,
        lesson_content,
        user_name,
        communication_style="friendly",
    ):
        """
        Генерирует ответ на вопрос пользователя по уроку.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson (str): Название урока
            user_question (str): Вопрос пользователя
            lesson_content (str): Содержание урока
            user_name (str): Имя пользователя
            communication_style (str): Стиль общения

        Returns:
            str: Ответ на вопрос

        Raises:
            Exception: Если не удалось сгенерировать ответ
        """
        return self.qa_gen.answer_question(
            course,
            section,
            topic,
            lesson,
            user_question,
            lesson_content,
            user_name,
            communication_style,
        )

    def get_detailed_explanation(
        self,
        course,
        section,
        topic,
        lesson,
        lesson_content,
        communication_style="friendly",
    ):
        """
        Генерирует подробное объяснение материала урока.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson (str): Название урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения

        Returns:
            str: Подробное объяснение

        Raises:
            Exception: Если не удалось сгенерировать объяснение
        """
        return self.explanation_gen.get_detailed_explanation(
            course, section, topic, lesson, lesson_content, communication_style
        )

    def generate_concepts(self, lesson_content, communication_style="friendly"):
        """
        Генерирует ключевые понятия из урока для детального изучения.

        Args:
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения

        Returns:
            list: Список ключевых понятий с описаниями

        Raises:
            Exception: Если не удалось извлечь понятия
        """
        # Создаем базовые данные урока для concepts_generator
        lesson_data = {
            "title": "Урок",
            "description": "Содержание урока",
            "keywords": [],
        }

        # Получаем понятия из concepts_generator
        concepts = self.concepts_gen.extract_key_concepts(lesson_content, lesson_data)

        # Преобразуем формат данных: "name" -> "title", "brief_description" -> "description"
        formatted_concepts = []
        for concept in concepts:
            formatted_concept = {
                "title": concept.get("name", "Понятие"),
                "description": concept.get("brief_description", "Нет описания"),
            }
            formatted_concepts.append(formatted_concept)

        return formatted_concepts

    # ========================================
    # НОВЫЕ МЕТОДЫ ДЛЯ ЛОГИЧЕСКОЙ МОДЕРНИЗАЦИИ
    # ========================================

    def extract_key_concepts(self, lesson_content, lesson_data):
        """
        НОВЫЙ: Извлекает ключевые понятия из урока для детального изучения.

        Args:
            lesson_content (str): Содержание урока
            lesson_data (dict): Метаданные урока

        Returns:
            list: Список ключевых понятий с описаниями

        Raises:
            Exception: Если не удалось извлечь понятия
        """
        return self.concepts_gen.extract_key_concepts(lesson_content, lesson_data)

    def explain_concept(self, concept, lesson_content, communication_style="friendly"):
        """
        НОВЫЙ: Генерирует детальное объяснение выбранного понятия.

        Args:
            concept (dict): Данные о понятии (name, brief_description)
            lesson_content (str): Содержание урока для контекста
            communication_style (str): Стиль общения

        Returns:
            str: Подробное объяснение понятия

        Raises:
            Exception: Если не удалось сгенерировать объяснение
        """
        return self.concepts_gen.explain_concept(
            concept, lesson_content, communication_style
        )

    def check_question_relevance(self, user_question, lesson_content, lesson_data):
        """
        НОВЫЙ: Проверяет релевантность вопроса пользователя к содержанию урока.

        Args:
            user_question (str): Вопрос пользователя
            lesson_content (str): Содержание урока
            lesson_data (dict): Метаданные урока

        Returns:
            dict: Результат проверки со следующими ключами:
                - is_relevant (bool): Релевантен ли вопрос
                - confidence (float): Уверенность в оценке (0-100)
                - reason (str): Объяснение решения
                - suggestions (list): Предложения альтернативных источников

        Raises:
            Exception: Если не удалось выполнить проверку
        """
        return self.relevance_checker.check_question_relevance(
            user_question, lesson_content, lesson_data
        )

    def generate_non_relevant_response(self, user_question, suggestions):
        """
        НОВЫЙ: Генерирует вежливый ответ для нерелевантного вопроса.

        Args:
            user_question (str): Вопрос пользователя
            suggestions (list): Предложения альтернативных источников

        Returns:
            str: Стилизованный ответ
        """
        return self.relevance_checker.generate_non_relevant_response(
            user_question, suggestions
        )

    def generate_multiple_questions_warning(self, questions_count):
        """
        НОВЫЙ: Генерирует предупреждение о большом количестве вопросов.

        Args:
            questions_count (int): Количество заданных вопросов

        Returns:
            str: Стилизованное предупреждение
        """
        return self.relevance_checker.generate_multiple_questions_warning(
            questions_count
        )

    def get_formatted_answer_with_relevance(
        self,
        user_question: str,
        lesson_content: str,
        lesson_data: dict,
        course: str,
        section: str,
        topic: str,
        lesson: str,
        user_name: str,
        communication_style: str,
        questions_count: int,
    ) -> str:
        """
        Проверяет релевантность вопроса и возвращает стилизованный HTML-ответ (или нерелевантный с рекомендациями),
        добавляет напоминание после 3-го вопроса.
        """
        relevance_result = self.check_question_relevance(
            user_question, lesson_content, lesson_data
        )
        if not relevance_result["is_relevant"]:
            answer_html = self.generate_non_relevant_response(
                user_question, relevance_result["suggestions"]
            )
        else:
            answer_html = self.answer_question(
                course=course,
                section=section,
                topic=topic,
                lesson=lesson,
                user_question=user_question,
                lesson_content=lesson_content,
                user_name=user_name,
                communication_style=communication_style,
            )
        # Добавляем напоминание, если нужно
        answer_html = append_question_reminder(answer_html, questions_count)
        return answer_html

    # ========================================
    # МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ СО СТАРЫМ КОДОМ
    # ========================================

    def _save_debug_response(
        self, response_type, prompt, response_content, additional_data=None
    ):
        """
        Сохраняет ответ API в файл для отладки.
        СОВМЕСТИМОСТЬ: Этот метод больше не используется напрямую, но оставлен для совместимости.

        Args:
            response_type (str): Тип запроса
            prompt (str): Отправленный промпт
            response_content (str): Ответ от API
            additional_data (dict): Дополнительные данные
        """
        # Для совместимости перенаправляем на один из специализированных генераторов
        self.lesson_gen.save_debug_response(
            response_type, prompt, response_content, additional_data
        )
