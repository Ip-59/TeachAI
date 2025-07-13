"""
Фасад интерфейса для системы TeachAI.
Координирует специализированные интерфейсы и управляет состояниями системы.

РЕФАКТОРИНГ ЭТАП 27: Разделен на компоненты для соблюдения лимитов размера модулей.
ИСПРАВЛЕНО ЭТАП 43: Порядок параметров в конструкторе + вызовы методов ContentGenerator (проблемы #181, #182)
ИСПРАВЛЕНО ЭТАП 44: ДОБАВЛЕН RETURN в show_lesson() - КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ (проблема #183)
"""

import logging
import ipywidgets as widgets
from interface_utils import InterfaceState
from lesson_interface import LessonInterface
from assessment_interface import AssessmentInterface
from student_profile_interface import StudentProfileInterface
from main_menu_interface import MainMenuInterface
from setup_interface import SetupInterface


class InterfaceFacade:
    """
    Фасад интерфейса TeachAI.
    Координирует специализированные интерфейсы и управляет состояниями.
    """

    def __init__(self, state_manager, content_generator, assessment, system_logger):
        """
        Инициализация фасада интерфейса.

        Args:
            state_manager: Менеджер состояния
            content_generator: Генератор контента
            assessment: Модуль оценивания
            system_logger: Системный логгер
        """
        self.state_manager = state_manager
        self.content_generator = content_generator
        self.assessment = assessment
        self.system_logger = system_logger
        self.logger = logging.getLogger(__name__)

        # Текущее состояние интерфейса
        self.current_state = InterfaceState.INITIAL_SETUP

        try:
            # Инициализируем специализированные интерфейсы
            self.lesson_interface = LessonInterface(
                state_manager=state_manager,
                content_generator=content_generator,
                system_logger=system_logger,
                assessment=assessment,
                parent_facade=self,  # ВАЖНО: Передаем ссылку на себя
            )

            self.assessment_interface = AssessmentInterface(
                state_manager=state_manager,
                assessment=assessment,
                system_logger=system_logger,
                parent_facade=self,  # ВАЖНО: Передаем ссылку на себя для доступа к content_generator
            )

            self.student_profile_interface = StudentProfileInterface(
                state_manager=state_manager,
                content_generator=content_generator,
                system_logger=system_logger,
                assessment=assessment,
            )

            self.main_menu_interface = MainMenuInterface(
                state_manager=state_manager,
                content_generator=content_generator,
                system_logger=system_logger,
                assessment=assessment,
            )

            self.setup_interface = SetupInterface(
                state_manager=state_manager,
                content_generator=content_generator,
                system_logger=system_logger,
                assessment=assessment,
            )

            self.logger.info(
                "InterfaceFacade успешно инициализирован со всеми специализированными интерфейсами"
            )

        except Exception as e:
            self.logger.error(f"Ошибка при инициализации InterfaceFacade: {str(e)}")
            raise

    # ========================================
    # МЕТОДЫ ОТОБРАЖЕНИЯ ИНТЕРФЕЙСОВ
    # ========================================

    def show_initial_setup(self):
        """
        Отображает интерфейс первоначальной настройки.

        Returns:
            widgets.VBox: Интерфейс настройки
        """
        try:
            self.logger.info("Отображение интерфейса первоначальной настройки")
            result = self.setup_interface.show_initial_setup()
            self.current_state = InterfaceState.INITIAL_SETUP
            return result

        except Exception as e:
            self.logger.error(f"Ошибка отображения настройки: {str(e)}")
            return self._create_error_interface(
                "Ошибка загрузки интерфейса настройки", str(e)
            )

    def show_course_selection(self):
        """
        Отображает интерфейс выбора курса.

        Returns:
            widgets.VBox: Интерфейс выбора курса
        """
        try:
            self.logger.info("Отображение интерфейса выбора курса")
            result = self.setup_interface.show_course_selection()
            self.current_state = InterfaceState.COURSE_SELECTION
            return result

        except Exception as e:
            self.logger.error(f"Ошибка отображения выбора курса: {str(e)}")
            return self._create_error_interface("Ошибка загрузки выбора курса", str(e))

    def show_lesson(self, lesson_id=None):
        """
        Отображает интерфейс урока.

        Args:
            lesson_id (str): Идентификатор урока в формате "section_id:topic_id:lesson_id"

        Returns:
            widgets.VBox: Интерфейс урока
        """
        try:
            self.logger.info(f"Отображение урока: {lesson_id}")

            # Получаем текущий урок, если lesson_id не указан
            if lesson_id is None:
                next_lesson = self.state_manager.get_next_lesson()
                if next_lesson and len(next_lesson) >= 3:
                    section_id, topic_id, lesson_id_current = next_lesson[:3]
                else:
                    self.logger.error("Не удалось определить текущий урок")
                    return self._create_error_interface(
                        "Ошибка", "Не удалось определить урок для отображения"
                    )
            else:
                # Парсим lesson_id
                lesson_parts = lesson_id.split(":")
                if len(lesson_parts) >= 3:
                    # Полный формат: section-1:topic-2:lesson-3
                    section_id, topic_id, lesson_id_current = lesson_parts[:3]
                elif len(lesson_parts) == 1:
                    # ИСПРАВЛЕНО ЭТАП 44: Сокращенный формат - получаем полную информацию из state_manager
                    self.logger.info(
                        f"Получен сокращенный lesson_id: {lesson_id}, получаем полную информацию"
                    )
                    next_lesson = self.state_manager.get_next_lesson()
                    if next_lesson and len(next_lesson) >= 3:
                        section_id, topic_id, lesson_id_current = next_lesson[:3]
                        self.logger.info(
                            f"Полный урок из state_manager: {section_id}:{topic_id}:{lesson_id_current}"
                        )
                    else:
                        self.logger.error(
                            "Не удалось получить полную информацию об уроке из state_manager"
                        )
                        return self._create_error_interface(
                            "Ошибка", "Не удалось определить полную информацию об уроке"
                        )
                else:
                    self.logger.error(f"Неверный формат lesson_id: {lesson_id}")
                    return self._create_error_interface(
                        "Ошибка", f"Неверный формат идентификатора урока: {lesson_id}"
                    )

            # ИСПРАВЛЕНО ЭТАП 44: ДОБАВЛЕН RETURN - КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ!
            # Отображение урока через lesson_interface
            result = self.lesson_interface.show_lesson(
                section_id, topic_id, lesson_id_current
            )
            self.current_state = InterfaceState.LESSON_VIEW
            return result  # ← ИСПРАВЛЕНО: Теперь возвращаем результат!

        except Exception as e:
            self.logger.error(f"Ошибка отображения урока {lesson_id}: {str(e)}")
            return self._create_error_interface("Ошибка загрузки урока", str(e))

    def show_assessment(self, lesson_id=None):
        """
        Отображает интерфейс тестирования.

        Args:
            lesson_id (str): Идентификатор урока

        Returns:
            widgets.VBox: Интерфейс тестирования
        """
        try:
            self.logger.info(f"Отображение тестирования для урока: {lesson_id}")

            # Получаем данные текущего урока
            current_lesson_data = self.lesson_interface.get_current_lesson_data()
            if not current_lesson_data:
                self.logger.error("Данные урока недоступны для тестирования")
                return self._create_error_interface("Ошибка", "Данные урока недоступны")

            # Извлекаем необходимые данные
            course_info = self.lesson_interface.current_course_info or {}
            lesson_content = self.lesson_interface.current_lesson_content or {}

            result = self.assessment_interface.show_assessment(
                current_course=course_info.get("course_title", "Текущий курс"),
                current_section=course_info.get("section_title", "Текущая секция"),
                current_topic=course_info.get("topic_title", "Текущая тема"),
                current_lesson=course_info.get("lesson_title", "Текущий урок"),
                current_lesson_content=lesson_content,
            )

            self.current_state = InterfaceState.ASSESSMENT
            return result

        except Exception as e:
            self.logger.error(f"Ошибка отображения тестирования: {str(e)}")
            return self._create_error_interface("Ошибка загрузки тестирования", str(e))

    def show_results(self, assessment_results=None):
        """
        Отображает результаты тестирования.

        Args:
            assessment_results (dict): Результаты тестирования

        Returns:
            widgets.VBox: Интерфейс результатов
        """
        try:
            self.logger.info("Отображение результатов тестирования")
            result = self.assessment_interface.show_results(assessment_results)
            self.current_state = InterfaceState.RESULTS_VIEW
            return result

        except Exception as e:
            self.logger.error(f"Ошибка отображения результатов: {str(e)}")
            return self._create_error_interface("Ошибка загрузки результатов", str(e))

    def show_completion(self):
        """
        Отображает интерфейс завершения курса.

        Returns:
            widgets.VBox: Интерфейс завершения
        """
        try:
            self.logger.info("Отображение интерфейса завершения курса")
            result = self.assessment_interface.show_course_completion()
            self.current_state = InterfaceState.COMPLETION
            return result

        except Exception as e:
            self.logger.error(f"Ошибка отображения завершения: {str(e)}")
            return self._create_error_interface("Ошибка загрузки завершения", str(e))

    def show_main_menu(self):
        """
        Отображает главное меню.

        Returns:
            widgets.VBox: Интерфейс главного меню
        """
        try:
            self.logger.info("Отображение главного меню")
            result = self.main_menu_interface.show_main_menu()
            self.current_state = InterfaceState.MAIN_MENU
            return result

        except Exception as e:
            self.logger.error(f"Ошибка отображения главного меню: {str(e)}")
            return self._create_error_interface("Ошибка загрузки главного меню", str(e))

    def show_student_profile(self):
        """
        Отображает профиль студента.

        Returns:
            widgets.VBox: Интерфейс профиля студента
        """
        try:
            self.logger.info("Отображение профиля студента")
            result = self.student_profile_interface.show_student_profile()
            self.current_state = InterfaceState.STUDENT_PROFILE
            return result

        except Exception as e:
            self.logger.error(f"Ошибка отображения профиля студента: {str(e)}")
            return self._create_error_interface("Ошибка загрузки профиля", str(e))

    # ========================================
    # МЕТОДЫ НАВИГАЦИИ И СОСТОЯНИЯ
    # ========================================

    def get_current_state(self):
        """
        Возвращает текущее состояние интерфейса.

        Returns:
            InterfaceState: Текущее состояние
        """
        return self.current_state

    def can_navigate_to(self, target_state):
        """
        Проверяет возможность перехода к указанному состоянию.

        Args:
            target_state (InterfaceState): Целевое состояние

        Returns:
            bool: True, если переход возможен
        """
        # Базовая логика навигации
        valid_transitions = {
            InterfaceState.INITIAL_SETUP: [
                InterfaceState.COURSE_SELECTION,
                InterfaceState.MAIN_MENU,
            ],
            InterfaceState.COURSE_SELECTION: [
                InterfaceState.LESSON_VIEW,
                InterfaceState.MAIN_MENU,
            ],
            InterfaceState.LESSON_VIEW: [
                InterfaceState.ASSESSMENT,
                InterfaceState.LESSON_VIEW,
                InterfaceState.MAIN_MENU,
            ],
            InterfaceState.ASSESSMENT: [
                InterfaceState.RESULTS_VIEW,
                InterfaceState.LESSON_VIEW,
            ],
            InterfaceState.RESULTS_VIEW: [
                InterfaceState.LESSON_VIEW,
                InterfaceState.COMPLETION,
                InterfaceState.MAIN_MENU,
            ],
            InterfaceState.COMPLETION: [
                InterfaceState.MAIN_MENU,
                InterfaceState.COURSE_SELECTION,
            ],
            InterfaceState.MAIN_MENU: [
                InterfaceState.COURSE_SELECTION,
                InterfaceState.LESSON_VIEW,
                InterfaceState.STUDENT_PROFILE,
            ],
            InterfaceState.STUDENT_PROFILE: [
                InterfaceState.MAIN_MENU,
                InterfaceState.LESSON_VIEW,
            ],
        }

        return target_state in valid_transitions.get(self.current_state, [])

    def navigate_to(self, target_state, **kwargs):
        """
        Выполняет навигацию к указанному состоянию.

        Args:
            target_state (InterfaceState): Целевое состояние
            **kwargs: Дополнительные параметры для навигации

        Returns:
            widgets.VBox: Интерфейс целевого состояния
        """
        try:
            if not self.can_navigate_to(target_state):
                self.logger.warning(
                    f"Навигация из {self.current_state} в {target_state} не разрешена"
                )
                return self._create_error_interface(
                    "Ошибка навигации",
                    f"Переход из {self.current_state.value} в {target_state.value} не разрешен",
                )

            # Выполняем навигацию в зависимости от целевого состояния
            if target_state == InterfaceState.INITIAL_SETUP:
                return self.show_initial_setup()
            elif target_state == InterfaceState.COURSE_SELECTION:
                return self.show_course_selection()
            elif target_state == InterfaceState.LESSON_VIEW:
                lesson_id = kwargs.get("lesson_id")
                return self.show_lesson(lesson_id)
            elif target_state == InterfaceState.ASSESSMENT:
                lesson_id = kwargs.get("lesson_id")
                return self.show_assessment(lesson_id)
            elif target_state == InterfaceState.RESULTS_VIEW:
                results = kwargs.get("assessment_results")
                return self.show_results(results)
            elif target_state == InterfaceState.COMPLETION:
                return self.show_completion()
            elif target_state == InterfaceState.MAIN_MENU:
                return self.show_main_menu()
            elif target_state == InterfaceState.STUDENT_PROFILE:
                return self.show_student_profile()
            else:
                self.logger.error(
                    f"Неизвестное состояние для навигации: {target_state}"
                )
                return self._create_error_interface(
                    "Ошибка навигации", f"Неизвестное состояние: {target_state}"
                )

        except Exception as e:
            self.logger.error(f"Ошибка навигации к {target_state}: {str(e)}")
            return self._create_error_interface("Ошибка навигации", str(e))

    # ========================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ========================================

    def _create_error_interface(self, title, message):
        """
        Создает интерфейс ошибки.

        Args:
            title (str): Заголовок ошибки
            message (str): Сообщение об ошибке

        Returns:
            widgets.VBox: Интерфейс ошибки
        """
        error_html = widgets.HTML(
            value=f"""
            <div style='color: red; padding: 20px; text-align: center; border: 1px solid red; border-radius: 8px; margin: 20px;'>
                <h3>{title}</h3>
                <p>{message}</p>
                <p><small>Проверьте логи для подробной информации об ошибке</small></p>
            </div>
            """
        )

        return widgets.VBox([error_html])

    def get_interface_info(self):
        """
        Возвращает информацию о доступных интерфейсах.

        Returns:
            dict: Информация об интерфейсах
        """
        return {
            "facade_initialized": True,
            "current_state": self.current_state.value if self.current_state else None,
            "available_interfaces": [
                "lesson_interface",
                "assessment_interface",
                "student_profile_interface",
                "main_menu_interface",
                "setup_interface",
            ],
            "available_states": [state.value for state in InterfaceState],
            "version": "2.0",
        }

    def validate_dependencies(self):
        """
        Проверяет наличие всех зависимостей.

        Returns:
            dict: Результаты проверки зависимостей
        """
        dependencies = {
            "state_manager": self.state_manager is not None,
            "content_generator": self.content_generator is not None,
            "assessment": self.assessment is not None,
            "system_logger": self.system_logger is not None,
            "lesson_interface": hasattr(self, "lesson_interface")
            and self.lesson_interface is not None,
            "assessment_interface": hasattr(self, "assessment_interface")
            and self.assessment_interface is not None,
            "student_profile_interface": hasattr(self, "student_profile_interface")
            and self.student_profile_interface is not None,
            "main_menu_interface": hasattr(self, "main_menu_interface")
            and self.main_menu_interface is not None,
            "setup_interface": hasattr(self, "setup_interface")
            and self.setup_interface is not None,
        }

        all_available = all(dependencies.values())

        return {
            "all_dependencies_available": all_available,
            "dependencies": dependencies,
            "missing_dependencies": [k for k, v in dependencies.items() if not v],
        }

    def get_status(self):
        """
        Возвращает полный статус фасада интерфейса.

        Returns:
            dict: Полный статус фасада
        """
        try:
            return {
                "facade_initialized": True,
                "current_state": self.current_state.value
                if self.current_state
                else None,
                "interface_info": self.get_interface_info(),
                "dependencies": self.validate_dependencies(),
                "lesson_data_available": hasattr(
                    self.lesson_interface, "current_lesson_data"
                )
                and self.lesson_interface.current_lesson_data is not None,
                "version": "2.0",
                "last_critical_fix": "ЭТАП 44: Добавлен return в show_lesson() - ПРОБЛЕМА #183 РЕШЕНА!",
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса фасада: {str(e)}")
            return {"error": str(e), "facade_initialized": False}
