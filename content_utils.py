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
            line-height: 1.5;
            border: 2px solid #333;
            white-space: pre;
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
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

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
            self.logger.info(
                "%s инициализирован с прокси, модель: %s",
                self.__class__.__name__,
                self.model,
            )
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

    def clean_lesson_html_for_analysis(self, content):
        """Готовит HTML урока для анализа LLM: чистит шум и теги.

        Что удаляется ДО снятия тегов (важно):
        - блоки ``<style>...</style>`` и ``<script>...</script>``
          вместе с содержимым (иначе CSS-/JS-текст утекает в анализ как
          «материал урока» и забивает контекст);
        - HTML-комментарии ``<!-- ... -->``.

        Затем снимаются теги и схлопываются пробельные последовательности.

        Args:
            content (str): Исходный HTML-фрагмент урока.

        Returns:
            str: Чистый текст урока, пригодный для отправки в LLM.
        """
        if not content:
            return ""
        cleaned = re.sub(
            r"<style\b[^>]*>[\s\S]*?</style>", " ", content, flags=re.IGNORECASE
        )
        cleaned = re.sub(
            r"<script\b[^>]*>[\s\S]*?</script>", " ", cleaned, flags=re.IGNORECASE
        )
        cleaned = re.sub(r"<!--[\s\S]*?-->", " ", cleaned)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        cleaned = re.sub(r"&[a-zA-Z]+;", " ", cleaned)
        cleaned = re.sub(r"&#\d+;", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def extract_lesson_headers(self, content):
        """Извлекает заголовки h1–h4 из HTML урока.

        Args:
            content (str): HTML-содержание урока.

        Returns:
            list[str]: Заголовки в порядке появления.
        """
        if not content:
            return []
        headers = re.findall(
            r"<h[1-4][^>]*>\s*([\s\S]*?)\s*</h[1-4]>", content, flags=re.IGNORECASE
        )
        result = []
        for header in headers:
            text = re.sub(r"<[^>]+>", " ", header)
            text = re.sub(r"\s+", " ", text).strip()
            if text and text not in result:
                result.append(text)
        return result

    def strip_plain_text_breadcrumb(
        self, text, course_context=None, lesson_title=None
    ):
        """Срезает ведущие названия курса/раздела/темы/урока из plain text.

        После ``clean_lesson_html_for_analysis`` breadcrumb часто остаётся
        первым абзацem текста («Введение в ML Основы Python ...»).

        Args:
            text (str): Очищенный текст урока.
            course_context (dict | None): Контекст курса.
            lesson_title (str | None): Название урока.

        Returns:
            str: Текст без ведущих breadcrumb-фрагментов.
        """
        if not text:
            return text

        titles = []
        if isinstance(course_context, dict):
            for key in ("course_title", "section_title", "topic_title"):
                title = (course_context.get(key) or "").strip()
                if title:
                    titles.append(title)
        if lesson_title:
            title = str(lesson_title).strip()
            if title and title not in titles:
                titles.append(title)

        result = text.lstrip()
        changed = True
        while changed and result:
            changed = False
            for title in titles:
                if result.lower().startswith(title.lower()):
                    result = result[len(title) :].lstrip(" ,:;—.-")
                    changed = True
        return result.strip()

    def prepare_lesson_text_for_analysis(
        self, content, course_context=None, max_chars=6000, lesson_title=None
    ):
        """Готовит текст урока для LLM-анализа (релевантность, понятия, QA).

        Последовательность: срез breadcrumb-шапки → удаление style/script →
        снятие HTML-тегов → срез plain-text breadcrumb → ограничение длины.

        Args:
            content (str): HTML или markdown урока.
            course_context (dict | None): Контекст курса для среза шапки.
            max_chars (int): Максимальная длина возвращаемого текста.
            lesson_title (str | None): Название урока для среза plain-text шапки.

        Returns:
            str: Чистый текст для промпта.
        """
        if not content:
            return ""
        stripped = self.strip_lesson_breadcrumb(content, course_context)
        clean = self.clean_lesson_html_for_analysis(stripped)
        clean = self.strip_plain_text_breadcrumb(
            clean, course_context, lesson_title=lesson_title
        )
        if max_chars and len(clean) > max_chars:
            return clean[:max_chars]
        return clean

    def strip_lesson_breadcrumb(self, content, course_context):
        """Срезает ведущие <h1>/<h2>/<h3>/<h4> с названиями курса/раздела/темы.

        LLM при генерации урока часто помещает в начало шапку с названиями
        курса, раздела и темы. Такая шапка не относится к телу конкретного
        урока, но при последующих запросах (генерация ключевых понятий,
        проверка релевантности, QA и т.п.) она затеняет содержание урока
        и сбивает LLM на общую тему курса.

        Удаляются ровно те идущие подряд заголовки в начале документа,
        текст которых совпадает (без учёта регистра и крайних пробелов)
        с одним из значений ``course_title / section_title / topic_title``
        в ``course_context``. Заголовки внутри тела урока не трогаются.

        Args:
            content (str): Исходный HTML урока.
            course_context (dict | None): Контекст курса.

        Returns:
            str: HTML без ведущей breadcrumb-шапки.
        """
        if not content or not isinstance(course_context, dict):
            return content

        breadcrumb_titles = [
            (course_context.get(key) or "").strip()
            for key in ("course_title", "section_title", "topic_title")
        ]
        breadcrumb_titles = [t for t in breadcrumb_titles if t]
        if not breadcrumb_titles:
            return content

        normalized_set = {t.lower() for t in breadcrumb_titles}

        # «Шум» допустимый ПЕРЕД breadcrumb-заголовком — это типичная служебная
        # обвязка от генератора урока: <style>, <script>, HTML-комментарии,
        # пробелы и переносы строк. Заголовки идут уже после неё.
        leading_noise_re = re.compile(
            r"(?:<style\b[^>]*>[\s\S]*?</style>"
            r"|<script\b[^>]*>[\s\S]*?</script>"
            r"|<!--[\s\S]*?-->"
            r"|\s+)+",
            re.IGNORECASE,
        )
        header_re = re.compile(
            r"<h[1-4][^>]*>\s*([\s\S]*?)\s*</h[1-4]>",
            re.IGNORECASE,
        )

        stripped = content
        while True:
            noise = leading_noise_re.match(stripped)
            offset = noise.end() if noise else 0
            header = header_re.match(stripped, offset)
            if not header:
                break
            header_text = re.sub(r"<[^>]+>", "", header.group(1)).strip().lower()
            if header_text in normalized_set:
                # Удаляем только сам заголовок, ведущий шум (style/script)
                # оставляем как был — clean_lesson_html_for_analysis уберёт
                # его дальше.
                stripped = stripped[:header.start()] + stripped[header.end():]
                continue
            break

        return stripped

    def clean_markdown_code_blocks(self, text):
        """
        Удаляет markdown/код-fences вокруг ответа LLM.

        Закрывает класс багов, когда LLM возвращает HTML-объяснение,
        обёрнутое в ```html ... ``` (или '''html ... ''', ~~~html ... ~~~),
        и пользователь видит эти метки прямо в выводе.

        Отступы внутри <pre><code> НЕ трогает (раньше здесь был самописный
        de-indent, который ломал тело циклов: `for x:\\n    body` → `for x:\\nbody`).
        Если нужно снять общий отступ — используется textwrap.dedent,
        который безопасен: ничего не трогает, если хоть одна строка
        не имеет общего префикса.

        Args:
            text (str): Исходный текст.

        Returns:
            str: Текст без обёрток-fences.
        """
        try:
            import textwrap

            # Снимаем все варианты блочных fences: ```lang, ```, '''lang, ''', ~~~lang, ~~~
            text = re.sub(r"```\s*[A-Za-z0-9_+\-]*\s*\n?", "", text)
            text = re.sub(r"```", "", text)
            text = re.sub(r"~~~\s*[A-Za-z0-9_+\-]*\s*\n?", "", text)
            text = re.sub(r"~~~", "", text)
            # '''html / ''' — только когда оборачивают блок (в начале строки),
            # чтобы не трогать docstring-ы внутри примеров кода.
            text = re.sub(r"(?m)^\s*'''\s*[A-Za-z0-9_+\-]*\s*\n", "", text)
            text = re.sub(r"(?m)^\s*'''\s*$", "", text)

            # Безопасный dedent внутри <pre><code>: снимает только общий
            # лидирующий пробельный префикс. Если у хотя бы одной строки
            # его нет — структура цикла/условия сохраняется как есть.
            code_pattern = r"<pre><code>([\s\S]*?)</code></pre>"

            def dedent_code_block(match):
                code_content = match.group(1).strip("\n")
                dedented = textwrap.dedent(code_content)
                return f"<pre><code>{dedented}</code></pre>"

            text = re.sub(code_pattern, dedent_code_block, text)

            return text

        except Exception as e:
            self.logger.warning(
                f"Ошибка при очистке markdown меток и отступов: {str(e)}"
            )
            return text

    def make_api_request(
        self,
        messages,
        temperature=0.7,
        max_tokens=3500,
        response_format=None,
        model=None,
    ):
        """
        Выполняет запрос к OpenAI API с едиными настройками.

        Args:
            messages (list): Список сообщений для API
            temperature (float): Температура генерации
            max_tokens (int): Максимальное количество токенов
            response_format (dict): Формат ответа (например, {"type": "json_object"})
            model (str): Модель; если не указана — self.model

        Returns:
            str: Ответ от API

        Raises:
            Exception: При ошибке API
        """
        try:
            kwargs = {
                "model": model or self.model,
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
        model=None,
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
                    model=model,
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
