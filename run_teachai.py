"""
Единая точка входа TeachAI.

- ``start_jupyter()`` — запуск из Jupyter Notebook (TeachAI.ipynb).
- ``main()`` / ``python run_teachai.py`` — запуск из командной строки.
"""

from __future__ import annotations

import importlib
import logging
import sys
from typing import Any, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Порядок важен: сначала базовые модули, затем зависящие от них.
_RELOAD_ORDER: tuple[str, ...] = (
    "content_utils",
    "relevance_checker",
    "concepts_generator",
    "content_generator",
    "lesson_generator",
    "lesson_display",
    "lesson_interface",
    "lesson_interaction",
    "state_manager",
    "engine",
    "interface",
)


def reload_project_modules() -> None:
    """Перезагружает модули проекта, уже загруженные в Jupyter kernel.

    При первом запуске kernel модули ещё не в sys.modules — они подтянутся
    свежими при импорте engine. При повторном запуске ячейки reload
    подхватывает правки в .py без Kernel → Restart.
    """
    for name in _RELOAD_ORDER:
        module = sys.modules.get(name)
        if module is not None:
            try:
                importlib.reload(module)
                logger.debug("Перезагружен модуль: %s", name)
            except Exception as exc:
                logger.warning("Не удалось перезагрузить %s: %s", name, exc)


def start_jupyter(*, reload_modules: bool = False) -> Optional[Any]:
    """Запускает TeachAI в Jupyter и отображает интерактивный интерфейс.

    Args:
        reload_modules: Перезагружать ли уже импортированные модули проекта.
            По умолчанию False — безопаснее для kernel (reload + виджеты
            часто вызывают зависание). True — только при активной разработке.

    Returns:
        Виджет интерфейса (VBox) или None при ошибке запуска.
    """
    load_dotenv(override=True)

    print("⏳ Запуск TeachAI...", flush=True)

    if reload_modules:
        reload_project_modules()

    from engine import TeachAIEngine

    print("⏳ Загрузка дашборда...", flush=True)
    engine = TeachAIEngine()
    interface_element = engine.start()

    if interface_element:
        print("✅ TeachAI запущен. Нажмите «Продолжить обучение».", flush=True)
        return interface_element

    print("❌ Ошибка при запуске системы TeachAI")
    return None


def main() -> None:
    """Запуск TeachAI из командной строки."""
    load_dotenv()

    print("🚀 Запуск TeachAI...")
    print("=" * 50)

    from engine import TeachAIEngine

    engine = TeachAIEngine()

    if engine.initialize():
        print("✅ Система TeachAI успешно инициализирована")

        interface_element = engine.start()

        if interface_element:
            print("✅ Интерфейс создан успешно!")
            print("🎯 TeachAI готов к работе!")
            print("\n📋 Доступные функции:")
            print("- Генерация уроков")
            print("- Интерактивные примеры")
            print("- Оценка знаний")
        else:
            print("❌ Интерфейс не был создан")
    else:
        print("❌ Ошибка при инициализации системы TeachAI")


if __name__ == "__main__":
    main()
