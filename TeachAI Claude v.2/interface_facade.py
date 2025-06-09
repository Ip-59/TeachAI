"""
Фасад интерфейса для TeachAI 2.
Обеспечивает единую точку доступа ко всем интерфейсам системы.
ИСПРАВЛЕНО ЭТАП 41: Добавлен parent_facade для решения проблемы #179
ИСПРАВЛЕНО ЭТАП 42: Исправлены ошибки InterfaceState и логика поиска уроков
ИСПРАВЛЕНО ЭТАП 43: Исправлены параметры ContentGenerator.generate_lesson_content()
"""

import logging
from IPython.display import clear_output
from enum import Enum

# Импорт интерфейсов
from lesson_interface import LessonInterface
from assessment_interface import AssessmentInterface


class InterfaceState(Enum):
    """Состояния интерфейса системы."""

    INITIAL_SETUP = "initial_setup"
    COURSE_SELECTION = "course_selection"
    LESSON_VIEW = "lesson_view"
    ASSESSMENT = "assessment"
    COMPLETION = "completion"


class InterfaceFacade:
    """
    Фасад для управления всеми интерфейсами системы.
    Предоставляет единую точку доступа к различным компонентам UI.
    """

    def __init__(self, state_manager, assessment, content_generator, system_logger):
        """
        Инициализация фасада интерфейса.

        Args:
            state_manager: Менеджер состояния системы
            assessment: Модуль оценки
            content_generator: Генератор контента
            system_logger: Системный логгер
        """
        # ДИАГНОСТИКА ЭТАП 43: Проверяем что получаем в конструкторе
        logger = logging.getLogger(__name__)
        logger.info(f"=== ДИАГНОСТИКА СОЗДАНИЯ INTERFACE_FACADE ===")
        logger.info(f"state_manager: {type(state_manager)}")
        logger.info(f"assessment: {type(assessment)}")
        logger.info(f"content_generator: {type(content_generator)}")
        logger.info(f"system_logger: {type(system_logger)}")

        self.state_manager = state_manager
        self.assessment = assessment
        self.content_generator = content_generator
        self.system_logger = system_logger
        self.logger = logging.getLogger(__name__)

        self.current_state = InterfaceState.INITIAL_SETUP

        # Инициализация интерфейсов
        self._initialize_core_interfaces()

        self.logger.info("InterfaceFacade инициализирован")

    def _initialize_core_interfaces(self):
        """Инициализация основных интерфейсов."""
        try:
            # ДИАГНОСТИКА ЭТАП 43: Проверяем что передаем в LessonInterface
            self.logger.info(f"=== ДИАГНОСТИКА СОЗДАНИЯ LESSON_INTERFACE ===")
            self.logger.info(f"state_manager: {type(self.state_manager)}")
            self.logger.info(f"content_generator: {type(self.content_generator)}")
            self.logger.info(f"system_logger: {type(self.system_logger)}")
            self.logger.info(f"assessment: {type(self.assessment)}")

            # ИСПРАВЛЕНО ЭТАП 43: Правильный порядок параметров для LessonInterface
            # LessonInterface(state_manager, content_generator, system_logger, assessment=None, parent_facade=None)
            self.lesson_interface = LessonInterface(
                state_manager=self.state_manager,
                content_generator=self.content_generator,
                system_logger=self.system_logger,
                assessment=self.assessment,
                parent_facade=self,
            )

            # ИСПРАВЛЕНО ЭТАП 41: Добавлен parent_facade=self для решения проблемы #179
            self.assessment_interface = AssessmentInterface(
                self.state_manager,
                self.assessment,
                self.system_logger,
                parent_facade=self,
            )

            self.logger.info("Основные интерфейсы успешно инициализированы")

        except Exception as e:
            self.logger.error(f"Ошибка инициализации интерфейсов: {str(e)}")
            raise

    def show_lesson(self, lesson_id):
        """
        Отображение урока.

        Args:
            lesson_id (str): Идентификатор урока
        """
        try:
            self.logger.info(f"=== ДИАГНОСТИКА show_lesson ===")
            self.logger.info(f"Входной lesson_id: {lesson_id}")

            # Поиск урока в плане курса
            lesson_location = self._find_lesson_in_course_plan(lesson_id)

            if lesson_location:
                section_id, topic_id, lesson_id = lesson_location
                self.logger.info(
                    f"Урок найден: {section_id} -> {topic_id} -> {lesson_id}"
                )

                # Отображение урока через lesson_interface
                self.lesson_interface.show_lesson(section_id, topic_id, lesson_id)
                self.current_state = InterfaceState.LESSON_VIEW

            else:
                # Fallback: используем данные из state_manager
                self.logger.warning(
                    f"Урок {lesson_id} не найден в плане курса, используем fallback"
                )
                next_lesson_data = self.state_manager.get_next_lesson()

                if next_lesson_data:
                    if len(next_lesson_data) >= 4:
                        (
                            section_id,
                            topic_id,
                            fallback_lesson_id,
                            lesson_data,
                        ) = next_lesson_data
                        self.lesson_interface.show_lesson(
                            section_id, topic_id, fallback_lesson_id
                        )
                        self.current_state = InterfaceState.LESSON_VIEW
                    else:
                        self.logger.error(
                            "Неожиданный формат данных от get_next_lesson()"
                        )
                        raise Exception("Не удалось получить данные урока")
                else:
                    self.logger.error("Не удалось получить данные урока")
                    raise Exception("Урок недоступен")

        except Exception as e:
            self.logger.error(f"Ошибка в show_lesson: {str(e)}")
            raise

    def show_assessment(self, lesson_id):
        """
        Отображение интерфейса тестирования.

        Args:
            lesson_id (str): Идентификатор урока для тестирования
        """
        try:
            self.logger.info(f"=== ОТЛАДКА FACADE ASSESSMENT ===")
            self.logger.info(
                f"Переход к интерфейсу тестирования (lesson_id: {lesson_id})"
            )

            # ПРИОРИТЕТ 1: Проверяем кэшированные данные из lesson_interface
            lesson_data = None
            lesson_content = None

            if (
                hasattr(self.lesson_interface, "current_course_info")
                and self.lesson_interface.current_course_info
            ):
                self.logger.info("ИСТОЧНИК: lesson_interface")

                cached_lesson_title = self.lesson_interface.current_course_info.get(
                    "lesson_title", ""
                )
                cached_lesson_id = getattr(
                    self.lesson_interface, "current_lesson_id", None
                )

                self.logger.info(f"Урок из lesson_interface: {cached_lesson_title}")
                self.logger.info(f"lesson_id из lesson_interface: {cached_lesson_id}")
                self.logger.info(f"Запрашиваемый lesson_id: {lesson_id}")
                self.logger.info(
                    f"Соответствие lesson_id: {cached_lesson_id == lesson_id}"
                )

                # ИСПРАВЛЕНО ЭТАП 42: Проверяем соответствие lesson_id
                if cached_lesson_id == lesson_id:
                    lesson_data = self.lesson_interface.current_course_info
                    lesson_content = getattr(
                        self.lesson_interface, "current_lesson_content", None
                    )
                    self.logger.info("✅ КЭШИРОВАННЫЕ ДАННЫЕ СООТВЕТСТВУЮТ")
                else:
                    self.logger.warning(
                        f"❌ КЭШИРОВАННЫЕ ДАННЫЕ НЕ СООТВЕТСТВУЮТ: cached={cached_lesson_id}, requested={lesson_id}"
                    )

            # ПРИОРИТЕТ 2: Получаем данные через state_manager.get_lesson_data()
            if not lesson_data:
                self.logger.info(
                    f"ИСТОЧНИК: lesson_id через state_manager ({lesson_id})"
                )

                if hasattr(self.state_manager, "get_lesson_data"):
                    lesson_data = self.state_manager.get_lesson_data(lesson_id)
                    self.logger.info(f"Данные урока из state_manager: {lesson_data}")
                else:
                    self.logger.warning("state_manager не имеет метода get_lesson_data")

            # ПРИОРИТЕТ 3: Используем state_manager.get_next_lesson()
            if not lesson_data:
                self.logger.info("ИСТОЧНИК: state_manager.get_next_lesson()")
                next_lesson_data = self.state_manager.get_next_lesson()

                if next_lesson_data and len(next_lesson_data) >= 4:
                    (
                        section_id,
                        topic_id,
                        lesson_id_from_next,
                        lesson_data,
                    ) = next_lesson_data
                    self.logger.info(
                        f"Получены данные из get_next_lesson: {lesson_data}"
                    )
                else:
                    self.logger.error("Не удалось получить данные урока")
                    raise Exception("Урок недоступен для тестирования")

            # Проверяем наличие контента урока
            if not lesson_content:
                if hasattr(lesson_data, "get") and lesson_data.get("content"):
                    lesson_content = lesson_data["content"]
                    self.logger.info(
                        f"КОНТЕНТ: найден в lesson_data, размер: {len(lesson_content)} символов"
                    )
                else:
                    self.logger.info(
                        "КОНТЕНТ: генерируем новый через content_generator"
                    )

                    # ИСПРАВЛЕНО ЭТАП 43: Правильные параметры для generate_lesson_content()
                    user_data = getattr(
                        self.state_manager, "user_data", {"name": "Пользователь"}
                    )
                    course_context = self._get_course_context()

                    # Метод принимает только 3 параметра: lesson_data, user_data, course_context
                    content_result = self.content_generator.generate_lesson_content(
                        lesson_data=lesson_data,
                        user_data=user_data,
                        course_context=course_context,
                    )

                    # Извлекаем контент из результата
                    if isinstance(content_result, dict):
                        lesson_content = content_result.get(
                            "content", str(content_result)
                        )
                    else:
                        lesson_content = str(content_result)

                    self.logger.info(
                        f"КОНТЕНТ: сгенерирован, размер: {len(lesson_content)} символов"
                    )

            # Переход к интерфейсу тестирования
            self.assessment_interface.show_assessment(
                lesson_data,
                lesson_content,
                lesson_id,
                self.content_generator,
                self.state_manager,
            )
            self.current_state = InterfaceState.ASSESSMENT

        except Exception as e:
            self.logger.error(f"Ошибка в show_assessment: {str(e)}")
            raise

    def show_completion(self):
        """Отображение экрана завершения курса."""
        try:
            clear_output(wait=True)
            print("🎉 Поздравляем! Курс успешно завершен!")
            print("Вы изучили все уроки и прошли все тесты.")

            self.current_state = InterfaceState.COMPLETION
            self.logger.info("Отображен экран завершения курса")

        except Exception as e:
            self.logger.error(f"Ошибка в show_completion: {str(e)}")
            raise

    # СЛУЖЕБНЫЕ МЕТОДЫ

    def _find_lesson_in_course_plan(self, lesson_id):
        """
        Поиск урока в плане курса.

        Args:
            lesson_id (str): ID урока для поиска

        Returns:
            tuple: (section_id, topic_id, lesson_id) или None если не найден
        """
        try:
            self.logger.info(f"=== ДИАГНОСТИКА ПОИСКА УРОКА {lesson_id} ===")

            course_plan = self._get_course_plan()

            if not course_plan:
                self.logger.warning("План курса недоступен")
                return None

            self.logger.info(f"План курса получен, тип: {type(course_plan)}")

            # ИСПРАВЛЕНО ЭТАП 42: Правильная структура поиска
            sections = course_plan.get("sections", [])
            self.logger.info(f"Количество разделов: {len(sections)}")

            if sections:
                first_section = sections[0]
                self.logger.info(
                    f"Раздел 0: id={first_section.get('id')}, title={first_section.get('title', 'Без названия')}"
                )

                first_topics = first_section.get("topics", [])
                if first_topics:
                    first_topic = first_topics[0]
                    self.logger.info(f"  Количество тем в разделе: {len(first_topics)}")
                    self.logger.info(
                        f"  Тема 0: id={first_topic.get('id')}, title={first_topic.get('title', 'Без названия')}"
                    )

                    first_lessons = first_topic.get("lessons", [])
                    if first_lessons:
                        first_lesson = first_lessons[0]
                        self.logger.info(
                            f"    Количество уроков в теме: {len(first_lessons)}"
                        )
                        self.logger.info(
                            f"    Урок 0: id={first_lesson.get('id')}, title={first_lesson.get('title', 'Без названия')}"
                        )

            # Поиск урока
            for section in sections:
                section_id = section.get("id")
                for topic in section.get("topics", []):
                    topic_id = topic.get("id")
                    for lesson in topic.get("lessons", []):
                        current_lesson_id = lesson.get("id")
                        if current_lesson_id == lesson_id:
                            self.logger.info(
                                f"✅ Урок найден: {section_id} -> {topic_id} -> {current_lesson_id}"
                            )
                            return (section_id, topic_id, current_lesson_id)

            self.logger.warning(f"❌ Урок {lesson_id} не найден в плане курса")
            return None

        except Exception as e:
            self.logger.error(f"Ошибка поиска урока в плане курса: {str(e)}")
            return None

    def _get_course_plan(self):
        """
        Получение плана курса.

        Returns:
            dict: План курса или None
        """
        try:
            # Способ 1: Из state_manager
            if hasattr(self.state_manager, "get_course_plan"):
                return self.state_manager.get_course_plan()

            # Способ 2: Из атрибута state_manager
            if hasattr(self.state_manager, "course_plan"):
                return self.state_manager.course_plan

            # Способ 3: Из текущего состояния
            if hasattr(self.state_manager, "current_state"):
                current_state = self.state_manager.current_state
                if isinstance(current_state, dict) and "course_plan" in current_state:
                    return current_state["course_plan"]

            self.logger.warning("Не удалось получить план курса")
            return None

        except Exception as e:
            self.logger.error(f"Ошибка получения плана курса: {str(e)}")
            return None

    def _get_course_context(self):
        """
        Получение контекста курса для генерации контента.

        Returns:
            dict: Контекст курса
        """
        try:
            # Базовый контекст
            context = {
                "course_name": "Основы Python",
                "course_description": "Изучение основ программирования на Python",
            }

            # Пытаемся получить более детальную информацию
            if hasattr(self.state_manager, "get_course_info"):
                course_info = self.state_manager.get_course_info()
                if course_info:
                    context.update(course_info)

            return context

        except Exception as e:
            self.logger.error(f"Ошибка получения контекста курса: {str(e)}")
            return {
                "course_name": "Основы Python",
                "course_description": "Изучение основ программирования на Python",
            }

    def get_current_state(self):
        """Получение текущего состояния интерфейса."""
        return self.current_state

    def set_state(self, state):
        """
        Установка состояния интерфейса.

        Args:
            state (InterfaceState): Новое состояние
        """
        if isinstance(state, InterfaceState):
            self.current_state = state
            self.logger.info(f"Состояние интерфейса изменено на: {state.value}")
        else:
            self.logger.warning(f"Попытка установить недопустимое состояние: {state}")
