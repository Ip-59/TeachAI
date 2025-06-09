"""
Модуль для создания интерактивного интерфейса с использованием ipywidgets.
Отвечает за взаимодействие с пользователем через Jupyter Notebook.

НОВАЯ АРХИТЕКТУРА: Этот модуль теперь служит фасадом для специализированных интерфейсов.
Обеспечивает полную обратную совместимость со старым интерфейсом.
НОВОЕ: Поддержка главного меню для повторных запусков
НОВОЕ: Интеграция личного кабинета студента
НОВОЕ: Расширенная навигация между интерфейсами
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
from datetime import datetime
import re
import traceback

# Импортируем все специализированные интерфейсы
from interface_utils import InterfaceState, InterfaceUtils
from setup_interface import SetupInterface
from lesson_interface import LessonInterface
from assessment_interface import AssessmentInterface
from completion_interface import CompletionInterface

# НОВОЕ: Импортируем новые интерфейсы
try:
    from main_menu_interface import MainMenuInterface

    MAIN_MENU_AVAILABLE = True
except ImportError:
    logging.warning("Модуль main_menu_interface не найден")
    MAIN_MENU_AVAILABLE = False

    class MainMenuInterface:
        def __init__(self, *args, **kwargs):
            pass

        def show_main_menu(self):
            return widgets.HTML("<p>Главное меню недоступно</p>")


try:
    from student_profile_interface import StudentProfileInterface

    STUDENT_PROFILE_AVAILABLE = True
except ImportError:
    logging.warning("Модуль student_profile_interface не найден")
    STUDENT_PROFILE_AVAILABLE = False

    class StudentProfileInterface:
        def __init__(self, *args, **kwargs):
            pass

        def show_student_profile(self):
            return widgets.HTML("<p>Личный кабинет недоступен</p>")


class UserInterface:
    """
    Фасад для создания интерактивного пользовательского интерфейса.

    ВАЖНО: Обеспечивает полную обратную совместимость с предыдущей версией.
    Все методы работают точно так же, как раньше!
    """

    def __init__(self, state_manager, content_generator, assessment, system_logger):
        """
        Инициализация интерфейса.

        Args:
            state_manager (StateManager): Объект менеджера состояния
            content_generator (ContentGenerator): Объект генератора контента
            assessment (Assessment): Объект модуля оценивания
            system_logger (Logger): Объект логгера
        """
        self.state_manager = state_manager
        self.content_generator = content_generator
        self.assessment = assessment
        self.system_logger = system_logger
        self.logger = logging.getLogger(__name__)

        # Текущее состояние интерфейса
        self.current_state = InterfaceState.INITIAL_SETUP

        # Данные текущего урока для совместимости
        self.current_course = None
        self.current_section = None
        self.current_topic = None
        self.current_lesson = None
        self.current_lesson_content = None
        self.current_questions = None
        self.current_answers = []

        # Инициализируем специализированные интерфейсы
        try:
            self.logger.debug("Инициализация специализированных интерфейсов...")

            # Отладочная информация
            print(f"🔍 ОТЛАДКА UserInterface.__init__:")
            print(f"🔍 assessment = {assessment}")
            print(f"🔍 type(assessment) = {type(assessment)}")

            self.setup_interface = SetupInterface(
                state_manager, content_generator, system_logger, assessment
            )
            self.lesson_interface = LessonInterface(
                state_manager, content_generator, system_logger, assessment
            )
            self.assessment_interface = AssessmentInterface(
                state_manager, assessment, system_logger
            )
            self.completion_interface = CompletionInterface(
                state_manager, system_logger, content_generator, assessment
            )

            # НОВОЕ: Инициализируем новые интерфейсы
            if MAIN_MENU_AVAILABLE:
                self.main_menu_interface = MainMenuInterface(
                    state_manager, content_generator, system_logger, assessment
                )
            else:
                self.main_menu_interface = None

            if STUDENT_PROFILE_AVAILABLE:
                self.student_profile_interface = StudentProfileInterface(
                    state_manager, content_generator, system_logger, assessment
                )
            else:
                self.student_profile_interface = None

            self.logger.info("UserInterface (фасад) успешно инициализирован")

        except Exception as e:
            self.logger.error(f"Ошибка при инициализации UserInterface: {str(e)}")
            raise

        # Утилиты интерфейса
        self.utils = InterfaceUtils()

        # Сохраняем старые стили для совместимости
        self.styles = {
            "correct": "background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin: 5px 0;",
            "incorrect": "background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 5px 0;",
            "info": "background-color: #d1ecf1; color: #0c5460; padding: 10px; border-radius: 5px; margin: 5px 0;",
            "warning": "background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; margin: 5px 0;",
            "header": "font-size: 24px; font-weight: bold; color: #495057; margin: 20px 0 10px 0;",
            "subheader": "font-size: 18px; font-weight: bold; color: #6c757d; margin: 15px 0 10px 0;",
            "button": "font-weight: bold;",
        }

    # ========================================
    # ПУБЛИЧНЫЕ МЕТОДЫ - ОБРАТНАЯ СОВМЕСТИМОСТЬ
    # ========================================

    def show_initial_setup(self):
        """
        Отображает форму первоначальной настройки.

        Returns:
            widgets.VBox: Виджет с формой настройки
        """
        self.current_state = InterfaceState.INITIAL_SETUP
        return self.setup_interface.show_initial_setup()

    def show_course_selection(self):
        """
        Отображает интерфейс выбора курса.

        Returns:
            widgets.VBox: Виджет с интерфейсом выбора курса
        """
        self.current_state = InterfaceState.COURSE_SELECTION
        return self.setup_interface.show_course_selection()

    def show_lesson(self, section_id, topic_id, lesson_id):
        """
        Отображает урок пользователю.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            widgets.VBox: Виджет с уроком
        """
        self.current_state = InterfaceState.LESSON_VIEW
        return self.lesson_interface.show_lesson(section_id, topic_id, lesson_id)

    def show_assessment(self, section_id, topic_id, lesson_id):
        """
        Отображает интерфейс тестирования.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            widgets.VBox: Виджет с тестом
        """
        self.current_state = InterfaceState.ASSESSMENT
        return self.assessment_interface.show_assessment(
            section_id, topic_id, lesson_id
        )

    def show_completion(self, lesson_data, test_results):
        """
        Отображает интерфейс завершения урока.

        Args:
            lesson_data (dict): Данные урока
            test_results (dict): Результаты тестирования

        Returns:
            widgets.VBox: Виджет завершения урока
        """
        self.current_state = InterfaceState.COMPLETION
        return self.completion_interface.show_completion(lesson_data, test_results)

    # ========================================
    # НОВЫЕ МЕТОДЫ - ГЛАВНОЕ МЕНЮ И ЛИЧНЫЙ КАБИНЕТ
    # ========================================

    def show_main_menu(self):
        """
        НОВОЕ: Отображает главное меню для повторных запусков.

        Returns:
            widgets.VBox: Виджет главного меню
        """
        try:
            self.current_state = InterfaceState.MAIN_MENU

            if self.main_menu_interface and MAIN_MENU_AVAILABLE:
                return self.main_menu_interface.show_main_menu()
            else:
                # Fallback на стандартный выбор курса
                self.logger.warning("Главное меню недоступно, переход к выбору курса")
                return self.show_course_selection()

        except Exception as e:
            self.logger.error(f"Ошибка при показе главного меню: {str(e)}")
            return self._create_fallback_menu()

    def show_student_profile(self):
        """
        НОВОЕ: Отображает личный кабинет студента.

        Returns:
            widgets.VBox: Виджет личного кабинета
        """
        try:
            self.current_state = InterfaceState.STUDENT_PROFILE

            if self.student_profile_interface and STUDENT_PROFILE_AVAILABLE:
                return self.student_profile_interface.show_student_profile()
            else:
                # Fallback интерфейс
                self.logger.warning(
                    "Личный кабинет недоступен, показ fallback интерфейса"
                )
                return self._create_fallback_profile()

        except Exception as e:
            self.logger.error(f"Ошибка при показе личного кабинета: {str(e)}")
            return self._create_fallback_profile()

    def navigate_to_lesson(self, section_id, topic_id, lesson_id):
        """
        НОВОЕ: Навигация к уроку из других интерфейсов.

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            widgets.VBox: Виджет урока
        """
        try:
            self.logger.info(f"Навигация к уроку: {section_id}:{topic_id}:{lesson_id}")
            return self.show_lesson(section_id, topic_id, lesson_id)
        except Exception as e:
            self.logger.error(f"Ошибка навигации к уроку: {str(e)}")
            return self.utils.create_styled_message(
                f"Ошибка при переходе к уроку: {str(e)}", "incorrect"
            )

    def navigate_to_course_selection(self):
        """
        НОВОЕ: Навигация к выбору курса из других интерфейсов.

        Returns:
            widgets.VBox: Виджет выбора курса
        """
        try:
            self.logger.info("Навигация к выбору курса")
            return self.show_course_selection()
        except Exception as e:
            self.logger.error(f"Ошибка навигации к выбору курса: {str(e)}")
            return self.utils.create_styled_message(
                f"Ошибка при переходе к выбору курса: {str(e)}", "incorrect"
            )

    def navigate_to_main_menu(self):
        """
        НОВОЕ: Навигация к главному меню из других интерфейсов.

        Returns:
            widgets.VBox: Виджет главного меню
        """
        try:
            self.logger.info("Навигация к главному меню")
            return self.show_main_menu()
        except Exception as e:
            self.logger.error(f"Ошибка навигации к главному меню: {str(e)}")
            return self.utils.create_styled_message(
                f"Ошибка при переходе к главному меню: {str(e)}", "incorrect"
            )

    # ========================================
    # FALLBACK ИНТЕРФЕЙСЫ
    # ========================================

    def _create_fallback_menu(self):
        """
        Создает fallback главное меню если основной модуль недоступен.

        Returns:
            widgets.VBox: Fallback главное меню
        """
        header = self.utils.create_header("🏠 Главное меню TeachAI")

        # Получаем данные пользователя
        try:
            user_profile = self.state_manager.user_profile.get_user_profile()
            user_name = user_profile.get("name", "Пользователь")
        except:
            user_name = "Пользователь"

        welcome = widgets.HTML(
            value=f"""
        <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; margin: 20px 0;">
            <h2>👋 Добро пожаловать, {user_name}!</h2>
            <p>Выберите действие для продолжения обучения:</p>
        </div>
        """
        )

        # Кнопки
        continue_button = widgets.Button(
            description="📚 Продолжить обучение",
            style={"button_color": "#007bff"},
            layout=widgets.Layout(width="300px", height="50px", margin="10px"),
        )

        courses_button = widgets.Button(
            description="🎓 Выбрать курс",
            style={"button_color": "#28a745"},
            layout=widgets.Layout(width="300px", height="50px", margin="10px"),
        )

        output = widgets.Output()

        def on_continue_clicked(b):
            with output:
                clear_output(wait=True)
                display(
                    self.utils.create_styled_message(
                        "Поиск незавершенного урока...", "info"
                    )
                )

        def on_courses_clicked(b):
            with output:
                clear_output(wait=True)
                display(self.show_course_selection())

        continue_button.on_click(on_continue_clicked)
        courses_button.on_click(on_courses_clicked)

        buttons_container = widgets.VBox(
            [continue_button, courses_button],
            layout=widgets.Layout(align_items="center"),
        )

        return widgets.VBox([header, welcome, buttons_container, output])

    def _create_fallback_profile(self):
        """
        Создает fallback личный кабинет если основной модуль недоступен.

        Returns:
            widgets.VBox: Fallback личный кабинет
        """
        header = self.utils.create_header("📊 Личный кабинет (упрощенная версия)")

        try:
            # Получаем базовую статистику
            progress = self.state_manager.learning_progress.get_learning_progress()
            course_progress = (
                self.state_manager.learning_progress.calculate_course_progress()
            )

            stats_html = f"""
            <div style="background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">
                <h3>📈 Прогресс обучения</h3>
                <p><strong>Текущий курс:</strong> {progress.get('current_course', 'Не выбран')}</p>
                <p><strong>Прогресс:</strong> {course_progress.get('percent', 0):.1f}%</p>
                <p><strong>Завершено уроков:</strong> {course_progress.get('completed', 0)} из {course_progress.get('total', 0)}</p>
                <p><strong>Средний балл:</strong> {progress.get('average_score', 0):.1f}%</p>
            </div>
            """

            stats_widget = widgets.HTML(value=stats_html)

        except Exception as e:
            stats_widget = self.utils.create_styled_message(
                f"Ошибка при загрузке статистики: {str(e)}", "warning"
            )

        # Кнопка возврата
        back_button = widgets.Button(
            description="🔙 Назад к главному меню",
            style={"button_color": "#6c757d"},
            layout=widgets.Layout(width="250px", margin="20px 0"),
        )

        output = widgets.Output()

        def on_back_clicked(b):
            with output:
                clear_output(wait=True)
                display(self.show_main_menu())

        back_button.on_click(on_back_clicked)

        return widgets.VBox(
            [header, stats_widget, back_button, output],
            layout=widgets.Layout(gap="15px"),
        )

    # ========================================
    # УСТАРЕВШИЕ МЕТОДЫ - ОБРАТНАЯ СОВМЕСТИМОСТЬ
    # ========================================

    def create_styled_button(self, description, style="default"):
        """УСТАРЕВШИЙ: Используйте utils.create_button()"""
        return self.utils.create_button(description, style)

    def create_styled_message(self, message, style="info"):
        """УСТАРЕВШИЙ: Используйте utils.create_styled_message()"""
        return self.utils.create_styled_message(message, style)

    def create_header(self, text):
        """УСТАРЕВШИЙ: Используйте utils.create_header()"""
        return self.utils.create_header(text)

    def create_progress_bar(self, current, total, description=""):
        """УСТАРЕВШИЙ: Используйте utils.create_progress_bar()"""
        return self.utils.create_progress_bar(current, total, description)

    def display_course_plan(self, course_plan):
        """
        УСТАРЕВШИЙ: Отображает план курса (оставлен для совместимости).

        Args:
            course_plan (dict): План курса

        Returns:
            widgets.VBox: Виджет с планом курса
        """
        # Делегируем функциональность setup_interface
        return self.setup_interface._display_course_plan(course_plan)

    def get_current_state(self):
        """
        Получает текущее состояние интерфейса.

        Returns:
            InterfaceState: Текущее состояние
        """
        return self.current_state

    def set_current_state(self, state):
        """
        Устанавливает текущее состояние интерфейса.

        Args:
            state (InterfaceState): Новое состояние
        """
        self.current_state = state
        self.logger.debug(f"Состояние интерфейса изменено на: {state}")
