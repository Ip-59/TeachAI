"""
Общие утилиты для генерации контента.
Содержит базовые классы, CSS стили, отладочные функции и общие инструменты.
ИСПРАВЛЕНО: добавлены контрастные стили для кода в BASE_CSS_STYLES
"""

import os
import json
import re
import logging
from datetime import datetime
import httpx
from openai import OpenAI


def append_question_reminder(answer_html: str, questions_count: int) -> str:
    """
    Добавляет напоминание к ответу, если вопросов больше 3.
    Args:
        answer_html (str): HTML-ответ
        questions_count (int): Количество заданных вопросов
    Returns:
        str: HTML-ответ с напоминанием (если нужно)
    """
    if questions_count > 3:
        reminder = (
            "<div style='margin-top: 16px; color: #0c5460; background: #e2f0fb; border-left: 4px solid #007bff; "
            "padding: 12px; border-radius: 8px; font-size: 15px;'>"
            "Мы несколько увлеклись вопросами, давайте продолжим обучение по плану курса."
            "</div>"
        )
        return answer_html + reminder
    return answer_html


class ContentUtils:
    """Базовые утилиты для работы с контентом."""

    # Стили общения для всех генераторов
    COMMUNICATION_STYLES = {
        "formal": "Формальный, академический стиль общения с использованием научной терминологии.",
        "friendly": "Дружелюбный стиль общения, использующий простые объяснения и аналогии.",
        "casual": "Непринужденный, разговорный стиль с элементами юмора.",
        "brief": "Краткий и четкий стиль, фокусирующийся только на ключевой информации.",
    }

    # ИСПРАВЛЕНО: Базовые CSS стили для контента с КОНТРАСТНЫМ кодом
    BASE_CSS_STYLES = """
    <style>
        .content-container {
            font-family: Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
        }
        .content-container h1 {
            font-size: 28px;
            margin-top: 15px;
            margin-bottom: 10px;
        }
        .content-container h2 {
            font-size: 24px;
            margin-top: 12px;
            margin-bottom: 8px;
        }
        .content-container h3 {
            font-size: 20px;
            margin-top: 10px;
            margin-bottom: 6px;
        }
        .content-container p {
            margin-bottom: 10px;
        }
        .content-container ul, .content-container ol {
            margin-bottom: 10px;
            padding-left: 30px;
        }
        .content-container li {
            margin-bottom: 4px;
        }
        .content-container code {
            font-family: 'Courier New', monospace;
            background-color: #1a1a1a;
            color: #00ff41;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 600;
            border: 1px solid #333;
        }
        .content-container pre {
            font-family: 'Courier New', monospace;
            background-color: #1a1a1a;
            color: #00ff41;
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 10px 0;
            font-size: 14px;
            line-height: 1.05;
            border: 2px solid #333;
        }
        .content-container pre code {
            background: none;
            color: inherit;
            padding: 0;
            font-size: inherit;
            border: none;
        }
        .content-container strong, .content-container b {
            font-weight: bold;
        }
    </style>
    <div class="content-container">
    """

    # ИСПРАВЛЕНО: CSS для примеров с уменьшенными интервалами
    EXAMPLES_CSS_STYLES = """
    <style>
        .examples-container {
            font-family: Arial, sans-serif;
            font-size: 16px;
            line-height: 1.5;
        }
        .example {
            margin-bottom: 15px;
            padding: 12px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        .example h3, .example h4 {
            margin-top: 0;
            margin-bottom: 8px;
            line-height: 1.3;
        }
        .example p {
            margin-bottom: 8px;
            line-height: 1.4;
        }
        .example pre {
            background-color: #1a1a1a;
            color: #00ff41;
            padding: 10px;
            border-radius: 3px;
            overflow-x: auto;
            margin: 8px 0;
            line-height: 1.2;
            font-family: 'Courier New', monospace;
            border: 1px solid #333;
        }
    </style>
    <div class="examples-container">
    """

    # ИСПРАВЛЕНО: CSS для объяснений с уменьшенными интервалами
    EXPLANATION_CSS_STYLES = """
    <style>
        .explanation-container {
            font-family: Arial, sans-serif;
            font-size: 16px;
            line-height: 1.5;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }
        .explanation-container h1, .explanation-container h2, .explanation-container h3 {
            margin-top: 15px;
            margin-bottom: 8px;
            line-height: 1.3;
        }
        .explanation-container p {
            margin-bottom: 10px;
            line-height: 1.4;
        }
        .explanation-container ul, .explanation-container ol {
            margin-bottom: 10px;
            padding-left: 30px;
            line-height: 1.4;
        }
        .explanation-container li {
            margin-bottom: 4px;
        }
        .explanation-container code {
            background-color: #1a1a1a;
            color: #00ff41;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-weight: 600;
        }
        .explanation-container pre {
            background-color: #1a1a1a;
            color: #00ff41;
            padding: 10px;
            overflow-x: auto;
            margin: 8px 0;
            line-height: 1.2;
            font-family: 'Courier New', monospace;
            border: 1px solid #333;
        }
    </style>
    <div class="explanation-container">
    """

    def get_style_prefix(self, communication_style, content_type="general"):
        """
        Возвращает префикс для контента в зависимости от стиля общения.

        Args:
            communication_style (str): Стиль общения
            content_type (str): Тип контента (examples, explanation, qa, general)

        Returns:
            str: HTML префикс
        """
        if content_type == "examples":
            if communication_style == "formal":
                return "<p style='font-size: 16px; line-height: 1.4;'>Представляем вашему вниманию примеры для данного учебного материала.</p>"
            elif communication_style == "casual":
                return "<p style='font-size: 16px; line-height: 1.4;'>Привет! Вот несколько примеров, которые помогут разобраться с темой! 👍</p>"
            elif communication_style == "brief":
                return "<p style='font-size: 16px; line-height: 1.4;'>Примеры:</p>"
            else:  # friendly по умолчанию
                return "<p style='font-size: 16px; line-height: 1.4;'>Вот несколько полезных примеров, которые помогут вам лучше понять материал урока:</p>"

        elif content_type == "explanation":
            if communication_style == "formal":
                return "<p style='font-size: 16px; line-height: 1.4;'>Уважаемый пользователь! Ниже представлено академическое объяснение материала.</p>"
            elif communication_style == "casual":
                return "<p style='font-size: 16px; line-height: 1.4;'>Привет! Вот более подробное и неформальное объяснение этой темы. 😊</p>"
            elif communication_style == "brief":
                return "<p style='font-size: 16px; line-height: 1.4;'>Краткое дополнительное объяснение:</p>"
            else:  # friendly по умолчанию
                return "<p style='font-size: 16px; line-height: 1.4;'>Добро пожаловать в подробное объяснение! Надеюсь, что этот материал поможет вам лучше понять тему.</p>"

        elif content_type == "qa":
            if communication_style == "formal":
                return "<p style='font-size: 16px; line-height: 1.4;'>Академический ответ на ваш вопрос:</p>"
            elif communication_style == "casual":
                return "<p style='font-size: 16px; line-height: 1.4;'>Отличный вопрос! Вот мой ответ: 😊</p>"
            elif communication_style == "brief":
                return (
                    "<p style='font-size: 16px; line-height: 1.4;'>Краткий ответ:</p>"
                )
            else:  # friendly по умолчанию
                return "<p style='font-size: 16px; line-height: 1.4;'>Спасибо за вопрос! Вот подробный ответ:</p>"

        return ""


class BaseContentGenerator:
    """Базовый класс для всех генераторов контента."""

    def __init__(self, api_key, debug_dir="debug_responses"):
        """
        Инициализация базового генератора.

        Args:
            api_key (str): API ключ OpenAI
            debug_dir (str): Директория для отладочных файлов
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.api_key = api_key
        self.debug_dir = debug_dir

        # Инициализация клиента OpenAI (с прокси из OPENAI_PROXY/HTTPS_PROXY/HTTP_PROXY)
        self.http_client = None
        try:
            proxy_url = (
                os.getenv("OPENAI_PROXY")
                or os.getenv("HTTPS_PROXY")
                or os.getenv("HTTP_PROXY")
                or ""
            ).strip()
            if not proxy_url or proxy_url.startswith("${"):
                raise RuntimeError(
                    "Прокси не задан. Укажите OPENAI_PROXY или HTTPS_PROXY/HTTP_PROXY."
                )

            self.http_client = httpx.Client(proxy=proxy_url)
            self.client = OpenAI(api_key=self.api_key, http_client=self.http_client)
            self.logger.info(f"{self.__class__.__name__} инициализирован с прокси")
        except Exception as e:
            self.logger.error(f"Ошибка при инициализации клиента OpenAI: {str(e)}")
            raise

        # Создаем директорию для отладочных файлов
        os.makedirs(self.debug_dir, exist_ok=True)

    def save_debug_response(
        self, response_type, prompt, response_content, additional_data=None
    ):
        """
        Сохраняет ответ API в файл для отладки.

        Args:
            response_type (str): Тип запроса (course_plan, lesson, assessment, etc.)
            prompt (str): Отправленный промпт
            response_content (str): Ответ от API
            additional_data (dict): Дополнительные данные для сохранения
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{response_type}_{timestamp}.json"
            filepath = os.path.join(self.debug_dir, filename)

            debug_data = {
                "timestamp": timestamp,
                "response_type": response_type,
                "prompt": (
                    prompt[:500] + "..." if len(prompt) > 500 else prompt
                ),  # Сокращаем длинные промпты
                "response_content": response_content,
                "additional_data": additional_data or {},
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Отладочный ответ сохранен: {filepath}")

        except Exception as e:
            self.logger.error(f"Ошибка при сохранении отладочного ответа: {str(e)}")

    def clean_markdown_code_blocks(self, text):
        """
        Удаляет markdown метки для блоков кода из текста и очищает лишние отступы.

        Args:
            text (str): Исходный текст

        Returns:
            str: Очищенный текст
        """
        try:
            # Убираем метки ```html, ```python, ``` и подобные
            text = re.sub(r"```\w*\n?", "", text)
            text = re.sub(r"```", "", text)

            # НОВОЕ: Очищаем лишние отступы в блоках кода <pre><code>
            code_pattern = r"<pre><code>(.*?)</code></pre>"

            def clean_code_block(match):
                code_content = match.group(1)

                # Разбиваем на строки
                lines = code_content.split("\n")

                # Находим минимальный отступ среди строк С ОТСТУПАМИ (исключая строки без отступов)
                min_indent = float("inf")
                lines_with_indent = []

                for line in lines:
                    if line.strip():  # Пропускаем пустые строки
                        indent = len(line) - len(line.lstrip())

                        if indent > 0:  # Только строки с отступами
                            lines_with_indent.append(indent)
                            if indent < min_indent:
                                min_indent = indent

                # Если есть строки с отступами, убираем минимальный отступ
                if min_indent > 0 and min_indent != float("inf"):
                    cleaned_lines = []
                    for line in lines:
                        if line.strip():  # Для непустых строк
                            if len(line) - len(line.lstrip()) > 0:  # Если есть отступ
                                cleaned_line = line[min_indent:]
                                cleaned_lines.append(cleaned_line)
                            else:  # Если отступа нет, оставляем как есть
                                cleaned_lines.append(line)
                        else:  # Пустые строки оставляем как есть
                            cleaned_lines.append("")
                    code_content = "\n".join(cleaned_lines)

                return f"<pre><code>{code_content}</code></pre>"

            # Применяем очистку ко всем блокам кода
            text = re.sub(code_pattern, clean_code_block, text, flags=re.DOTALL)

            return text

        except Exception as e:
            self.logger.warning(
                f"Ошибка при очистке markdown меток и отступов: {str(e)}"
            )
            return text

    def make_api_request(
        self, messages, temperature=0.7, max_tokens=3500, response_format=None
    ):
        """
        Выполняет запрос к OpenAI API с едиными настройками.

        Args:
            messages (list): Список сообщений для API
            temperature (float): Температура генерации
            max_tokens (int): Максимальное количество токенов
            response_format (dict): Формат ответа (например, {"type": "json_object"})

        Returns:
            str: Ответ от API

        Raises:
            Exception: При ошибке API
        """
        try:
            kwargs = {
                "model": "gpt-3.5-turbo-16k",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if response_format:
                kwargs["response_format"] = response_format

            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"Ошибка при запросе к OpenAI API: {str(e)}")
            raise

    def make_api_request_with_retries(
        self,
        messages,
        temperature=0.7,
        max_tokens=3500,
        response_format=None,
        retries=3,
        backoff_factor=2,
        initial_delay=2,
    ):
        """Выполняет запрос к OpenAI API с повторными попытками для ошибок сети."""
        last_exception = None
        delay = initial_delay

        for attempt in range(1, retries + 1):
            try:
                return self.make_api_request(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"Попытка {attempt}/{retries} неудачна: {str(e)}. "
                    f"Повтор через {delay} сек..."
                )

                if attempt == retries:
                    break

                import time

                time.sleep(delay)
                delay *= backoff_factor

        raise Exception(
            "Сервер не отвечает. Попробуйте повторить запрос через несколько секунд. "
            f"Если ошибка сохраняется, проверьте подключение и настройки прокси. "
            f"Исходная ошибка: {str(last_exception)}"
        )
