"""
Модуль запуска и управления циклом выполнения TeachAI.
Отвечает за основную логику работы системы и переходы между состояниями.
"""

import logging
from interface_utils import InterfaceState


class TeachAIEngineRunner:
    """Управляет основным циклом выполнения системы TeachAI."""

    def __init__(self, core):
        """
        Инициализация модуля запуска.

        Args:
            core: Экземпляр TeachAIEngineCore
        """
        self.core = core
        self.logger = logging.getLogger(__name__)

        # Флаги управления выполнением
        self.is_running = False
        self.should_continue = True

        self.logger.info("TeachAIEngineRunner инициализирован")

    def determine_initial_flow(self):
        """
        Определяет начальный поток выполнения на основе состояния пользователя.

        Returns:
            str: Тип начального потока ('first_run', 'continue_learning', 'main_menu')
        """
        try:
            if not self.core.state_manager:
                self.logger.error("StateManager не инициализирован")
                return "first_run"

            # Проверяем, является ли это первым запуском
            if self.core.state_manager.is_first_run():
                self.logger.info("Определен первый запуск системы")
                return "first_run"

            # Проверяем наличие незавершенных уроков
            try:
                next_lesson = self.core.state_manager.get_next_lesson()
                if next_lesson:
                    self.logger.info("Найден незавершенный урок, переход к обучению")
                    return "continue_learning"
                else:
                    self.logger.info("Все уроки завершены, переход к главному меню")
                    return "main_menu"
            except Exception as e:
                self.logger.warning(f"Ошибка проверки уроков: {str(e)}")
                return "main_menu"

        except Exception as e:
            self.logger.error(f"Ошибка определения начального потока: {str(e)}")
            return "first_run"

    def run_first_time_setup(self):
        """
        Выполняет настройку для первого запуска.

        Returns:
            bool: True если настройка прошла успешно
        """
        try:
            self.logger.info("🚀 Запуск настройки для первого пользователя")

            # Отображаем интерфейс первоначальной настройки
            self.core.interface.show_initial_setup()

            # После настройки снимаем флаг первого запуска
            self.core.state_manager.set_not_first_run()

            self.logger.info("Настройка первого запуска завершена")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка настройки первого запуска: {str(e)}")
            return False

    def run_continue_learning(self):
        """
        Продолжает обучение с незавершенного урока.

        Returns:
            bool: True если продолжение прошло успешно
        """
        try:
            self.logger.info("📚 Продолжение изучения курса")

            # Получаем следующий урок
            next_lesson = self.core.state_manager.get_next_lesson()
            if next_lesson:
                lesson_id = next_lesson.get("id")
                self.logger.info(f"Переход к уроку: {lesson_id}")

                # Отображаем урок
                self.core.interface.show_lesson(lesson_id)
                return True
            else:
                self.logger.info("Нет незавершенных уроков, переход к главному меню")
                return self.run_main_menu()

        except Exception as e:
            self.logger.error(f"Ошибка продолжения обучения: {str(e)}")
            return False

    def run_main_menu(self):
        """
        Отображает главное меню системы.

        Returns:
            bool: True если отображение прошло успешно
        """
        try:
            self.logger.info("🏠 Отображение главного меню")

            # Проверяем доступность главного меню
            if hasattr(self.core.interface, "show_main_menu"):
                self.core.interface.show_main_menu()
            else:
                # Fallback к интерфейсу урока
                self.logger.warning("Главное меню недоступно, fallback к уроку")
                self.core.interface.show_lesson()

            return True

        except Exception as e:
            self.logger.error(f"Ошибка отображения главного меню: {str(e)}")
            return False

    def handle_course_completion(self):
        """
        Обрабатывает завершение курса.

        Returns:
            bool: True если обработка прошла успешно
        """
        try:
            self.logger.info("🎉 Обработка завершения курса")

            # Отображаем интерфейс завершения
            self.core.interface.show_completion()

            # Логируем статистику
            if hasattr(self.core.state_manager, "get_course_statistics"):
                stats = self.core.state_manager.get_course_statistics()
                self.logger.info(f"Статистика курса: {stats}")

            return True

        except Exception as e:
            self.logger.error(f"Ошибка обработки завершения курса: {str(e)}")
            return False

    def run_interactive_session(self):
        """
        Запускает интерактивную сессию обучения.

        Returns:
            bool: True если сессия прошла успешно
        """
        try:
            self.logger.info("🎓 Запуск интерактивной сессии обучения")
            self.is_running = True

            # Определяем начальный поток
            initial_flow = self.determine_initial_flow()
            self.logger.info(f"Начальный поток: {initial_flow}")

            # Выполняем соответствующий поток
            if initial_flow == "first_run":
                success = self.run_first_time_setup()
            elif initial_flow == "continue_learning":
                success = self.run_continue_learning()
            elif initial_flow == "main_menu":
                success = self.run_main_menu()
            else:
                self.logger.error(f"Неизвестный начальный поток: {initial_flow}")
                success = False

            if success:
                self.logger.info("Интерактивная сессия завершена успешно")
            else:
                self.logger.error("Интерактивная сессия завершена с ошибками")

            self.is_running = False
            return success

        except Exception as e:
            self.logger.error(f"Ошибка интерактивной сессии: {str(e)}")
            self.is_running = False
            return False

    def run_demo_mode(self):
        """
        Запускает демонстрационный режим (без API).

        Returns:
            bool: True если демо режим прошел успешно
        """
        try:
            self.logger.info("🎭 Запуск демонстрационного режима")

            print("\n" + "=" * 50)
            print("🎭 ДЕМОНСТРАЦИОННЫЙ РЕЖИМ TeachAI")
            print("=" * 50)
            print("📝 API ключ не настроен или недоступен")
            print("🎯 Система работает с демонстрационным контентом")
            print("⚙️  Для полной функциональности настройте API ключ в .env файле")
            print("=" * 50 + "\n")

            # В демо режиме показываем базовый интерфейс
            self.core.interface.show_initial_setup()

            return True

        except Exception as e:
            self.logger.error(f"Ошибка демонстрационного режима: {str(e)}")
            return False

    def run_diagnostics_mode(self):
        """
        Запускает режим диагностики системы.

        Returns:
            dict: Результаты диагностики
        """
        try:
            self.logger.info("🔍 Запуск режима диагностики")

            diagnostics = {
                "timestamp": self.get_current_timestamp(),
                "system_status": {},
                "component_tests": {},
            }

            # Проверка компонентов
            diagnostics["system_status"] = self.core.get_initialization_status()

            # Валидация компонентов
            validation = self.core.validate_components()
            diagnostics["component_tests"]["validation"] = validation

            # Тест состояния
            if self.core.state_manager:
                try:
                    state_integrity = self.core.state_manager.validate_state_integrity()
                    diagnostics["component_tests"]["state_integrity"] = state_integrity
                except Exception as e:
                    diagnostics["component_tests"]["state_integrity"] = {
                        "error": str(e)
                    }

            # Тест конфигурации
            if self.core.config_manager:
                try:
                    config_status = {
                        "api_key_present": bool(self.core.config_manager.get_api_key()),
                        "model_name": self.core.config_manager.get_model_name(),
                        "debug_mode": self.core.config_manager.is_debug_mode(),
                    }
                    diagnostics["component_tests"]["configuration"] = config_status
                except Exception as e:
                    diagnostics["component_tests"]["configuration"] = {"error": str(e)}

            # Общая оценка
            all_components_ok = diagnostics["system_status"].get("is_ready", False)
            validation_ok = validation.get("valid", False)

            diagnostics["overall_status"] = {
                "healthy": all_components_ok and validation_ok,
                "ready_for_use": all_components_ok,
                "issues_count": len(validation.get("issues", [])),
                "warnings_count": len(validation.get("warnings", [])),
            }

            return diagnostics

        except Exception as e:
            self.logger.error(f"Ошибка режима диагностики: {str(e)}")
            return {"error": str(e)}

    def get_current_timestamp(self):
        """
        Возвращает текущую временную метку.

        Returns:
            str: Временная метка в ISO формате
        """
        try:
            from datetime import datetime

            return datetime.now().isoformat()
        except Exception:
            return "unknown"

    def stop_execution(self):
        """Останавливает выполнение системы."""
        try:
            self.logger.info("Получен сигнал остановки выполнения")
            self.should_continue = False
            self.is_running = False
        except Exception as e:
            self.logger.error(f"Ошибка остановки выполнения: {str(e)}")

    def get_execution_status(self):
        """
        Возвращает статус выполнения.

        Returns:
            dict: Статус выполнения
        """
        return {
            "is_running": self.is_running,
            "should_continue": self.should_continue,
            "core_ready": self.core.is_ready if self.core else False,
            "runner_initialized": True,
        }

    def handle_error(self, error, context="unknown"):
        """
        Обрабатывает ошибки выполнения.

        Args:
            error: Объект ошибки
            context (str): Контекст возникновения ошибки

        Returns:
            dict: Информация об обработке ошибки
        """
        try:
            error_info = {
                "context": context,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "timestamp": self.get_current_timestamp(),
                "handled": True,
            }

            self.logger.error(f"Обработка ошибки в контексте '{context}': {str(error)}")

            # Определяем стратегию восстановления
            if "initialization" in context.lower():
                error_info["recovery_strategy"] = "restart_initialization"
            elif "interface" in context.lower():
                error_info["recovery_strategy"] = "fallback_interface"
            elif "state" in context.lower():
                error_info["recovery_strategy"] = "reset_state"
            else:
                error_info["recovery_strategy"] = "graceful_degradation"

            return error_info

        except Exception as e:
            self.logger.critical(f"Критическая ошибка в обработчике ошибок: {str(e)}")
            return {
                "context": context,
                "error_message": str(error),
                "handler_error": str(e),
                "handled": False,
            }

    def cleanup_session(self):
        """Очищает ресурсы сессии."""
        try:
            self.logger.info("Очистка ресурсов сессии...")

            self.is_running = False
            self.should_continue = True  # Сброс для следующего запуска

            # Очистка ресурсов ядра
            if self.core:
                self.core.cleanup()

            self.logger.info("Очистка сессии завершена")

        except Exception as e:
            self.logger.error(f"Ошибка очистки сессии: {str(e)}")

    def __str__(self):
        """Строковое представление TeachAIEngineRunner."""
        return f"TeachAIEngineRunner(running={self.is_running}, core_ready={self.core.is_ready if self.core else False})"

    def __repr__(self):
        """Представление TeachAIEngineRunner для отладки."""
        return (
            f"TeachAIEngineRunner(core={bool(self.core)}, is_running={self.is_running})"
        )
