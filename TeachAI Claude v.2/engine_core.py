"""
Ядро основного модуля системы TeachAI.
Отвечает за инициализацию компонентов и базовую настройку системы.
"""

import os
import logging
from pathlib import Path

# Импортируем компоненты системы
from config import ConfigManager
from state_manager import StateManager
from content_generator import ContentGenerator
from assessment import Assessment
from logger import Logger
from interface import UserInterface, InterfaceState


class TeachAIEngineCore:
    """Ядро системы TeachAI - инициализация и настройка компонентов."""

    def __init__(self):
        """Инициализация ядра системы TeachAI."""
        # Настраиваем базовый логгер
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Инициализация TeachAI Core...")

        # Инициализируем компоненты
        self.config_manager = None
        self.state_manager = None
        self.system_logger = None
        self.content_generator = None
        self.assessment = None
        self.interface = None

        # Флаг готовности системы
        self.is_ready = False

    def _setup_logging(self):
        """Настраивает базовый логгер для системы."""
        # Создаем директорию для логов, если она не существует
        Path("logs").mkdir(exist_ok=True)

        # Настраиваем формат логов
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                # Явно указываем кодировку UTF-8 для файлового логгера
                logging.FileHandler("logs/teachai.log", mode="a", encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )

    def initialize_config(self):
        """
        Инициализирует конфигурационный менеджер.

        Returns:
            bool: True если инициализация прошла успешно
        """
        try:
            self.logger.info("Создание ConfigManager...")
            self.config_manager = ConfigManager()

            # Создаем необходимые директории
            self.logger.info("Создание директорий...")
            self.config_manager.ensure_directories()

            return True

        except Exception as e:
            self.logger.error(f"Ошибка инициализации конфигурации: {str(e)}")
            return False

    def check_environment(self):
        """
        Проверяет окружение и конфигурацию.

        Returns:
            dict: Результат проверки с деталями
        """
        try:
            self.logger.info("Проверка окружения...")

            # Проверяем существование .env файла
            env_file_exists = self.config_manager.check_env_file()

            # Загружаем конфигурацию
            config_loaded = self.config_manager.load_config()

            # Проверяем API ключ
            api_key = self.config_manager.get_api_key()
            api_key_present = api_key is not None
            api_key_format_valid = False

            if api_key_present:
                api_key_format_valid = self.config_manager.validate_api_key_format(
                    api_key
                )

            # Формируем результат
            result = {
                "success": env_file_exists
                and config_loaded
                and api_key_present
                and api_key_format_valid,
                "env_file_exists": env_file_exists,
                "config_loaded": config_loaded,
                "api_key_present": api_key_present,
                "api_key_format_valid": api_key_format_valid,
            }

            if result["success"]:
                self.logger.info("Проверка окружения прошла успешно")
            else:
                self.logger.warning("Проверка окружения выявила проблемы")

            return result

        except Exception as e:
            self.logger.error(f"Ошибка проверки окружения: {str(e)}")
            return {"success": False, "error": str(e)}

    def initialize_state_manager(self):
        """
        Инициализирует менеджер состояния.

        Returns:
            bool: True если инициализация прошла успешно
        """
        try:
            self.logger.info("Создание StateManager...")
            self.state_manager = StateManager()
            return True
        except Exception as e:
            self.logger.error(f"Ошибка инициализации StateManager: {str(e)}")
            return False

    def initialize_system_logger(self):
        """
        Инициализирует системный логгер.

        Returns:
            bool: True если инициализация прошла успешно
        """
        try:
            self.logger.info("Создание системного логгера...")
            self.system_logger = Logger()
            return True
        except Exception as e:
            self.logger.error(f"Ошибка инициализации системного логгера: {str(e)}")
            return False

    def initialize_content_generator(self):
        """
        Инициализирует генератор контента.

        Returns:
            bool: True если инициализация прошла успешно
        """
        try:
            self.logger.info("Создание ContentGenerator...")
            api_key = self.config_manager.get_api_key()
            self.content_generator = ContentGenerator(api_key)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка инициализации ContentGenerator: {str(e)}")
            return False

    def initialize_assessment(self):
        """
        Инициализирует модуль оценивания.

        Returns:
            bool: True если инициализация прошла успешно
        """
        try:
            self.logger.info("Создание Assessment...")
            # ИСПРАВЛЕНО ЭТАП 36: Правильные параметры для Assessment (проблема #145)
            self.assessment = Assessment(self.content_generator, self.system_logger)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка инициализации Assessment: {str(e)}")
            return False

    def initialize_interface(self):
        """
        Инициализирует пользовательский интерфейс.

        Returns:
            bool: True если инициализация прошла успешно
        """
        try:
            self.logger.info("Создание UserInterface...")
            self.interface = UserInterface(
                self.state_manager,
                self.content_generator,
                self.assessment,
                self.system_logger,
            )
            return True
        except Exception as e:
            self.logger.error(f"Ошибка инициализации UserInterface: {str(e)}")
            return False

    def initialize(self):
        """
        Выполняет полную инициализацию всех компонентов системы.

        Returns:
            dict: Результат инициализации
        """
        try:
            self.logger.info("Начало полной инициализации системы...")

            initialization_steps = [
                ("config", self.initialize_config),
                ("environment", lambda: self.check_environment().get("success", False)),
                ("state_manager", self.initialize_state_manager),
                ("system_logger", self.initialize_system_logger),
                ("content_generator", self.initialize_content_generator),
                ("assessment", self.initialize_assessment),
                ("interface", self.initialize_interface),
            ]

            results = {}

            for step_name, step_func in initialization_steps:
                self.logger.info(f"Выполнение шага: {step_name}")
                try:
                    result = step_func()
                    results[step_name] = result

                    if not result:
                        self.logger.error(f"Шаг {step_name} завершился неудачно")
                        results["failed_step"] = step_name
                        results["success"] = False
                        return results

                except Exception as e:
                    self.logger.error(f"Ошибка на шаге {step_name}: {str(e)}")
                    results[step_name] = False
                    results["failed_step"] = step_name
                    results["error"] = str(e)
                    results["success"] = False
                    return results

            # Если все шаги прошли успешно
            self.is_ready = True
            results["success"] = True
            results["all_components_initialized"] = True

            self.logger.info("Полная инициализация системы завершена успешно")
            return results

        except Exception as e:
            self.logger.error(f"Критическая ошибка инициализации: {str(e)}")
            return {"success": False, "error": str(e), "critical_failure": True}

    def get_initialization_status(self):
        """
        Возвращает статус инициализации всех компонентов.

        Returns:
            dict: Статус инициализации
        """
        return {
            "is_ready": self.is_ready,
            "config_manager": self.config_manager is not None,
            "state_manager": self.state_manager is not None,
            "system_logger": self.system_logger is not None,
            "content_generator": self.content_generator is not None,
            "assessment": self.assessment is not None,
            "interface": self.interface is not None,
            "components_count": sum(
                [
                    self.config_manager is not None,
                    self.state_manager is not None,
                    self.system_logger is not None,
                    self.content_generator is not None,
                    self.assessment is not None,
                    self.interface is not None,
                ]
            ),
        }

    def cleanup(self):
        """Очищает ресурсы системы."""
        try:
            self.logger.info("Очистка ресурсов системы...")

            # Очищаем компоненты в обратном порядке инициализации
            if self.interface:
                self.interface = None
            if self.assessment:
                self.assessment = None
            if self.content_generator:
                self.content_generator = None
            if self.system_logger:
                self.system_logger = None
            if self.state_manager:
                self.state_manager = None
            if self.config_manager:
                self.config_manager = None

            self.is_ready = False
            self.logger.info("Очистка ресурсов завершена")

        except Exception as e:
            self.logger.error(f"Ошибка очистки ресурсов: {str(e)}")

    def validate_components(self):
        """
        Проверяет корректность инициализированных компонентов.

        Returns:
            dict: Результат валидации
        """
        try:
            results = {"valid": True, "issues": []}

            # Проверяем наличие всех компонентов
            required_components = [
                ("config_manager", self.config_manager),
                ("state_manager", self.state_manager),
                ("system_logger", self.system_logger),
                ("content_generator", self.content_generator),
                ("assessment", self.assessment),
                ("interface", self.interface),
            ]

            for name, component in required_components:
                if component is None:
                    results["valid"] = False
                    results["issues"].append(f"Компонент {name} не инициализирован")

            # Проверяем готовность системы
            if not self.is_ready:
                results["valid"] = False
                results["issues"].append("Система не готова к работе")

            return results

        except Exception as e:
            return {"valid": False, "error": str(e)}
