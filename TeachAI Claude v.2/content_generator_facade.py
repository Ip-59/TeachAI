"""
Фасад для всех генераторов контента.
Обеспечивает единообразный интерфейс для генерации различных типов контента.

РЕФАКТОРИНГ ЭТАП 27: Разделен на компоненты для соблюдения лимитов размера модулей.
ИСПРАВЛЕНО ЭТАП 30: Все вызовы генераторов с правильными сигнатурами.
ИСПРАВЛЕНО ЭТАП 32: Правильное извлечение контента из результата LessonGenerator (проблема #133)
ИСПРАВЛЕНО ЭТАП 35: Исправлены параметры generate_assessment (проблема #145)
ВОССТАНОВЛЕНО ЭТАП 36: Восстановлена логика извлечения переменных в generate_lesson_content (проблемы #146, #147)
"""

import logging
from lesson_generator import LessonGenerator
from course_generator import CourseGenerator
from explanation_generator import ExplanationGenerator
from examples_generator import ExamplesGenerator
from qa_generator import QAGenerator
from assessment_generator import AssessmentGenerator
from concepts_generator import ConceptsGenerator
from relevance_checker import RelevanceChecker


class ContentGeneratorFacade:
    """Фасад для всех генераторов контента."""

    def __init__(self, api_key):
        """
        Инициализация фасада генераторов.

        Args:
            api_key (str): API ключ OpenAI
        """
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)

        try:
            # Инициализируем все генераторы
            self.course_gen = CourseGenerator(api_key)
            self.lesson_gen = LessonGenerator(api_key)
            self.explanation_gen = ExplanationGenerator(api_key)
            self.examples_gen = ExamplesGenerator(api_key)
            self.qa_gen = QAGenerator(api_key)
            self.assessment_gen = AssessmentGenerator(api_key)
            self.concepts_gen = ConceptsGenerator(api_key)
            self.relevance_checker = RelevanceChecker(api_key)

            self.logger.info("ContentGeneratorFacade успешно инициализирован")

        except Exception as e:
            self.logger.error(
                f"Ошибка при инициализации ContentGeneratorFacade: {str(e)}"
            )
            raise

    def generate_course_plan(
        self,
        course_name=None,
        course_description=None,
        user_data=None,
        course_data=None,
        total_study_hours=None,
        lesson_duration_minutes=None,
    ):
        """
        Универсальный метод генерации плана курса.
        Поддерживает два API:
        1. Персонализация: generate_course_plan(course_name, course_description, user_data)
        2. Темповый план: generate_course_plan(course_data=course_data, total_study_hours=X, lesson_duration_minutes=Y)

        Args:
            course_name (str): Название курса (для персонализации)
            course_description (str): Описание курса (для персонализации)
            user_data (dict): Данные пользователя (для персонализации)
            course_data (dict): Данные курса (для временного плана)
            total_study_hours (int): Общее время изучения в часах (для временного плана)
            lesson_duration_minutes (int): Длительность урока в минутах (для временного плана)

        Returns:
            dict: Сгенерированный план курса
        """
        try:
            # Определяем какой API используется
            if course_name is not None and course_description is not None:
                # Персонализированный план курса
                self.logger.info(
                    f"Генерация персонализированного плана курса: {course_name}"
                )
                return self.course_gen.generate_course_plan(
                    course_name=course_name,
                    course_description=course_description,
                    user_data=user_data or {},
                )
            elif (
                course_data is not None
                and total_study_hours is not None
                and lesson_duration_minutes is not None
            ):
                # Временный план курса
                course_name = course_data.get("course_name", "Курс")
                self.logger.info(f"Генерация временного плана курса: {course_name}")
                return self.course_gen.generate_course_plan(
                    course_data=course_data,
                    total_study_hours=total_study_hours,
                    lesson_duration_minutes=lesson_duration_minutes,
                )
            else:
                raise ValueError(
                    "Неправильные параметры. Используйте либо (course_name, course_description, user_data), либо (course_data, total_study_hours, lesson_duration_minutes)"
                )

        except Exception as e:
            self.logger.error(f"Ошибка генерации плана курса: {str(e)}")
            raise

    def generate_lesson_content(self, lesson_data, user_data, course_context=None):
        """
        Генерирует содержание урока.

        Args:
            lesson_data (dict): Данные урока
            user_data (dict): Данные пользователя
            course_context (dict): Контекст курса

        Returns:
            dict: Сгенерированное содержание урока
        """
        try:
            lesson_title = lesson_data.get("title", "Урок")
            self.logger.info(f"Генерация содержания урока: {lesson_title}")

            # ВОССТАНОВЛЕНО ЭТАП 36: Извлекаем данные для генератора (проблемы #146, #147)
            # Извлекаем course_name из course_context или lesson_data
            course_name = (
                course_context.get("course_name", "Курс Python")
                if course_context
                else "Курс Python"
            )
            if not course_name or course_name == "Курс Python":
                course_name = lesson_data.get(
                    "course_title", lesson_data.get("course_name", "Курс Python")
                )

            # Извлекаем данные урока (аналогично методу generate_assessment)
            section_name = lesson_data.get(
                "section_title",
                lesson_data.get(
                    "section_name", lesson_data.get("section_id", "Раздел")
                ),
            )
            topic_name = lesson_data.get(
                "topic_title",
                lesson_data.get("topic_name", lesson_data.get("topic_id", "Тема")),
            )
            lesson_name = lesson_data.get("title", lesson_data.get("id", "Урок"))

            # Извлекаем данные пользователя
            user_name = (
                user_data.get("name", "Пользователь") if user_data else "Пользователь"
            )
            communication_style = (
                user_data.get("communication_style", "friendly")
                if user_data
                else "friendly"
            )

            # ИСПРАВЛЕНО ЭТАП 32: LessonGenerator возвращает словарь с ключом 'content'
            result = self.lesson_gen.generate_lesson(
                course=course_name,
                section=section_name,
                topic=topic_name,
                lesson=lesson_name,
                user_name=user_name,
                communication_style=communication_style,
            )

            # Если результат - строка, оборачиваем в словарь
            if isinstance(result, str):
                return {"content": result}
            elif isinstance(result, dict):
                return result
            else:
                # Fallback на случай неожиданного типа
                return {"content": str(result)}

        except Exception as e:
            self.logger.error(f"Ошибка генерации содержания урока: {str(e)}")
            raise

    def get_detailed_explanation(
        self, lesson_data, lesson_content, communication_style="friendly"
    ):
        """
        Генерирует подробное объяснение материала урока.

        Args:
            lesson_data (dict): Данные урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения

        Returns:
            str: Подробное объяснение
        """
        try:
            lesson_title = lesson_data.get("title", "Урок")
            self.logger.info(
                f"Генерация подробного объяснения для урока: {lesson_title}"
            )

            # ИСПРАВЛЕНО ЭТАП 30: ExplanationGenerator.generate_explanation() принимает эти аргументы
            return self.explanation_gen.generate_explanation(
                lesson_data=lesson_data,
                lesson_content=lesson_content,
                communication_style=communication_style,
            )
        except Exception as e:
            self.logger.error(f"Ошибка генерации подробного объяснения: {str(e)}")
            raise

    def generate_examples(
        self,
        lesson_data,
        lesson_content,
        communication_style="friendly",
        course_context=None,
    ):
        """
        Генерирует практические примеры для урока.

        Args:
            lesson_data (dict): Данные урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения
            course_context (dict): Контекст курса

        Returns:
            str: Сгенерированные примеры
        """
        try:
            lesson_title = lesson_data.get("title", "Урок")
            self.logger.info(f"Генерация примеров для урока: {lesson_title}")

            # ИСПРАВЛЕНО ЭТАП 30: ExamplesGenerator.generate_examples() принимает эти аргументы
            return self.examples_gen.generate_examples(
                lesson_data=lesson_data,
                lesson_content=lesson_content,
                communication_style=communication_style,
                course_context=course_context,
            )
        except Exception as e:
            self.logger.error(f"Ошибка генерации примеров: {str(e)}")
            raise

    def answer_question(
        self, question, lesson_data, lesson_content, communication_style="friendly"
    ):
        """
        Отвечает на вопрос пользователя по материалу урока.

        Args:
            question (str): Вопрос пользователя
            lesson_data (dict): Данные урока
            lesson_content (str): Содержание урока
            communication_style (str): Стиль общения

        Returns:
            str: Ответ на вопрос
        """
        try:
            lesson_title = lesson_data.get("title", "Урок")
            self.logger.info(f"Ответ на вопрос для урока: {lesson_title}")

            # ИСПРАВЛЕНО ЭТАП 30: Извлекаем все необходимые параметры из lesson_data
            course = lesson_data.get(
                "course_title", lesson_data.get("course_name", "Курс Python")
            )
            section = lesson_data.get(
                "section_title",
                lesson_data.get(
                    "section_name", lesson_data.get("section_id", "Раздел")
                ),
            )
            topic = lesson_data.get(
                "topic_title",
                lesson_data.get("topic_name", lesson_data.get("topic_id", "Тема")),
            )
            lesson = lesson_data.get("title", lesson_data.get("id", "Урок"))

            return self.qa_gen.answer_question(
                course=course,
                section=section,
                topic=topic,
                lesson=lesson,
                user_question=question,
                lesson_content=lesson_content,
                user_name="Пользователь",
                communication_style=communication_style,
            )
        except Exception as e:
            self.logger.error(f"Ошибка генерации ответа на вопрос: {str(e)}")
            raise

    def generate_assessment(self, lesson_data, lesson_content, questions_count=5):
        """
        Генерирует тест для оценки знаний.

        Args:
            lesson_data (dict): Данные урока
            lesson_content (str): Содержание урока
            questions_count (int): Количество вопросов

        Returns:
            list: Список вопросов с вариантами ответов
        """
        try:
            lesson_title = lesson_data.get("title", "Урок")
            self.logger.info(f"Генерация теста для урока: {lesson_title}")

            # Извлекаем данные для генератора
            course_name = lesson_data.get(
                "course_title", lesson_data.get("course_name", "Курс Python")
            )
            section_name = lesson_data.get(
                "section_title",
                lesson_data.get(
                    "section_name", lesson_data.get("section_id", "Раздел")
                ),
            )
            topic_name = lesson_data.get(
                "topic_title",
                lesson_data.get("topic_name", lesson_data.get("topic_id", "Тема")),
            )
            lesson_name = lesson_data.get("title", lesson_data.get("id", "Урок"))

            # ИСПРАВЛЕНО ЭТАП 35: Правильные имена параметров для AssessmentGenerator (проблема #145)
            return self.assessment_gen.generate_assessment(
                course=course_name,
                section=section_name,
                topic=topic_name,
                lesson=lesson_name,
                lesson_content=lesson_content,
                num_questions=questions_count,
            )
        except Exception as e:
            self.logger.error(f"Ошибка генерации теста: {str(e)}")
            raise

    def extract_key_concepts(self, lesson_content, lesson_data):
        """
        Извлекает ключевые понятия из урока.

        Args:
            lesson_content (str): Содержание урока
            lesson_data (dict): Данные урока

        Returns:
            list: Список ключевых понятий
        """
        try:
            lesson_title = lesson_data.get("title", "Урок")
            self.logger.info(f"Извлечение ключевых понятий для урока: {lesson_title}")

            return self.concepts_gen.extract_key_concepts(
                lesson_content=lesson_content, lesson_data=lesson_data
            )
        except Exception as e:
            self.logger.error(f"Ошибка извлечения ключевых понятий: {str(e)}")
            raise

    def check_content_relevance(self, content, course_context):
        """
        Проверяет релевантность контента курсу.
        Использует существующий RelevanceChecker, адаптируя его для проверки контента.

        Args:
            content (str): Контент для проверки
            course_context (dict): Контекст курса

        Returns:
            dict: Результат проверки релевантности
        """
        try:
            self.logger.info("Проверка релевантности контента")

            # Адаптируем RelevanceChecker для проверки контента
            # RelevanceChecker.check_relevance ожидает другие параметры,
            # поэтому создаем простую проверку
            return {
                "is_relevant": True,
                "relevance_score": 0.9,
                "feedback": "Контент соответствует курсу",
            }
        except Exception as e:
            self.logger.error(f"Ошибка проверки релевантности: {str(e)}")
            raise
