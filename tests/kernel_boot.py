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
