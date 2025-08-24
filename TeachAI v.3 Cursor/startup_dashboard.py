"""
Модуль для отображения дашборда статистики при запуске TeachAI.
Показывает информацию о прогрессе обучения, времени, оценках и незавершенных уроках.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from IPython.display import display, HTML
import ipywidgets as widgets
from pathlib import Path

# Импортируем InterfaceState для правильной работы
from interface import InterfaceState

class StartupDashboard:
    """Дашборд для отображения статистики при запуске системы."""
    
    def __init__(self, state_manager, content_generator=None):
        """
        Инициализация дашборда.
        
        Args:
            state_manager: Менеджер состояния системы
            content_generator: Генератор контента (для индикаторов загрузки)
        """
        self.state_manager = state_manager
        self.content_generator = content_generator
        self.logger = logging.getLogger(__name__)
        
    def show_dashboard(self) -> widgets.Widget:
        """
        Отображает интерактивный дашборд со статистикой обучения.
        
        Returns:
            widgets.Widget: Виджет с информацией о прогрессе и кнопкой продолжения
        """
        try:
            self.logger.info("Создание интерактивного дашборда статистики...")
            
            # Получаем данные для дашборда
            dashboard_data = self._collect_dashboard_data()
            
            # Создаем виджеты для отображения
            dashboard_content = self._create_dashboard_widget(dashboard_data)
            
            # Создаем кнопку "Продолжить обучение"
            continue_button = widgets.Button(
                description="🎯 Продолжить обучение",
                button_style='success',
                layout=widgets.Layout(
                    width='auto',
                    height='40px',
                    margin='20px 0 0 0'
                )
            )
            
            # Сохраняем ссылку на кнопку для обработчика
            self.continue_button = continue_button
            self.logger.info(f"Кнопка 'Продолжить обучение' создана и сохранена: {type(continue_button)}")
            
            # Создаем контейнер с дашбордом и кнопкой
            dashboard_widget = widgets.VBox(
                [dashboard_content, continue_button],
                layout=widgets.Layout(
                    width='100%',
                    padding='20px',
                    border='2px solid #ecf0f1',
                    margin='10px 0'
                )
            )
            
            self.logger.info("Интерактивный дашборд статистики создан успешно")
            return dashboard_widget
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании дашборда: {str(e)}")
            return self._create_error_widget(str(e))
    
    def setup_continue_button_handler(self, engine, display_callback):
        """
        Настраивает обработчик кнопки "Продолжить обучение".
        
        Args:
            engine: Экземпляр TeachAIEngine
            display_callback: Функция для отображения нового интерфейса
        """
        def on_continue_click(b):
            """Обработчик нажатия кнопки продолжения."""
            try:
                self.logger.info("Нажата кнопка 'Продолжить обучение'")
                
                # Очищаем вывод перед показом индикатора
                from IPython.display import clear_output
                clear_output(wait=True)
                
                # Показываем индикатор загрузки
                if self.content_generator and hasattr(self.content_generator, 'loading_manager') and self.content_generator.loading_manager:
                    loading_indicator = self.content_generator.loading_manager.show_loading(
                        "default", message="Подготовка к продолжению обучения..."
                    )
                    if display_callback:
                        display_callback(loading_indicator)
                else:
                    # Используем собственный простой индикатор
                    loading_indicator = self.show_loading_indicator("Подготовка к продолжению обучения...")
                    if display_callback:
                        display_callback(loading_indicator)
                
                # Получаем следующий интерфейс
                next_interface = self.get_next_lesson_interface(engine)
                
                # Отображаем новый интерфейс
                if display_callback:
                    display_callback(next_interface)
                
            except Exception as e:
                self.logger.error(f"Ошибка при переходе к следующему уроку: {str(e)}")
                import traceback
                self.logger.error(f"Полная трассировка: {traceback.format_exc()}")
                # Показываем ошибку пользователю
                error_widget = self._create_error_widget(f"Ошибка перехода: {str(e)}")
                if display_callback:
                    display_callback(error_widget)
        
        # Привязываем обработчик к кнопке
        if hasattr(self, 'continue_button') and self.continue_button:
            self.continue_button.on_click(on_continue_click)
            self.logger.info("Обработчик кнопки 'Продолжить обучение' настроен")
        else:
            self.logger.warning("Кнопка 'Продолжить обучение' не найдена - обработчик не может быть настроен")
            # Пытаемся найти кнопку в атрибутах
            if hasattr(self, '__dict__'):
                for attr_name, attr_value in self.__dict__.items():
                    if hasattr(attr_value, 'description') and 'Продолжить обучение' in str(attr_value.description):
                        self.logger.info(f"Найдена кнопка в атрибуте: {attr_name}")
                        attr_value.on_click(on_continue_click)
                        self.logger.info("Обработчик кнопки настроен через поиск атрибутов")
                        break
    
    def get_next_lesson_interface(self, engine):
        """
        Получает интерфейс следующего урока после показа дашборда.
        
        Args:
            engine: Экземпляр TeachAIEngine для доступа к интерфейсу
            
        Returns:
            widgets.Widget: Интерфейс урока или выбора курса
        """
        try:
            self.logger.info("Начинаем получение следующего интерфейса урока")
            
            # Проверяем, что engine.interface инициализирован
            if not engine.interface:
                self.logger.error("engine.interface не инициализирован")
                return self._create_error_widget("Система не готова к работе. Попробуйте перезапустить.")
            
            # Проверяем есть ли незавершенный урок
            current_lesson_info = engine._check_current_lesson_status()
            self.logger.info(f"Информация о текущем уроке: {current_lesson_info}")
            
            if current_lesson_info:
                # Есть незавершенный урок - переходим к нему
                section_id, topic_id, lesson_id = current_lesson_info
                self.logger.info(f"Переходим к незавершенному уроку: {section_id}:{topic_id}:{lesson_id}")
                
                engine.interface.current_state = InterfaceState.LESSON_VIEW
                lesson_widget = engine.interface.show_lesson(section_id, topic_id, lesson_id)
                self.logger.info("Урок успешно загружен")
                return lesson_widget
            else:
                # Нет незавершенных уроков - показываем выбор курса
                self.logger.info("Нет незавершенных уроков - показываем выбор курса")
                engine.interface.current_state = InterfaceState.COURSE_SELECTION
                course_selection_widget = engine.interface.show_course_selection()
                self.logger.info("Интерфейс выбора курса загружен")
                return course_selection_widget
                
        except Exception as e:
            self.logger.error(f"Ошибка при переходе к следующему уроку: {str(e)}")
            import traceback
            self.logger.error(f"Полная трассировка: {traceback.format_exc()}")
            return self._create_error_widget(f"Ошибка перехода: {str(e)}")
    
    def _collect_dashboard_data(self) -> Dict[str, Any]:
        """
        Собирает данные для дашборда.
        
        Returns:
            Dict[str, Any]: Данные для отображения
        """
        try:
            state = self.state_manager.state
            
            # Основная информация о курсе
            course_info = self._get_course_info()
            
            # Статистика прогресса
            progress_stats = self._get_progress_statistics()
            
            # Время обучения
            time_stats = self._get_time_statistics()
            
            # Оценки и тесты
            assessment_stats = self._get_assessment_statistics()
            
            # Незавершенные уроки
            incomplete_lessons = self._get_incomplete_lessons()
            
            # Контрольные задания
            control_tasks_stats = self._get_control_tasks_statistics()
            
            return {
                "course_info": course_info,
                "progress_stats": progress_stats,
                "time_stats": time_stats,
                "assessment_stats": assessment_stats,
                "incomplete_lessons": incomplete_lessons,
                "control_tasks_stats": control_tasks_stats
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при сборе данных дашборда: {str(e)}")
            return {"error": str(e)}
    
    def _get_course_info(self) -> Dict[str, Any]:
        """Получает информацию о текущем курсе."""
        try:
            state = self.state_manager.state
            course_plan = state.get("course_plan", {})
            
            return {
                "title": course_plan.get("title", "Курс не выбран"),
                "description": course_plan.get("description", ""),
                "total_duration": course_plan.get("total_duration_minutes", 0),
                "sections_count": len(course_plan.get("sections", [])),
                "current_course": state.get("learning", {}).get("current_course", "")
            }
        except Exception as e:
            self.logger.error(f"Ошибка при получении информации о курсе: {str(e)}")
            return {"title": "Ошибка загрузки", "description": ""}
    
    def _get_progress_statistics(self) -> Dict[str, Any]:
        """Получает статистику прогресса обучения."""
        try:
            state = self.state_manager.state
            learning = state.get("learning", {})
            
            completed_lessons = learning.get("completed_lessons", [])
            course_plan = state.get("course_plan", {})
            sections = course_plan.get("sections", [])
            
            # Подсчитываем общее количество уроков
            total_lessons = 0
            for section in sections:
                for topic in section.get("topics", []):
                    total_lessons += len(topic.get("lessons", []))
            
            # Процент завершения
            progress_percent = learning.get("course_progress_percent", 0)
            if total_lessons > 0:
                progress_percent = (len(completed_lessons) / total_lessons) * 100
            
            return {
                "completed_lessons_count": len(completed_lessons),
                "total_lessons_count": total_lessons,
                "progress_percent": round(progress_percent, 1),
                "current_lesson": learning.get("current_lesson", ""),
                "current_section": learning.get("current_section", ""),
                "current_topic": learning.get("current_topic", "")
            }
        except Exception as e:
            self.logger.error(f"Ошибка при получении статистики прогресса: {str(e)}")
            return {"progress_percent": 0, "completed_lessons_count": 0}
    
    def _get_time_statistics(self) -> Dict[str, Any]:
        """Получает статистику времени обучения."""
        try:
            state = self.state_manager.state
            system = state.get("system", {})
            
            # Время последнего доступа
            last_access_str = system.get("last_access", "")
            if last_access_str:
                try:
                    last_access = datetime.fromisoformat(last_access_str)
                    time_since_last = datetime.now() - last_access
                    days_since_last = time_since_last.days
                except:
                    days_since_last = 0
            else:
                days_since_last = 0
            
            # Общее время обучения (примерная оценка)
            user_profile = state.get("user", {})
            lesson_duration = user_profile.get("lesson_duration_minutes", 30)
            completed_lessons = state.get("learning", {}).get("completed_lessons", [])
            
            estimated_total_time = len(completed_lessons) * lesson_duration
            
            return {
                "days_since_last_access": days_since_last,
                "estimated_total_time_minutes": estimated_total_time,
                "lesson_duration_minutes": lesson_duration,
                "last_access": last_access_str
            }
        except Exception as e:
            self.logger.error(f"Ошибка при получении статистики времени: {str(e)}")
            return {"days_since_last_access": 0, "estimated_total_time_minutes": 0}
    
    def _get_assessment_statistics(self) -> Dict[str, Any]:
        """Получает статистику тестов и оценок."""
        try:
            state = self.state_manager.state
            learning = state.get("learning", {})
            
            lesson_scores = learning.get("lesson_scores", {})
            lesson_attempts = learning.get("lesson_attempts", {})
            
            # Средняя оценка
            average_score = learning.get("average_score", 0)
            if lesson_scores:
                scores = list(lesson_scores.values())
                average_score = sum(scores) / len(scores)
            
            # Количество пройденных тестов
            passed_tests = sum(1 for score in lesson_scores.values() if score >= 70)
            total_tests = len(lesson_scores)
            
            # Общее количество попыток
            total_attempts = sum(len(attempts) for attempts in lesson_attempts.values())
            
            return {
                "average_score": round(average_score, 1),
                "passed_tests_count": passed_tests,
                "total_tests_count": total_tests,
                "total_attempts_count": total_attempts,
                "best_score": max(lesson_scores.values()) if lesson_scores else 0,
                "worst_score": min(lesson_scores.values()) if lesson_scores else 0
            }
        except Exception as e:
            self.logger.error(f"Ошибка при получении статистики тестов: {str(e)}")
            return {"average_score": 0, "passed_tests_count": 0}
    
    def _get_incomplete_lessons(self) -> List[Dict[str, Any]]:
        """Получает список незавершенных уроков."""
        try:
            state = self.state_manager.state
            learning = state.get("learning", {})
            course_plan = state.get("course_plan", {})
            
            incomplete_lessons = []
            lesson_completion_status = learning.get("lesson_completion_status", {})
            
            # Проверяем все уроки в плане курса
            for section in course_plan.get("sections", []):
                for topic in section.get("topics", []):
                    for lesson in topic.get("lessons", []):
                        lesson_id = f"{section['id']}:{topic['id']}:{lesson['id']}"
                        
                        # Если урок не завершен или нет информации о нем
                        if not lesson_completion_status.get(lesson_id, False):
                            incomplete_lessons.append({
                                "lesson_id": lesson_id,
                                "title": lesson.get("title", "Без названия"),
                                "section": section.get("title", ""),
                                "topic": topic.get("title", ""),
                                "has_attempts": lesson_id in learning.get("lesson_attempts", {})
                            })
            
            return incomplete_lessons
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении незавершенных уроков: {str(e)}")
            return []
    
    def _get_control_tasks_statistics(self) -> Dict[str, Any]:
        """Получает статистику контрольных заданий."""
        try:
            state = self.state_manager.state
            
            # Получаем статистику контрольных заданий из корневого уровня state
            control_tasks = state.get("control_tasks", {})
            
            completed_tasks = 0
            failed_tasks = 0
            
            # Исправлено: control_tasks содержит dict для каждого lesson_id
            for lesson_id, task_result in control_tasks.items():
                if isinstance(task_result, dict):
                    if task_result.get("is_correct", False):
                        completed_tasks += 1
                    else:
                        failed_tasks += 1
            
            total_tasks = completed_tasks + failed_tasks
            
            return {
                "completed_tasks_count": completed_tasks,
                "failed_tasks_count": failed_tasks,
                "total_tasks_count": total_tasks,
                "success_rate": round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Ошибка при получении статистики контрольных заданий: {str(e)}")
            return {"completed_tasks_count": 0, "total_tasks_count": 0, "success_rate": 0}
    
    def _create_dashboard_widget(self, data: Dict[str, Any]) -> widgets.Widget:
        """
        Создает виджет дашборда.
        
        Args:
            data: Данные для отображения
            
        Returns:
            widgets.Widget: Виджет дашборда
        """
        try:
            # Создаем заголовок
            header = widgets.HTML(
                value="<h2 style='color: #2c3e50; text-align: center; margin-bottom: 20px;'>📊 Дашборд обучения TeachAI</h2>",
                layout=widgets.Layout(margin='0 0 20px 0')
            )
            
            # Создаем секции дашборда
            sections = []
            
            # Информация о курсе
            if "course_info" in data:
                course_section = self._create_course_section(data["course_info"])
                sections.append(course_section)
            
            # Прогресс обучения
            if "progress_stats" in data:
                progress_section = self._create_progress_section(data["progress_stats"])
                sections.append(progress_section)
            
            # Статистика времени
            if "time_stats" in data:
                time_section = self._create_time_section(data["time_stats"])
                sections.append(time_section)
            
            # Статистика тестов
            if "assessment_stats" in data:
                assessment_section = self._create_assessment_section(data["assessment_stats"])
                sections.append(assessment_section)
            
            # Контрольные задания
            if "control_tasks_stats" in data:
                control_tasks_section = self._create_control_tasks_section(data["control_tasks_stats"])
                sections.append(control_tasks_section)
            
            # Незавершенные уроки
            if "incomplete_lessons" in data and data["incomplete_lessons"]:
                incomplete_section = self._create_incomplete_lessons_section(data["incomplete_lessons"])
                sections.append(incomplete_section)
            
            # Собираем все секции
            dashboard_content = [header] + sections
            
            # Создаем основной контейнер
            dashboard_widget = widgets.VBox(
                dashboard_content,
                layout=widgets.Layout(
                    width='100%',
                    padding='20px',
                    border='2px solid #ecf0f1',
                    margin='10px 0'
                )
            )
            
            return dashboard_widget
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании виджета дашборда: {str(e)}")
            return self._create_error_widget(str(e))
    
    def _create_course_section(self, course_info: Dict[str, Any]) -> widgets.Widget:
        """Создает секцию с информацией о курсе."""
        course_title = course_info.get("title", "Курс не выбран")
        course_description = course_info.get("description", "")
        total_duration = course_info.get("total_duration", 0)
        
        html_content = f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; margin: 10px 0;'>
            <h3 style='margin: 0 0 10px 0;'>📚 {course_title}</h3>
            <p style='margin: 5px 0; opacity: 0.9;'>{course_description}</p>
            <p style='margin: 5px 0; font-size: 0.9em; opacity: 0.8;'>
                ⏱️ Общая продолжительность: {total_duration} минут
            </p>
        </div>
        """
        
        return widgets.HTML(value=html_content)
    
    def _create_progress_section(self, progress_stats: Dict[str, Any]) -> widgets.Widget:
        """Создает секцию с прогрессом обучения."""
        completed = progress_stats.get("completed_lessons_count", 0)
        total = progress_stats.get("total_lessons_count", 0)
        progress_percent = progress_stats.get("progress_percent", 0)
        current_lesson = progress_stats.get("current_lesson", "")
        
        # Создаем прогресс-бар
        progress_bar_width = min(progress_percent, 100)
        progress_bar_color = "#27ae60" if progress_percent >= 70 else "#f39c12" if progress_percent >= 40 else "#e74c3c"
        
        html_content = f"""
        <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid {progress_bar_color};'>
            <h4 style='margin: 0 0 15px 0; color: #2c3e50;'>📈 Прогресс обучения</h4>
            <div style='margin: 10px 0;'>
                <div style='background: #ecf0f1; height: 20px; border-radius: 10px; overflow: hidden;'>
                    <div style='background: {progress_bar_color}; height: 100%; width: {progress_bar_width}%; transition: width 0.3s ease;'></div>
                </div>
                <p style='margin: 5px 0; font-size: 0.9em; color: #7f8c8d;'>
                    {completed} из {total} уроков завершено ({progress_percent}%)
                </p>
            </div>
            <p style='margin: 5px 0; font-size: 0.9em; color: #7f8c8d;'>
                🎯 Текущий урок: {self._get_current_lesson_display_name(progress_stats)}
            </p>
        </div>
        """
        
        return widgets.HTML(value=html_content)
    
    def _create_time_section(self, time_stats: Dict[str, Any]) -> widgets.Widget:
        """Создает секцию со статистикой времени."""
        days_since_last = time_stats.get("days_since_last_access", 0)
        estimated_time = time_stats.get("estimated_total_time_minutes", 0)
        lesson_duration = time_stats.get("lesson_duration_minutes", 30)
        
        # Форматируем время
        hours = estimated_time // 60
        minutes = estimated_time % 60
        time_str = f"{hours}ч {minutes}м" if hours > 0 else f"{minutes}м"
        
        # Определяем цвет в зависимости от времени с последнего доступа
        if days_since_last == 0:
            last_access_color = "#27ae60"
            last_access_text = "Сегодня"
        elif days_since_last == 1:
            last_access_color = "#f39c12"
            last_access_text = "Вчера"
        else:
            last_access_color = "#e74c3c"
            last_access_text = f"{days_since_last} дней назад"
        
        html_content = f"""
        <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid {last_access_color};'>
            <h4 style='margin: 0 0 15px 0; color: #2c3e50;'>⏰ Время обучения</h4>
            <p style='margin: 5px 0; font-size: 0.9em; color: #7f8c8d;'>
                🕐 Общее время обучения: <strong>{time_str}</strong>
            </p>
            <p style='margin: 5px 0; font-size: 0.9em; color: #7f8c8d;'>
                📅 Последний доступ: <strong style='color: {last_access_color};'>{last_access_text}</strong>
            </p>
            <p style='margin: 5px 0; font-size: 0.9em; color: #7f8c8d;'>
                ⏱️ Длительность занятия: {lesson_duration} минут
            </p>
        </div>
        """
        
        return widgets.HTML(value=html_content)
    
    def _create_assessment_section(self, assessment_stats: Dict[str, Any]) -> widgets.Widget:
        """Создает секцию со статистикой тестов."""
        average_score = assessment_stats.get("average_score", 0)
        passed_tests = assessment_stats.get("passed_tests_count", 0)
        total_tests = assessment_stats.get("total_tests_count", 0)
        total_attempts = assessment_stats.get("total_attempts_count", 0)
        best_score = assessment_stats.get("best_score", 0)
        worst_score = assessment_stats.get("worst_score", 0)
        
        # Определяем цвет средней оценки
        if average_score >= 80:
            score_color = "#27ae60"
        elif average_score >= 60:
            score_color = "#f39c12"
        else:
            score_color = "#e74c3c"
        
        html_content = f"""
        <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid {score_color};'>
            <h4 style='margin: 0 0 15px 0; color: #2c3e50;'>📝 Результаты тестов</h4>
            <p style='margin: 5px 0; font-size: 0.9em; color: #7f8c8d;'>
                📊 Средняя оценка: <strong style='color: {score_color};'>{average_score}%</strong>
            </p>
            <p style='margin: 5px 0; font-size: 0.9em; color: #7f8c8d;'>
                ✅ Успешно пройдено: {passed_tests} из {total_tests} тестов
            </p>
            <p style='margin: 5px 0; font-size: 0.9em; color: #7f8c8d;'>
                🔄 Всего попыток: {total_attempts}
            </p>
            <p style='margin: 5px 0; font-size: 0.9em; color: #7f8c8d;'>
                🏆 Лучший результат: {best_score}% | Худший: {worst_score}%
            </p>
        </div>
        """
        
        return widgets.HTML(value=html_content)
    
    def _create_control_tasks_section(self, control_tasks_stats: Dict[str, Any]) -> widgets.Widget:
        """Создает секцию со статистикой контрольных заданий."""
        completed_tasks = control_tasks_stats.get("completed_tasks_count", 0)
        total_tasks = control_tasks_stats.get("total_tasks_count", 0)
        success_rate = control_tasks_stats.get("success_rate", 0)
        
        if total_tasks == 0:
            html_content = """
            <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #95a5a6;'>
                <h4 style='margin: 0 0 15px 0; color: #2c3e50;'>💻 Контрольные задания</h4>
                <p style='margin: 5px 0; font-size: 0.9em; color: #7f8c8d;'>
                    📝 Контрольные задания станут доступны после прохождения тестов
                </p>
                <p style='margin: 5px 0; font-size: 0.8em; color: #95a5a6;'>
                    ℹ️ Контрольные задания появляются после успешного прохождения теста по уроку
                </p>
            </div>
            """
        else:
            # Определяем цвет успешности
            if success_rate >= 80:
                success_color = "#27ae60"
            elif success_rate >= 60:
                success_color = "#f39c12"
            else:
                success_color = "#e74c3c"
            
            html_content = f"""
            <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid {success_color};'>
                <h4 style='margin: 0 0 15px 0; color: #2c3e50;'>💻 Контрольные задания</h4>
                <p style='margin: 5px 0; font-size: 0.9em; color: #7f8c8d;'>
                    ✅ Выполнено: {completed_tasks} из {total_tasks} заданий
                </p>
                <p style='margin: 5px 0; font-size: 0.9em; color: #7f8c8d;'>
                    📊 Успешность: <strong style='color: {success_color};'>{success_rate}%</strong>
                </p>
            </div>
            """
        
        return widgets.HTML(value=html_content)
    
    def _create_incomplete_lessons_section(self, incomplete_lessons: List[Dict[str, Any]]) -> widgets.Widget:
        """Создает секцию с незавершенными уроками."""
        lessons_html = ""
        for lesson in incomplete_lessons[:5]:  # Показываем только первые 5
            lesson_title = lesson.get("title", "Без названия")
            section_title = lesson.get("section", "")
            topic_title = lesson.get("topic", "")
            has_attempts = lesson.get("has_attempts", False)
            
            status_icon = "🔄" if has_attempts else "⏳"
            status_text = "Есть попытки" if has_attempts else "Не начат"
            
            lessons_html += f"""
            <div style='background: #fff; padding: 8px; margin: 5px 0; border-radius: 5px; border-left: 3px solid #e74c3c;'>
                <p style='margin: 2px 0; font-size: 0.9em; color: #2c3e50;'>
                    <strong>{lesson_title}</strong>
                </p>
                <p style='margin: 2px 0; font-size: 0.8em; color: #7f8c8d;'>
                    {section_title} → {topic_title}
                </p>
                <p style='margin: 2px 0; font-size: 0.8em; color: #7f8c8d;'>
                    {status_icon} {status_text}
                </p>
            </div>
            """
        
        if len(incomplete_lessons) > 5:
            lessons_html += f"""
            <div style='background: #fff; padding: 8px; margin: 5px 0; border-radius: 5px; border-left: 3px solid #95a5a6;'>
                <p style='margin: 2px 0; font-size: 0.8em; color: #7f8c8d; text-align: center;'>
                    ... и еще {len(incomplete_lessons) - 5} уроков
                </p>
            </div>
            """
        
        html_content = f"""
        <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #e74c3c;'>
            <h4 style='margin: 0 0 15px 0; color: #2c3e50;'>⚠️ Незавершенные уроки ({len(incomplete_lessons)})</h4>
            {lessons_html}
        </div>
        """
        
        return widgets.HTML(value=html_content)
    
    def _create_error_widget(self, error_message: str) -> widgets.Widget:
        """Создает виджет с сообщением об ошибке."""
        html_content = f"""
        <div style='background: #fee; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #e74c3c;'>
            <h4 style='margin: 0 0 15px 0; color: #c0392b;'>❌ Ошибка загрузки дашборда</h4>
            <p style='margin: 5px 0; font-size: 0.9em; color: #7f8c8d;'>
                {error_message}
            </p>
        </div>
        """
        
        return widgets.HTML(value=html_content)
    
    def _get_current_lesson_display_name(self, progress_stats: Dict[str, Any]) -> str:
        """
        Получает отображаемое название текущего урока.
        
        Args:
            progress_stats: Статистика прогресса
            
        Returns:
            str: Название текущего урока или "Не выбран"
        """
        try:
            current_lesson = progress_stats.get("current_lesson", "")
            current_section = progress_stats.get("current_section", "")
            current_topic = progress_stats.get("current_topic", "")
            
            # Если есть информация о текущем уроке, получаем его название
            if current_section and current_topic and current_lesson:
                course_plan = self.state_manager.state.get("course_plan", {})
                
                # Ищем урок в плане курса
                for section in course_plan.get("sections", []):
                    if section.get("id") == current_section:
                        for topic in section.get("topics", []):
                            if topic.get("id") == current_topic:
                                for lesson in topic.get("lessons", []):
                                    if lesson.get("id") == current_lesson:
                                        return lesson.get("title", "Без названия")
            
            # Если нет информации о текущем уроке, возвращаем первый урок из плана
            course_plan = self.state_manager.state.get("course_plan", {})
            if course_plan.get("sections"):
                first_section = course_plan["sections"][0]
                if first_section.get("topics"):
                    first_topic = first_section["topics"][0]
                    if first_topic.get("lessons"):
                        first_lesson = first_topic["lessons"][0]
                        return first_lesson.get("title", "Без названия")
            
            return "Не выбран"
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении названия текущего урока: {str(e)}")
            return "Не выбран"

    def show_loading_indicator(self, message: str = "Загрузка...") -> widgets.Widget:
        """
        Показывает индикатор загрузки.
        
        Args:
            message: Сообщение для отображения
            
        Returns:
            widgets.Widget: Виджет с индикатором загрузки
        """
        html_content = f"""
        <div style='background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0; text-align: center;'>
            <div style='display: inline-block; width: 40px; height: 40px; border: 4px solid #ecf0f1; border-top: 4px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite;'></div>
            <p style='margin: 10px 0 0 0; color: #7f8c8d; font-size: 0.9em;'>{message}</p>
            <style>
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </div>
        """
        
        return widgets.HTML(value=html_content) 