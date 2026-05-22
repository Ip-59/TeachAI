"""Утилиты для JSON-формата примеров и одностороннего рендера в HTML.

Внутри проекта примеры передаются как list[dict] {"title", "description", "code"}.
Этот модуль содержит:
  * парсинг JSON-ответа LLM и его валидацию,
  * нормализацию примеров (фильтрация мусора, очистка заглушек),
  * односторонний рендер JSON → HTML для финального вывода
    в местах, где интерфейс ещё работает на HTML-строках.

Обратного парсинга HTML здесь нет — он не нужен и был источником
повторяющихся багов (потеря отступов, повреждение `<`/`>` в коде).
"""

from __future__ import annotations

import html
import json
from typing import Any, Dict, List


STUB_PHRASES = (
    "в этом примере мы",
    "здесь мы создадим",
    "давайте создадим",
    "мы создадим",
    "будем использовать",
    "рассмотрим пример",
)


def is_stub_only_description(text: str) -> bool:
    """True, если описание — заглушка («в этом примере мы создадим…»)."""
    lower = (text or "").lower()
    return any(phrase in lower for phrase in STUB_PHRASES)


def looks_like_python_code(code: str) -> bool:
    """Проверяет, что строка похожа на исполняемый Python-код."""
    text = (code or "").strip()
    if not text:
        return False
    if text.startswith("<"):
        return False
    python_markers = (
        "print(",
        "import ",
        "from ",
        "def ",
        "class ",
        "for ",
        "while ",
        "if ",
        "return ",
        "=",
        "range(",
    )
    return any(marker in text for marker in python_markers)


def parse_examples_json_response(response: str) -> Dict[str, Any]:
    """Парсит JSON-ответ LLM с примерами."""
    start = response.find("{")
    end = response.rfind("}") + 1
    if start == -1 or end <= start:
        raise ValueError("JSON с примерами не найден")
    return json.loads(response[start:end])


def normalize_examples_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Нормализует JSON-ответ LLM: только примеры с непустым исполняемым code.

    Описания, состоящие только из «заглушечных» фраз вроде
    «в этом примере мы создадим…», очищаются (заменяются пустой строкой),
    но сам пример сохраняется, если код валиден.
    """
    examples = payload.get("examples") or []
    if isinstance(examples, dict):
        examples = [examples]
    normalized: List[Dict[str, str]] = []
    for index, item in enumerate(examples, start=1):
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or item.get("content") or "").strip()
        if not code or not looks_like_python_code(code):
            continue
        description = str(item.get("description") or "").strip()
        if is_stub_only_description(description):
            description = ""
        normalized.append(
            {
                "title": str(item.get("title") or f"Пример {index}").strip(),
                "description": description,
                "code": code,
            }
        )
    return {"examples": normalized}


def validate_examples_payload(payload: Dict[str, Any], min_examples: int = 3) -> None:
    """Проверяет структуру JSON до нормализации.

    Главный критерий — наличие исполняемого кода. Текст в description
    не блокирует пример: «заглушечные» фразы в описании будут удалены
    на этапе нормализации.

    Raises:
        ValueError: Если структура некорректна или примеров недостаточно.
    """
    raw_examples = payload.get("examples") or []
    if isinstance(raw_examples, dict):
        raw_examples = [raw_examples]

    for index, item in enumerate(raw_examples, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Пример {index} должен быть объектом JSON")
        code = str(item.get("code") or item.get("content") or "").strip()
        if not looks_like_python_code(code):
            raise ValueError(
                f"Пример '{item.get('title', index)}' не содержит рабочий Python-код"
            )

    normalized = normalize_examples_payload(payload)
    if len(normalized["examples"]) < min_examples:
        raise ValueError(
            f"JSON должен содержать минимум {min_examples} примеров с полем code"
        )
    for example in normalized["examples"]:
        lines = [
            line
            for line in example["code"].splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if len(lines) < 2:
            raise ValueError(f"Пример '{example['title']}' содержит слишком мало кода")


def render_examples_json_to_html(payload: Dict[str, Any]) -> str:
    """Один из двух единственно допустимых преобразований: JSON → HTML (для вывода).

    Используется только когда консьюмеру нужна HTML-строка (legacy UI).
    Никогда не должна вызываться внутри пайплайна между этапами обработки —
    это привело бы к ненужному round-trip через HTML.
    """
    parts: List[str] = []
    for index, example in enumerate(payload.get("examples", []), start=1):
        title = str(example.get("title") or f"Пример {index}").strip()
        description = str(example.get("description") or "").strip()
        code = str(example.get("code") or "").strip()
        if not code:
            continue
        parts.append('<div class="example-block">')
        parts.append(f"<h3>{html.escape(title)}</h3>")
        if description:
            parts.append(f"<p>{html.escape(description)}</p>")
        parts.append(f"<pre><code>{html.escape(code)}</code></pre>")
        parts.append("</div>")
    return "\n".join(parts)
