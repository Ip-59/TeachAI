"""
Модуль создания HTML-секций для интерфейса личного кабинета студента.
Отвечает за генерацию всех визуальных компонентов профиля.
"""

import ipywidgets as widgets
import logging
from datetime import datetime


class StudentProfileSections:
    """
    Класс для создания HTML-секций интерфейса личного кабинета.
    """

    def __init__(self, core):
        """
        Инициализация модуля секций.

        Args:
            core: Ядро интерфейса StudentProfileCore
        """
        self.core = core
        self.state_manager = core.state_manager
        self.logger = logging.getLogger(__name__)

        self.logger.info("StudentProfileSections инициализирован")

    def create_profile_info_section(self, progress_data):
        """
        Создает секцию с основной информацией о профиле.

        Args:
            progress_data (dict): Данные о прогрессе

        Returns:
            widgets.HTML: Секция профиля
        """
        try:
            user_data = self.core._get_user_profile_data()
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

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                    <div>
                        <h4 style="margin: 0 0 10px 0; color: #e3f2fd;">📚 Текущий курс</h4>
                        <p style="margin: 0; font-size: 16px; font-weight: bold;">{current_course}</p>
                    </div>

                    <div>
                        <h4 style="margin: 0 0 10px 0; color: #e3f2fd;">📖 Текущий урок</h4>
                        <p style="margin: 0; font-size: 16px; font-weight: bold;">{current_lesson}</p>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h4 style="margin: 0 0 10px 0; color: #e3f2fd;">📂 Раздел</h4>
                        <p style="margin: 0; font-size: 14px;">{current_section}</p>
                    </div>

                    <div>
                        <h4 style="margin: 0 0 10px 0; color: #e3f2fd;">🎯 Тема</h4>
                        <p style="margin: 0; font-size: 14px;">{current_topic}</p>
                    </div>
                </div>

                <div style="
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid rgba(255,255,255,0.3);
                    text-align: center;
                    font-size: 12px;
                    color: #e3f2fd;
                ">
                    Последнее обновление: {current_date}
                </div>
            </div>
            """

            return widgets.HTML(value=profile_html)

        except Exception as e:
            self.logger.error(f"Ошибка при создании секции профиля: {str(e)}")
            return widgets.HTML(value="<div>Ошибка загрузки информации о профиле</div>")

    def create_course_progress_section(self, detailed_stats):
        """
        Создает секцию с прогрессом по курсу.

        Args:
            detailed_stats (dict): Детальная статистика

        Returns:
            widgets.HTML: Секция прогресса курса
        """
        try:
            if not detailed_stats:
                return widgets.HTML(value="")

            # Получаем статистику прогресса
            completed_lessons = detailed_stats.get("completed_lessons", 0)
            total_lessons = detailed_stats.get("total_lessons", 1)
            progress_percentage = (
                (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
            )

            # Определяем цвет прогресса
            if progress_percentage >= 80:
                progress_color = "#28a745"
                progress_text = "Отличный прогресс! Продолжайте в том же духе!"
            elif progress_percentage >= 50:
                progress_color = "#ffc107"
                progress_text = "Хороший прогресс. Вы на верном пути!"
            elif progress_percentage >= 25:
                progress_color = "#17a2b8"
                progress_text = "Неплохое начало. Продолжайте обучение!"
            else:
                progress_color = "#dc3545"
                progress_text = "Начните изучение материала."

            progress_html = f"""
            <div style="
                background: white;
                padding: 25px;
                border-radius: 12px;
                border: 1px solid #e9ecef;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            ">
                <h3 style="margin: 0 0 25px 0; color: #495057;">📈 Прогресс по курсу</h3>

                <div style="margin-bottom: 20px;">
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 10px;
                    ">
                        <span style="font-weight: bold; color: #495057;">Общий прогресс</span>
                        <span style="font-weight: bold; color: {progress_color};">{progress_percentage:.1f}%</span>
                    </div>
                    <div style="
                        width: 100%;
                        height: 12px;
                        background-color: #e9ecef;
                        border-radius: 6px;
                        overflow: hidden;
                    ">
                        <div style="
                            width: {progress_percentage}%;
                            height: 100%;
                            background: linear-gradient(90deg, {progress_color}, {progress_color}80);
                            transition: width 0.3s ease;
                        "></div>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 20px;">
                    <div>
                        <div style="font-size: 28px; font-weight: bold; color: #28a745;">{completed_lessons}</div>
                        <div style="color: #6c757d; font-size: 14px;">Пройдено уроков</div>
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

        except Exception as e:
            self.logger.error(f"Ошибка при создании секции прогресса: {str(e)}")
            return widgets.HTML(value="<div>Ошибка загрузки прогресса курса</div>")

    def create_lessons_statistics_section(self, detailed_stats):
        """
        Создает секцию со статистикой по урокам и тестам.

        Args:
            detailed_stats (dict): Статистика курса

        Returns:
            widgets.HTML: Секция статистики по урокам
        """
        try:
            if not detailed_stats:
                return widgets.HTML(value="")

            # Получаем статистику по тестам
            average_score = detailed_stats.get("average_score", 0)
            highest_score = detailed_stats.get("highest_score", 0)
            lowest_score = detailed_stats.get("lowest_score", 0)
            total_assessments = detailed_stats.get("total_assessments", 0)
            lessons_passed = detailed_stats.get("completed_lessons", 0)

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
                    ">
                        <div style="font-size: 32px; font-weight: bold; color: {score_color};">
                            {average_score:.1f}%
                        </div>
                        <div style="color: #6c757d; margin-top: 5px;">Средний балл</div>
                    </div>

                    <div style="
                        background: linear-gradient(135deg, #28a74520, #28a74510);
                        padding: 20px;
                        border-radius: 10px;
                        border: 1px solid #28a74540;
                    ">
                        <div style="font-size: 32px; font-weight: bold; color: #28a745;">
                            {highest_score:.1f}%
                        </div>
                        <div style="color: #6c757d; margin-top: 5px;">Лучший результат</div>
                    </div>

                    <div style="
                        background: linear-gradient(135deg, #17a2b820, #17a2b810);
                        padding: 20px;
                        border-radius: 10px;
                        border: 1px solid #17a2b840;
                    ">
                        <div style="font-size: 32px; font-weight: bold; color: #17a2b8;">
                            {total_assessments}
                        </div>
                        <div style="color: #6c757d; margin-top: 5px;">Тестов пройдено</div>
                    </div>

                    <div style="
                        background: linear-gradient(135deg, #6f42c120, #6f42c110);
                        padding: 20px;
                        border-radius: 10px;
                        border: 1px solid #6f42c140;
                    ">
                        <div style="font-size: 32px; font-weight: bold; color: #6f42c1;">
                            {lessons_passed}
                        </div>
                        <div style="color: #6c757d; margin-top: 5px;">Уроков завершено</div>
                    </div>
                </div>
            </div>
            """

            return widgets.HTML(value=lessons_html)

        except Exception as e:
            self.logger.error(f"Ошибка при создании секции статистики уроков: {str(e)}")
            return widgets.HTML(value="<div>Ошибка загрузки статистики уроков</div>")

    def create_control_tasks_section(self, detailed_stats):
        """
        Создает секцию со статистикой по контрольным заданиям.

        Args:
            detailed_stats (dict): Статистика курса

        Returns:
            widgets.HTML: Секция контрольных заданий
        """
        try:
            if not detailed_stats:
                return widgets.HTML(value="")

            # Получаем статистику по контрольным заданиям
            completed_control_tasks = detailed_stats.get("completed_control_tasks", 0)
            total_control_tasks = detailed_stats.get("total_control_tasks", 0)

            if total_control_tasks > 0:
                completion_rate = (completed_control_tasks / total_control_tasks) * 100

                # Определяем цвет и сообщение
                if completion_rate >= 80:
                    tasks_color = "#28a745"
                    tasks_message = "Отличная работа с контрольными заданиями!"
                elif completion_rate >= 50:
                    tasks_color = "#ffc107"
                    tasks_message = "Хороший прогресс в выполнении заданий."
                else:
                    tasks_color = "#dc3545"
                    tasks_message = (
                        "Рекомендуется уделить больше внимания контрольным заданиям."
                    )
            else:
                completion_rate = 0
                tasks_color = "#6c757d"
                tasks_message = "Контрольные задания пока не доступны."

            control_tasks_html = f"""
            <div style="
                background: white;
                padding: 25px;
                border-radius: 12px;
                border: 1px solid #e9ecef;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            ">
                <h3 style="margin: 0 0 25px 0; color: #495057;">⚡ Контрольные задания</h3>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; margin-bottom: 20px;">
                    <div style="
                        background: linear-gradient(135deg, #28a74520, #28a74510);
                        padding: 20px;
                        border-radius: 10px;
                        border: 1px solid #28a74540;
                    ">
                        <div style="font-size: 32px; font-weight: bold; color: #28a745;">
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

        except Exception as e:
            self.logger.error(
                f"Ошибка при создании секции контрольных заданий: {str(e)}"
            )
            return widgets.HTML(value="<div>Ошибка загрузки контрольных заданий</div>")

    def create_detailed_breakdown_section(self):
        """
        ИСПРАВЛЕНО: Создает секцию с детализированной разбивкой по урокам (проблема #97).

        Returns:
            widgets.VBox: Секция с детализацией по урокам
        """
        try:
            header = widgets.HTML(
                value="<h3 style='margin: 0 0 20px 0; color: #495057;'>📋 Детализация по урокам</h3>"
            )

            # Получаем детальную информацию по урокам
            lessons_data = self._get_lessons_breakdown_data()
            lessons_list = []

            for lesson_data in lessons_data:
                lesson_name = lesson_data.get("name", "Урок без названия")
                lesson_status = lesson_data.get("status", "not_started")
                lesson_score = lesson_data.get("score", 0)
                lesson_attempts_count = lesson_data.get(
                    "attempts_count", 0
                )  # ИСПРАВЛЕНО: правильный подсчет
                tasks_completion = lesson_data.get("tasks_completion", "Не выполнено")

                # Определяем цвет статуса
                if lesson_status == "completed":
                    status_color = "#28a745"
                    status_text = "✅ Завершен"
                elif lesson_status == "in_progress":
                    status_color = "#ffc107"
                    status_text = "🔄 В процессе"
                else:
                    status_color = "#6c757d"
                    status_text = "⏸️ Не начат"

                # Цвет для балла
                if lesson_score >= 80:
                    score_color = "#28a745"
                elif lesson_score >= 60:
                    score_color = "#ffc107"
                else:
                    score_color = "#dc3545"

                lesson_html = f"""
                <div style="
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid #e9ecef;
                    margin-bottom: 10px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <div style="
                                font-size: 16px;
                                font-weight: bold;
                                color: #495057;
                                margin-bottom: 8px;
                            ">
                                {lesson_name}
                            </div>

                            <div style="display: flex; align-items: center; gap: 20px;">
                                <div style="
                                    display: inline-block;
                                    padding: 4px 8px;
                                    background-color: {status_color}20;
                                    color: {status_color};
                                    border-radius: 4px;
                                    font-size: 12px;
                                    font-weight: bold;
                                ">
                                    {status_text}
                                </div>

                                <div style="font-size: 12px; color: #6c757d;">
                                    Попыток: {lesson_attempts_count} | Контрольные: {tasks_completion}
                                </div>
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

        except Exception as e:
            self.logger.error(
                f"Ошибка при создании детализированной разбивки: {str(e)}"
            )
            return widgets.VBox(
                [widgets.HTML(value="<div>Ошибка загрузки детализации уроков</div>")]
            )

    def _get_lessons_breakdown_data(self):
        """
        Получает данные для детализированной разбивки по урокам.

        Returns:
            list: Список данных уроков
        """
        try:
            # ИСПРАВЛЕНО: Правильная логика получения breakdown данных (проблема #97)
            return self.state_manager.learning_progress.get_lessons_breakdown()
        except Exception as e:
            self.logger.error(f"Ошибка при получении breakdown данных: {str(e)}")
            return []
