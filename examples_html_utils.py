"""Утилиты парсинга и рендеринга HTML-примеров для уроков."""

from __future__ import annotations

import html
import json
import re
from typing import Any, Dict, List, Tuple


STUB_PHRASES = (
    "в этом примере мы",
    "здесь мы создадим",
    "давайте создадим",
    "мы создадим",
    "будем использовать",
    "рассмотрим пример",
)


def strip_examples_wrapper(text: str) -> str:
    """Убирает обёртку стилей, чтобы валидировать только содержимое примеров."""
    cleaned = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(
        r'<div class="examples-visible"[^>]*>',
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"</div>\s*$", "", cleaned.strip(), flags=re.IGNORECASE)
    return cleaned.strip()


def normalize_markdown_fences_to_html(text: str) -> str:
    """Преобразует markdown-блоки ```python в <pre><code>."""

    def _replace_fence(match: re.Match) -> str:
        code = match.group(1).strip()
        return f"<pre><code>{html.escape(code)}</code></pre>"

    pattern = r"```(?:python|py)?\s*\n([\s\S]*?)```"
    return re.sub(pattern, _replace_fence, text)


def extract_code_blocks_from_html(text: str) -> List[str]:
    """Извлекает Python-код из HTML."""
    blocks: List[str] = []
    for match in re.finditer(r"<pre><code>([\s\S]*?)</code></pre>", text, re.IGNORECASE):
        code = html.unescape(match.group(1))
        code = re.sub(r"<.*?>", "", code).strip()
        if code:
            blocks.append(code)
    return blocks


def extract_titles_and_texts(text: str) -> List[Tuple[str | None, str | None]]:
    """Извлекает пары (заголовок, пояснение) из HTML."""
    blocks: List[Tuple[str | None, str | None]] = []
    pattern = re.compile(r"(<h[34]>.*?</h[34]>|<p>.*?</p>)", re.DOTALL | re.IGNORECASE)
    matches = list(pattern.finditer(text))
    i = 0
    while i < len(matches):
        current = matches[i].group(0)
        if re.match(r"<h[34]>", current, re.IGNORECASE):
            title = re.sub(r"<.*?>", "", current).strip()
            desc = None
            if i + 1 < len(matches) and re.match(r"<p>", matches[i + 1].group(0), re.IGNORECASE):
                desc = re.sub(r"<.*?>", "", matches[i + 1].group(0)).strip()
                i += 2
            else:
                i += 1
            blocks.append((title, desc))
        elif re.match(r"<p>", current, re.IGNORECASE):
            desc = re.sub(r"<.*?>", "", current).strip()
            blocks.append((None, desc))
            i += 1
        else:
            i += 1
    return blocks


def is_stub_only_description(text: str) -> bool:
    """True, если текст — заглушка без реального кода."""
    lower = text.lower()
    return any(phrase in lower for phrase in STUB_PHRASES)


def count_meaningful_code_blocks(text: str, min_lines: int = 3) -> int:
    """Считает блоки кода с достаточным количеством строк."""
    count = 0
    for block in extract_code_blocks_from_html(text):
        lines = [line for line in block.splitlines() if line.strip() and not line.strip().startswith("#")]
        if len(lines) >= min_lines:
            count += 1
    return count


def has_runnable_examples(text: str, min_blocks: int = 3, min_lines: int = 3) -> bool:
    """Проверяет, что в ответе есть исполняемые блоки кода."""
    return count_meaningful_code_blocks(text, min_lines=min_lines) >= min_blocks


def contains_forbidden_non_python_code(text: str) -> bool:
    """Ищет явный JavaScript/HTML-код внутри блоков Python, не в разметке."""
    for block in extract_code_blocks_from_html(text):
        lower = block.lower()
        forbidden = (
            "document.",
            "function(",
            "var ",
            "let ",
            "const ",
            "<html",
            "<script",
            "onclick",
        )
        if any(item in lower for item in forbidden):
            return True
    return False


def render_examples_json_to_html(payload: Dict[str, Any]) -> str:
    """Рендерит JSON с примерами в HTML с гарантированными блоками кода."""
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


def normalize_examples_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Нормализует JSON-ответ LLM: только примеры с непустым code."""
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
    """Проверяет структуру JSON до рендеринга.

    Главный критерий — наличие исполняемого кода. Текст в description
    не блокирует пример: даже если он начинается со слов «В этом примере мы...»,
    при наличии рабочего code пример считается валидным. Заглушечные
    фразы будут удалены из description на этапе нормализации.
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


def parse_examples_json_response(response: str) -> Dict[str, Any]:
    """Парсит JSON-ответ LLM с примерами."""
    start = response.find("{")
    end = response.rfind("}") + 1
    if start == -1 or end <= start:
        raise ValueError("JSON с примерами не найден")
    return json.loads(response[start:end])


def extract_example_sections(text: str) -> List[Dict[str, str]]:
    """Извлекает секции примеров (title, description, code) из HTML."""
    content = strip_examples_wrapper(text)
    codes = extract_code_blocks_from_html(content)
    meta = [(title, desc) for title, desc in extract_titles_and_texts(content) if title]
    sections: List[Dict[str, str]] = []
    for index, code in enumerate(codes):
        title = f"Пример {index + 1}"
        description = ""
        if index < len(meta):
            title = meta[index][0] or title
            description = meta[index][1] or ""
        sections.append({"title": title, "description": description, "code": code})
    return sections
