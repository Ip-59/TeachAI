"""
Модуль для работы с конфигурационными файлами и переменными окружения.
Отвечает за загрузку API ключей и основных настроек системы.

Маршрут LLM (direct / gptunnel / proxy) — в ``llm_route.py``;
здесь тонкие обёртки для обратной совместимости.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

from llm_route import (
    apply_saved_route_preference,
    describe_llm_route,
    get_llm_api_key,
    get_llm_route,
    set_llm_route,
    validate_llm_credentials,
)


def get_openai_connection_mode() -> str:
    """
    Совместимость: сеть/транспорт.

    Returns:
        ``direct`` | ``proxy`` | ``gptunnel`` (см. ``get_llm_route``).
    """
    return get_llm_route()


def apply_openai_connection_environment() -> str:
    """
    Применяет маршрут LLM к процессу (preference + очистка прокси).

    Returns:
        Активный маршрут (``direct`` / ``gptunnel`` / ``proxy``).
    """
    route = apply_saved_route_preference()
    # Нормализуем env через set_llm_route без лишней записи на диск
    return set_llm_route(route, persist=False)


def get_openai_proxy_url() -> str | None:
    """URL HTTP-прокси только в маршруте ``proxy``."""
    if get_llm_route() != "proxy":
        return None
    for key in (
        "OPENAI_PROXY",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "https_proxy",
        "http_proxy",
    ):
        value = (os.getenv(key) or "").strip()
        if value and not value.startswith("${"):
            return value
    return None


def describe_openai_connection() -> str:
    """Краткое описание маршрута LLM для логов и консоли."""
    return describe_llm_route()


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
            apply_openai_connection_environment()

            ok, err = validate_llm_credentials()
            if not ok:
                self.logger.error(err)
                return False

            self.logger.info(
                "Конфигурация загружена (%s)", describe_openai_connection()
            )
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке конфигурации: {str(e)}")
            return False

    def get_api_key(self):
        """
        Получает API ключ для активного маршрута (OpenAI или GPTunnel).

        Returns:
            str: API ключ или None, если ключ не найден
        """
        api_key = get_llm_api_key()
        if not api_key:
            return None

        route = get_llm_route()
        if route != "gptunnel":
            valid_prefixes = ("sk-", "sk-proj-", "org-")
            if not api_key.startswith(valid_prefixes):
                self.logger.warning("API ключ OpenAI имеет необычный формат")

        return api_key

    def create_sample_env(self, file_path=".env.sample"):
        """
        Создает образец .env файла с инструкциями.

        Args:
            file_path (str): Путь для сохранения образца файла

        Returns:
            bool: True если файл создан или уже существует, иначе False
        """
        try:
            if os.path.exists(file_path):
                # Образец мог быть отредактирован пользователем: не затираем.
                self.logger.info(f"Образец .env уже есть, не перезаписываем: {file_path}")
                return True
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# Конфигурационный файл для TeachAI\n\n")
                f.write("# API ключ OpenAI (маршрут direct / proxy)\n")
                f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
                f.write("\n# Модель (gpt-4o-mini — по умолчанию)\n")
                f.write("LLM_MODEL=gpt-4o-mini\n")
                f.write("\n# Маршрут API: direct | gptunnel | proxy\n")
                f.write("OPENAI_API_ROUTE=gptunnel\n")
                f.write("GPTUNNEL_API_KEY=your_gptunnel_api_key_here\n")
                f.write("# GPTUNNEL_BASE_URL=https://gptunnel.ru/v1\n")
                f.write("\n# HTTP-прокси только при OPENAI_API_ROUTE=proxy\n")
                f.write("# OPENAI_PROXY=http://user:pass@host:port\n")

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
