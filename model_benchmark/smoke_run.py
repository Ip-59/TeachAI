"""Дымовой прогон бенчмарка: один урок."""

from __future__ import annotations

import json

from model_benchmark.runner import run_lesson_benchmark


def main() -> None:
    """Запускает прогон lesson-variables и печатает сводку."""
    report = run_lesson_benchmark(lesson_ids=["lesson-variables"])
    print("SAVED:", report.get("saved_to"))
    print(json.dumps(report.get("leaderboard"), ensure_ascii=False, indent=2))
    for lesson in report["lessons"]:
        for pid, gen in lesson["generations"].items():
            fg = gen["format_gate"]
            print(
                "GEN",
                pid,
                "format_ok=",
                fg["passed"],
                "chars=",
                fg["char_count"],
                "latency=",
                gen["latency_sec"],
                "reasons=",
                fg.get("reasons"),
            )


if __name__ == "__main__":
    main()
