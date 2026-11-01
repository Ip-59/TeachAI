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
