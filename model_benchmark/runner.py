"""
Раннер бенчмарка: генерация уроков участниками + слепая оценка судьями.
"""

from __future__ import annotations

import json
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from model_benchmark.client import GPTunnelClient
from model_benchmark.format_gate import check_lesson_format
from model_benchmark.prompts import (
    build_judge_prompt,
    build_lesson_system_prompt,
    build_lesson_user_prompt,
)

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
load_dotenv(PROJECT_ROOT / ".env")


def load_json(path: Path) -> Any:
    """Загружает JSON-файл."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, data: Any) -> None:
    """Сохраняет JSON-файл."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def _blind_labels(n: int) -> list[str]:
    """Метки A, B, C… для слепой оценки."""
    return list(string.ascii_uppercase[:n])


def run_lesson_benchmark(
    config_path: Path | None = None,
    scenarios_path: Path | None = None,
    rubric_path: Path | None = None,
    lesson_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Полный прогон: участники генерируют уроки, судьи ставят баллы.

    Args:
        config_path: Путь к config.json.
        scenarios_path: Путь к scenarios/lessons.json.
        rubric_path: Путь к rubric.json.
        lesson_ids: Ограничить список уроков (для дымового теста).

    Returns:
        Сводный отчёт (также пишется в results/).
    """
    config = load_json(config_path or ROOT / "config.json")
    scenarios = load_json(scenarios_path or ROOT / "scenarios" / "lessons.json")
    rubric = load_json(rubric_path or ROOT / "rubric.json")

    lessons = scenarios["lessons"]
    if lesson_ids:
        lessons = [item for item in lessons if item["id"] in lesson_ids]

    api_cfg = config["api"]
    client = GPTunnelClient(
        base_url=api_cfg.get("base_url", "https://gptunnel.ru/v1"),
        use_wallet_balance=bool(api_cfg.get("use_wallet_balance", True)),
    )

    gen_cfg = config["generation"]
    judge_cfg = config["judging"]
    participants = config["participants"]
    judges = config["judges"]

    report: dict[str, Any] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "course": scenarios["course_title"],
        "participants": participants,
        "judges": judges,
        "lessons": [],
    }

    for lesson in lessons:
        lesson_result = _run_one_lesson(
            client=client,
            config=config,
            scenarios=scenarios,
            rubric=rubric,
            lesson=lesson,
            participants=participants,
            judges=judges,
            gen_cfg=gen_cfg,
            judge_cfg=judge_cfg,
        )
        report["lessons"].append(lesson_result)

    report["leaderboard"] = _build_leaderboard(report)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = ROOT / "results" / f"lesson_benchmark_{stamp}.json"
    save_json(out_path, report)
    report["saved_to"] = str(out_path)
    return report


def _run_one_lesson(
    client: GPTunnelClient,
    config: dict[str, Any],
    scenarios: dict[str, Any],
    rubric: dict[str, Any],
    lesson: dict[str, Any],
    participants: list[dict[str, Any]],
    judges: list[dict[str, Any]],
    gen_cfg: dict[str, Any],
    judge_cfg: dict[str, Any],
) -> dict[str, Any]:
    """Один урок: генерации + format gate + судьи."""
    user_prompt = build_lesson_user_prompt(
        course=scenarios["course_title"],
        section=scenarios["section"],
        topic=lesson["topic"],
        lesson_title=lesson["lesson"],
        user_name=scenarios.get("user_name", config.get("user_name", "Студент")),
        communication_style=scenarios.get(
            "communication_style", config.get("communication_style", "friendly")
        ),
    )
    messages = [
        {"role": "system", "content": build_lesson_system_prompt()},
        {"role": "user", "content": user_prompt},
    ]

    generations: dict[str, Any] = {}
    for participant in participants:
        raw = client.chat(
            model=participant["model"],
            messages=messages,
            temperature=gen_cfg.get("temperature", 0.7),
            max_tokens=gen_cfg.get("max_tokens", 3500),
        )
        gate = check_lesson_format(raw["content"], rubric["format_gate"])
        generations[participant["id"]] = {
            "participant": participant,
            "response": raw,
            "format_gate": gate,
        }

    # Слепая карта: label -> participant_id
    labels = _blind_labels(len(participants))
    label_to_pid = {
        labels[i]: participants[i]["id"] for i in range(len(participants))
    }
    pid_to_label = {pid: label for label, pid in label_to_pid.items()}

    labeled_texts: dict[str, str] = {}
    for pid, payload in generations.items():
        if payload["format_gate"]["passed"]:
            labeled_texts[pid_to_label[pid]] = _truncate_for_judge(
                payload["response"]["content"]
            )
        else:
            labeled_texts[pid_to_label[pid]] = (
                "[FORMAT_FAIL] Текст не прошёл формальную проверку:\n"
                + "; ".join(payload["format_gate"]["reasons"])
                + "\n\nФрагмент:\n"
                + payload["response"]["content"][:500]
            )

    lesson_meta = {
        "course": scenarios["course_title"],
        "section": scenarios["section"],
        "topic": lesson["topic"],
        "lesson": lesson["lesson"],
    }
    judge_prompt = build_judge_prompt(lesson_meta, rubric, labeled_texts)

    judge_scores: list[dict[str, Any]] = []
    for judge in judges:
        parsed, raw = _ask_judge(
            client=client,
            judge=judge,
            judge_prompt=judge_prompt,
            judge_cfg=judge_cfg,
        )
        judge_scores.append(
            {
                "judge": judge,
                "raw": {
                    "content": raw.get("content"),
                    "latency_sec": raw.get("latency_sec"),
                    "usage": raw.get("usage"),
                    "model": raw.get("model"),
                },
                "parsed": parsed,
                "by_participant": _map_scores_to_participants(
                    parsed, label_to_pid
                ),
            }
        )

    return {
        "lesson": lesson,
        "label_to_participant": label_to_pid,
        "generations": {
            pid: {
                "model": generations[pid]["participant"]["model"],
                "latency_sec": generations[pid]["response"]["latency_sec"],
                "usage": generations[pid]["response"]["usage"],
                "format_gate": generations[pid]["format_gate"],
                "content": generations[pid]["response"]["content"],
            }
            for pid in generations
        },
        "judges": judge_scores,
    }


def _truncate_for_judge(text: str, limit: int = 3500) -> str:
    """Укорачивает длинный урок для судьи, чтобы JSON ответа не обрезался."""
    content = text or ""
    if len(content) <= limit:
        return content
    return content[:limit] + "\n\n[... текст урока обрезан для оценки ...]"


def _ask_judge(
    client: GPTunnelClient,
    judge: dict[str, Any],
    judge_prompt: str,
    judge_cfg: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Запрос к судье с одной повторной попыткой при битом JSON."""
    messages = [
        {
            "role": "system",
            "content": (
                "Ты методист. Отвечай ТОЛЬКО валидным JSON-объектом без "
                "markdown и без текста вокруг. Комментарии — короткие строки."
            ),
        },
        {"role": "user", "content": judge_prompt},
    ]
    last_raw: dict[str, Any] = {}
    parsed: dict[str, Any] = {"scores": {}, "parse_error": True}
    for attempt in range(2):
        last_raw = client.chat(
            model=judge["model"],
            messages=messages,
            temperature=judge_cfg.get("temperature", 0.2),
            max_tokens=judge_cfg.get("max_tokens", 4000),
        )
        parsed = _parse_judge_json(last_raw.get("content", ""))
        if not parsed.get("parse_error"):
            return parsed, last_raw
        messages = messages + [
            {
                "role": "assistant",
                "content": last_raw.get("content") or "",
            },
            {
                "role": "user",
                "content": (
                    "Ответ был невалидным JSON. Верни ТОЛЬКО исправленный "
                    "JSON по той же схеме scores."
                ),
            },
        ]
    return parsed, last_raw


def _parse_judge_json(text: str) -> dict[str, Any]:
    """Достаёт JSON из ответа судьи; при ошибке не падает."""
    content = (text or "").strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()
        if content.startswith("json"):
            content = content[4:].strip()

    candidates = [content]
    start = content.find("{")
    end = content.rfind("}")
    if start >= 0 and end > start:
        candidates.append(content[start : end + 1])

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return {"scores": {}, "parse_error": True, "raw_text": text}


def _map_scores_to_participants(
    parsed: dict[str, Any], label_to_pid: dict[str, str]
) -> dict[str, Any]:
    """Переводит слепые метки судьи в id участников."""
    scores = parsed.get("scores") or {}
    mapped: dict[str, Any] = {}
    for label, pid in label_to_pid.items():
        mapped[pid] = scores.get(label)
    return mapped


def _usage_cost(usage: Any) -> float | None:
    """Достаёт стоимость запроса из usage GPTunnel."""
    if not isinstance(usage, dict):
        return None
    value = usage.get("total_cost")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _build_leaderboard(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Сводка: качество судей + стоимость генерации + latency."""
    totals: dict[str, list[float]] = {}
    costs: dict[str, list[float]] = {}
    latencies: dict[str, list[float]] = {}

    for lesson in report["lessons"]:
        for judge_block in lesson["judges"]:
            by_participant = judge_block.get("by_participant") or {}
            for pid, score in by_participant.items():
                if not isinstance(score, dict):
                    continue
                total = score.get("total")
                if isinstance(total, (int, float)):
                    totals.setdefault(pid, []).append(float(total))

        for pid, gen in (lesson.get("generations") or {}).items():
            cost = _usage_cost(gen.get("usage"))
            if cost is not None:
                costs.setdefault(pid, []).append(cost)
            latency = gen.get("latency_sec")
            if isinstance(latency, (int, float)):
                latencies.setdefault(pid, []).append(float(latency))

    judge_costs: list[float] = []
    for lesson in report["lessons"]:
        for judge_block in lesson.get("judges") or []:
            cost = _usage_cost((judge_block.get("raw") or {}).get("usage"))
            if cost is not None:
                judge_costs.append(cost)

    rows = []
    for participant in report["participants"]:
        pid = participant["id"]
        values = totals.get(pid, [])
        cost_values = costs.get(pid, [])
        latency_values = latencies.get(pid, [])
        avg = sum(values) / len(values) if values else None
        avg_cost = sum(cost_values) / len(cost_values) if cost_values else None
        sum_cost = sum(cost_values) if cost_values else None
        avg_latency = (
            sum(latency_values) / len(latency_values) if latency_values else None
        )
        score_per_ruble = None
        if avg is not None and avg_cost and avg_cost > 0:
            score_per_ruble = round(avg / avg_cost, 3)

        rows.append(
            {
                "participant_id": pid,
                "model": participant["model"],
                "label": participant["label"],
                "avg_total": round(avg, 3) if avg is not None else None,
                "n_scores": len(values),
                "avg_gen_cost_rub": round(avg_cost, 4) if avg_cost is not None else None,
                "sum_gen_cost_rub": round(sum_cost, 4) if sum_cost is not None else None,
                "avg_latency_sec": round(avg_latency, 3) if avg_latency is not None else None,
                "score_per_ruble": score_per_ruble,
            }
        )

    rows.sort(
        key=lambda row: (
            row["avg_total"] is None,
            -(row["avg_total"] or 0),
            row["avg_gen_cost_rub"] is None,
            row["avg_gen_cost_rub"] or 0,
        )
    )
    report["cost_summary"] = {
        "currency": "RUB",
        "sum_judge_cost_rub": round(sum(judge_costs), 4) if judge_costs else None,
        "note": (
            "avg_gen_cost_rub — стоимость генерации участника; "
            "sum_judge_cost_rub — накладные расходы эксперимента (судьи), "
            "не стоимость продакшена TeachAI."
        ),
    }
    return rows


if __name__ == "__main__":
    # Дымовой режим: один урок, если ключ есть.
    result = run_lesson_benchmark(lesson_ids=["lesson-variables"])
    print(json.dumps(result.get("leaderboard"), ensure_ascii=False, indent=2))
    print("saved:", result.get("saved_to"))
