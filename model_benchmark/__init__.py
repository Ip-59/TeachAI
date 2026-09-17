"""Пакет бенчмарка моделей TeachAI."""

__all__ = ["run_lesson_benchmark"]


def __getattr__(name: str):
    """Ленивый импорт, чтобы утилиты работали без openai до прогона."""
    if name == "run_lesson_benchmark":
        from model_benchmark.runner import run_lesson_benchmark

        return run_lesson_benchmark
    raise AttributeError(name)
