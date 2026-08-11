"""
Модуль для работы с конфигурационными файлами и переменными окружения.
Отвечает за загрузку API ключей и основных настроек системы.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

_PROXY_ENV_KEYS = (
    "OPENAI_PROXY",
    "HTTPS_PROXY",
    "HTTP_PROXY",
    "https_proxy",
    "http_proxy",
)

_PROXY_ENV_KEYS_TO_CLEAR = _PROXY_ENV_KEYS + (
    "ALL_PROXY",
    "all_proxy",
    "NO_PROXY",
    "no_proxy",
)


def _read_proxy_url_from_env() -> str | None:
    """Читает URL прокси из переменных окружения (без учёта режима подключения)."""
    for key in _PROXY_ENV_KEYS:
        value = (os.getenv(key) or "").strip()
        if value and not value.startswith("${"):
            return value
    return None


def get_openai_connection_mode() -> str:
    """
    Режим подключения TeachAI к OpenAI API.

    По умолчанию ``direct``: приложение не использует HTTP-прокси
    (доступ через VPN или сеть на уровне ОС). Режим ``proxy`` включается
    только явно через ``OPENAI_CONNECTION_MODE=proxy`` или
    ``OPENAI_USE_PROXY=true``.

    Returns:
        str: ``proxy`` — HTTP-прокси из .env; ``direct`` — без прокси в приложении.
    """
    raw = (os.getenv("OPENAI_CONNECTION_MODE") or "").strip().lower()
    use_proxy = (os.getenv("OPENAI_USE_PROXY") or "").strip().lower()

    if use_proxy in ("true", "1", "yes", "on"):
        return "proxy"
    if use_proxy in ("false", "0", "no", "off"):
        return "direct"

    if raw in ("proxy", "http_proxy"):
        return "proxy"
    if raw in ("direct", "vpn", "auto", "noproxy", "no_proxy", "none", ""):
        return "direct"

    logging.getLogger(__name__).warning(
        "Неизвестный OPENAI_CONNECTION_MODE=%r — используем direct", raw
    )
    return "direct"


def apply_openai_connection_environment() -> str:
    """
    Применяет режим подключения к текущему процессу Python.

    В режиме ``direct`` удаляет переменные прокси из ``os.environ``, чтобы
    httpx/OpenAI и другие библиотеки не подхватывали старые HTTP_PROXY
    из shell или Cursor.

    Returns:
        str: Активный режим (``direct`` или ``proxy``).
    """
    mode = get_openai_connection_mode()
    if mode == "direct":
        for key in _PROXY_ENV_KEYS_TO_CLEAR:
            os.environ.pop(key, None)
        os.environ["OPENAI_CONNECTION_MODE"] = "direct"
        os.environ["OPENAI_USE_PROXY"] = "false"
    return mode


def get_openai_proxy_url() -> str | None:
    """
    URL прокси для httpx/OpenAI с учётом ``OPENAI_CONNECTION_MODE``.

    В режиме ``direct`` всегда ``None`` (игнорируются и OPENAI_PROXY, и системные
    HTTP_PROXY), чтобы VPN работал на уровне системы без прокси в коде.
    """
    if get_openai_connection_mode() == "direct":
        return None
    return _read_proxy_url_from_env()


def describe_openai_connection() -> str:
    """Краткое описание режима подключения для логов и консоли."""
    mode = get_openai_connection_mode()
    if mode == "direct":
        return "прямое подключение (без прокси в приложении; VPN/сеть на уровне ОС)"
    proxy = _read_proxy_url_from_env()
    if not proxy:
        return "прокси (URL не задан — проверьте OPENAI_PROXY в .env)"
    host = proxy.split("@")[-1] if "@" in proxy else proxy
    return f"через прокси ({host})"


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

            # Проверяем наличие обязательных переменных
            required_vars = ["OPENAI_API_KEY"]
            missing_vars = [var for var in required_vars if not os.getenv(var)]

            if missing_vars:
                self.logger.error(
                    f"Отсутствуют обязательные переменные: {', '.join(missing_vars)}"
                )
                return False

            mode = get_openai_connection_mode()
            if mode == "proxy" and not _read_proxy_url_from_env():
                self.logger.error(
                    "OPENAI_CONNECTION_MODE=proxy, но прокси не задан. "
                    "Укажите OPENAI_PROXY (или HTTPS_PROXY) в .env."
                )
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
        Получает API ключ OpenAI.

        Returns:
            str: API ключ или None, если ключ не найден
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.logger.error("API ключ OpenAI не найден")
            return None

        # Валидация ключа по формату (базовая, не проверяем актуальность)
        valid_prefixes = ("sk-", "sk-proj-", "org-")
        if not api_key.startswith(valid_prefixes):
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
                f.write("\n# Модель OpenAI (gpt-4o-mini — по умолчанию, gpt-4o — для сложных задач)\n")
                f.write("LLM_MODEL=gpt-4o-mini\n")
                f.write("\n# --- Режим подключения к OpenAI ---\n")
                f.write("# direct / vpn / auto — без прокси в приложении (VPN на уровне ОС)\n")
                f.write("# proxy — через HTTP-прокси из OPENAI_PROXY (сейчас не используем)\n")
                f.write("OPENAI_CONNECTION_MODE=direct\n")
                f.write("\n# Прокси (только при OPENAI_CONNECTION_MODE=proxy)\n")
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
