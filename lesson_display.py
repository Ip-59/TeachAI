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
            from system_clock import mark_stage

            mark_stage("урок")
            # Создаем ключ кэша для текущего урока
            cache_key = f"{section_id}:{topic_id}:{lesson_id}"

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
                self.lesson_interface.cached_lesson_raw_content = lesson_content_data.get(
                    "raw_content"
                )
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
                if self.lesson_interface.cached_lesson_raw_content:
                    lesson_content_data["raw_content"] = (
                        self.lesson_interface.cached_lesson_raw_content
                    )
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
                    self.lesson_interface.cached_lesson_raw_content = lesson_content_data.get(
                        "raw_content"
                    )
                    self.lesson_interface.current_lesson_cache_key = cache_key

                    # ИСПРАВЛЕНО: Сохраняем в постоянный кэш для повторного использования
                    self.lesson_interface.state_manager.save_lesson_content(
                        cache_key, 
                        lesson_content_data["title"], 
                        lesson_content_data["content"],
                        raw_content=lesson_content_data.get("raw_content"),
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
            self.lesson_interface.current_lesson_raw_content = lesson_content_data.get(
                "raw_content"
            )
            self.lesson_interface.current_lesson_id = cache_key  # Полный ID урока
            # Сбрасываем in-memory кэши интерактивных разделов — они только для этого урока
            self.lesson_interface.current_lesson_concepts = None
            self._ensure_lesson_concepts(
                cache_key,
                lesson_content_data.get("raw_content") or lesson_content_data.get("content") or "",
                lesson_data,
                user_profile.get("communication_style", "friendly"),
            )
            self.lesson_interface.current_lesson_examples = None
            self.lesson_interface.current_lesson_examples_key = None
            self._reset_interactive_containers()

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
                "lesson_content": lesson_content_data["content"],
                "lesson_raw_content": lesson_content_data.get("raw_content"),
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

            lesson_body = lesson_content_data.get("content") or ""
            raw_body = lesson_content_data.get("raw_content")

            from content_formatter_final import content_has_unresolved_code_placeholders
            from student_content import render_student_content

            source = lesson_body
            if content_has_unresolved_code_placeholders(lesson_body) and raw_body:
                self.logger.warning(
                    "В уроке заглушки CODE_BLOCK — рендер из raw_content"
                )
                source = raw_body

            html_with_styles = render_student_content(source)
            
            content_html = widgets.HTML(
                value=html_with_styles,
                layout=widgets.Layout(
                    width="100%",
                    padding="20px",
                    border="1px solid #ddd",
                    border_radius="8px",
                    margin="10px 0",
                    background_color="#ffffff",
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
            self.lesson_interface.test_container = widgets.VBox(
                layout=widgets.Layout(display="none", width="100%")
            )

            # Логируем создание контейнеров
            self.logger.info("Контейнеры созданы:")
            self.logger.info(f"  - explain_container: {self.lesson_interface.explain_container}")
            self.logger.info(f"  - examples_container: {self.lesson_interface.examples_container}")
            self.logger.info(f"  - qa_container: {self.lesson_interface.qa_container}")
            self.logger.info(f"  - control_tasks_container: {self.lesson_interface.control_tasks_container}")

            # Настраиваем QA контейнер
            from lesson_interaction import LessonInteraction

            interaction = LessonInteraction(self.lesson_interface)
            interaction.setup_enhanced_qa_container(self.lesson_interface.qa_container)
            self.logger.info("QA контейнер настроен")

            # Создаем кнопки навигации
            from lesson_navigation import LessonNavigation

            # Обновляем navigation в lesson_interface, чтобы assessment_results_handler мог получить доступ к кнопкам
            self.lesson_interface.navigation = LessonNavigation(self.lesson_interface)
            navigation_buttons = (
                self.lesson_interface.navigation.create_enhanced_navigation_buttons(
                    section_id, topic_id, lesson_id
                )
            )
            from lesson_outline import build_outline_widget

            outline_widget = build_outline_widget(
                self.lesson_interface, section_id, topic_id, lesson_id
            )

            # ИСПРАВЛЕНО: Добавляем индикатор статуса урока после перезапуска
            lesson_full_id = f"{section_id}:{topic_id}:{lesson_id}"
            sm = self.lesson_interface.state_manager
            test_passed = sm.is_test_passed(lesson_full_id)
            test_bypassed = sm.is_test_bypassed(lesson_full_id)

            if test_passed or test_bypassed:
                # Если тест пройден, показываем статус и напоминание о контрольных заданиях
                control_task_completed = self.lesson_interface.state_manager.is_control_task_completed(lesson_full_id)
                
                if control_task_completed:
                    gate_text = (
                        "Тест пройден"
                        if test_passed
                        else "Переход к практике без теста подтверждён"
                    )
                    status_html = widgets.HTML(
                        value=f"""
                        <div style='background-color: #d4edda; color: #155724; padding: 12px; 
                                    border-radius: 8px; margin: 10px 0; border: 1px solid #c3e6cb;'>
                            <h4 style='margin: 0 0 8px 0; font-size: 16px;'>✅ Урок завершен</h4>
                            <p style='margin: 0; font-size: 14px;'>
                                {gate_text}, контрольное задание выполнено. Урок полностью завершен!
                            </p>
                        </div>
                        """
                    )
                elif test_passed:
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
                    status_html = widgets.HTML(
                        value="""
                        <div style='background-color: #e2e3e5; color: #383d41; padding: 12px; 
                                    border-radius: 8px; margin: 10px 0; border: 1px solid #d6d8db;'>
                            <h4 style='margin: 0 0 8px 0; font-size: 16px;'>🛠️ Практика без теста</h4>
                            <p style='margin: 0; font-size: 14px;'>
                                Вход в контрольное задание без прохождения теста подтверждён.
                                Оценка теста не ставится.
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
                outline_widget,
                content_html,
                navigation_buttons,
                self.lesson_interface.explain_container,
                self.lesson_interface.examples_container,
                self.lesson_interface.qa_container,
                self.lesson_interface.test_container,
                self.lesson_interface.control_tasks_container,
            ]

            # Добавляем индикатор статуса если он есть
            if status_html:
                lesson_children.insert(3, status_html)

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
    
    def _ensure_lesson_concepts(
        self,
        cache_key: str,
        lesson_content: str,
        lesson_data: dict,
        communication_style: str,
    ) -> None:
        """Составляет понятия вместе с уроком и кладёт их в кэш."""
        from student_knowledge import ensure_lesson_concepts

        info = self.lesson_interface.current_course_info or {}
        concepts = ensure_lesson_concepts(
            self.lesson_interface.state_manager,
            self.lesson_interface.content_generator,
            cache_key,
            lesson_content,
            lesson_data,
            communication_style,
            info,
        )
        self.lesson_interface.current_lesson_concepts = concepts or None

    def _reset_interactive_containers(self):
        """Скрывает и очищает контейнеры примеров/QA/объяснений при смене урока."""
        li = self.lesson_interface
        for name in (
            "examples_container",
            "qa_container",
            "explain_container",
            "control_tasks_container",
            "test_container",
        ):
            container = getattr(li, name, None)
            if container is not None:
                container.layout.display = "none"
                container.children = []

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


