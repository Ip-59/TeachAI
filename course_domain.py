"""Проверка темы своего курса запросом к языковой модели."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Literal

logger = logging.getLogger(__name__)

DomainStatus = Literal["in", "out", "error"]


@dataclass(frozen=True)
class DomainVerdict:
    """Ответ модели: тема в области Python/AI/ML или нет."""

    status: DomainStatus
    reason: str
    source: Literal["llm", "none"] = "llm"


_JSON_OBJECT = re.compile(r"\{[\s\S]*\}")


def _parse_verdict(raw: str) -> DomainVerdict:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    match = _JSON_OBJECT.search(text)
    if not match:
        raise ValueError("в ответе нет JSON")
    data = json.loads(match.group(0))
    flag = data.get("in_domain")
    if isinstance(flag, str):
        flag = flag.strip().lower() in ("true", "да", "yes", "1")
    in_domain = bool(flag)
    reason = str(data.get("reason") or "").strip()
    if not reason:
        reason = (
            "Модель отнесла тему к Python / AI/ML."
            if in_domain
            else "Модель не отнесла тему к Python / AI/ML."
        )
    return DomainVerdict("in" if in_domain else "out", reason, "llm")


def resolve_api_generator(generator: Any | None) -> Any | None:
    """
    Находит объект с ``make_api_request``.

    ``ContentGenerator`` — фасад без этого метода; API у вложенных
    ``lesson_gen`` / ``course_plan_gen`` / … (``BaseContentGenerator``).
    """
    if generator is None:
        return None
    if hasattr(generator, "make_api_request"):
        return generator
    for attr in (
        "lesson_gen",
        "course_plan_gen",
        "qa_gen",
        "explanation_gen",
        "concepts_gen",
        "assessment_gen",
        "examples_gen",
        "relevance_checker",
    ):
        child = getattr(generator, attr, None)
        if child is not None and hasattr(child, "make_api_request"):
            return child
    return None


def classify_course_topic(
    title: str,
    description: str = "",
    generator: Any | None = None,
) -> DomainVerdict:
    """
    Спрашивает LLM, относится ли тема к Python и AI/ML.

    Без генератора или при ошибке API — ``error`` (курс сам не стартует).
    """
    name = (title or "").strip()
    if not name:
        return DomainVerdict("error", "Пустое название курса.", "none")
    api = resolve_api_generator(generator)
    if api is None:
        return DomainVerdict(
            "error",
            "Нет подключения к модели, чтобы проверить тему. "
            "Повторите попытку после инициализации системы.",
            "none",
        )
    generator = api

    prompt = (
        f'Относится ли тема курса «{name}» к сфере Python и AI/ML '
        "(язык Python, анализ данных, машинное обучение, нейросети, LLM, "
        "компьютерное зрение, библиотеки вроде pandas/numpy/scikit-learn)?\n"
        f"Описание: {(description or '').strip() or '(нет)'}\n\n"
        "Другой язык программирования как основной предмет (Java, C++, JavaScript) — нет.\n"
        "Бытовые, гуманитарные и прочие темы без Python/ML — нет.\n"
        'Ответь JSON: {"in_domain": true или false, "reason": "кратко на русском"}.'
    )
    messages = [
        {
            "role": "system",
            "content": "Ты классификатор учебной темы. Отвечай только JSON, без markdown.",
        },
        {"role": "user", "content": prompt},
    ]
    try:
        try:
            raw = generator.make_api_request(
                messages=messages,
                temperature=0,
                max_tokens=250,
                response_format={"type": "json_object"},
            )
        except Exception as fmt_exc:
            logger.info("json_object недоступен, повтор без schema: %s", fmt_exc)
            raw = generator.make_api_request(
                messages=messages,
                temperature=0,
                max_tokens=250,
            )
        return _parse_verdict(raw)
    except Exception as exc:
        logger.warning("Проверка темы через LLM не удалась: %s", exc)
        return DomainVerdict(
            "error",
            f"Не удалось проверить тему через модель: {exc}",
            "none",
        )
