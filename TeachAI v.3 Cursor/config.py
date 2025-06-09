"""
Модуль для работы с конфигурационными файлами и переменными окружения.
Отвечает за загрузку API ключей и основных настроек системы.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv, dotenv_values


class ConfigManager:
    """Менеджер конфигурации для работы с .env файлом и переменными окружения."""

    def __init__(self, env_file=".env"):
        """
        Инициализация менеджера конфигурации.

        Args:
            env_file (str): Путь к .env файлу
        """
        self.env_file = env_file
        self.logger = logging.getLogger(__name__)

    def check_env_file(self):
        """
        Проверяет наличие .env файла.

        Returns:
            bool: True если файл существует, иначе False
        """
        return os.path.exists(self.env_file)

    def load_config(self):
        """
        Загружает переменные окружения из .env файла.

        Returns:
            bool: True если загрузка успешна, иначе False
        """
        try:
            # Используем python-dotenv для загрузки переменных
            if not os.path.exists(self.env_file):
                self.logger.warning(f"Не удалось загрузить файл {self.env_file}")
                return False

            # Загружаем .env файл
            load_dotenv(self.env_file)

            # Проверяем наличие обязательных переменных
            required_vars = ["OPENAI_API_KEY"]
            missing_vars = [var for var in required_vars if not os.getenv(var)]

            if missing_vars:
                self.logger.error(
                    f"Отсутствуют обязательные переменные: {', '.join(missing_vars)}"
                )
                return False

            self.logger.info("Конфигурация успешно загружена")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке конфигурации: {str(e)}")
            return False

    def get_api_key(self):
        """
        Получает API ключ OpenAI.

        Returns:
            str: API ключ или None, если ключ не найден
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.logger.error("API ключ OpenAI не найден")
            return None

        # Валидация ключа по формату (базовая, не проверяем актуальность)
        if not api_key.startswith(("REMOVED", "org-")):
            self.logger.warning("API ключ имеет неправильный формат")

        return api_key

    def create_sample_env(self, file_path=".env.sample"):
        """
        Создает образец .env файла с инструкциями.

        Args:
            file_path (str): Путь для сохранения образца файла

        Returns:
            bool: True если файл создан успешно, иначе False
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# Конфигурационный файл для TeachAI\n\n")
                f.write("# API ключ OpenAI\n")
                f.write("OPENAI_API_KEY=your_openai_api_key_here\n")

            self.logger.info(f"Образец .env файла создан: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при создании образца .env файла: {str(e)}")
            return False

    def create_env_file(self, api_key):
        """
        Создает .env файл с указанным API ключом.

        Args:
            api_key (str): API ключ OpenAI

        Returns:
            bool: True если файл создан успешно, иначе False
        """
        try:
            with open(self.env_file, "w", encoding="utf-8") as f:
                f.write(f"OPENAI_API_KEY={api_key}\n")

            # Перезагружаем переменные окружения
            load_dotenv(self.env_file, override=True)

            self.logger.info(f".env файл успешно создан и API ключ загружен")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при создании .env файла: {str(e)}")
            return False

    def ensure_directories(self):
        """
        Создает необходимые директории для работы системы.

        Returns:
            bool: True если директории созданы успешно, иначе False
        """
        try:
            # Определяем путь к директории проекта
            project_dir = Path(__file__).parent.absolute()

            # Создаем директории для логов и данных
            directories = ["logs", "data"]
            for directory in directories:
                dir_path = project_dir / directory
                dir_path.mkdir(exist_ok=True, parents=True)
                self.logger.debug(
                    f"Директория {directory} создана или уже существует: {dir_path}"
                )

            self.logger.info("Необходимые директории созданы")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при создании директорий: {str(e)}")
            # Пытаемся создать директории альтернативным способом
            try:
                import os

                for directory in directories:
                    os.makedirs(directory, exist_ok=True)
                self.logger.info("Директории созданы альтернативным способом")
                return True
            except Exception as alt_e:
                self.logger.error(
                    f"Альтернативный способ также не сработал: {str(alt_e)}"
                )
                return False

    def get_config_value(self, key, default=None):
        """
        Получает значение конфигурационной переменной.

        Args:
            key (str): Ключ переменной
            default: Значение по умолчанию, если переменная не найдена

        Returns:
            str: Значение переменной или значение по умолчанию
        """
        return os.getenv(key, default)
