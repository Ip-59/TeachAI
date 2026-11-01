# Задача для Cursor: пакет 6 — рефакторинг content_utils (6a–6e)

Скопируй файл целиком в чат Cursor. Исполнитель — Cursor-агент в проекте TeachAI на локальном компьютере.

**База:** `main` = **`d2207c9`** (прогон: `154 passed, 1 deselected`).  
**Ветка:** работай **прямо на `main`** — этапы мелкие и поведенчески нейтральные. Отдельную ветку не заводи, если не упрёшься в незакоммиченный чужой хвост (тогда остановись и напиши).

Все этапы **проверены в прототипе** на копии `d2207c9` (Linux, Python 3.13, venv_box):

| После этапа | Полный `python -m pytest -q` |
|---|---|
| старт `d2207c9` | `154 passed, 1 deselected` |
| **6a** | **`162 passed, 1 deselected`** (+8 characterization) |
| **6b** | **`162 passed, 1 deselected`** |
| **6c** | **`163 passed, 1 deselected`** (+1 smoke re-export) |
| **6d** | **`163 passed, 1 deselected`** |
| **6e** | **`163 passed, 1 deselected`** (формулировки релевантности) |

Будь максимально внимателен: поведение ученику не менять. Если контекст не совпал — **остановись и напиши**, не подгоняй.

---

## 0. Жёсткие правила

1. Менять только то, что описано в текущем этапе. Без «заодно»-рефакторинга сверх этапа.
2. Поведение TeachAI не менять (кроме явно согласованной правки текста промпта в **6e**).
3. **Один этап — один коммит — один push.** Push на машине Игоря:
   ```bash
   bash .secrets/github_ssh/push_origin.sh
   ```
   Обычный `git push` на домашней машине часто падает с `Permission denied (publickey)` — не чинить SSH в этом пакете, использовать скрипт.
4. Venv **текущей** машины: `venv_W_L` или `venv_H_L`. После каждого этапа: `python -m pytest -q -rx`.
5. **Не** force-push, **не** rewrite history.
6. Никогда не печатать и не echo **OPENAI_API_KEY** и секреты. В тестах — `sk-test-not-a-real-key`.
7. Не коммитить локальные outputs `TeachAI.ipynb` (execution_count / widget output). Если ноутбук грязный — не добавляй его в коммит.
8. Не трогать `data/`, `.env`, `.env.sample`.
9. В конце сессии: «сохрани чат», блок «Итог» сверху, закоммить `.md` лог по `docs/chat_logs/README.md` (отдельным коммитом или вместе с последним этапом — как принято).
10. Новых `xfail`/`skip` без согласования не добавлять.

---

## 1. Зачем пакет

`content_utils.py` смешивал JSON-парсер, стили общения, мёртвый CSS, базовый LLM-клиент и мелкие QA-утилиты. Пакет 6: characterization → удаление мёртвого → сплит с безопасным патчем FakeLLM → смена импортов → перенос `*_checks.py` → микро-выравнивание формулировок релевантности.

**Главная ловушка (6b):** `tests/fake_llm.py` делал  
`content_utils.create_openai_client = ...`.  
После переноса `BaseContentGenerator` в `llm_api_base` вызов идёт в **глобалы `llm_api_base`**. Патч только `content_utils` **молча** снова ходил бы в сеть / ломал бы сценарии. В 6b патчим **оба** модуля.

---

## 2. Состав

| Этап | Суть | Pytest |
|---|---|---|
| **6a** | Characterization + удаление мёртвого CSS и `code_formatter.py` | **162** |
| **6b** | Сплит модулей + re-export в `content_utils` + правка FakeLLM | **162** |
| **6c** | Импорты генераторов/тестов на новые модули; shim остаётся | **163** |
| **6d** | `*_checks.py` → `tests/legacy_checks/` | **163** |
| **6e** | «в тексте или коде» в system+user релевантности | **163** |

---

## ЭТАП 6a. Characterization и удаление мёртвого

### A. Новый файл `tests/unit/test_content_utils_characterization.py`

Создай **целиком** (пока импорты из `content_utils` — так и надо до сплита):

```python
"""Характеризация публичного API content_utils до/после сплита (пакет 6)."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_parse_llm_json_plain_object():
    from content_utils import parse_llm_json

    assert parse_llm_json('{"a": 1, "b": [2]}') == {"a": 1, "b": [2]}


def test_parse_llm_json_fenced_and_surrounding_text():
    from content_utils import parse_llm_json

    fenced = """```json
{"ok": true, "n": 3}
```"""
    assert parse_llm_json(fenced) == {"ok": True, "n": 3}
    wrapped = 'Преамбула\n{"x": 7}\nхвост'
    assert parse_llm_json(wrapped) == {"x": 7}


def test_parse_llm_json_rejects_garbage():
    from content_utils import parse_llm_json

    with pytest.raises(ValueError):
        parse_llm_json("это не json")


def test_communication_styles_and_get_style_prefix():
    from content_utils import ContentUtils

    styles = ContentUtils.COMMUNICATION_STYLES
    assert set(styles) >= {"formal", "friendly", "casual", "brief"}
    utils = ContentUtils()
    examples = utils.get_style_prefix("friendly", "examples")
    assert "пример" in examples.lower() or "Примеры" in examples or "примеров" in examples.lower()
    qa = utils.get_style_prefix("brief", "qa")
    assert "Краткий" in qa or "кратк" in qa.lower()
    assert utils.get_style_prefix("friendly", "unknown_type") == ""


def test_append_question_reminder_threshold():
    from content_utils import append_question_reminder

    base = "<p>ответ</p>"
    assert append_question_reminder(base, 3) == base
    with_note = append_question_reminder(base, 4)
    assert with_note.startswith(base)
    assert "продолжим обучение" in with_note


def test_non_retryable_api_error_by_status_and_quota():
    from content_utils import non_retryable_api_error

    class Exc(Exception):
        def __init__(self, code=None, msg="err"):
            super().__init__(msg)
            if code is not None:
                self.status_code = code

    assert "401" in non_retryable_api_error(Exc(401))
    assert "400" in non_retryable_api_error(Exc(400))
    assert non_retryable_api_error(Exc(msg="Error code: 403 boom"))
    assert "квот" in non_retryable_api_error(Exc(msg="insufficient_quota")).lower()
    assert non_retryable_api_error(Exc(429)) == ""
    assert non_retryable_api_error(Exc(500)) == ""


def test_extract_lesson_headers_order_and_strip_tags():
    from content_utils import BaseContentGenerator

    gen = BaseContentGenerator.__new__(BaseContentGenerator)
    html = "<h2>A</h2><p>x</p><h3><b>B</b></h3><h2>A</h2>"
    assert gen.extract_lesson_headers(html) == ["A", "B"]
    assert gen.extract_lesson_headers("") == []


def test_prepare_lesson_text_for_analysis_strips_breadcrumb():
    from content_utils import BaseContentGenerator

    gen = BaseContentGenerator.__new__(BaseContentGenerator)
    html = (
        "<style>.x{color:red}</style>"
        "<h1>Курс Python</h1>"
        "<h2>Раздел 1</h2>"
        "<h3>Тема A</h3>"
        "<h2>Тело урока</h2>"
        "<p>Важный текст про списки.</p>"
        "<script>alert(1)</script>"
    )
    ctx = {
        "course_title": "Курс Python",
        "section_title": "Раздел 1",
        "topic_title": "Тема A",
    }
    text = gen.prepare_lesson_text_for_analysis(
        html, course_context=ctx, lesson_title="Урок 1", max_chars=6000
    )
    assert "Важный текст про списки" in text
    assert "Тело урока" in text
    assert "alert" not in text
    assert "color:red" not in text
    assert not text.lower().startswith("курс python")

```

### B. Удалить три мёртвых CSS-константы из `ContentUtils` в `content_utils.py`

Удалить атрибуты **`BASE_CSS_STYLES`**, **`EXAMPLES_CSS_STYLES`**, **`EXPLANATION_CSS_STYLES`** целиком (включая комментарии «ИСПРАВЛЕНО: … CSS»).  
Оставить `COMMUNICATION_STYLES` и метод `get_style_prefix`.  
В модульном docstring убрать фразу про `BASE_CSS_STYLES`.

Перед коммитом — проверки (ожидается **пустой** вывод на runtime-коде; упоминания только в старых docs/chat_logs допустимы и **не** трогать):

```bash
rg -n "BASE_CSS_STYLES|EXAMPLES_CSS_STYLES|EXPLANATION_CSS_STYLES" -g '*.py' -g '*.ipynb' .
# ожидается: нет совпадений в *.py / TeachAI.ipynb
# (в docs/chat_logs и старых md могут остаться — не чистить в этом этапе)

rg -n "BASE_CSS_STYLES|EXAMPLES_CSS_STYLES|EXPLANATION_CSS_STYLES" TeachAI.ipynb tests doc model_benchmark
# ожидается: пусто
```

### C. Удалить `code_formatter.py`

Сначала:

```bash
rg -n "from code_formatter|import code_formatter|CodeFormatter" -g '*.py' -g '*.ipynb' --glob '!doc/**' --glob '!docs/**' .
# ожидается: пусто (кроме самого code_formatter.py)

rg -n "from code_formatter|import code_formatter|CodeFormatter" TeachAI.ipynb tests doc model_benchmark
# в doc/backup и docs/ могут быть исторические упоминания — файл всё равно удаляем:
# runtime и tests его не импортируют.
```

Затем: `git rm code_formatter.py` (или удали файл и `git add -u`).

### D. Решение по `clean_markdown_code_blocks` — **оставить**

Метод остаётся на `BaseContentGenerator` и в 6b уедет в `llm_api_base.py`.  
Снаружи живого кода его не вызывают (только `doc/examples_generation_backup.py` и старые отчёты). Реальная логика уже в `student_content.unwrap_outer_fence`. Удалять метод в 6a **не** нужно: нулевой выигрыш, лишний риск для локальных скриптов.

### E. Тесты, коммит, push

```bash
python -m pytest -q -rx
git add tests/unit/test_content_utils_characterization.py content_utils.py
git add -u code_formatter.py
git status   # нет data/, .env, грязного ipynb
git commit -m "6a: характеристика content_utils; удалены мёртвый CSS и code_formatter"
bash .secrets/github_ssh/push_origin.sh
```

**Ожидание:** `162 passed, 1 deselected`.

**Отчёт:** SHA, pytest, вывод двух `rg` (пусто по runtime).

---

## ЭТАП 6b. Сплит + re-export + FakeLLM

### A. Создать модули (полные файлы)

**`llm_json.py`:**

```python
"""Разбор JSON из ответов LLM (ограждения ``` и лишний текст вокруг)."""
from __future__ import annotations

import json
import re


def parse_llm_json(text):
    """Разбирает JSON из ответа модели; снимает обёртку ```json ... ``` и лишний текст вокруг.

    Raises:
        ValueError: (json.JSONDecodeError — его подкласс), если JSON не найден.
    """
    raw = (text or "").strip()
    fenced = re.match(r"^```[A-Za-z0-9_-]*[ \t]*\n?(.*?)\n?```\s*$", raw, re.S)
    if fenced:
        raw = fenced.group(1).strip()
    try:
        return json.loads(raw)
    except ValueError:
        starts = [i for i in (raw.find("{"), raw.find("[")) if i != -1]
        end = max(raw.rfind("}"), raw.rfind("]"))
        if starts and end > min(starts):
            return json.loads(raw[min(starts) : end + 1])
        raise

```

**`qa_response_utils.py`:**

```python
"""Мелкие правки HTML-ответов ученику (напоминания и т.п.)."""
from __future__ import annotations


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

```

**`communication_style.py`:**

```python
"""Стили общения для промптов и короткие HTML-префиксы ответа."""
from __future__ import annotations

COMMUNICATION_STYLES = {
    "formal": "Формальный, академический стиль общения с использованием научной терминологии.",
    "friendly": "Дружелюбный стиль общения, использующий простые объяснения и аналогии.",
    "casual": "Непринужденный, разговорный стиль с элементами юмора.",
    "brief": "Краткий и четкий стиль, фокусирующийся только на ключевой информации.",
}


def get_style_prefix(communication_style, content_type="general"):
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


class ContentUtils:
    """Совместимость: генераторы делают ContentUtils() / ContentUtils.COMMUNICATION_STYLES."""

    COMMUNICATION_STYLES = COMMUNICATION_STYLES

    def get_style_prefix(self, communication_style, content_type="general"):
        return get_style_prefix(communication_style, content_type)

```

**`llm_api_base.py`:**

```python
"""Базовый генератор контента: клиент LLM, retries, подготовка текста урока."""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime

from llm_route import chat_extra_body, create_openai_client, describe_llm_route

_NON_RETRYABLE_STATUS = {400: "Запрос отклонён сервером (400).", 401: "Неверный API-ключ или нет доступа (401). Проверьте ключ в .env.",
                         403: "Доступ запрещён (403). Проверьте ключ, регион и маршрут.", 404: "Модель или адрес API не найдены (404)."}


def non_retryable_api_error(exc: Exception) -> str:
    """Русское пояснение для ошибок, которые не лечатся повтором; "" — повторять можно.

    401/403/404/400 и нехватка квоты не пройдут со второй попытки.
    Таймауты, обрывы связи, 429 и 5xx повторяются как раньше.
    """
    status = getattr(exc, "status_code", None)
    if status is None:
        match = re.search(r"Error code:\s*(\d{3})", str(exc))
        status = int(match.group(1)) if match else None
    if status in _NON_RETRYABLE_STATUS:
        return _NON_RETRYABLE_STATUS[status]
    if "insufficient_quota" in str(exc).lower():
        return "Недостаточно средств или превышена квота API."
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
        self.llm_meta: dict = {}

        try:
            self.client, self.http_client, self.llm_meta = create_openai_client(
                self.api_key
            )
            self.logger.info(
                "%s: %s, модель %s",
                self.__class__.__name__,
                describe_llm_route(),
                self.model,
            )
        except Exception as e:
            self.logger.error(f"Ошибка при инициализации LLM-клиента: {str(e)}")
            raise

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
        Снимает одну внешнюю обёртку ``` вокруг всего ответа.

        Внутренние блоки кода не удаляет (раньше снимались все fences).
        """
        try:
            from student_content import unwrap_outer_fence

            text = unwrap_outer_fence(text)
            import textwrap

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

            extra = chat_extra_body(getattr(self, "llm_meta", None))
            if extra:
                kwargs["extra_body"] = extra

            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"Ошибка при запросе к LLM API: {str(e)}")
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
                fatal = non_retryable_api_error(e)
                if fatal:
                    # Повтор не поможет: ключ, права или запрос не изменятся.
                    self.logger.error(f"Запрос к LLM не повторяется: {str(e)}")
                    raise Exception(f"{fatal} Исходная ошибка: {str(e)}") from e
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

```

### B. Заменить `content_utils.py` фасадом (ещё полные публичные имена)

```python
"""Общие утилиты для генерации контента (совместимый фасад).

Реальная реализация разнесена по модулям:
``llm_json``, ``llm_api_base``, ``communication_style``, ``qa_response_utils``.
Импорты вида ``from content_utils import ...`` продолжают работать.
"""
from __future__ import annotations

# Реэкспорт клиента: FakeLLM патчит content_utils.create_openai_client.
# BaseContentGenerator живёт в llm_api_base и читает имя ОТТУДА —
# поэтому fake_llm.install() обязан патчить ОБА модуля (см. tests/fake_llm.py).
from llm_route import chat_extra_body, create_openai_client, describe_llm_route

from communication_style import COMMUNICATION_STYLES, ContentUtils, get_style_prefix
from llm_api_base import (
    BaseContentGenerator,
    non_retryable_api_error,
)
from llm_json import parse_llm_json
from qa_response_utils import append_question_reminder

__all__ = [
    "COMMUNICATION_STYLES",
    "ContentUtils",
    "BaseContentGenerator",
    "append_question_reminder",
    "parse_llm_json",
    "non_retryable_api_error",
    "get_style_prefix",
    "create_openai_client",
    "chat_extra_body",
    "describe_llm_route",
]

```

На 6b генераторы **ещё** импортируют из `content_utils` — так задумано.

### C. `tests/fake_llm.py` — метод `install`

Заменить тело `install` на патч **обоих** модулей (критично):

```python
    def install(self) -> None:
        """Подменяет создание клиента там, где его вызывает BaseContentGenerator.

        После сплита класс живёт в llm_api_base и читает create_openai_client
        из глобалов ЭТОГО модуля. Патч только content_utils не действует.
        """
        import content_utils
        import llm_api_base

        content_utils.create_openai_client = self.create_openai_client
        llm_api_base.create_openai_client = self.create_openai_client
```

### D. Проверки импорта (без циклов)

```bash
python -c "import llm_json, llm_api_base, communication_style, qa_response_utils, content_utils"
python -c "from content_utils import BaseContentGenerator, parse_llm_json, ContentUtils; from llm_api_base import BaseContentGenerator as B; assert BaseContentGenerator is B"
```

Ожидание: без traceback; `is B` истинно.

### E. Тесты, коммит, push

```bash
python -m pytest -q -rx
git add llm_json.py llm_api_base.py communication_style.py qa_response_utils.py \
  content_utils.py tests/fake_llm.py
git commit -m "6b: сплит content_utils с re-export; FakeLLM патчит llm_api_base"
bash .secrets/github_ssh/push_origin.sh
```

**Ожидание:** `162 passed, 1 deselected`.

**Отчёт:** SHA, pytest, подтверждение что scenario/LLM-тесты зелёные (не только unit).

---

## ЭТАП 6c. Импорты на новые модули

### A. Замены в генераторах (точный смысл)

| Файл | Было | Стало |
|---|---|---|
| `lesson_generator.py`, `qa_generator.py`, `explanation_generator.py`, `examples_generation.py` | `from content_utils import BaseContentGenerator, ContentUtils` | `from communication_style import ContentUtils` + `from llm_api_base import BaseContentGenerator` |
| `course_plan_generator.py`, `assessment_generator.py`, `relevance_checker.py` | `BaseContentGenerator, parse_llm_json` | `llm_api_base` + `llm_json` |
| `concepts_generator.py` | оба импорта (верх + внутри функции ContentUtils) | `llm_api_base`/`llm_json` + `from communication_style import ContentUtils` |
| `control_tasks_generator.py`, `examples_validation.py` | только BaseContentGenerator | `from llm_api_base import BaseContentGenerator` |
| `content_generator.py` | `append_question_reminder` | `from qa_response_utils import append_question_reminder` |

В корневых `*.py` после этапа **не** должно остаться `from content_utils import` / `import content_utils` (кроме самого `content_utils.py`):

```bash
rg -n "from content_utils import|import content_utils" -g '*.py' --glob '!tests/**' --glob '!doc/**'
# ожидается: только content_utils.py (если вообще; у фасада своих from content_utils нет) → пусто по корню
```

### B. Тесты

- `tests/unit/test_followup_state.py`: `parse_llm_json` ← `llm_json`
- `tests/unit/test_content_utils_characterization.py`: перевести на новые модули и **добавить** `test_content_utils_shim_still_reexports` (как в прототипе):

```python
"""Характеризация API после сплита content_utils (пакет 6)."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_parse_llm_json_plain_object():
    from llm_json import parse_llm_json

    assert parse_llm_json('{"a": 1, "b": [2]}') == {"a": 1, "b": [2]}


def test_parse_llm_json_fenced_and_surrounding_text():
    from llm_json import parse_llm_json

    fenced = """```json
{"ok": true, "n": 3}
```"""
    assert parse_llm_json(fenced) == {"ok": True, "n": 3}
    wrapped = 'Преамбула\n{"x": 7}\nхвост'
    assert parse_llm_json(wrapped) == {"x": 7}


def test_parse_llm_json_rejects_garbage():
    from llm_json import parse_llm_json

    with pytest.raises(ValueError):
        parse_llm_json("это не json")


def test_communication_styles_and_get_style_prefix():
    from communication_style import COMMUNICATION_STYLES, ContentUtils, get_style_prefix

    assert set(COMMUNICATION_STYLES) >= {"formal", "friendly", "casual", "brief"}
    utils = ContentUtils()
    examples = utils.get_style_prefix("friendly", "examples")
    assert "пример" in examples.lower() or "Примеры" in examples or "примеров" in examples.lower()
    qa = get_style_prefix("brief", "qa")
    assert "Краткий" in qa or "кратк" in qa.lower()
    assert get_style_prefix("friendly", "unknown_type") == ""


def test_append_question_reminder_threshold():
    from qa_response_utils import append_question_reminder

    base = "<p>ответ</p>"
    assert append_question_reminder(base, 3) == base
    with_note = append_question_reminder(base, 4)
    assert with_note.startswith(base)
    assert "продолжим обучение" in with_note


def test_non_retryable_api_error_by_status_and_quota():
    from llm_api_base import non_retryable_api_error

    class Exc(Exception):
        def __init__(self, code=None, msg="err"):
            super().__init__(msg)
            if code is not None:
                self.status_code = code

    assert "401" in non_retryable_api_error(Exc(401))
    assert "400" in non_retryable_api_error(Exc(400))
    assert non_retryable_api_error(Exc(msg="Error code: 403 boom"))
    assert "квот" in non_retryable_api_error(Exc(msg="insufficient_quota")).lower()
    assert non_retryable_api_error(Exc(429)) == ""
    assert non_retryable_api_error(Exc(500)) == ""


def test_extract_lesson_headers_order_and_strip_tags():
    from llm_api_base import BaseContentGenerator

    gen = BaseContentGenerator.__new__(BaseContentGenerator)
    html = "<h2>A</h2><p>x</p><h3><b>B</b></h3><h2>A</h2>"
    assert gen.extract_lesson_headers(html) == ["A", "B"]
    assert gen.extract_lesson_headers("") == []


def test_prepare_lesson_text_for_analysis_strips_breadcrumb():
    from llm_api_base import BaseContentGenerator

    gen = BaseContentGenerator.__new__(BaseContentGenerator)
    html = (
        "<style>.x{color:red}</style>"
        "<h1>Курс Python</h1>"
        "<h2>Раздел 1</h2>"
        "<h3>Тема A</h3>"
        "<h2>Тело урока</h2>"
        "<p>Важный текст про списки.</p>"
        "<script>alert(1)</script>"
    )
    ctx = {
        "course_title": "Курс Python",
        "section_title": "Раздел 1",
        "topic_title": "Тема A",
    }
    text = gen.prepare_lesson_text_for_analysis(
        html, course_context=ctx, lesson_title="Урок 1", max_chars=6000
    )
    assert "Важный текст про списки" in text
    assert "Тело урока" in text
    assert "alert" not in text
    assert "color:red" not in text
    assert not text.lower().startswith("курс python")


def test_content_utils_shim_still_reexports():
    """Старые импорты из content_utils не должны ломаться."""
    from content_utils import (
        BaseContentGenerator,
        ContentUtils,
        append_question_reminder,
        parse_llm_json,
    )
    from llm_api_base import BaseContentGenerator as BCG
    from communication_style import ContentUtils as CU

    assert BaseContentGenerator is BCG
    assert ContentUtils is CU
    assert parse_llm_json('{"z": 1}') == {"z": 1}
    assert append_question_reminder("<p>a</p>", 1) == "<p>a</p>"

```

### C. Утончить `content_utils.py` (deprecated shim)

```python
"""Устаревший фасад: re-export для старых импортов и ноутбуков.

Новый код должен импортировать из ``llm_json``, ``llm_api_base``,
``communication_style``, ``qa_response_utils``.
"""
from __future__ import annotations

from llm_route import chat_extra_body, create_openai_client, describe_llm_route

from communication_style import COMMUNICATION_STYLES, ContentUtils, get_style_prefix
from llm_api_base import BaseContentGenerator, non_retryable_api_error
from llm_json import parse_llm_json
from qa_response_utils import append_question_reminder

__all__ = [
    "COMMUNICATION_STYLES",
    "ContentUtils",
    "BaseContentGenerator",
    "append_question_reminder",
    "parse_llm_json",
    "non_retryable_api_error",
    "get_style_prefix",
    "create_openai_client",
    "chat_extra_body",
    "describe_llm_route",
]

```

### D. `tests/kernel_boot.py`

Перед `FAKE.install()` импортировать и `llm_api_base`, и `content_utils` (оба патчатся):

```python
"""Выполняется ВНУТРИ ядра Jupyter до ячейки TeachAI: подменяет LLM и ведёт журнал вызовов."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fake_llm import FakeLLM  # noqa: E402

import llm_api_base  # noqa: E402  — сюда BaseContentGenerator и create_openai_client
import content_utils  # noqa: E402  — устаревший фасад; FakeLLM патчит оба

FAKE = FakeLLM(log_path=Path(os.environ["TEACHAI_FAKE_LOG"]))
FAKE.install()

# Страховка: из ядра теста нельзя выйти в сеть.
import httpx  # noqa: E402


def _no_network(*args, **kwargs):
    raise AssertionError("тест пытался выйти в сеть из ядра")


httpx.Client.send = _no_network

```

### E. Тесты, коммит, push

```bash
python -c "import llm_json, llm_api_base, communication_style, qa_response_utils, content_utils"
# плюс выборочно генераторы:
python -c "import lesson_generator, control_tasks_generator, relevance_checker, examples_generation"
python -m pytest -q -rx
git add -u
git add tests/unit/test_content_utils_characterization.py
git commit -m "6c: импорты на llm_*; content_utils оставлен как deprecated shim"
bash .secrets/github_ssh/push_origin.sh
```

**Ожидание:** `163 passed, 1 deselected`.

**Отчёт:** SHA, pytest, пустой rg по корневым импортам `content_utils`.

---

## ЭТАП 6d. `*_checks.py` → `tests/legacy_checks/`

### A. Каталог и перенос

```bash
mkdir -p tests/legacy_checks
# пустой пакет:
printf '%s\n' '"""Legacy *_checks.py, раньше лежали в корне репозитория."""' > tests/legacy_checks/__init__.py
git mv *_checks.py tests/legacy_checks/
```

В **каждый** перенесённый файл сразу после `from __future__ import annotations` (он уже есть почти везде) вставь:

```python
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
```

Если `from __future__` нет — вставь блок после модульного docstring.  
`parents[2]`: `tests/legacy_checks/file.py` → корень репо.

Не дублируй `from __future__`. Если `Path`/`sys` уже импортированы ниже — допустим повторный import (безопасно) или аккуратно объедини.

### B. Заменить `tests/unit/test_legacy_checks.py` целиком

```python
"""Legacy *_checks.py из tests/legacy_checks/ — как есть, в изолированной среде.

Файлы не оставляем в корне; если проверка разошлась с кодом, правят её или код.
Запуск одного файла из корня репозитория:
  PYTHONPATH=. python tests/legacy_checks/course_portfolio_checks.py
"""
import importlib
import inspect
from pathlib import Path

import pytest

LEGACY = Path(__file__).resolve().parents[1] / "legacy_checks"
pytestmark = pytest.mark.unit

# Устаревшие проверки: сейчас таких нет. Если проверка разошлась с кодом, правьте её или код,
# а не добавляйте сюда запись без причины.
STALE: dict[str, str] = {}


def _cases():
    for path in sorted(LEGACY.glob("*_checks.py")):
        mod = importlib.import_module(f"tests.legacy_checks.{path.stem}")
        for name, fn in inspect.getmembers(mod, inspect.isfunction):
            if name.startswith("test_") and fn.__module__ == mod.__name__:
                case_id = f"{path.stem}::{name}"
                marks = []
                if case_id in STALE:
                    marks.append(
                        pytest.mark.xfail(
                            strict=True,
                            raises=AssertionError,
                            reason=STALE[case_id],
                        )
                    )
                yield pytest.param(fn, id=case_id, marks=marks)


@pytest.mark.parametrize("fn", list(_cases()))
def test_legacy_check(fn):
    fn()

```

### C. Проверка `__main__` с корня репо

```bash
PYTHONPATH=. python tests/legacy_checks/course_portfolio_checks.py
PYTHONPATH=. python tests/legacy_checks/relevance_prompt_checks.py
# все 13:
for f in tests/legacy_checks/*_checks.py; do PYTHONPATH=. python "$f" || exit 1; done
```

Ожидание: печать `OK …` / «Все проверки…», exit 0.

### D. Тесты, коммит, push

```bash
python -m pytest -q -rx
git add tests/legacy_checks tests/unit/test_legacy_checks.py
git add -u   # удаления из корня
git commit -m "6d: legacy *_checks.py перенесены в tests/legacy_checks"
bash .secrets/github_ssh/push_origin.sh
```

**Ожидание:** `163 passed, 1 deselected`.

**Отчёт:** SHA, pytest, что цикл `__main__` прошёл.

---

## ЭТАП 6e. Формулировки релевантности («в тексте или коде»)

Микро-этап, отдельный коммит. System и user в `relevance_checker.py` говорили по-разному («в коде» vs «в тексте и коде»). Выровнять на **«в тексте или коде»**.

### A. `relevance_checker.py`

1. System (около L96):  
   `что урок вводит или показывает в коде,`  
   → `что урок вводит или показывает в тексте или коде,`

2. User prompt (около L379):  
   `… показывает в тексте и коде.`  
   → `… показывает в тексте или коде.`

### B. `tests/legacy_checks/relevance_prompt_checks.py`

Добавь assert (рядом с «в основном опирается»):

```python
    assert "в тексте или коде" in lowered
```

Старые assert оставь; они должны пройти.

### C. Тесты, коммит, push

```bash
PYTHONPATH=. python tests/legacy_checks/relevance_prompt_checks.py
python -m pytest -q -rx
git add relevance_checker.py tests/legacy_checks/relevance_prompt_checks.py
git commit -m "6e: релевантность — единая формулировка «в тексте или коде»"
bash .secrets/github_ssh/push_origin.sh
```

**Ожидание:** `163 passed, 1 deselected`.

**Отчёт:** SHA, pytest, что в `relevance_checker.py` больше нет «в тексте и коде».

---

## Чеклист приёмки пакета 6

- [ ] Нет `BASE_CSS_*` / `EXAMPLES_CSS_*` / `EXPLANATION_CSS_*` в runtime `.py`
- [ ] Нет `code_formatter.py`
- [ ] Есть `llm_json.py`, `llm_api_base.py`, `communication_style.py`, `qa_response_utils.py`
- [ ] `content_utils.py` — короткий deprecated shim
- [ ] `FakeLLM.install` патчит `llm_api_base` и `content_utils`
- [ ] Корневые генераторы не импортируют `content_utils`
- [ ] 13 checks в `tests/legacy_checks/`, `__main__` через `PYTHONPATH=. python tests/legacy_checks/…`
- [ ] Релевантность: «в тексте или коде» в system и user
- [ ] Полный pytest: **163 passed, 1 deselected**
