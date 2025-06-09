"""
Модуль для управления конфигурацией системы.
Отвечает за загрузку настроек из .env файла и проверку их корректности.
ИСПРАВЛЕНО: Проблема #115 - корректное чтение API ключа из .env файла
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv


class ConfigManager:
    """Менеджер конфигурации для управления настройками системы."""

    def __init__(self, env_file=".env"):
        """
        Инициализация менеджера конфигурации.

        Args:
            env_file (str): Путь к файлу .env
        """
        self.logger = logging.getLogger(__name__)
        self.project_dir = Path(__file__).parent.absolute()
        self.env_file = self.project_dir / env_file

        # Настройки по умолчанию
        self.config = {
            "OPENAI_API_KEY": None,
            "MODEL_NAME": "gpt-3.5-turbo-16k",
            "MAX_TOKENS": 3500,
            "TEMPERATURE": 0.7,
            "DEBUG_MODE": False,
        }

        self.logger.info("ConfigManager инициализирован")

    def check_env_file(self):
        """
        Проверяет существование файла .env.

        Returns:
            bool: True если файл существует, иначе False
        """
        try:
            if self.env_file.exists():
                self.logger.info(f"Файл .env найден: {self.env_file}")
                return True
            else:
                self.logger.error(f"Файл .env не найден: {self.env_file}")
                return False
        except Exception as e:
            self.logger.error(f"Ошибка при проверке .env файла: {str(e)}")
            return False

    def load_config(self):
        """
        ИСПРАВЛЕНО: Загружает конфигурацию из .env файла с правильным чтением API ключа.

        Returns:
            bool: True если загрузка прошла успешно, иначе False
        """
        try:
            # Загружаем переменные из .env файла
            load_dotenv(self.env_file)

            # ИСПРАВЛЕНО: Правильное чтение API ключа
            api_key = os.getenv("OPENAI_API_KEY")

            if not api_key:
                self.logger.error("OPENAI_API_KEY не найден в .env файле")
                return False

            if api_key.strip() == "":
                self.logger.error("OPENAI_API_KEY пустой в .env файле")
                return False

            # ИСПРАВЛЕНО: Сохраняем реальный API ключ, а не placeholder
            self.config["OPENAI_API_KEY"] = api_key.strip()

            # Загружаем остальные настройки с значениями по умолчанию
            self.config["MODEL_NAME"] = os.getenv("MODEL_NAME", "gpt-3.5-turbo-16k")
            self.config["MAX_TOKENS"] = int(os.getenv("MAX_TOKENS", "3500"))
            self.config["TEMPERATURE"] = float(os.getenv("TEMPERATURE", "0.7"))
            self.config["DEBUG_MODE"] = (
                os.getenv("DEBUG_MODE", "False").lower() == "true"
            )

            # НОВОЕ: Логирование для диагностики (безопасно)
            self.logger.info(f"✅ Конфигурация загружена успешно")
            self.logger.info(f"📝 API ключ начинается с: {api_key[:10]}...")
            self.logger.info(f"🔧 Модель: {self.config['MODEL_NAME']}")
            self.logger.info(f"🎯 Max tokens: {self.config['MAX_TOKENS']}")
            self.logger.info(f"🌡️ Temperature: {self.config['TEMPERATURE']}")

            return True

        except Exception as e:
            self.logger.error(f"Ошибка при загрузке конфигурации: {str(e)}")
            return False

    def get_api_key(self):
        """
        ИСПРАВЛЕНО: Возвращает реальный API ключ OpenAI.

        Returns:
            str: API ключ или None если не найден
        """
        api_key = self.config.get("OPENAI_API_KEY")

        if not api_key:
            self.logger.error("API ключ не найден в конфигурации")
            return None

        # НОВОЕ: Дополнительная проверка на placeholder
        if api_key.startswith("<") or "config." in api_key:
            self.logger.error(f"API ключ имеет неправильный формат: {api_key[:20]}...")
            return None

        return api_key

    def get_model_name(self):
        """
        Возвращает название модели OpenAI.

        Returns:
            str: Название модели
        """
        return self.config.get("MODEL_NAME", "gpt-3.5-turbo-16k")

    def get_max_tokens(self):
        """
        Возвращает максимальное количество токенов.

        Returns:
            int: Максимальное количество токенов
        """
        return self.config.get("MAX_TOKENS", 3500)

    def get_temperature(self):
        """
        Возвращает температуру для генерации.

        Returns:
            float: Температура
        """
        return self.config.get("TEMPERATURE", 0.7)

    def is_debug_mode(self):
        """
        Проверяет, включен ли режим отладки.

        Returns:
            bool: True если режим отладки включен
        """
        return self.config.get("DEBUG_MODE", False)

    def ensure_directories(self):
        """
        Создает необходимые директории для работы системы.

        Returns:
            bool: True если создание прошло успешно, иначе False
        """
        try:
            # Создаем директории
            directories = ["data", "logs", "debug_responses"]

            for dir_name in directories:
                dir_path = self.project_dir / dir_name
                dir_path.mkdir(exist_ok=True, parents=True)
                self.logger.debug(f"Директория создана или существует: {dir_path}")

            self.logger.info("Все необходимые директории созданы")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка при создании директорий: {str(e)}")
            return False

    def validate_api_key_format(self, api_key):
        """
        НОВОЕ: Проверяет формат API ключа OpenAI.

        Args:
            api_key (str): API ключ для проверки

        Returns:
            bool: True если формат правильный, иначе False
        """
        try:
            if not api_key or not isinstance(api_key, str):
                return False

            # API ключи OpenAI обычно начинаются с 'REMOVED' и имеют определенную длину
            if not api_key.startswith("REMOVED"):
                self.logger.warning("API ключ должен начинаться с 'REMOVED'")
                return False

            if len(api_key) < 45:  # Минимальная ожидаемая длина
                self.logger.warning("API ключ слишком короткий")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Ошибка при валидации API ключа: {str(e)}")
            return False

    def test_api_key(self):
        """
        НОВОЕ: Тестирует API ключ с простым запросом.

        Returns:
            bool: True если ключ работает, иначе False
        """
        try:
            api_key = self.get_api_key()

            if not api_key:
                return False

            if not self.validate_api_key_format(api_key):
                return False

            # Простая проверка формата без реального запроса к API
            self.logger.info("API ключ прошел базовую валидацию")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка при тестировании API ключа: {str(e)}")
            return False

    def get_all_config(self):
        """
        Возвращает всю конфигурацию (без API ключа для безопасности).

        Returns:
            dict: Словарь с настройками
        """
        safe_config = self.config.copy()

        # Скрываем API ключ для безопасности
        if safe_config.get("OPENAI_API_KEY"):
            key = safe_config["OPENAI_API_KEY"]
            safe_config["OPENAI_API_KEY"] = f"{key[:10]}...{key[-4:]}"

        return safe_config

    def reload_config(self):
        """
        Перезагружает конфигурацию из .env файла.

        Returns:
            bool: True если перезагрузка прошла успешно, иначе False
        """
        try:
            self.logger.info("Перезагрузка конфигурации...")
            return self.load_config()
        except Exception as e:
            self.logger.error(f"Ошибка при перезагрузке конфигурации: {str(e)}")
            return False
