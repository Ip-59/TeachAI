"""
Судейство КЗ через LLM: предмет урока и «задание относится к уроку?».

Без списков ключевых слов — только вопрос модели и разбор JSON.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Mapping, Optional

logger = logging.getLogger(__name__)

_JSON_OBJECT = re.compile(r"\{[\s\S]*\}")

_DEFAULT_SUBJECT = "программирование на Python"


def _parse_json_object(raw: str) -> dict:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    match = _JSON_OBJECT.search(text)
    if not match:
        raise ValueError("в ответе нет JSON")
    data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("JSON не объект")
    return data


def _bool_field(data: dict, key: str) -> bool:
    value = data.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "да", "yes", "1")
    return bool(value)


def classify_lesson_subject(
    generator: Any,
    *,
    lesson_title: str,
    lesson_content: str,
    course_context: Optional[Mapping[str, Any]] = None,
) -> str:
    """
    Спрашивает LLM, к какой предметной области относится урок.

    Returns:
        Краткая формулировка на русском (для промпта генерации КЗ).
    """
    if generator is None or not hasattr(generator, "make_api_request"):
        logger.warning("classify_lesson_subject: нет API — %s", _DEFAULT_SUBJECT)
        return _DEFAULT_SUBJECT

    course_title = ""
    topic_title = ""
    if isinstance(course_context, dict):
        course_title = str(course_context.get("course_title") or "")
        topic_title = str(course_context.get("topic_title") or "")

    # Текст урока может быть длинным — для классификации хватает начала + хвоста.
    body = (lesson_content or "").strip()
    if len(body) > 8000:
        body = body[:5000] + "\n…\n" + body[-2000:]

    prompt = (
        "Определи предметную область учебного урока для генерации практики.\n"
        f"Курс: {course_title or '(не указан)'}\n"
        f"Тема: {topic_title or '(не указана)'}\n"
        f"Урок: {lesson_title or '(без названия)'}\n\n"
        f"Текст урока (фрагмент):\n{body}\n\n"
        "Ответь ТОЛЬКО JSON:\n"
        '{"subject": "кратко на русском, напр. машинное обучение с Python / '
        'анализ данных с Python / основы Python / веб на Python / …", '
        '"reason": "одно предложение"}\n'
        "Опирайся на содержание урока, не на догадки по одному слову."
    )
    messages = [
        {
            "role": "system",
            "content": (
                "Ты классификатор учебной темы. Отвечай только JSON, без markdown."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    try:
        try:
            raw = generator.make_api_request(
                messages=messages,
                temperature=0,
                max_tokens=200,
                response_format={"type": "json_object"},
            )
        except Exception as fmt_exc:
            logger.info("json_object недоступен для subject: %s", fmt_exc)
            raw = generator.make_api_request(
                messages=messages, temperature=0, max_tokens=200
            )
        data = _parse_json_object(raw)
        subject = str(data.get("subject") or "").strip()
        if not subject:
            return _DEFAULT_SUBJECT
        logger.info(
            "LLM subject для «%s»: %s (%s)",
            lesson_title,
            subject,
            data.get("reason", ""),
        )
        return subject
    except Exception as exc:
        logger.warning("classify_lesson_subject не удался: %s", exc)
        return _DEFAULT_SUBJECT


def task_matches_lesson(
    generator: Any,
    *,
    task: Mapping[str, Any],
    lesson_title: str,
    lesson_content: str,
    lesson_subject: str,
) -> bool:
    """
    Спрашивает LLM: относится ли сгенерированное КЗ к этому уроку.

    Returns:
        True — относится; False — нет или ошибка API (безопаснее перегенерировать).
    """
    if generator is None or not hasattr(generator, "make_api_request"):
        return False
    if not isinstance(task, dict):
        return False

    body = (lesson_content or "").strip()
    if len(body) > 6000:
        body = body[:4000] + "\n…\n" + body[-1500:]

    task_summary = {
        "title": task.get("title"),
        "description": task.get("description"),
        "student_steps": task.get("student_steps"),
        "task_code": (task.get("task_code") or "")[:1500],
        "solution_code": (task.get("solution_code") or "")[:1500],
        "condition_rule": task.get("condition_rule"),
    }
    prompt = (
        "Проверь, относится ли контрольное задание к ДАННОМУ уроку.\n"
        f"Урок: «{lesson_title}»\n"
        f"Предметная область урока (ранее): {lesson_subject}\n\n"
        f"Текст урока (фрагмент):\n{body}\n\n"
        f"Контрольное задание (JSON):\n{json.dumps(task_summary, ensure_ascii=False)}\n\n"
        "Критерии matches=false (НЕ относится / плохое задание):\n"
        "- другая тема, чем в уроке (напр. установка Python / sys.version, "
        "если урок не об этом);\n"
        "- «основы» age/status вместо библиотек/концепций урока;\n"
        "- требует терминал ОС, shell, python --version в командной строке "
        "вместо кода Python в редакторе TeachAI;\n"
        "- буквально копирует код/примеры из текста урока: те же имена "
        "переменных и те же литералы (строки, числа), что в примерах урока — "
        "это тоже matches=false; нужны другие имена и значения той же идеи.\n"
        "Ответь ТОЛЬКО JSON: "
        '{"matches": true или false, "reason": "кратко на русском"}.'
    )
    messages = [
        {
            "role": "system",
            "content": (
                "Ты проверяешь соответствие практики уроку. "
                "Отвечай только JSON, без markdown."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    try:
        try:
            raw = generator.make_api_request(
                messages=messages,
                temperature=0,
                max_tokens=200,
                response_format={"type": "json_object"},
            )
        except Exception as fmt_exc:
            logger.info("json_object недоступен для matches: %s", fmt_exc)
            raw = generator.make_api_request(
                messages=messages, temperature=0, max_tokens=200
            )
        data = _parse_json_object(raw)
        matched = _bool_field(data, "matches")
        logger.info(
            "LLM matches для «%s»: %s (%s)",
            lesson_title,
            matched,
            data.get("reason", ""),
        )
        return matched
    except Exception as exc:
        logger.warning("task_matches_lesson не удался: %s", exc)
        return False
