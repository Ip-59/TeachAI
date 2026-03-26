import os
import json
from typing import Any, Dict, List
import httpx
from openai import OpenAI
try:
    # Azure client доступен в новой версии SDK
    from openai import AzureOpenAI  # type: ignore
except Exception:
    AzureOpenAI = None  # type: ignore


class LLMGenerator:
    def __init__(self):
        self.log_path = "log_openai.jsonl"

        # Выбор провайдера через переменную окружения
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        model = os.getenv("LLM_MODEL", "gpt-4")

        self.model = model
        self.provider = provider

        # Настройка клиента в зависимости от провайдера
        if provider == "openai":
            http_client = self._build_http_client()
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL") or None,
                http_client=http_client,
            )
        elif provider == "azure":
            if AzureOpenAI is None:
                raise RuntimeError("Библиотека OpenAI SDK не поддерживает Azure в текущей версии")
            # Ожидаемые переменные окружения для Azure OpenAI
            # AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT
            http_client = self._build_http_client()
            self.client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-07-01-preview"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                http_client=http_client,
            )
            # Для Azure в качестве model следует передавать имя деплоймента
            self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT", self.model)
        elif provider == "openrouter":
            # OpenRouter использует OpenAI-совместимый API
            http_client = self._build_http_client()
            self.client = OpenAI(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
                http_client=http_client,
            )
            # Требуется указать корректную модель через LLM_MODEL
        elif provider == "local":
            self.client = None  # Локальный режим, без внешнего API
        else:
            raise ValueError(f"Неизвестный LLM провайдер: {provider}")

    def _log(self, role: str, content: str):
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(
                json.dumps({"role": role, "content": content}, ensure_ascii=False)
                + "\n"
            )

    def _build_http_client(self) -> httpx.Client:
        proxy = (
            os.getenv("OPENAI_PROXY")
            or os.getenv("HTTPS_PROXY")
            or os.getenv("HTTP_PROXY")
            or os.getenv("https_proxy")
            or os.getenv("http_proxy")
        )
        no_proxy = os.getenv("NO_PROXY") or os.getenv("no_proxy")

        if not proxy:
            raise RuntimeError(
                "Прокси не задан. Укажите OPENAI_PROXY или HTTPS_PROXY/HTTP_PROXY."
            )

        verify = True
        ca_bundle = (
            os.getenv("SSL_CERT_FILE")
            or os.getenv("REQUESTS_CA_BUNDLE")
            or os.getenv("OPENAI_CA_CERT")
        )
        if ca_bundle:
            verify = ca_bundle

        if proxy:
            client = httpx.Client(
                mounts={
                    "https://": httpx.HTTPTransport(proxy=proxy, verify=verify),
                    "http://": httpx.HTTPTransport(proxy=proxy, verify=verify),
                },
                timeout=httpx.Timeout(30.0, read=120.0),
            )
        else:
            client = httpx.Client(
                verify=verify,
                timeout=httpx.Timeout(30.0, read=120.0),
            )
        if no_proxy:
            os.environ["NO_PROXY"] = no_proxy
        return client

    def _safe_chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        if self.provider == "local" or self.client is None:
            raise RuntimeError("Внешний LLM отключён (local). Нет удалённого ответа.")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Дружелюбная диагностика для 403 и сетевых ограничений
            msg = str(e)
            if "unsupported_country_region_territory" in msg or "request_forbidden" in msg:
                raise RuntimeError(
                    "Запрос отклонён провайдером (403: регион не поддерживается). "
                    "Смените провайдера (LLM_PROVIDER=openrouter/azure) или укажите допустимый endpoint."
                )
            raise

    def _local_course(self, config: Dict[str, Any]) -> List[Dict[str, str]]:
        # Простейшая локальная генерация структуры курса
        hours = int(config.get("total_hours", 8))
        sessions = max(hours // 2, 4)
        topics = [
            "Введение в Python",
            "Первая программа и основы синтаксиса",
            "Типы данных и операции",
            "Условия и циклы",
            "Функции и модули",
            "Работа с файлами",
            "Исключения",
            "Практический мини‑проект",
        ]
        plan = []
        for i, t in enumerate(topics[:sessions], start=1):
            plan.append({
                "title": t,
                "content": f"Занятие {i}: краткий анонс темы \"{t}\" для уровня {config.get('level','базовый')}.",
            })
        return plan

    def _local_lesson(self, topic_title: str, config: Dict[str, Any]) -> str:
        return (
            f"Тема: {topic_title}\n\n"
            f"Уровень: {config.get('level','базовый')} | Время: {config.get('session_minutes',45)} мин.\n\n"
            "Цели урока:\n"
            "- Понять ключевые понятия темы.\n"
            "- Закрепить навыки через примеры.\n\n"
            "Содержание:\n"
            "1) Краткое объяснение основных идей.\n"
            "2) Пример кода и разбор.\n"
            "3) Малые практические задания.\n\n"
            "Итоги и рекомендации по дальнейшему изучению."
        )

    def _local_quiz(self, topic_title: str, lesson_text: str) -> List[Dict[str, Any]]:
        return [
            {
                "question": f"Что является ключевой идеей темы: {topic_title}?",
                "options": ["Определение", "Пример", "Практика"],
                "answer": "Определение",
            },
            {
                "question": "Какой шаг рекомендуется выполнить после чтения урока?",
                "options": ["Ничего", "Попробовать задания", "Удалить код"],
                "answer": "Попробовать задания",
            },
            {
                "question": "Что включает содержание урока?",
                "options": ["Только теорию", "Теорию и практику", "Только тест"],
                "answer": "Теорию и практику",
            },
        ]

    def generate_course(self, config: Dict[str, Any]):
        prompt = f"""
Создай учебный план по теме "Искусственный интеллект и машинное обучение" для уровня: {config['level']}.
Курс рассчитан на {config['total_hours']} часов, с занятиями по {config['session_minutes']} минут.
Верни структуру в JSON: список тем с полями title и content (анонс).
        """
        self._log("prompt", prompt)
        if self.provider == "local" or self.client is None:
            content_json = self._local_course(config)
            self._log("response", json.dumps(content_json, ensure_ascii=False))
            return content_json

        content = self._safe_chat(messages=[{"role": "user", "content": prompt}], temperature=0.7)
        self._log("response", content)
        try:
            return json.loads(content)
        except Exception as e:
            raise ValueError(f"Ошибка парсинга плана курса: {e}")

    def generate_lesson_text(self, topic_title: str, config: Dict[str, Any]):
        prompt = f"""
Сформируй подробный текст урока на тему: "{topic_title}" для уровня: {config['level']}.
Объём должен соответствовать времени {config['session_minutes']} минут. Напиши на русском языке, стиль: {config['style']}.
        """
        self._log("prompt", prompt)
        if self.provider == "local" or self.client is None:
            content = self._local_lesson(topic_title, config)
        else:
            content = self._safe_chat(messages=[{"role": "user", "content": prompt}], temperature=0.7)
        self._log("response", content)
        return content

    def generate_quiz_for_lesson(self, topic_title: str, lesson_text: str):
        prompt = f"""
Составь 3 вопроса викторины с 3 вариантами ответов каждый по теме: "{topic_title}".
Используй следующий текст урока как источник: {lesson_text}
Ответ верни в JSON-формате:
[
  {{"question": "...", "options": ["A", "B", "C"], "answer": "A"}},
  ...
]
        """
        self._log("prompt", prompt)
        if self.provider == "local" or self.client is None:
            content_json = self._local_quiz(topic_title, lesson_text)
            self._log("response", json.dumps(content_json, ensure_ascii=False))
            return content_json

        content = self._safe_chat(messages=[{"role": "user", "content": prompt}], temperature=0.7)
        self._log("response", content)
        try:
            return json.loads(content)
        except Exception as e:
            raise ValueError(f"Ошибка парсинга викторины: {e}")
