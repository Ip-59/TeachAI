"""
Маршрут LLM для TeachAI: прямой OpenAI или шлюз GPTunnel.

Источник истины — ``OPENAI_API_ROUTE`` в .env (или сессионный override).
Кнопка на дашборде только переключает маршрут до инициализации клиентов.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Literal

import httpx
from openai import OpenAI

logger = logging.getLogger(__name__)

LlmRoute = Literal["direct", "gptunnel", "proxy"]

_DEFAULT_GPTUNNEL_BASE = "https://gptunnel.ru/v1"
_PREFERENCE_FILE = Path("data") / "llm_route_preference.json"

_PROXY_ENV_KEYS = (
    "OPENAI_PROXY",
    "HTTPS_PROXY",
    "HTTP_PROXY",
    "https_proxy",
    "http_proxy",
)
_PROXY_ENV_KEYS_TO_CLEAR = _PROXY_ENV_KEYS + (
    "ALL_PROXY",
    "all_proxy",
    "NO_PROXY",
    "no_proxy",
)


def _read_proxy_url() -> str | None:
    for key in _PROXY_ENV_KEYS:
        value = (os.getenv(key) or "").strip()
        if value and not value.startswith("${"):
            return value
    return None


def get_llm_route() -> LlmRoute:
    """
    Активный маршрут к LLM.

    Приоритет: ``OPENAI_API_ROUTE`` → совместимость с ``OPENAI_CONNECTION_MODE``
    (``proxy`` / ``gptunnel``) → иначе ``direct``.
    """
    raw = (os.getenv("OPENAI_API_ROUTE") or "").strip().lower()
    if raw in ("direct", "openai", "vpn"):
        return "direct"
    if raw in ("gptunnel", "gateway", "tunnel"):
        return "gptunnel"
    if raw in ("proxy", "http_proxy"):
        return "proxy"

    # Совместимость со старым OPENAI_CONNECTION_MODE / OPENAI_USE_PROXY
    use_proxy = (os.getenv("OPENAI_USE_PROXY") or "").strip().lower()
    if use_proxy in ("true", "1", "yes", "on"):
        return "proxy"

    conn = (os.getenv("OPENAI_CONNECTION_MODE") or "").strip().lower()
    if conn in ("proxy", "http_proxy"):
        return "proxy"
    if conn in ("gptunnel", "gateway", "tunnel"):
        return "gptunnel"

    return "direct"


def set_llm_route(route: str, *, persist: bool = True) -> LlmRoute:
    """
    Устанавливает маршрут для текущего процесса (и опционально в файл).

    Args:
        route: ``direct`` | ``gptunnel`` | ``proxy``.
        persist: Сохранить выбор в ``data/llm_route_preference.json``.

    Returns:
        Нормализованный маршрут.
    """
    normalized = (route or "").strip().lower()
    if normalized in ("openai", "vpn"):
        normalized = "direct"
    if normalized in ("gateway", "tunnel"):
        normalized = "gptunnel"
    if normalized not in ("direct", "gptunnel", "proxy"):
        raise ValueError(f"Неизвестный маршрут LLM: {route!r}")

    os.environ["OPENAI_API_ROUTE"] = normalized
    # Держим OPENAI_CONNECTION_MODE согласованным для старого кода/логов
    if normalized == "proxy":
        os.environ["OPENAI_CONNECTION_MODE"] = "proxy"
        os.environ["OPENAI_USE_PROXY"] = "true"
    else:
        os.environ["OPENAI_CONNECTION_MODE"] = (
            "gptunnel" if normalized == "gptunnel" else "direct"
        )
        os.environ["OPENAI_USE_PROXY"] = "false"
        for key in _PROXY_ENV_KEYS_TO_CLEAR:
            os.environ.pop(key, None)

    if persist:
        save_route_preference(normalized)

    logger.info("Маршрут LLM установлен: %s", normalized)
    return normalized  # type: ignore[return-value]


def save_route_preference(route: str) -> None:
    """Пишет выбранный маршрут на диск (между запусками Jupyter)."""
    try:
        _PREFERENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _PREFERENCE_FILE.write_text(
            json.dumps({"route": route}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning("Не удалось сохранить llm_route_preference: %s", exc)


def load_route_preference() -> str | None:
    """Читает сохранённый маршрут или None."""
    try:
        if not _PREFERENCE_FILE.is_file():
            return None
        data = json.loads(_PREFERENCE_FILE.read_text(encoding="utf-8"))
        route = (data.get("route") or "").strip().lower()
        return route if route in ("direct", "gptunnel", "proxy") else None
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def apply_saved_route_preference() -> LlmRoute:
    """
    Если в .env нет явного OPENAI_API_ROUTE — подставить preference с диска.

    Явный .env всегда побеждает.
    """
    if (os.getenv("OPENAI_API_ROUTE") or "").strip():
        return get_llm_route()
    saved = load_route_preference()
    if saved:
        return set_llm_route(saved, persist=False)
    return get_llm_route()


def get_gptunnel_base_url() -> str:
    """Базовый URL GPTunnel (OpenAI-совместимый /v1)."""
    return (os.getenv("GPTUNNEL_BASE_URL") or _DEFAULT_GPTUNNEL_BASE).rstrip("/")


def get_llm_api_key() -> str | None:
    """Ключ для активного маршрута."""
    route = get_llm_route()
    if route == "gptunnel":
        key = (os.getenv("GPTUNNEL_API_KEY") or "").strip()
        if not key:
            logger.error("Маршрут gptunnel, но GPTUNNEL_API_KEY не задан")
            return None
        return key

    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not key:
        logger.error("OPENAI_API_KEY не найден")
        return None
    return key


def validate_llm_credentials() -> tuple[bool, str]:
    """
    Проверяет наличие ключей/прокси для текущего маршрута.

    Returns:
        (ok, сообщение_об_ошибке_или_пусто).
    """
    route = get_llm_route()
    if route == "gptunnel":
        if not (os.getenv("GPTUNNEL_API_KEY") or "").strip():
            return False, "OPENAI_API_ROUTE=gptunnel, но GPTUNNEL_API_KEY не задан в .env"
        return True, ""
    if route == "proxy":
        if not (os.getenv("OPENAI_API_KEY") or "").strip():
            return False, "Нет OPENAI_API_KEY в .env"
        if not _read_proxy_url():
            return (
                False,
                "Маршрут proxy, но OPENAI_PROXY (или HTTPS_PROXY) не задан",
            )
        return True, ""
    if not (os.getenv("OPENAI_API_KEY") or "").strip():
        return False, "Нет OPENAI_API_KEY в .env"
    return True, ""


def describe_llm_route() -> str:
    """Краткое описание маршрута для консоли и дашборда."""
    route = get_llm_route()
    if route == "gptunnel":
        host = get_gptunnel_base_url().replace("https://", "").replace("http://", "")
        return f"шлюз GPTunnel ({host})"
    if route == "proxy":
        proxy = _read_proxy_url()
        if not proxy:
            return "прокси (URL не задан — проверьте OPENAI_PROXY)"
        host = proxy.split("@")[-1] if "@" in proxy else proxy
        return f"через HTTP-прокси ({host})"
    return "напрямую OpenAI (VPN/сеть на уровне ОС)"


def _strip_bearer_hook(request: httpx.Request) -> None:
    """GPTunnel: Authorization = ключ без префикса Bearer."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        request.headers["Authorization"] = auth[len("Bearer ") :]


def create_openai_client(
    api_key: str | None = None,
    *,
    timeout: httpx.Timeout | None = None,
) -> tuple[OpenAI, httpx.Client, dict[str, Any]]:
    """
    Создаёт OpenAI SDK-клиент с учётом маршрута.

    Returns:
        (client, httpx_client, meta) где meta содержит route / use_wallet_balance.
    """
    route = get_llm_route()
    key = api_key or get_llm_api_key()
    if not key:
        raise ValueError("Нет API-ключа для выбранного маршрута LLM")

    timeout = timeout or httpx.Timeout(120.0, connect=20.0)
    meta: dict[str, Any] = {
        "route": route,
        "use_wallet_balance": False,
        "base_url": None,
    }

    if route == "gptunnel":
        base_url = get_gptunnel_base_url()
        http_client = httpx.Client(
            timeout=timeout,
            event_hooks={"request": [_strip_bearer_hook]},
        )
        client = OpenAI(api_key=key, base_url=base_url, http_client=http_client)
        meta["use_wallet_balance"] = True
        meta["base_url"] = base_url
        logger.info("LLM-клиент: GPTunnel %s", base_url)
        return client, http_client, meta

    client_kwargs: dict[str, Any] = {"timeout": timeout}
    if route == "proxy":
        proxy_url = _read_proxy_url()
        if not proxy_url:
            raise ValueError("Маршрут proxy без OPENAI_PROXY")
        client_kwargs["proxy"] = proxy_url
        logger.info("LLM-клиент: OpenAI через прокси")
    else:
        logger.info("LLM-клиент: OpenAI direct")

    http_client = httpx.Client(**client_kwargs)
    client = OpenAI(api_key=key, http_client=http_client)
    return client, http_client, meta


def chat_extra_body(meta: dict[str, Any] | None) -> dict[str, Any] | None:
    """Доп. поля тела запроса (GPTunnel useWalletBalance)."""
    if meta and meta.get("use_wallet_balance"):
        return {"useWalletBalance": True}
    return None


def make_route_selector_widget(
    on_change: Callable[[str], None] | None = None,
):
    """
    RadioButtons выбора маршрута для дашборда.

    Returns:
        ipywidgets.VBox с подписью и RadioButtons (атрибут ``.route_radio``).
    """
    import ipywidgets as widgets

    current = get_llm_route()
    # proxy в UI не предлагаем по умолчанию — редкий режим
    options = [
        ("Напрямую OpenAI (дома / VPN)", "direct"),
        ("Через шлюз GPTunnel (работа / мобильный)", "gptunnel"),
    ]
    radio = widgets.RadioButtons(
        options=options,
        value=current if current in ("direct", "gptunnel") else "gptunnel",
        description="",
        layout=widgets.Layout(width="100%", margin="4px 0"),
    )
    hint = widgets.HTML(
        value=(
            "<div style='margin:8px 0 4px 0;color:#495057;'>"
            "<strong>Маршрут API:</strong> на этом ПК при блокировке OpenAI "
            "выбирайте GPTunnel. Дома можно снова «напрямую»."
            f"<br><span style='color:#6c757d;font-size:13px;'>"
            f"Сейчас: {describe_llm_route()}</span></div>"
        )
    )

    def _handle(change):
        if change.get("name") == "value" and change.get("new"):
            set_llm_route(change["new"], persist=True)
            hint.value = (
                "<div style='margin:8px 0 4px 0;color:#495057;'>"
                "<strong>Маршрут API:</strong> на этом ПК при блокировке OpenAI "
                "выбирайте GPTunnel. Дома можно снова «напрямую»."
                f"<br><span style='color:#6c757d;font-size:13px;'>"
                f"Сейчас: {describe_llm_route()}</span></div>"
            )
            if on_change:
                on_change(change["new"])

    radio.observe(_handle, names="value")
    box = widgets.VBox([hint, radio])
    box.route_radio = radio  # type: ignore[attr-defined]
    return box
