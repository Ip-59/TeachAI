"""Маршрут API из ноутбука: приоритет, клиент, сброс, дашборд без выбора."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.unit

FAKE_KEY = "sk-test-not-a-real-key"
GT_KEY = "gt-test-not-a-real-key"
PROXY_URL = "http://127.0.0.1:9"
LEAK = "token-should-not-appear-in-output"


@pytest.fixture(autouse=True)
def _reset_notebook_route_state():
    import llm_route

    llm_route._explicit_notebook_route = None
    llm_route._notebook_env_snapshot = None
    yield
    llm_route._explicit_notebook_route = None
    llm_route._notebook_env_snapshot = None


@pytest.fixture(autouse=True)
def _only_temp_dotenv(monkeypatch, isolated_project):
    """load_dotenv в тестах читает только временный .env, не файл проекта."""
    from dotenv import load_dotenv as real_load

    root = isolated_project.resolve()

    def _load(*args: Any, **kwargs: Any) -> bool:
        override = bool(kwargs.get("override", False))
        if args and args[0] is not None:
            path = Path(args[0])
            if not path.is_absolute():
                path = root / path
            resolved = path.resolve()
            if resolved != root and root not in resolved.parents:
                raise AssertionError("тест пытался прочитать .env вне временной папки")
        else:
            resolved = root / ".env"
        return bool(real_load(resolved, override=override))

    monkeypatch.setattr("run_teachai.load_dotenv", _load)
    monkeypatch.setattr("config.load_dotenv", _load)
    monkeypatch.setattr("dotenv.load_dotenv", _load)


@pytest.fixture
def started(monkeypatch):
    """Подмена движка: start_jupyter не строит учебный UI и не ходит в сеть."""
    created = {"n": 0}

    class Engine:
        def __init__(self) -> None:
            created["n"] += 1

        def initialize(self) -> bool:
            return True

        def start(self) -> str:
            return "dashboard"

    monkeypatch.setattr("engine.TeachAIEngine", Engine)
    return created


def _write_env(work: Path, text: str) -> None:
    (work / ".env").write_text(text, encoding="utf-8")


def _preference(work: Path, route: str) -> Path:
    path = work / "data" / "llm_route_preference.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"route": route}) + "\n", encoding="utf-8")
    return path


def _same_key(actual: str, expected: str) -> None:
    if actual != expected:
        raise AssertionError("клиент взял ключ не из ожидаемой переменной")


def _client_facts() -> dict[str, Any]:
    from llm_route import create_openai_client

    client, http_client, meta = create_openai_client()
    try:
        proxy_urls: list[str] = []
        for transport in getattr(http_client, "_mounts", {}).values():
            pool = getattr(transport, "_pool", None)
            proxy_url = getattr(pool, "_proxy_url", None)
            if proxy_url is not None:
                proxy_urls.append(str(proxy_url))
        hooks = [
            getattr(hook, "__name__", "")
            for hook in http_client.event_hooks.get("request", [])
        ]
        return {
            "api_key": client.api_key,
            "base_url": str(client.base_url),
            "route": meta.get("route"),
            "wallet": bool(meta.get("use_wallet_balance")),
            "proxy_urls": proxy_urls,
            "hooks": hooks,
        }
    finally:
        client.close()
        http_client.close()


def _forbid_client(monkeypatch) -> dict[str, int]:
    calls = {"n": 0}

    def boom(*_args: Any, **_kwargs: Any) -> None:
        calls["n"] += 1
        raise AssertionError("клиент не должен создаваться")

    monkeypatch.setattr("llm_route.create_openai_client", boom)
    return calls


def test_none_without_env_or_preference_uses_direct(
    isolated_project, monkeypatch, started
):
    monkeypatch.delenv("OPENAI_API_ROUTE", raising=False)
    monkeypatch.delenv("OPENAI_USE_PROXY", raising=False)
    monkeypatch.delenv("OPENAI_CONNECTION_MODE", raising=False)
    _write_env(isolated_project, f"OPENAI_API_KEY={FAKE_KEY}\n")

    from run_teachai import start_jupyter

    assert start_jupyter(api_route=None) == "dashboard"
    facts = _client_facts()
    assert facts["route"] == "direct"
    _same_key(facts["api_key"], FAKE_KEY)
    assert "api.openai.com" in facts["base_url"]
    assert facts["proxy_urls"] == []
    assert facts["wallet"] is False


def test_none_keeps_env_over_preference(isolated_project, monkeypatch, started):
    monkeypatch.setenv("OPENAI_API_ROUTE", "gptunnel")
    monkeypatch.setenv("GPTUNNEL_API_KEY", GT_KEY)
    _write_env(
        isolated_project,
        f"OPENAI_API_KEY={FAKE_KEY}\nOPENAI_API_ROUTE=gptunnel\nGPTUNNEL_API_KEY={GT_KEY}\n",
    )
    _preference(isolated_project, "direct")

    from run_teachai import start_jupyter

    assert start_jupyter(api_route=None) == "dashboard"
    facts = _client_facts()
    assert facts["route"] == "gptunnel"
    _same_key(facts["api_key"], GT_KEY)
    assert "gptunnel.ru" in facts["base_url"]
    assert facts["wallet"] is True
    assert "_strip_bearer_hook" in facts["hooks"]


def test_none_uses_preference_when_env_route_absent(
    isolated_project, monkeypatch, started
):
    monkeypatch.delenv("OPENAI_API_ROUTE", raising=False)
    monkeypatch.delenv("OPENAI_USE_PROXY", raising=False)
    monkeypatch.delenv("OPENAI_CONNECTION_MODE", raising=False)
    monkeypatch.setenv("OPENAI_PROXY", PROXY_URL)
    _write_env(
        isolated_project,
        f"OPENAI_API_KEY={FAKE_KEY}\nOPENAI_PROXY={PROXY_URL}\n",
    )
    _preference(isolated_project, "proxy")

    from run_teachai import start_jupyter

    assert start_jupyter(api_route=None) == "dashboard"
    facts = _client_facts()
    assert facts["route"] == "proxy"
    _same_key(facts["api_key"], FAKE_KEY)
    assert "api.openai.com" in facts["base_url"]
    assert any("127.0.0.1" in url for url in facts["proxy_urls"])


def test_none_uses_legacy_use_proxy_flag(isolated_project, monkeypatch, started):
    monkeypatch.delenv("OPENAI_API_ROUTE", raising=False)
    monkeypatch.delenv("OPENAI_CONNECTION_MODE", raising=False)
    monkeypatch.setenv("OPENAI_USE_PROXY", "true")
    monkeypatch.setenv("OPENAI_PROXY", PROXY_URL)
    _write_env(
        isolated_project,
        f"OPENAI_API_KEY={FAKE_KEY}\nOPENAI_USE_PROXY=true\nOPENAI_PROXY={PROXY_URL}\n",
    )

    from run_teachai import start_jupyter

    assert start_jupyter(api_route=None) == "dashboard"
    facts = _client_facts()
    assert facts["route"] == "proxy"
    assert any("127.0.0.1" in url for url in facts["proxy_urls"])


def test_explicit_routes_configure_client(isolated_project, monkeypatch, started):
    monkeypatch.setenv("GPTUNNEL_API_KEY", GT_KEY)
    monkeypatch.setenv("OPENAI_PROXY", PROXY_URL)
    _write_env(
        isolated_project,
        f"OPENAI_API_KEY={FAKE_KEY}\nGPTUNNEL_API_KEY={GT_KEY}\nOPENAI_API_ROUTE=direct\n",
    )
    from run_teachai import start_jupyter

    assert start_jupyter(api_route="direct") == "dashboard"
    direct = _client_facts()
    assert direct["route"] == "direct"
    _same_key(direct["api_key"], FAKE_KEY)
    assert "api.openai.com" in direct["base_url"]
    assert direct["proxy_urls"] == []

    assert start_jupyter(api_route="gptunnel") == "dashboard"
    tunnel = _client_facts()
    assert tunnel["route"] == "gptunnel"
    _same_key(tunnel["api_key"], GT_KEY)
    assert "gptunnel.ru" in tunnel["base_url"]
    assert tunnel["wallet"] is True

    assert start_jupyter(api_route="proxy") == "dashboard"
    proxied = _client_facts()
    assert proxied["route"] == "proxy"
    _same_key(proxied["api_key"], FAKE_KEY)
    assert "api.openai.com" in proxied["base_url"]
    assert any("127.0.0.1" in url for url in proxied["proxy_urls"])


def test_dotenv_override_does_not_beat_explicit_route(
    isolated_project, monkeypatch, started
):
    monkeypatch.setenv("GPTUNNEL_API_KEY", GT_KEY)
    _write_env(
        isolated_project,
        f"OPENAI_API_KEY={FAKE_KEY}\nOPENAI_API_ROUTE=direct\nGPTUNNEL_API_KEY={GT_KEY}\n",
    )
    from config import apply_openai_connection_environment
    from llm_route import get_llm_route
    from run_teachai import load_dotenv, start_jupyter

    assert start_jupyter(api_route="gptunnel") == "dashboard"
    load_dotenv(override=True)
    assert get_llm_route() == "gptunnel"
    apply_openai_connection_environment()
    assert get_llm_route() == "gptunnel"
    import os

    assert os.environ["OPENAI_API_ROUTE"] == "gptunnel"
    facts = _client_facts()
    assert facts["route"] == "gptunnel"
    _same_key(facts["api_key"], GT_KEY)
    assert "gptunnel.ru" in facts["base_url"]


@pytest.mark.parametrize("bad", ["vpn", "openai", "DIRECT", "proxy ", "", LEAK, 1])
def test_invalid_route_is_error_and_skips_client(
    isolated_project, monkeypatch, started, capsys, bad
):
    monkeypatch.setenv("GPTUNNEL_API_KEY", GT_KEY)
    _write_env(
        isolated_project,
        f"OPENAI_API_KEY={FAKE_KEY}\nOPENAI_API_ROUTE=gptunnel\nGPTUNNEL_API_KEY={GT_KEY}\n",
    )
    calls = _forbid_client(monkeypatch)
    from llm_route import get_llm_route
    from run_teachai import start_jupyter

    assert start_jupyter(api_route=bad) is None
    out = capsys.readouterr().out
    assert "API_ROUTE" in out
    assert LEAK not in out
    assert calls["n"] == 0
    assert started["n"] == 0
    assert get_llm_route() == "gptunnel"


@pytest.mark.parametrize(
    ("route", "missing"),
    [
        ("gptunnel", "GPTUNNEL_API_KEY"),
        ("direct", "OPENAI_API_KEY"),
        ("proxy", "OPENAI_PROXY"),
    ],
)
def test_missing_credentials_name_variable_only(
    isolated_project, monkeypatch, started, capsys, route, missing
):
    monkeypatch.delenv("GPTUNNEL_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_PROXY", raising=False)
    if route == "direct":
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        _write_env(isolated_project, "OPENAI_API_ROUTE=direct\n")
    else:
        _write_env(isolated_project, f"OPENAI_API_KEY={FAKE_KEY}\nOPENAI_API_ROUTE=direct\n")
    calls = _forbid_client(monkeypatch)
    from run_teachai import start_jupyter

    assert start_jupyter(api_route=route) is None
    out = capsys.readouterr().out
    assert missing in out
    assert FAKE_KEY not in out
    assert GT_KEY not in out
    assert calls["n"] == 0
    assert started["n"] == 0


def test_second_start_builds_client_for_new_route(
    isolated_project, monkeypatch, started
):
    monkeypatch.setenv("GPTUNNEL_API_KEY", GT_KEY)
    monkeypatch.setenv("OPENAI_PROXY", PROXY_URL)
    _write_env(
        isolated_project,
        f"OPENAI_API_KEY={FAKE_KEY}\nGPTUNNEL_API_KEY={GT_KEY}\nOPENAI_API_ROUTE=direct\n",
    )
    from run_teachai import start_jupyter

    assert start_jupyter(api_route="gptunnel") == "dashboard"
    first = _client_facts()
    _same_key(first["api_key"], GT_KEY)
    assert "gptunnel.ru" in first["base_url"]

    assert start_jupyter(api_route="proxy") == "dashboard"
    second = _client_facts()
    assert second["route"] == "proxy"
    _same_key(second["api_key"], FAKE_KEY)
    assert "api.openai.com" in second["base_url"]
    assert any("127.0.0.1" in url for url in second["proxy_urls"])


def test_none_after_explicit_drops_stale_route(isolated_project, monkeypatch, started):
    monkeypatch.delenv("OPENAI_API_ROUTE", raising=False)
    monkeypatch.delenv("OPENAI_USE_PROXY", raising=False)
    monkeypatch.delenv("OPENAI_CONNECTION_MODE", raising=False)
    monkeypatch.setenv("OPENAI_PROXY", PROXY_URL)
    monkeypatch.setenv("GPTUNNEL_API_KEY", GT_KEY)
    _write_env(
        isolated_project,
        f"OPENAI_API_KEY={FAKE_KEY}\nGPTUNNEL_API_KEY={GT_KEY}\nOPENAI_PROXY={PROXY_URL}\n",
    )
    _preference(isolated_project, "proxy")
    from run_teachai import start_jupyter

    assert start_jupyter(api_route="gptunnel") == "dashboard"
    assert _client_facts()["route"] == "gptunnel"
    assert start_jupyter(api_route=None) == "dashboard"
    facts = _client_facts()
    assert facts["route"] == "proxy"
    _same_key(facts["api_key"], FAKE_KEY)
    assert any("127.0.0.1" in url for url in facts["proxy_urls"])


def test_explicit_route_does_not_write_preference_or_env(
    isolated_project, monkeypatch, started
):
    monkeypatch.setenv("GPTUNNEL_API_KEY", GT_KEY)
    _write_env(
        isolated_project,
        f"OPENAI_API_KEY={FAKE_KEY}\nOPENAI_API_ROUTE=direct\nGPTUNNEL_API_KEY={GT_KEY}\n",
    )
    pref = _preference(isolated_project, "direct")
    env_before = (isolated_project / ".env").read_bytes()
    pref_before = pref.read_bytes()
    from run_teachai import start_jupyter

    assert start_jupyter(api_route="gptunnel") == "dashboard"
    assert (isolated_project / ".env").read_bytes() == env_before
    assert pref.read_bytes() == pref_before
    assert _client_facts()["route"] == "gptunnel"


def test_dashboard_has_no_route_selector():
    from helpers import make_state
    from startup_dashboard import StartupDashboard

    dashboard = StartupDashboard(make_state(), None)
    widget = dashboard.show_dashboard()
    assert not hasattr(dashboard, "route_selector")

    texts: list[str] = []
    radios: list[object] = []

    def walk(node: object) -> None:
        if type(node).__name__ == "RadioButtons":
            radios.append(node)
        for attr in ("value", "description"):
            raw = getattr(node, attr, None)
            if isinstance(raw, str):
                texts.append(raw)
        for child in getattr(node, "children", ()) or ():
            walk(child)

    walk(widget)
    blob = "\n".join(texts)
    assert "Маршрут" not in blob
    assert "GPTunnel" not in blob
    assert radios == []
    assert "Продолжить обучение" in blob


def test_cli_main_still_starts_without_notebook_route(started, capsys):
    from run_teachai import main

    main()
    out = capsys.readouterr().out
    assert "Интерфейс создан успешно" in out
    assert started["n"] == 1
