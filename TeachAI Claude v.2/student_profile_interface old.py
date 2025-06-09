"""
Интерфейс личного кабинета студента.
Отображает подробную информацию о прогрессе обучения, статистику по урокам,
результаты тестов и контрольных заданий.
НОВОЕ: Полная интеграция с системой отслеживания прогресса
НОВОЕ: Детальная статистика по контрольным заданиям и тестам
НОВОЕ: Визуализация прогресса с индикаторами завершенности
ИСПРАВЛЕНО: Проблема #97 с lesson_attempts_count - правильный подсчет попыток
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
from datetime import datetime
from interface_utils import InterfaceUtils, InterfaceState


class StudentProfileInterface:
    """Интерфейс личного кабинета студента."""

    def __init__(
        self, state_manager, content_generator, system_logger, assessment=None
    ):
        """
        Инициализация интерфейса личного кабинета.

        Args:
            state_manager: Менеджер состояния
            content_generator: Генератор контента
            system_logger: Системный логгер
            assessment: Модуль оценивания (опционально)
        """
        self.state_manager = state_manager
        self.content_generator = content_generator
        self.system_logger = system_logger
        self.assessment = assessment
        self.logger = logging.getLogger(__name__)

        # Утилиты интерфейса
        self.utils = InterfaceUtils()

        # Контейнер для основного интерфейса
        self.main_container = None

        # Выходной контейнер для управления
        self.output_container = widgets.Output()

    def show_student_profile(self):
        """
        Отображает личный кабинет студента с полной статистикой.

        Returns:
            widgets.VBox: Интерфейс личного кабинета
        """
        try:
            # Создаем заголовок
            header = self.utils.create_header("📊 Личный кабинет")

            # Получаем данные о прогрессе
            progress_data = self.state_manager.learning_progress.get_learning_progress()
            detailed_stats = (
                self.state_manager.learning_progress.get_detailed_course_statistics()
            )

            # Создаем секции интерфейса
            profile_info = self._create_profile_info_section(progress_data)
            course_progress = self._create_course_progress_section(detailed_stats)
            lessons_statistics = self._create_lessons_statistics_section(detailed_stats)
            control_tasks_stats = self._create_control_tasks_section(detailed_stats)
            detailed_breakdown = self._create_detailed_breakdown_section()

            # Создаем кнопки действий
            action_buttons = self._create_action_buttons()

            # Собираем все в контейнер
            self.main_container = widgets.VBox(
                [
                    header,
                    profile_info,
                    course_progress,
                    lessons_statistics,
                    control_tasks_stats,
                    detailed_breakdown,
                    action_buttons,
                    self.output_container,
                ],
                layout=widgets.Layout(gap="20px", padding="20px"),
            )

            return self.main_container

        except Exception as e:
            self.logger.error(f"Ошибка при создании личного кабинета: {str(e)}")
            return self._create_error_interface(str(e))

    def _create_profile_info_section(self, progress_data):
        """
        Создает секцию с основной информацией о профиле.

        Args:
            progress_data (dict): Данные о прогрессе

        Returns:
            widgets.HTML: Секция профиля
        """
        user_data = self.state_manager.user_profile.get_user_profile()
        current_date = datetime.now().strftime("%d.%m.%Y %H:%M")

        # Получаем информацию о текущем курсе
        current_course = progress_data.get("current_course", "Не выбран")
        current_section = progress_data.get("current_section", "Не выбрано")
        current_topic = progress_data.get("current_topic", "Не выбрано")
        current_lesson = progress_data.get("current_lesson", "Не выбрано")

        profile_html = f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        ">
            <h2 style="margin: 0 0 20px 0; font-size: 28px;">
                👋 Добро пожаловать, {user_data['name']}!
            </h2>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                <div>
                    <h4 style="margin: 0 0 10px 0; opacity: 0.9;">📚 Обучение</h4>
                    <p style="margin: 5px 0;"><strong>Текущий курс:</strong> {current_course}</p>
                    <p style="margin: 5px 0;"><strong>Раздел:</strong> {current_section}</p>
                    <p style="margin: 5px 0;"><strong>Тема:</strong> {current_topic}</p>
                    <p style="margin: 5px 0;"><strong>Урок:</strong> {current_lesson}</p>
                </div>

                <div>
                    <h4 style="margin: 0 0 10px 0; opacity: 0.9;">⚙️ Настройки</h4>
                    <p style="margin: 5px 0;"><strong>Время обучения:</strong> {user_data.get('total_study_hours', 0)} ч.</p>
                    <p style="margin: 5px 0;"><strong>Длительность урока:</strong> {user_data.get('lesson_duration_minutes', 0)} мин.</p>
                    <p style="margin: 5px 0;"><strong>Стиль общения:</strong> {user_data.get('communication_style', 'friendly')}</p>
                    <p style="margin: 5px 0; opacity: 0.8;"><small>Обновлено: {current_date}</small></p>
                </div>
            </div>
        </div>
        """

        return widgets.HTML(value=profile_html)

    def _create_course_progress_section(self, stats):
        """
        Создает секцию с общим прогрессом по курсу.

        Args:
            stats (dict): Статистика курса

        Returns:
            widgets.HTML: Секция прогресса
        """
        if not stats:
            no_progress_html = """
            <div style="
                background: white;
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #e9ecef;
                text-align: center;
                color: #6c757d;
            ">
                <h3 style="margin: 0 0 10px 0;">📈 Прогресс по курсу</h3>
                <p>Данные о прогрессе появятся после начала изучения курса.</p>
            </div>
            """
            return widgets.HTML(value=no_progress_html)

        # Вычисляем общую статистику
        total_lessons = stats.get("total_lessons", 0)
        completed_lessons = stats.get("completed_lessons", 0)
        progress_percentage = (
            (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        )

        # Определяем цвет прогресса
        if progress_percentage >= 80:
            progress_color = "#28a745"
            progress_text = "Отличный прогресс!"
        elif progress_percentage >= 50:
            progress_color = "#ffc107"
            progress_text = "Хорошая работа!"
        elif progress_percentage > 0:
            progress_color = "#17a2b8"
            progress_text = "Начало положено!"
        else:
            progress_color = "#6c757d"
            progress_text = "Время начинать!"

        progress_html = f"""
        <div style="
            background: white;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #e9ecef;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        ">
            <h3 style="margin: 0 0 20px 0; color: #495057;">📈 Прогресс по курсу</h3>

            <div style="
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 20px;
            ">
                <div style="flex: 1;">
                    <div style="
                        background-color: #f1f3f4;
                        border-radius: 10px;
                        height: 20px;
                        overflow: hidden;
                        margin-right: 20px;
                    ">
                        <div style="
                            background-color: {progress_color};
                            height: 100%;
                            width: {progress_percentage:.1f}%;
                            transition: width 0.3s ease;
                        "></div>
                    </div>
                </div>

                <div style="
                    font-size: 24px;
                    font-weight: bold;
                    color: {progress_color};
                    margin-left: 20px;
                ">
                    {progress_percentage:.1f}%
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; text-align: center;">
                <div>
                    <div style="font-size: 28px; font-weight: bold; color: #17a2b8;">{completed_lessons}</div>
                    <div style="color: #6c757d; font-size: 14px;">Завершено уроков</div>
                </div>

                <div>
                    <div style="font-size: 28px; font-weight: bold; color: #6c757d;">{total_lessons}</div>
                    <div style="color: #6c757d; font-size: 14px;">Всего уроков</div>
                </div>

                <div>
                    <div style="font-size: 28px; font-weight: bold; color: {progress_color};">{total_lessons - completed_lessons}</div>
                    <div style="color: #6c757d; font-size: 14px;">Осталось уроков</div>
                </div>
            </div>

            <div style="
                margin-top: 20px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 8px;
                text-align: center;
                color: {progress_color};
                font-weight: bold;
            ">
                {progress_text}
            </div>
        </div>
        """

        return widgets.HTML(value=progress_html)

    def _create_lessons_statistics_section(self, stats):
        """
        Создает секцию со статистикой по урокам и тестам.

        Args:
            stats (dict): Статистика курса

        Returns:
            widgets.HTML: Секция статистики по урокам
        """
        if not stats:
            return widgets.HTML(value="")

        # Получаем статистику по тестам
        average_score = stats.get("average_score", 0)
        highest_score = stats.get("highest_score", 0)
        lowest_score = stats.get("lowest_score", 0)
        total_assessments = stats.get("total_assessments", 0)
        lessons_passed = stats.get("completed_lessons", 0)

        # Определяем цвет для среднего балла
        if average_score >= 80:
            score_color = "#28a745"
        elif average_score >= 60:
            score_color = "#ffc107"
        else:
            score_color = "#dc3545"

        lessons_html = f"""
        <div style="
            background: white;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #e9ecef;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        ">
            <h3 style="margin: 0 0 25px 0; color: #495057;">📝 Статистика по урокам и тестам</h3>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px;">

                <div style="
                    background: linear-gradient(135deg, {score_color}20, {score_color}10);
                    padding: 20px;
                    border-radius: 10px;
                    border: 1px solid {score_color}40;
                    text-align: center;
                ">
                    <div style="font-size: 32px; font-weight: bold; color: {score_color};">
                        {average_score:.1f}%
                    </div>
                    <div style="color: #6c757d; margin-top: 5px;">Средний балл</div>
                </div>

                <div style="
                    background: linear-gradient(135deg, #17a2b820, #17a2b810);
                    padding: 20px;
                    border-radius: 10px;
                    border: 1px solid #17a2b840;
                    text-align: center;
                ">
                    <div style="font-size: 32px; font-weight: bold; color: #17a2b8;">
                        {total_assessments}
                    </div>
                    <div style="color: #6c757d; margin-top: 5px;">Пройдено тестов</div>
                </div>

                <div style="
                    background: linear-gradient(135deg, #28a74520, #28a74510);
                    padding: 20px;
                    border-radius: 10px;
                    border: 1px solid #28a74540;
                    text-align: center;
                ">
                    <div style="font-size: 32px; font-weight: bold; color: #28a745;">
                        {highest_score:.1f}%
                    </div>
                    <div style="color: #6c757d; margin-top: 5px;">Лучший результат</div>
                </div>

                <div style="
                    background: linear-gradient(135deg, #6f42c120, #6f42c110);
                    padding: 20px;
                    border-radius: 10px;
                    border: 1px solid #6f42c140;
                    text-align: center;
                ">
                    <div style="font-size: 32px; font-weight: bold; color: #6f42c1;">
                        {lessons_passed}
                    </div>
                    <div style="color: #6c757d; margin-top: 5px;">Уроков завершено</div>
                </div>

            </div>

            {"" if total_assessments == 0 else f'''
            <div style="
                margin-top: 20px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid #17a2b8;
            ">
                <p style="margin: 0; color: #495057;">
                    <strong>📊 Дополнительная информация:</strong><br>
                    Самый низкий балл: {lowest_score:.1f}% |
                    Разброс результатов: {highest_score - lowest_score:.1f} баллов
                </p>
            </div>
            '''}
        </div>
        """

        return widgets.HTML(value=lessons_html)

    def _create_control_tasks_section(self, stats):
        """
        Создает секцию со статистикой по контрольным заданиям.

        Args:
            stats (dict): Статистика курса

        Returns:
            widgets.HTML: Секция контрольных заданий
        """
        if not stats:
            return widgets.HTML(value="")

        # Получаем статистику по контрольным заданиям
        total_control_tasks = stats.get("total_control_tasks", 0)
        completed_control_tasks = stats.get("completed_control_tasks", 0)

        if total_control_tasks == 0:
            control_tasks_html = """
            <div style="
                background: white;
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #e9ecef;
                text-align: center;
                color: #6c757d;
            ">
                <h3 style="margin: 0 0 10px 0;">🎯 Контрольные задания</h3>
                <p>Контрольные задания пока не выполнялись.</p>
            </div>
            """
        else:
            completion_rate = completed_control_tasks / total_control_tasks * 100

            # Определяем цвет и сообщение
            if completion_rate >= 80:
                tasks_color = "#28a745"
                tasks_message = "Отличная практическая работа!"
            elif completion_rate >= 50:
                tasks_color = "#ffc107"
                tasks_message = "👍 Хорошая практическая подготовка!"
            else:
                tasks_color = "#17a2b8"
                tasks_message = "💡 Рекомендуем больше практиковаться!"

            control_tasks_html = f"""
            <div style="
                background: white;
                padding: 25px;
                border-radius: 12px;
                border: 1px solid #e9ecef;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            ">
                <h3 style="margin: 0 0 20px 0; color: #495057;">🎯 Контрольные задания</h3>

                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center; margin-bottom: 20px;">
                    <div style="
                        background: linear-gradient(135deg, {tasks_color}20, {tasks_color}10);
                        padding: 20px;
                        border-radius: 10px;
                        border: 1px solid {tasks_color}40;
                    ">
                        <div style="font-size: 32px; font-weight: bold; color: {tasks_color};">
                            {completed_control_tasks}
                        </div>
                        <div style="color: #6c757d; margin-top: 5px;">Выполнено</div>
                    </div>

                    <div style="
                        background: linear-gradient(135deg, #6c757d20, #6c757d10);
                        padding: 20px;
                        border-radius: 10px;
                        border: 1px solid #6c757d40;
                    ">
                        <div style="font-size: 32px; font-weight: bold; color: #6c757d;">
                            {total_control_tasks}
                        </div>
                        <div style="color: #6c757d; margin-top: 5px;">Всего заданий</div>
                    </div>

                    <div style="
                        background: linear-gradient(135deg, {tasks_color}20, {tasks_color}10);
                        padding: 20px;
                        border-radius: 10px;
                        border: 1px solid {tasks_color}40;
                    ">
                        <div style="font-size: 32px; font-weight: bold; color: {tasks_color};">
                            {completion_rate:.1f}%
                        </div>
                        <div style="color: #6c757d; margin-top: 5px;">Завершено</div>
                    </div>
                </div>

                <div style="
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    border-left: 4px solid {tasks_color};
                    text-align: center;
                ">
                    <p style="margin: 0; color: #495057; font-weight: bold;">
                        {tasks_message}
                    </p>
                </div>
            </div>
            """

        return widgets.HTML(value=control_tasks_html)

    def _create_detailed_breakdown_section(self):
        """
        ИСПРАВЛЕНО: Создает секцию с детализированной разбивкой по урокам (проблема #97).

        Returns:
            widgets.VBox: Секция детализации
        """
        # Получаем детальную информацию
        lesson_scores = self.state_manager.learning_progress.state_manager.state[
            "learning"
        ].get("lesson_scores", {})
        lesson_attempts = self.state_manager.learning_progress.state_manager.state[
            "learning"
        ].get("lesson_attempts", {})
        control_tasks_status = self.state_manager.learning_progress.state_manager.state[
            "learning"
        ].get("control_tasks_status", {})
        completion_status = self.state_manager.learning_progress.state_manager.state[
            "learning"
        ].get("lesson_completion_status", {})

        # Заголовок секции
        header = widgets.HTML(
            value="""
        <h3 style="margin: 20px 0 15px 0; color: #495057;">
            📋 Детальная разбивка по урокам
        </h3>
        """
        )

        if not lesson_scores and not control_tasks_status:
            # Если данных нет
            no_data = widgets.HTML(
                value="""
            <div style="
                background: white;
                padding: 25px;
                border-radius: 12px;
                border: 1px solid #e9ecef;
                text-align: center;
                color: #6c757d;
                font-style: italic;
            ">
                Пока нет данных о завершенных уроках.<br>
                Начните изучение курса, чтобы увидеть подробную статистику.
            </div>
            """
            )
            return widgets.VBox([header, no_data])

        # Создаем список уроков
        lessons_list = []

        # Объединяем все данные по урокам
        all_lesson_ids = set()
        all_lesson_ids.update(lesson_scores.keys())
        all_lesson_ids.update(control_tasks_status.keys())
        all_lesson_ids.update(completion_status.keys())

        for lesson_id in sorted(all_lesson_ids):
            lesson_score = lesson_scores.get(lesson_id, 0)

            # ИСПРАВЛЕНО: Правильный подсчет попыток (проблема #97)
            lesson_attempts_data = lesson_attempts.get(lesson_id, [])
            if isinstance(lesson_attempts_data, list):
                lesson_attempts_count = len(lesson_attempts_data)
            else:
                # Fallback: если это не список, считаем как число
                lesson_attempts_count = (
                    int(lesson_attempts_data) if lesson_attempts_data else 0
                )

            is_completed = completion_status.get(lesson_id, False)
            control_tasks = control_tasks_status.get(lesson_id, {})

            # Считаем статистику по контрольным заданиям
            if control_tasks:
                completed_tasks = sum(
                    1 for completed in control_tasks.values() if completed
                )
                total_tasks = len(control_tasks)
                tasks_completion = f"{completed_tasks}/{total_tasks}"
            else:
                tasks_completion = "Нет заданий"

            # Определяем статус урока
            if is_completed:
                status_icon = "✅"
                status_color = "#28a745"
                status_text = "Завершен"
            elif lesson_score > 0:
                status_icon = "📝"
                status_color = "#ffc107"
                status_text = "Пройден тест"
            else:
                status_icon = "⏳"
                status_color = "#6c757d"
                status_text = "В процессе"

            # Определяем цвет оценки
            if lesson_score >= 80:
                score_color = "#28a745"
            elif lesson_score >= 60:
                score_color = "#ffc107"
            elif lesson_score > 0:
                score_color = "#dc3545"
            else:
                score_color = "#6c757d"

            lesson_html = f"""
            <div style="
                background: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="font-weight: bold; color: #495057; margin-bottom: 5px;">
                            {status_icon} Урок: {lesson_id}
                        </div>
                        <div style="color: {status_color}; font-size: 14px; margin-bottom: 5px;">
                            {status_text}
                        </div>
                        <div style="font-size: 13px; color: #6c757d;">
                            Попыток: {lesson_attempts_count} | Контрольные: {tasks_completion}
                        </div>
                    </div>

                    <div style="text-align: right;">
                        <div style="
                            font-size: 20px;
                            font-weight: bold;
                            color: {score_color};
                            margin-bottom: 5px;
                        ">
                            {lesson_score:.1f}%
                        </div>
                        <div style="font-size: 12px; color: #6c757d;">
                            {'Балл за тест' if lesson_score > 0 else 'Тест не пройден'}
                        </div>
                    </div>
                </div>
            </div>
            """

            lessons_list.append(widgets.HTML(value=lesson_html))

        if not lessons_list:
            return widgets.VBox(
                [header, widgets.HTML(value="<p>Нет данных для отображения</p>")]
            )

        # Контейнер для уроков с ограниченной высотой и прокруткой
        lessons_container = widgets.VBox(
            lessons_list,
            layout=widgets.Layout(
                max_height="400px",
                overflow_y="auto",
                border="1px solid #e9ecef",
                border_radius="8px",
                padding="10px",
            ),
        )

        return widgets.VBox([header, lessons_container])

    def _create_action_buttons(self):
        """
        Создает кнопки действий в личном кабинете.

        Returns:
            widgets.HBox: Контейнер с кнопками
        """
        # Кнопка "Продолжить обучение"
        continue_button = widgets.Button(
            description="📚 Продолжить обучение",
            button_style="primary",
            layout=widgets.Layout(width="200px", margin="5px"),
        )

        # Кнопка "Вернуться в главное меню"
        menu_button = widgets.Button(
            description="🏠 Главное меню",
            button_style="",
            layout=widgets.Layout(width="150px", margin="5px"),
        )

        # Кнопка "Настройки профиля"
        settings_button = widgets.Button(
            description="⚙️ Настройки",
            button_style="info",
            layout=widgets.Layout(width="150px", margin="5px"),
        )

        def on_continue_clicked(b):
            """ИСПРАВЛЕНО: Обработчик кнопки продолжения обучения (проблема #99)."""
            with self.output_container:
                clear_output(wait=True)

                try:
                    # Определяем куда перенаправить пользователя
                    learning_state = (
                        self.state_manager.learning_progress.state_manager.state[
                            "learning"
                        ]
                    )

                    current_course = learning_state.get("current_course")
                    current_section = learning_state.get("current_section")
                    current_topic = learning_state.get("current_topic")
                    current_lesson = learning_state.get("current_lesson")

                    if (
                        current_course
                        and current_section
                        and current_topic
                        and current_lesson
                    ):
                        # Есть текущий урок - переходим к нему
                        display(
                            self.utils.create_styled_message(
                                f"Переход к уроку: {current_section} → {current_topic} → {current_lesson}",
                                "info",
                            )
                        )

                        # ИСПРАВЛЕНО: Реализован фактический переход к уроку
                        from lesson_interface import LessonInterface

                        lesson_ui = LessonInterface(
                            self.state_manager,
                            self.content_generator,
                            self.system_logger,
                            self.assessment,
                        )

                        clear_output(wait=True)
                        lesson_widget = lesson_ui.show_lesson(
                            current_section, current_topic, current_lesson
                        )
                        display(lesson_widget)

                    else:
                        # Нет текущего урока - предлагаем выбрать курс
                        display(
                            self.utils.create_styled_message(
                                "Перенаправление к выбору курса...", "info"
                            )
                        )

                        # ИСПРАВЛЕНО: Реализован переход к выбору курса
                        from interface import UserInterface

                        interface = UserInterface(
                            self.state_manager,
                            self.content_generator,
                            self.assessment,
                            self.system_logger,
                        )

                        clear_output(wait=True)
                        display(interface.show_course_selection())

                except Exception as e:
                    self.logger.error(f"Ошибка при переходе к обучению: {str(e)}")
                    display(
                        self.utils.create_styled_message(
                            f"Ошибка при переходе к обучению: {str(e)}", "incorrect"
                        )
                    )

        def on_menu_clicked(b):
            """Обработчик кнопки главного меню."""
            with self.output_container:
                clear_output(wait=True)
                display(
                    self.utils.create_styled_message(
                        "Переход к главному меню...", "info"
                    )
                )

                try:
                    from interface import UserInterface

                    interface = UserInterface(
                        self.state_manager,
                        self.content_generator,
                        self.assessment,
                        self.system_logger,
                    )
                    clear_output(wait=True)
                    display(interface.show_main_menu())
                except Exception as e:
                    self.logger.error(f"Ошибка при переходе к главному меню: {str(e)}")
                    display(
                        self.utils.create_styled_message(
                            f"Ошибка: {str(e)}", "incorrect"
                        )
                    )

        def on_settings_clicked(b):
            """Обработчик кнопки настроек."""
            with self.output_container:
                clear_output(wait=True)
                display(
                    self.utils.create_styled_message(
                        "Переход к настройкам профиля...", "info"
                    )
                )

                try:
                    from interface import UserInterface

                    interface = UserInterface(
                        self.state_manager,
                        self.content_generator,
                        self.assessment,
                        self.system_logger,
                    )
                    clear_output(wait=True)
                    display(interface.show_initial_setup())
                except Exception as e:
                    self.logger.error(f"Ошибка при переходе к настройкам: {str(e)}")
                    display(
                        self.utils.create_styled_message(
                            f"Ошибка: {str(e)}", "incorrect"
                        )
                    )

        # Подключаем обработчики
        continue_button.on_click(on_continue_clicked)
        menu_button.on_click(on_menu_clicked)
        settings_button.on_click(on_settings_clicked)

        return widgets.HBox(
            [continue_button, menu_button, settings_button],
            layout=widgets.Layout(justify_content="center", margin="20px 0"),
        )

    def _create_error_interface(self, error_message):
        """
        Создает интерфейс ошибки.

        Args:
            error_message (str): Сообщение об ошибке

        Returns:
            widgets.VBox: Интерфейс ошибки
        """
        error_header = self.utils.create_header("❌ Ошибка личного кабинета")
        error_widget = self.utils.create_styled_message(
            f"Произошла ошибка при создании личного кабинета: {error_message}",
            "incorrect",
        )

        back_button = widgets.Button(
            description="🔙 Вернуться к главному меню",
            button_style="primary",
            layout=widgets.Layout(width="250px", margin="20px auto"),
        )

        def go_back_to_menu(b):
            """Возвращение к главному меню."""
            clear_output(wait=True)
            try:
                from interface import UserInterface

                interface = UserInterface(
                    self.state_manager,
                    self.content_generator,
                    self.assessment,
                    self.system_logger,
                )
                display(interface.show_main_menu())
            except Exception as e:
                self.logger.error(f"Ошибка при возврате к главному меню: {str(e)}")
                display(
                    self.utils.create_styled_message(
                        f"Критическая ошибка: {str(e)}", "incorrect"
                    )
                )

        back_button.on_click(go_back_to_menu)

        return widgets.VBox(
            [error_header, error_widget, back_button],
            layout=widgets.Layout(align_items="center", padding="20px"),
        )
