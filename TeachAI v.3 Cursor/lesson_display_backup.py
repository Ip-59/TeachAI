"""
Отображение уроков.
Вынесено из lesson_interface.py для улучшения модульности.
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import logging
from lesson_utils import LessonUtils

# Импорт адаптера для интеграции ячеек (безопасно)
try:
    from cell_integration import cell_adapter

    CELLS_INTEGRATION_AVAILABLE = True
except ImportError:
    CELLS_INTEGRATION_AVAILABLE = False

# ВРЕМЕННО ОТКЛЮЧАЕМ АВТОМАТИЧЕСКУЮ ИНТЕГРАЦИЮ ЯЧЕЕК
CELLS_INTEGRATION_AVAILABLE = False


class LessonDisplay:
    """Отображение уроков."""

    def __init__(self, lesson_interface):
        """
        Инициализация отображения уроков.

        Args:
            lesson_interface: Экземпляр LessonInterface
        """
        self.lesson_interface = lesson_interface
        self.logger = logging.getLogger(__name__)
        self.utils = LessonUtils()

    def show_lesson(self, section_id, topic_id, lesson_id):
        """
        Отображает урок пользователю с постоянным кэшированием содержания.
        ИСПРАВЛЕНО: Добавлено постоянное кэширование в state.json для сохранения между сессиями

        Args:
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока

        Returns:
            widgets.VBox: Виджет с уроком
        """
        try:
            # Создаем ключ кэша для текущего урока
            cache_key = f"{section_id}:{topic_id}:{lesson_id}"
            
            # ИСПРАВЛЕНО: Принудительно очищаем кэш для перегенерации с исправленным промптом
            self.lesson_interface.state_manager.clear_specific_lesson_cache(cache_key)
            self.logger.info(f"Кэш урока {cache_key} очищен для перегенерации")

            # Получаем данные о курсе и уроке из учебного плана
            course_plan = self.lesson_interface.state_manager.get_course_plan()
            lesson_data = self.lesson_interface.state_manager.get_lesson_data(
                section_id, topic_id, lesson_id
            )

            # ИСПРАВЛЕНО: Проверяем завершение курса
            if lesson_id is None:
                self.logger.info("Курс завершен - показываем экран завершения")
                return self._show_course_completion()
            
            if not lesson_data:
                raise ValueError(f"Урок с ID {lesson_id} не найден в учебном плане")

            # Получаем названия элементов
            (
                course_title,
                section_title,
                topic_title,
                lesson_title,
            ) = self.utils.get_element_titles(
                course_plan, section_id, topic_id, lesson_id
            )

            # Получаем профиль пользователя для генерации урока
            user_profile = self.lesson_interface.state_manager.get_user_profile()

            # ИСПРАВЛЕНО: Сначала проверяем постоянный кэш в state.json
            cached_content = self.lesson_interface.state_manager.get_cached_lesson_content(cache_key)
            
            if cached_content:
                # Используем содержание из постоянного кэша
                self.logger.info(f"Используется постоянно кэшированное содержание урока '{lesson_title}'")
                lesson_content_data = cached_content
                
                # Обновляем кэш в памяти для текущей сессии
                self.lesson_interface.cached_lesson_content = lesson_content_data["content"]
                self.lesson_interface.cached_lesson_title = lesson_content_data["title"]
                self.lesson_interface.current_lesson_cache_key = cache_key
                
            elif (
                self.lesson_interface.current_lesson_cache_key == cache_key
                and self.lesson_interface.cached_lesson_content is not None
                and self.lesson_interface.cached_lesson_title is not None
            ):
                # Используем кэш в памяти (для текущей сессии)
                self.logger.info(f"Используется кэшированное содержание урока '{lesson_title}' из памяти")
                lesson_content_data = {
                    "title": self.lesson_interface.cached_lesson_title,
                    "content": self.lesson_interface.cached_lesson_content,
                }
            else:
                # Генерируем новое содержание урока
                try:
                    self.logger.info(f"Генерация нового содержания урока '{lesson_title}'")

                    lesson_content_data = (
                        self.lesson_interface.content_generator.generate_lesson(
                            course=course_title,
                            section=section_title,
                            topic=topic_title,
                            lesson=lesson_title,
                            user_name=user_profile["name"],
                            communication_style=user_profile["communication_style"],
                        )
                    )

                    # Кэшируем в памяти для текущей сессии
                    self.lesson_interface.cached_lesson_content = lesson_content_data["content"]
                    self.lesson_interface.cached_lesson_title = lesson_content_data["title"]
                    self.lesson_interface.current_lesson_cache_key = cache_key

                    # ИСПРАВЛЕНО: Сохраняем в постоянный кэш для повторного использования
                    self.lesson_interface.state_manager.save_lesson_content(
                        cache_key, 
                        lesson_content_data["title"], 
                        lesson_content_data["content"]
                    )

                    self.logger.info("Урок успешно сгенерирован и сохранен в постоянный кэш")

                except Exception as e:
                    self.logger.error(f"Ошибка при генерации урока: {str(e)}")
                    return self.utils.create_lesson_error_interface(
                        "Ошибка при генерации урока",
                        f"Не удалось сгенерировать содержание урока '{lesson_title}': {str(e)}",
                        self.lesson_interface,
                    )

            # Сохраняем данные для интерактивных функций
            self.lesson_interface.current_lesson_data = lesson_data
            self.lesson_interface.current_lesson_content = lesson_content_data["content"]
            self.lesson_interface.current_lesson_id = cache_key  # Полный ID урока

            # Проверяем, пройден ли тест для этого урока
            test_passed = self.lesson_interface.state_manager.is_test_passed(cache_key)
            
            self.lesson_interface.current_course_info = {
                "course_title": course_title,
                "section_title": section_title,
                "topic_title": topic_title,
                "lesson_title": lesson_title,
                "section_id": section_id,
                "topic_id": topic_id,
                "lesson_id": lesson_id,
                "user_profile": user_profile,
                "course_plan": course_plan,
                "test_passed": test_passed,  # Добавляем информацию о тесте
            }

            # Получаем ID курса безопасно
            course_id = self.utils.get_course_id(course_plan)

            # Обновляем прогресс обучения
            self.lesson_interface.state_manager.update_learning_progress(
                course=course_id, section=section_id, topic=topic_id, lesson=lesson_id
            )

            # Логируем урок
            self.lesson_interface.system_logger.log_lesson(
                course=course_title,
                section=section_title,
                topic=topic_title,
                lesson_title=lesson_content_data["title"],
                lesson_content=lesson_content_data["content"],
            )

            # Создаем интерфейс урока
            return self.create_lesson_interface(
                lesson_content_data,
                lesson_data,
                course_title,
                section_title,
                topic_title,
                lesson_title,
                section_id,
                topic_id,
                lesson_id,
                user_profile,
            )

        except Exception as e:
            self.logger.error(f"Ошибка при отображении урока: {str(e)}")

            # Логируем ошибку
            self.lesson_interface.system_logger.log_activity(
                action_type="lesson_display_error",
                status="error",
                error=str(e),
                details={
                    "section_id": section_id,
                    "topic_id": topic_id,
                    "lesson_id": lesson_id,
                },
            )

            return self.utils.create_lesson_error_interface(
                "Ошибка при отображении урока",
                f"Не удалось отобразить урок: {str(e)}",
                self.lesson_interface,
            )

    def create_lesson_interface(
        self,
        lesson_content_data,
        lesson_data,
        course_title,
        section_title,
        topic_title,
        lesson_title,
        section_id,
        topic_id,
        lesson_id,
        user_profile,
    ):
        """
        Создает интерфейс урока.

        Args:
            lesson_content_data (dict): Данные содержания урока
            lesson_data (dict): Данные урока
            course_title (str): Название курса
            section_title (str): Название раздела
            topic_title (str): Название темы
            lesson_title (str): Название урока
            section_id (str): ID раздела
            topic_id (str): ID темы
            lesson_id (str): ID урока
            user_profile (dict): Профиль пользователя

        Returns:
            widgets.VBox: Виджет с интерфейсом урока
        """
        try:
            # Создаем заголовок урока
            header_html = widgets.HTML(
                value=f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                           color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h1 style="margin: 0; font-size: 24px;">{lesson_content_data['title']}</h1>
                    <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 14px;">
                        {course_title} → {section_title} → {topic_title}
                    </p>
                </div>
                """
            )

            # ИСПРАВЛЕНО: Безопасно форматируем код в тексте урока
            try:
                from code_formatter import code_formatter
                formatted_content = code_formatter.format_code_in_text(lesson_content_data["content"])
                self.logger.info("Код в тексте урока успешно отформатирован")
            except Exception as e:
                self.logger.warning(f"Ошибка форматирования кода (не критично): {e}")
                formatted_content = lesson_content_data["content"]
            
            # ИСПРАВЛЕНО: Очищаем markdown метки кода (```html, ```python и т.д.)
            try:
                import re
                # Убираем метки ```html, ```python, ``` и подобные
                formatted_content = re.sub(r"```\w*\n?", "", formatted_content)
                formatted_content = re.sub(r"```", "", formatted_content)
                self.logger.info("Markdown метки кода успешно очищены")
            except Exception as e:
                self.logger.warning(f"Ошибка очистки markdown меток (не критично): {e}")
            
            # ИСПРАВЛЕНО: Очищаем HTML стили из текста урока
            try:
                import re
                # Убираем все <style> блоки
                formatted_content = re.sub(r'<style>.*?</style>', '', formatted_content, flags=re.DOTALL)
                # Убираем все <div class="content-container"> и </div>
                formatted_content = re.sub(r'<div class="content-container">', '', formatted_content)
                formatted_content = re.sub(r'</div>', '', formatted_content)
                # ИСПРАВЛЕНО: Убираем лишние ***
                formatted_content = re.sub(r'\*\*\*', '', formatted_content)
                self.logger.info("HTML стили и лишние *** успешно удалены из текста урока")
            except Exception as e:
                self.logger.warning(f"Ошибка очистки HTML стилей (не критично): {e}")
            
            # ИСПРАВЛЕНО: Проверяем, является ли контент уже HTML
            if formatted_content.strip().startswith('<div class="lesson-content">'):
                # Контент уже отформатирован как HTML (от ContentFormatterFinal)
                self.logger.info("Контент уже отформатирован как HTML, используем как есть")
                html_content = formatted_content
            else:
                # Контент в markdown формате, конвертируем в HTML
                try:
                    import markdown
                    
                    # ИСПРАВЛЕНО: Более умная обработка списков
                    content = formatted_content
                    
                    # Обрабатываем только настоящие нумерованные списки (начинающиеся с новой строки)
                    content = re.sub(r'(\n\s*\d+\.\s+)([^\n]+)', r'\n<li>\2</li>', content)
                    content = re.sub(r'(<li>.*?</li>)+', lambda m: '<ol>' + m.group(0) + '</ol>', content, flags=re.DOTALL)
                    
                    # Обрабатываем маркированные списки (- )
                    content = re.sub(r'(\n\s*-\s+)([^\n]+)', r'\n<li>\2</li>', content)
                    content = re.sub(r'(<li>.*?</li>)+', lambda m: '<ul>' + m.group(0) + '</ul>', content, flags=re.DOTALL)
                    
                    # Конвертируем Markdown в HTML
                    html_content = markdown.markdown(content, extensions=['fenced_code', 'codehilite'])
                    
                    # ИСПРАВЛЕНО: Добавляем CSS стили для лучшей читаемости
                    css_styles = """
                    <style>
                    .lesson-content {
                        font-family: Arial, sans-serif;
                        font-size: 18px;
                        font-weight: 500;
                        line-height: 1.6;
                        color: #1a1a1a;  /* Делаю текст темнее для лучшего контраста */
                    }
                    .lesson-content h1, .lesson-content h2, .lesson-content h3 {
                        font-weight: 700;
                        color: #000000;  /* Делаю заголовки максимально темными */
                    }
                    .lesson-content h1 { font-size: 28px; }
                    .lesson-content h2 { font-size: 24px; }
                    .lesson-content h3 { font-size: 20px; }
                    .lesson-content p { margin-bottom: 15px; }
                    .lesson-content ul, .lesson-content ol {
                        margin-bottom: 15px;
                        padding-left: 30px;
                    }
                    .lesson-content li {
                        margin-bottom: 8px;
                        line-height: 1.5;
                    }
                    .lesson-content code {
                        background-color: #f8f9fa;
                        color: #000000 !important;  /* ЧИСТО ЧЕРНЫЙ ЦВЕТ для максимального контраста */
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-weight: 900 !important;  /* Максимальная жирность */
                        font-size: 16px;
                        text-shadow: 0 0 3px rgba(0,0,0,1), 0 0 5px rgba(0,0,0,1) !important;  /* Усиленная черная тень */
                    }
                    .lesson-content pre {
                        background-color: #1a1a1a;  /* Делаю фон темнее для лучшего контраста */
                        color: #ffffff;  /* Белый текст для максимального контраста */
                        padding: 15px;
                        border-radius: 8px;
                        font-weight: 600;
                        font-size: 16px;
                        border: 2px solid #000000;  /* Черная рамка для контраста */
                    }
                    .lesson-content pre code {
                        background: none !important;
                        color: #ffffff !important;
                        padding: 0;
                        font-size: 18px;  /* Увеличиваю размер шрифта для лучшей читаемости */
                        border: none;
                        font-weight: 900 !important;  /* Максимальная жирность */
                        text-shadow: 0 0 4px rgba(0,0,0,1), 0 0 6px rgba(0,0,0,1), 0 0 8px rgba(0,0,0,1) !important;  /* Тройная черная тень для максимального контраста */
                    }
                    </style>
                    """
                    
                    # Оборачиваем контент в div с нашими стилями
                    html_content = css_styles + '<div class="lesson-content">' + html_content + '</div>'
                    
                    self.logger.info("Markdown успешно конвертирован в HTML с правильной обработкой списков")
                except Exception as e:
                    self.logger.warning(f"Ошибка конвертации Markdown (не критично): {e}")
                    # Если markdown не работает, используем простую обработку
                    html_content = formatted_content.replace('\n', '<br>')
            
            # Создаем контейнер для содержания урока
            content_html = widgets.HTML(
                value=html_content,
                layout=widgets.Layout(
                    width="100%",
                    padding="20px",
                    border="1px solid #ddd",
                    border_radius="10px",
                    margin="10px 0",
                ),
            )

            # ВРЕМЕННО ОТКЛЮЧАЕМ АВТОМАТИЧЕСКУЮ ИНТЕГРАЦИЮ ЯЧЕЕК
            # cells_container = None
            # if CELLS_INTEGRATION_AVAILABLE and cell_adapter.is_available():
            #     try:
            #         cells_container = cell_adapter.integrate_cells_into_lesson(
            #             lesson_content_data["content"],
            #             lesson_content_data["title"]
            #         )
            #         if cells_container:
            #             self.logger.info("Образовательные ячейки успешно интегрированы в урок")
            #     except Exception as e:
            #         self.logger.warning(f"Ошибка интеграции ячеек (не критично): {e}")

            # Создаем контейнеры для интерактивных функций
            self.lesson_interface.explain_container = widgets.VBox(
                layout=widgets.Layout(display="none", width="100%")
            )
            self.lesson_interface.examples_container = widgets.VBox(
                layout=widgets.Layout(display="none", width="100%")
            )
            self.lesson_interface.qa_container = widgets.VBox(
                layout=widgets.Layout(display="none", width="100%")
            )
            self.lesson_interface.control_tasks_container = widgets.VBox(
                layout=widgets.Layout(display="none", width="100%")
            )

            # Настраиваем QA контейнер
            from lesson_interaction import LessonInteraction

            interaction = LessonInteraction(self.lesson_interface)
            interaction.setup_enhanced_qa_container(self.lesson_interface.qa_container)

            # Создаем кнопки навигации
            from lesson_navigation import LessonNavigation

            # Обновляем navigation в lesson_interface, чтобы assessment_results_handler мог получить доступ к кнопкам
            self.lesson_interface.navigation = LessonNavigation(self.lesson_interface)
            navigation_buttons = (
                self.lesson_interface.navigation.create_enhanced_navigation_buttons(
                    section_id, topic_id, lesson_id
                )
            )

            # ИСПРАВЛЕНО: Добавляем индикатор статуса урока после перезапуска
            lesson_full_id = f"{section_id}:{topic_id}:{lesson_id}"
            test_passed = self.lesson_interface.state_manager.is_test_passed(lesson_full_id)
            
            if test_passed:
                # Если тест пройден, показываем статус и напоминание о контрольных заданиях
                control_task_completed = self.lesson_interface.state_manager.is_control_task_completed(lesson_full_id)
                
                if control_task_completed:
                    # Урок полностью завершен
                    status_html = widgets.HTML(
                        value=f"""
                        <div style='background-color: #d4edda; color: #155724; padding: 12px; 
                                    border-radius: 8px; margin: 10px 0; border: 1px solid #c3e6cb;'>
                            <h4 style='margin: 0 0 8px 0; font-size: 16px;'>✅ Урок завершен</h4>
                            <p style='margin: 0; font-size: 14px;'>
                                Тест пройден, контрольное задание выполнено. Урок полностью завершен!
                            </p>
                        </div>
                        """
                    )
                else:
                    # Тест пройден, но контрольное задание не выполнено
                    status_html = widgets.HTML(
                        value=f"""
                        <div style='background-color: #fff3cd; color: #856404; padding: 12px; 
                                    border-radius: 8px; margin: 10px 0; border: 1px solid #ffeaa7;'>
                            <h4 style='margin: 0 0 8px 0; font-size: 16px;'>📝 Тест пройден</h4>
                            <p style='margin: 0; font-size: 14px;'>
                                Тест успешно пройден! Теперь доступны контрольные задания. 
                                Нажмите кнопку <strong>"🛠️ Контрольные задания"</strong> ниже для завершения урока.
                            </p>
                        </div>
                        """
                    )
            else:
                # Если тест не пройден, статус не показываем
                status_html = None

            # Создаем основной контейнер урока
            lesson_children = [
                header_html,
                content_html,
                navigation_buttons,
                self.lesson_interface.explain_container,
                self.lesson_interface.examples_container,
                self.lesson_interface.qa_container,
                self.lesson_interface.control_tasks_container,
            ]

            # Добавляем индикатор статуса если он есть
            if status_html:
                lesson_children.insert(2, status_html)  # Вставляем после content_html, но перед navigation_buttons

            lesson_container = widgets.VBox(
                lesson_children, layout=widgets.Layout(width="100%", padding="20px")
            )

            return lesson_container

        except Exception as e:
            self.logger.error(f"Ошибка при создании интерфейса урока: {str(e)}")
            return self.utils.create_lesson_error_interface(
                "Ошибка при создании интерфейса",
                f"Не удалось создать интерфейс урока: {str(e)}",
                self.lesson_interface,
            )
    
    def _show_course_completion(self):
        """
        Показывает экран завершения курса.
        
        Returns:
            widgets.VBox: Виджет с экраном завершения курса
        """
        try:
            from completion_interface import CompletionInterface
            
            # Создаем интерфейс завершения курса
            completion_interface = CompletionInterface(
                self.lesson_interface.state_manager,
                self.lesson_interface.system_logger,
                self.lesson_interface.content_generator,
                self.lesson_interface.assessment
            )
            
            # Показываем экран завершения
            completion_widget = completion_interface.show_course_completion()
            
            self.logger.info("Экран завершения курса успешно отображен")
            return completion_widget
            
        except Exception as e:
            self.logger.error(f"Ошибка при отображении экрана завершения курса: {str(e)}")
            return self.utils.create_lesson_error_interface(
                "Ошибка при отображении экрана завершения курса",
                f"Не удалось отобразить экран завершения курса: {str(e)}",
                self.lesson_interface,
            )


