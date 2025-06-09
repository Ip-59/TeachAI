"""
Фасад для генерации учебного контента - основной класс.
Координирует работу всех специализированных генераторов.

ИСПРАВЛЕНО ЭТАП 29: Устранена ошибка вызова несуществующего метода generate_lesson_content в LessonGenerator
"""

import logging
from datetime import datetime

# Импортируем все специализированные генераторы
from course_plan_generator import CoursePlanGenerator
from lesson_generator import LessonGenerator
from examples_generator import ExamplesGenerator
from explanation_generator import ExplanationGenerator
from assessment_generator import AssessmentGenerator
from qa_generator import QAGenerator
from concepts_generator import ConceptsGenerator
from relevance_checker import RelevanceChecker


class ContentGeneratorFacade:
    """
    Основной фасад для генерации учебного контента.
    Координирует работу всех специализированных генераторов.
    """

    def __init__(self, api_key):
        """
        Инициализация фасада генератора контента.

        Args:
            api_key (str): API ключ OpenAI
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key

        try:
            # Инициализируем все специализированные генераторы
            self.course_plan_gen = CoursePlanGenerator(api_key)
            self.lesson_gen = LessonGenerator(api_key)
            self.examples_gen = ExamplesGenerator(api_key)
            self.explanation_gen = ExplanationGenerator(api_key)
            self.assessment_gen = AssessmentGenerator(api_key)
            self.qa_gen = QAGenerator(api_key)
            self.concepts_gen = ConceptsGenerator(api_key)
            self.relevance_checker = RelevanceChecker(api_key)

            self.logger.info("ContentGeneratorFacade успешно инициализирован")

        except Exception as e:
            self.logger.error(
                f"Ошибка при инициализации ContentGeneratorFacade: {str(e)}"
            )
            raise

    # ========================================
    # ОСНОВНЫЕ МЕТОДЫ ГЕНЕРАЦИИ
    # ========================================

    def generate_course_plan(self, course_name, course_description, user_data):
        """
        Генерирует план курса.

        Args:
            course_name (str): Название курса
            course_description (str): Описание курса
            user_data (dict): Данные пользователя

        Returns:
            dict: Сгенерированный план курса
        """
        try:
            self.logger.info(f"Генерация плана курса: {course_name}")
            return self.course_plan_gen.generate_course_plan(
                course_name, course_description, user_data
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
            dict: Сгенерированное содержание урока с полной структурой
        """
        try:
            lesson_title = lesson_data.get("title", "Урок")
            self.logger.info(f"Генерация содержания урока: {lesson_title}")

            # ИСПРАВЛЕНО: Правильный вызов метода generate_lesson() в LessonGenerator
            # Извлекаем необходимые параметры из входных данных
            course_name = self._extract_course_name(lesson_data, course_context)
            section_name = lesson_data.get(
                "section_title", lesson_data.get("section_id", "Раздел")
            )
            topic_name = lesson_data.get(
                "topic_title", lesson_data.get("topic_id", "Тема")
            )
            lesson_name = lesson_data.get("title", lesson_data.get("id", "Урок"))
            user_name = user_data.get("name", "Пользователь")
            communication_style = user_data.get("communication_style", "friendly")

            # Вызываем правильный метод LessonGenerator
            result = self.lesson_gen.generate_lesson(
                course=course_name,
                section=section_name,
                topic=topic_name,
                lesson=lesson_name,
                user_name=user_name,
                communication_style=communication_style,
            )

            # ИСПРАВЛЕНО: Всегда возвращаем правильную структуру словаря
            lesson_content_dict = {
                "title": lesson_title,
                "content": "",
                "estimated_time": lesson_data.get("estimated_time", 30),
                "objectives": lesson_data.get("objectives", []),
                "description": lesson_data.get("description", ""),
            }

            # Обрабатываем результат от LessonGenerator
            if isinstance(result, dict):
                # Если вернулся словарь, используем его content
                lesson_content_dict["content"] = result.get("content", str(result))
                if result.get("title"):
                    lesson_content_dict["title"] = result["title"]
            else:
                # Если вернулась строка, используем её как content
                lesson_content_dict["content"] = str(result)

            return lesson_content_dict

        except Exception as e:
            self.logger.error(f"Ошибка генерации содержания урока: {str(e)}")
            raise

    def _extract_course_name(self, lesson_data, course_context):
        """
        Извлекает название курса из доступных данных.

        Args:
            lesson_data (dict): Данные урока
            course_context (dict): Контекст курса

        Returns:
            str: Название курса
        """
        try:
            # Пытаемся получить название курса из разных источников
            if course_context and course_context.get("course_title"):
                return course_context["course_title"]
            elif course_context and course_context.get("course_plan", {}).get("title"):
                return course_context["course_plan"]["title"]
            elif lesson_data.get("course_title"):
                return lesson_data["course_title"]
            else:
                return "Курс Python"  # Fallback значение
        except Exception:
            return "Курс Python"

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
            return self.examples_gen.generate_examples(
                lesson_data, lesson_content, communication_style, course_context
            )
        except Exception as e:
            self.logger.error(f"Ошибка генерации примеров: {str(e)}")
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
            return self.explanation_gen.get_detailed_explanation(
                lesson_data, lesson_content, communication_style
            )
        except Exception as e:
            self.logger.error(f"Ошибка генерации подробного объяснения: {str(e)}")
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
            self.logger.info(f"Ответ на вопрос по уроку: {lesson_title}")
            return self.qa_gen.answer_question(
                question, lesson_data, lesson_content, communication_style
            )
        except Exception as e:
            self.logger.error(f"Ошибка ответа на вопрос: {str(e)}")
            raise

    def generate_assessment(self, lesson_data, lesson_content, questions_count=5):
        """
        Генерирует тест для оценки знаний.

        Args:
            lesson_data (dict): Данные урока
            lesson_content (str): Содержание урока
            questions_count (int): Количество вопросов

        Returns:
            list: Список вопросов теста
        """
        try:
            lesson_title = lesson_data.get("title", "Урок")
            self.logger.info(f"Генерация теста для урока: {lesson_title}")
            return self.assessment_gen.generate_assessment(
                lesson_data, lesson_content, questions_count
            )
        except Exception as e:
            self.logger.error(f"Ошибка генерации теста: {str(e)}")
            raise

    # ========================================
    # НОВЫЕ МЕТОДЫ (логическая модернизация)
    # ========================================

    def extract_key_concepts(self, lesson_content, lesson_data):
        """
        Извлекает ключевые понятия из урока.

        Args:
            lesson_content (str): Содержание урока
            lesson_data (dict): Данные урока

        Returns:
            list: Ключевые понятия
        """
        try:
            lesson_title = lesson_data.get("title", "Урок")
            self.logger.info(f"Извлечение ключевых понятий из урока: {lesson_title}")
            return self.concepts_gen.extract_key_concepts(lesson_content, lesson_data)
        except Exception as e:
            self.logger.error(f"Ошибка извлечения ключевых понятий: {str(e)}")
            raise

    def check_content_relevance(self, content, course_context):
        """
        Проверяет релевантность контента курсу.

        Args:
            content (str): Контент для проверки
            course_context (dict): Контекст курса

        Returns:
            dict: Результат проверки релевантности
        """
        try:
            course_title = (
                course_context.get("course_title", "Курс") if course_context else "Курс"
            )
            self.logger.info(
                f"Проверка релевантности контента для курса: {course_title}"
            )
            return self.relevance_checker.check_content_relevance(
                content, course_context
            )
        except Exception as e:
            self.logger.error(f"Ошибка проверки релевантности: {str(e)}")
            raise

    # ========================================
    # СЛУЖЕБНЫЕ МЕТОДЫ
    # ========================================

    def get_generator_status(self):
        """
        Возвращает статус всех генераторов.

        Returns:
            dict: Статус генераторов
        """
        return {
            "facade_initialized": True,
            "api_key_set": bool(self.api_key),
            "generators": {
                "course_plan": bool(self.course_plan_gen),
                "lesson": bool(self.lesson_gen),
                "examples": bool(self.examples_gen),
                "explanation": bool(self.explanation_gen),
                "assessment": bool(self.assessment_gen),
                "qa": bool(self.qa_gen),
                "concepts": bool(self.concepts_gen),
                "relevance_checker": bool(self.relevance_checker),
            },
            "available_methods": [
                "generate_course_plan",
                "generate_lesson_content",
                "generate_examples",
                "get_detailed_explanation",
                "answer_question",
                "generate_assessment",
                "extract_key_concepts",
                "check_content_relevance",
            ],
        }

    def validate_generators(self):
        """
        Проверяет корректность инициализации всех генераторов.

        Returns:
            dict: Результат валидации
        """
        try:
            generators = [
                ("course_plan_gen", self.course_plan_gen),
                ("lesson_gen", self.lesson_gen),
                ("examples_gen", self.examples_gen),
                ("explanation_gen", self.explanation_gen),
                ("assessment_gen", self.assessment_gen),
                ("qa_gen", self.qa_gen),
                ("concepts_gen", self.concepts_gen),
                ("relevance_checker", self.relevance_checker),
            ]

            validation = {}
            all_valid = True

            for name, generator in generators:
                is_valid = generator is not None and hasattr(generator, "__class__")
                validation[name] = is_valid
                if not is_valid:
                    all_valid = False

            validation["all_generators_valid"] = all_valid
            validation["api_key_set"] = bool(self.api_key)

            return validation

        except Exception as e:
            self.logger.error(f"Ошибка валидации генераторов: {str(e)}")
            return {"error": str(e)}

    def get_current_timestamp(self):
        """Возвращает текущую временную метку."""
        try:
            return datetime.now().isoformat()
        except Exception:
            return "unknown"
