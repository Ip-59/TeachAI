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
