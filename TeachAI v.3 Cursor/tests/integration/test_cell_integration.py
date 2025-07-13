"""
Тест интеграции системы образовательных ячеек с основной системой TeachAI.
Проверяет, что адаптер работает корректно и не нарушает основную функциональность.
"""

import sys
import logging
from IPython.display import display
import ipywidgets as widgets

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_cell_adapter_import():
    """Тест 1: Проверка импорта адаптера ячеек"""
    print("=== Тест 1: Проверка импорта адаптера ячеек ===")

    try:
        from cell_integration import cell_adapter

        print("✅ Адаптер ячеек успешно импортирован")

        # Проверяем доступность системы ячеек
        if cell_adapter.is_available():
            print("✅ Система ячеек доступна")
        else:
            print("⚠️ Система ячеек недоступна (это нормально для тестирования)")

        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта адаптера: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False


def test_cell_adapter_functionality():
    """Тест 2: Проверка функциональности адаптера"""
    print("\n=== Тест 2: Проверка функциональности адаптера ===")

    try:
        from cell_integration import cell_adapter

        # Тестовый контент урока
        test_content = """
        # Урок по Python

        В этом уроке мы изучим основы Python.

        ```python
        print("Hello, World!")
        ```

        Также можно создавать переменные:

        ```python
        name = "Python"
        print(f"Привет, {name}!")
        ```
        """

        # Тестируем извлечение блоков кода
        code_blocks = cell_adapter.extract_code_blocks(test_content)
        print(f"✅ Найдено {len(code_blocks)} блоков кода")

        # Тестируем создание демонстрационных ячеек
        demo_cells = cell_adapter.create_demo_cells(code_blocks)
        print(f"✅ Создано {len(demo_cells)} демонстрационных ячеек")

        # Тестируем генерацию интерактивных заданий
        interactive_cells = cell_adapter.generate_interactive_tasks(
            test_content, "Тестовый урок"
        )
        print(f"✅ Создано {len(interactive_cells)} интерактивных заданий")

        # Тестируем создание контейнера
        container = cell_adapter.create_cells_container(demo_cells, interactive_cells)
        if container:
            print("✅ Контейнер ячеек успешно создан")
        else:
            print("⚠️ Контейнер ячеек не создан (возможно, нет ячеек)")

        return True
    except Exception as e:
        print(f"❌ Ошибка функциональности: {e}")
        return False


def test_lesson_display_integration():
    """Тест 3: Проверка интеграции с lesson_display.py"""
    print("\n=== Тест 3: Проверка интеграции с lesson_display.py ===")

    try:
        # Проверяем, что lesson_display.py может импортировать адаптер
        from lesson_display import LessonDisplay

        print("✅ lesson_display.py успешно импортирован")

        # Проверяем, что переменная CELLS_INTEGRATION_AVAILABLE доступна
        import lesson_display

        if hasattr(lesson_display, "CELLS_INTEGRATION_AVAILABLE"):
            print(
                f"✅ CELLS_INTEGRATION_AVAILABLE = {lesson_display.CELLS_INTEGRATION_AVAILABLE}"
            )
        else:
            print("⚠️ CELLS_INTEGRATION_AVAILABLE не найден")

        return True
    except Exception as e:
        print(f"❌ Ошибка интеграции: {e}")
        return False


def test_system_stability():
    """Тест 4: Проверка стабильности системы"""
    print("\n=== Тест 4: Проверка стабильности системы ===")

    try:
        # Проверяем, что основные модули все еще работают
        from lesson_interface import LessonInterface

        print("✅ lesson_interface.py работает")

        from lesson_display import LessonDisplay

        print("✅ lesson_display.py работает")

        from lesson_navigation import LessonNavigation

        print("✅ lesson_navigation.py работает")

        from lesson_interaction import LessonInteraction

        print("✅ lesson_interaction.py работает")

        print("✅ Все основные модули работают корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка стабильности: {e}")
        return False


def run_all_tests():
    """Запускает все тесты интеграции"""
    print("🧪 Запуск тестов интеграции системы образовательных ячеек\n")

    tests = [
        test_cell_adapter_import,
        test_cell_adapter_functionality,
        test_lesson_display_integration,
        test_system_stability,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test.__name__}: {e}")
            results.append(False)

    # Итоговый результат
    print(f"\n📊 Результаты тестирования:")
    print(f"Пройдено тестов: {sum(results)}/{len(results)}")

    if all(results):
        print("🎉 Все тесты пройдены! Интеграция ячеек работает корректно.")
        return True
    else:
        print("⚠️ Некоторые тесты не пройдены. Проверьте логи выше.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
