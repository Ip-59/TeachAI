"""
Фасад интерфейса TeachAI.
Обеспечивает единую точку доступа к различным интерфейсам системы.

ИСПРАВЛЕНО ЭТАП 49: КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ - правильная передача данных урока в тестирование
"""

import logging
from interface_utils import InterfaceState
import ipywidgets as widgets


class InterfaceFacade:
    """
    Фасад для всех интерфейсов системы TeachAI.
    Предоставляет единую точку доступа ко всем интерфейсным компонентам.
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

        self.current_state = InterfaceState.INITIAL_SETUP

        # Инициализируем специализированные интерфейсы
        self._initialize_interfaces()

        self.logger.info("InterfaceFacade инициализирован")

    def _initialize_interfaces(self):
        """Инициализирует все специализированные интерфейсы."""
        try:
            # Импортируем интерфейсы здесь чтобы избежать циклических импортов
            from lesson_interface import LessonInterface
            from assessment_interface import AssessmentInterface

            # Инициализируем lesson_interface с ссылкой на фасад
            self.lesson_interface = LessonInterface(
                self.state_manager,
                self.content_generator,
                self.system_logger,
                self.assessment,
                parent_facade=self,  # Передаем ссылку на фасад
            )

            # Инициализируем assessment_interface
            self.assessment_interface = AssessmentInterface(
                self.state_manager,
                self.content_generator,
                self.assessment,
                self.system_logger,
            )

            self.logger.info("Все специализированные интерфейсы инициализированы")

        except Exception as e:
            self.logger.error(f"Ошибка инициализации интерфейсов: {str(e)}")
            # Создаем заглушки если интерфейсы не найдены
            self.lesson_interface = None
            self.assessment_interface = None

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

            if not self.lesson_interface:
                return self._create_error_interface(
                    "Ошибка", "Интерфейс уроков недоступен"
                )

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
                    # Сокращенный формат - получаем полную информацию из state_manager
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

            # Отображение урока через lesson_interface
            result = self.lesson_interface.show_lesson(
                section_id, topic_id, lesson_id_current
            )
            self.current_state = InterfaceState.LESSON_VIEW
            return result

        except Exception as e:
            self.logger.error(f"Ошибка отображения урока {lesson_id}: {str(e)}")
            return self._create_error_interface("Ошибка загрузки урока", str(e))

    def show_assessment(self, lesson_id=None):
        """
        ИСПРАВЛЕНО ЭТАП 49: Правильная передача данных урока в тестирование.

        Args:
            lesson_id (str): Идентификатор урока

        Returns:
            widgets.VBox: Интерфейс тестирования
        """
        try:
            self.logger.info(
                f"🚀 НАЧАЛО: Отображение тестирования для урока: {lesson_id}"
            )

            # ИСПРАВЛЕНО: Проверяем доступность lesson_interface
            if not self.lesson_interface:
                error_msg = "LessonInterface недоступен для получения данных урока"
                self.logger.error(error_msg)
                return self._create_error_interface("Ошибка инициализации", error_msg)

            # ИСПРАВЛЕНО: Получаем данные урока напрямую из lesson_interface
            self.logger.info("📊 Получение данных урока для тестирования...")

            current_lesson_content = getattr(
                self.lesson_interface, "current_lesson_content", None
            )
            current_course_info = getattr(
                self.lesson_interface, "current_course_info", None
            )
            current_lesson_id = getattr(
                self.lesson_interface, "current_lesson_id", None
            )

            # Детальное логирование состояния данных
            self.logger.info(
                f"📊 current_lesson_content: {type(current_lesson_content)} ({'Есть' if current_lesson_content else 'None'})"
            )
            self.logger.info(
                f"📊 current_course_info: {type(current_course_info)} ({'Есть' if current_course_info else 'None'})"
            )
            self.logger.info(f"📊 current_lesson_id: {current_lesson_id}")

            # ИСПРАВЛЕНО: Проверяем наличие данных урока
            if not current_lesson_content and not current_course_info:
                error_details = self._diagnose_assessment_data_issue(
                    current_lesson_content, current_course_info, current_lesson_id
                )
                self.logger.error(
                    f"❌ Данные урока недоступны для тестирования: {error_details}"
                )
                return self._create_error_interface(
                    "Ошибка данных урока", error_details
                )

            # ИСПРАВЛЕНО: Безопасно извлекаем данные для тестирования
            course_info = current_course_info or {}

            # Формируем параметры для тестирования
            assessment_params = {
                "current_course": course_info.get("course_title", "Текущий курс"),
                "current_section": course_info.get("section_title", "Текущая секция"),
                "current_topic": course_info.get("topic_title", "Текущая тема"),
                "current_lesson": course_info.get("lesson_title", "Текущий урок"),
                "current_lesson_content": current_lesson_content,
            }

            self.logger.info(
                f"📊 Параметры для тестирования: {list(assessment_params.keys())}"
            )

            # ИСПРАВЛЕНО: Проверяем доступность assessment_interface
            if not self.assessment_interface:
                # Создаем простой интерфейс тестирования если assessment_interface недоступен
                return self._create_simple_assessment_interface(
                    assessment_params, current_lesson_id
                )

            # Вызываем тестирование через assessment_interface
            result = self.assessment_interface.show_assessment(**assessment_params)

            if result:
                self.current_state = InterfaceState.ASSESSMENT
                self.logger.info("✅ Тестирование успешно запущено")
                return result
            else:
                error_msg = "assessment_interface.show_assessment() вернул None"
                self.logger.error(error_msg)
                return self._create_error_interface("Ошибка тестирования", error_msg)

        except Exception as e:
            error_msg = f"Критическая ошибка при запуске тестирования: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(f"📋 Traceback: {__import__('traceback').format_exc()}")
            return self._create_error_interface(
                "Критическая ошибка тестирования", error_msg
            )

    def _diagnose_assessment_data_issue(
        self, current_lesson_content, current_course_info, current_lesson_id
    ):
        """
        Диагностирует проблемы с данными для тестирования.

        Returns:
            str: Детальная диагностика проблем
        """
        diagnosis = []
        diagnosis.append("ПРОБЛЕМЫ С ДАННЫМИ ДЛЯ ТЕСТИРОВАНИЯ:")

        # Проверяем содержание урока
        if current_lesson_content is None:
            diagnosis.append(
                "• current_lesson_content = None (содержание урока не передано)"
            )
        elif not current_lesson_content:
            diagnosis.append(
                "• current_lesson_content пуст (содержание урока отсутствует)"
            )
        else:
            content_size = len(str(current_lesson_content))
            diagnosis.append(
                f"• current_lesson_content доступен ({content_size} символов)"
            )

        # Проверяем информацию о курсе
        if current_course_info is None:
            diagnosis.append(
                "• current_course_info = None (информация о курсе не передана)"
            )
        elif not current_course_info:
            diagnosis.append(
                "• current_course_info пуст (информация о курсе отсутствует)"
            )
        else:
            info_keys = (
                list(current_course_info.keys())
                if isinstance(current_course_info, dict)
                else []
            )
            diagnosis.append(
                f"• current_course_info доступен ({len(info_keys)} ключей: {info_keys})"
            )

        # Проверяем ID урока
        if current_lesson_id is None:
            diagnosis.append("• current_lesson_id = None (ID урока не передан)")
        elif not current_lesson_id:
            diagnosis.append("• current_lesson_id пуст (ID урока отсутствует)")
        else:
            diagnosis.append(f"• current_lesson_id доступен: {current_lesson_id}")

        diagnosis.append("")
        diagnosis.append("ВОЗМОЖНЫЕ ПРИЧИНЫ:")
        diagnosis.append(
            "• Урок не сгенерировался из-за ошибки API (проверьте логи урока)"
        )
        diagnosis.append(
            "• Ошибка в lesson_interface._store_lesson_data() (данные не сохранились)"
        )
        diagnosis.append("• Проблема с передачей данных между модулями")
        diagnosis.append("• Ошибка в content_generator (проверьте API ключ OpenAI)")
        diagnosis.append("• Сбой инициализации системы (проверьте engine.py)")

        return "\\n".join(diagnosis)

    def _create_simple_assessment_interface(self, assessment_params, lesson_id):
        """
        Создает простой интерфейс тестирования когда assessment_interface недоступен.

        Args:
            assessment_params (dict): Параметры для тестирования
            lesson_id (str): ID урока

        Returns:
            widgets.VBox: Простой интерфейс тестирования
        """
        self.logger.info("Создание простого интерфейса тестирования")

        # Проверяем доступность содержания урока
        lesson_content = assessment_params.get("current_lesson_content")
        if not lesson_content:
            return self._create_error_interface(
                "Тестирование недоступно",
                "Содержание урока недоступно для генерации вопросов.\\n\\n"
                + "Проверьте что урок корректно загрузился перед запуском тестирования.",
            )

        # Проверяем доступность assessment модуля
        if not self.assessment:
            return self._create_error_interface(
                "Модуль оценивания недоступен",
                "Assessment модуль не инициализирован.\\n\\n"
                + "Проверьте конфигурацию системы и повторите попытку.",
            )

        # Пытаемся создать простое тестирование
        try:
            # Создаем заголовок
            header = widgets.HTML(
                value=f"""
                <div style="background: linear-gradient(135deg, #6366f1, #8b5cf6);
                           padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="color: white; margin: 0; text-align: center;">
                        📝 Тестирование по уроку
                    </h2>
                    <p style="color: #e5e7eb; margin: 10px 0 0 0; text-align: center;">
                        {assessment_params.get('current_lesson', 'Текущий урок')}
                    </p>
                </div>
            """
            )

            # Информация о проблеме
            info = widgets.HTML(
                value=f"""
                <div style="background: #fef3c7; border: 1px solid #f59e0b;
                           padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <h3 style="color: #92400e; margin: 0 0 10px 0;">⚠️ Ограниченный режим тестирования</h3>
                    <p style="color: #92400e; margin: 0;">
                        Assessment интерфейс недоступен, но основные данные урока присутствуют:<br>
                        • Курс: {assessment_params.get('current_course', 'Не указан')}<br>
                        • Раздел: {assessment_params.get('current_section', 'Не указан')}<br>
                        • Тема: {assessment_params.get('current_topic', 'Не указана')}<br>
                        • Урок: {assessment_params.get('current_lesson', 'Не указан')}<br>
                        • Содержание: {'Доступно' if lesson_content else 'Недоступно'}
                    </p>
                </div>
            """
            )

            # Кнопка для попытки запуска полного тестирования
            retry_button = widgets.Button(
                description="🔄 Попробовать снова",
                button_style="info",
                layout=widgets.Layout(width="200px"),
            )

            def on_retry_click(b):
                # Очищаем вывод и пытаемся снова
                from IPython.display import clear_output, display

                clear_output(wait=True)
                display(self.show_assessment(lesson_id))

            retry_button.on_click(on_retry_click)

            return widgets.VBox([header, info, retry_button])

        except Exception as e:
            return self._create_error_interface(
                "Ошибка создания тестирования",
                f"Не удалось создать интерфейс тестирования: {str(e)}",
            )

    def _create_error_interface(self, title, message):
        """
        Создает интерфейс с сообщением об ошибке.

        Args:
            title (str): Заголовок ошибки
            message (str): Сообщение об ошибке

        Returns:
            widgets.VBox: Интерфейс с ошибкой
        """
        return widgets.VBox(
            [
                widgets.HTML(
                    f"""
                <div style="padding: 20px; background: #fee; border: 1px solid #fcc; border-radius: 8px;">
                    <h3 style="color: #c33; margin: 0 0 10px 0;">{title}</h3>
                    <p style="margin: 0; color: #666; white-space: pre-line;">{message}</p>
                </div>
            """
                )
            ]
        )

    def get_current_state(self):
        """Возвращает текущее состояние интерфейса."""
        return self.current_state

    def get_status(self):
        """
        Возвращает полный статус фасада.

        Returns:
            dict: Полный статус фасада
        """
        try:
            return {
                "facade_initialized": True,
                "current_state": self.current_state.value
                if self.current_state
                else None,
                "lesson_interface_available": self.lesson_interface is not None,
                "assessment_interface_available": self.assessment_interface is not None,
                "lesson_data_available": hasattr(
                    self.lesson_interface, "current_lesson_data"
                )
                and self.lesson_interface.current_lesson_data is not None
                if self.lesson_interface
                else False,
                "version": "2.0",
                "last_critical_fix": "ЭТАП 49: Исправлена передача данных урока в тестирование",
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса фасада: {str(e)}")
            return {"error": str(e), "facade_initialized": False}
