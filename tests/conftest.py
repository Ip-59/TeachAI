from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

FAKE_KEY = "sk-test-not-a-real-key"


@pytest.fixture(autouse=True, scope="session")
def real_data_untouched():
    """Страховка: реальные data/state.json и .env проекта тестами не меняются."""
    def snap():
        return {p: (p.stat().st_mtime_ns, p.stat().st_size) for p in
                [ROOT / "data" / "state.json", ROOT / ".env", ROOT / ".env.sample"] if p.exists()}
    before = snap()
    yield
    assert snap() == before, "тесты изменили реальные файлы проекта"


@pytest.fixture(autouse=True)
def no_network(monkeypatch, request):
    """Любой реальный HTTP-запрос в тесте — ошибка (кроме тестов с маркером live)."""
    if request.node.get_closest_marker("live"):
        return
    import httpx

    def boom(*a, **k):
        raise AssertionError("тест пытался выйти в сеть")

    monkeypatch.setattr(httpx.Client, "send", boom)


@pytest.fixture(autouse=True)
def isolated_project(tmp_path, monkeypatch):
    """Каждый тест живёт во временной папке: ни data/state.json, ни logs, ни .env проекта не трогаются."""
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)  # logs/, data/llm_route_preference.json, debug_responses/ — относительные пути
    (work / ".env").write_text(f"OPENAI_API_KEY={FAKE_KEY}\nOPENAI_API_ROUTE=direct\n", encoding="utf-8")
    for var in ("OPENAI_PROXY", "HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy",
                "ALL_PROXY", "all_proxy", "GPTUNNEL_API_KEY", "OPENAI_USE_PROXY", "OPENAI_CONNECTION_MODE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    monkeypatch.setenv("OPENAI_API_ROUTE", "direct")
    # StateManager строит путь как <папка модуля>/<state_file>; абсолютный путь это обходит.
    import state_manager

    state_file = str(work / "data" / "state.json")
    monkeypatch.setattr(state_manager.StateManager.__init__, "__defaults__", (state_file,))
    yield work


@pytest.fixture
def fake_llm():
    from fake_llm import FakeLLM

    fake = FakeLLM()
    fake.install()
    return fake
