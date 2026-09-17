"""Полный прогон бенчмарка: все уроки из scenarios/lessons.json."""

from __future__ import annotations

import json

from model_benchmark.runner import run_lesson_benchmark


def main() -> None:
    """Запускает полный прогон и печатает leaderboard с ценой."""
    report = run_lesson_benchmark(lesson_ids=None)
    print("SAVED:", report.get("saved_to"))
    print("COST_SUMMARY:", json.dumps(report.get("cost_summary"), ensure_ascii=False))
    print(json.dumps(report.get("leaderboard"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
