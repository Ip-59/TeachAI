"""Подмена LLM: клиент с тем же интерфейсом, что у openai.OpenAI (chat.completions.create).

Работает и в процессе pytest, и внутри ядра Jupyter (см. tests/kernel_boot.py).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

FIXTURES = Path(__file__).parent / "fixtures" / "llm"

# (kind, regex по system, regex по user | None). Порядок важен: первое совпадение.
RULES: list[tuple[str, str, str | None]] = [
    ("domain", r"классификатор учебной темы", r"Относится ли тема курса"),
    ("subject", r"классификатор учебной темы", r"Определи предметную область"),
    ("code_practice", r"решаешь, есть ли у урока практика кодом", None),
    ("task_matches", r"проверяешь соответствие практики уроку", None),
    ("plan", r"методист образовательных программ", None),
    ("lesson", r"Пиши подробный урок", None),
    ("concepts", r"выделяет ключевые понятия", None),
    ("concept_explain", r"подробные и понятные объяснения сложных понятий", None),
    ("explanation", r"эксперт в данной области", None),
    ("examples", r"Сначала реши, есть ли у этого урока", None),
    ("examples_repair", r"генерируешь только JSON с рабочими Python-примерами", None),
    ("assessment", r"создающий тесты для проверки знаний", None),
    ("relevance", r"scope=lesson, если вопрос", None),
    ("qa", r"отвечает на вопросы студентов", None),
    ("task_gen", r"Создавай однозначные контрольные задания", None),
    ("task_validate", r"Проверяешь контрольные задания по смыслу решения", None),
]


@dataclass
class Call:
    kind: str
    messages: list
    kwargs: dict


def classify(messages: list) -> str:
    system = "\n".join(m["content"] for m in messages if m.get("role") == "system")
    user = "\n".join(m["content"] for m in messages if m.get("role") == "user")
    for kind, sys_re, user_re in RULES:
        if re.search(sys_re, system) and (user_re is None or re.search(user_re, user)):
            return kind
    raise AssertionError(
        "Неизвестный запрос к LLM (нет правила в tests/fake_llm.py RULES):\n"
        + system[:200]
    )


@dataclass
class FakeLLM:
    """Выбирает записанный ответ по типу запроса и ведёт журнал вызовов."""

    fixtures: Path = FIXTURES
    calls: list[Call] = field(default_factory=list)
    overrides: dict[str, list[Any]] = field(default_factory=dict)
    log_path: Path | None = None  # для ядра: журнал в JSONL, читает pytest

    # --- настройка ---------------------------------------------------------
    def use(self, kind: str, *responses: Any) -> None:
        """Следующие ответы на ``kind``: имя фикстуры (str без пробелов и '{'),
        dict/list (будет JSON), готовая строка, Exception или callable(messages).
        Последний элемент повторяется, пока не заменён."""
        self.overrides[kind] = list(responses)

    # --- ответ -------------------------------------------------------------
    def _load(self, kind_or_name: str) -> str:
        for ext in (".json", ".md", ".txt"):
            p = self.fixtures / f"{kind_or_name}{ext}"
            if p.exists():
                return p.read_text(encoding="utf-8")
        raise FileNotFoundError(f"нет фикстуры {kind_or_name} в {self.fixtures}")

    def _log(self, row: dict) -> None:
        if self.log_path:
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def answer(self, messages: list, kwargs: dict) -> str:
        try:
            return self._answer(messages, kwargs)
        except (AssertionError, FileNotFoundError) as exc:  # ошибки самого стенда, а не приложения
            self._log({"harness_error": str(exc)})
            raise

    def _answer(self, messages: list, kwargs: dict) -> str:
        kind = classify(messages)
        self.calls.append(Call(kind, messages, kwargs))
        self._log({"kind": kind})
        queue = self.overrides.get(kind)
        item: Any = self._load(kind)
        if queue:
            item = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(item, BaseException):
            raise item
        if callable(item):
            item = item(messages)
        if isinstance(item, (dict, list)):
            return json.dumps(item, ensure_ascii=False)
        if isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9_\-]+", item):
            return self._load(item)
        return str(item)

    def count(self, kind: str | None = None) -> int:
        return sum(1 for c in self.calls if kind is None or c.kind == kind)

    # --- интерфейс клиента OpenAI -------------------------------------------
    def client(self) -> Any:
        fake = self

        def create(**kwargs: Any) -> Any:
            text = fake.answer(kwargs["messages"], kwargs)
            msg = SimpleNamespace(content=text)
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)])

        completions = SimpleNamespace(create=create)
        return SimpleNamespace(chat=SimpleNamespace(completions=completions))

    def create_openai_client(self, api_key: str | None = None, **_: Any):
        meta = {"route": "fake", "use_wallet_balance": False, "base_url": None}
        return self.client(), None, meta

    def install(self) -> None:
        """Подменяет единственную точку создания клиента: content_utils.create_openai_client."""
        import content_utils

        content_utils.create_openai_client = self.create_openai_client
