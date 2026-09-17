"""Клиент GPTunnel для участников и судей бенчмарка."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any


class GPTunnelClient:
    """
    HTTP-клиент к GPTunnel (OpenAI-совместимый /v1/chat/completions).

    Важно: в Authorization передаётся ключ БЕЗ префикса Bearer
    (см. docs.gptunnel.ru).
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://gptunnel.ru/v1",
        use_wallet_balance: bool = True,
    ) -> None:
        """
        Args:
            api_key: Ключ GPTunnel или переменная GPTUNNEL_API_KEY.
            base_url: Базовый URL API.
            use_wallet_balance: Списывать с личного кошелька (тест).
        """
        key = api_key or os.getenv("GPTUNNEL_API_KEY")
        if not key:
            raise ValueError(
                "Нет GPTUNNEL_API_KEY. Добавьте ключ в окружение или .env"
            )
        self.api_key = key
        self.base_url = base_url.rstrip("/")
        self.use_wallet_balance = use_wallet_balance

    def list_models(self) -> list[dict[str, Any]]:
        """Возвращает каталог моделей GPTunnel."""
        payload = self._request("GET", "/models")
        data = payload.get("data") or []
        return data if isinstance(data, list) else []

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 3500,
    ) -> dict[str, Any]:
        """
        Один chat-запрос.

        Returns:
            content, latency_sec, usage, model, raw.
        """
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if self.use_wallet_balance:
            body["useWalletBalance"] = True

        started = time.perf_counter()
        response = self._request("POST", "/chat/completions", body=body)
        latency = time.perf_counter() - started

        choices = response.get("choices") or []
        content = ""
        if choices:
            message = choices[0].get("message") or {}
            content = message.get("content") or ""

        usage = response.get("usage")
        return {
            "content": content,
            "latency_sec": round(latency, 3),
            "usage": usage,
            "model": response.get("model", model),
            "raw": response,
        }

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        timeout: float = 180.0,
        retries: int = 5,
    ) -> dict[str, Any]:
        """Низкоуровневый HTTP-запрос к GPTunnel с ретраями на 502/503/429."""
        url = f"{self.base_url}{path}"
        data = None if body is None else json.dumps(body).encode("utf-8")
        last_error: Exception | None = None

        for attempt in range(retries):
            request = urllib.request.Request(
                url,
                data=data,
                method=method,
                headers={
                    "Authorization": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=timeout) as resp:
                    raw = resp.read().decode("utf-8")
                if not raw:
                    return {}
                return json.loads(raw)
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                last_error = RuntimeError(
                    f"GPTunnel HTTP {exc.code} {path}: {detail[:500]}"
                )
                if exc.code not in {429, 500, 502, 503, 504}:
                    raise last_error from exc
            except urllib.error.URLError as exc:
                last_error = RuntimeError(f"GPTunnel сеть {path}: {exc}")

            sleep_sec = min(60.0, 2.0 ** attempt)
            time.sleep(sleep_sec)

        assert last_error is not None
        raise last_error


# Обратная совместимость со старым именем в runner.
OpenRouterClient = GPTunnelClient
