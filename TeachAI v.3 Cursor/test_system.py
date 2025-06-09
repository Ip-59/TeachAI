#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы системы TeachAI после рефакторинга.
Проверяет импорты и базовую функциональность.
"""

import sys
import traceback


def test_imports():
    """Тестирует импорты всех основных модулей."""
    print("🔍 Тестирование импортов...")

    try:
        # Тест основных модулей
        print("  📦 Импорт engine...")
        from engine import TeachAIEngine

        print("    ✅ engine.py - OK")

        print("  📦 Импорт examples_generator...")
        from examples_generator import ExamplesGenerator

        print("    ✅ examples_generator.py - OK")

        print("  📦 Импорт examples_generation...")
        from examples_generation import ExamplesGeneration

        print("    ✅ examples_generation.py - OK")

        print("  📦 Импорт examples_validation...")
        from examples_validation import ExamplesValidation

        print("    ✅ examples_validation.py - OK")

        print("  📦 Импорт content_generator...")
        from content_generator import ContentGenerator

        print("    ✅ content_generator.py - OK")

        print("  📦 Импорт lesson_interface...")
        from lesson_interface import LessonInterface

        print("    ✅ lesson_interface.py - OK")

        print("  📦 Импорт lesson_display...")
        from lesson_display import LessonDisplay

        print("    ✅ lesson_display.py - OK")

        print("  📦 Импорт lesson_navigation...")
        from lesson_navigation import LessonNavigation

        print("    ✅ lesson_navigation.py - OK")

        print("  📦 Импорт lesson_interaction...")
        from lesson_interaction import LessonInteraction

        print("    ✅ lesson_interaction.py - OK")

        print("  📦 Импорт lesson_utils...")
        from lesson_utils import LessonUtils

        print("    ✅ lesson_utils.py - OK")

        print("✅ Все импорты работают корректно!")
        return True

    except Exception as e:
        print(f"❌ Ошибка импорта: {str(e)}")
        print(f"🔍 Детали: {traceback.format_exc()}")
        return False


def test_objects_creation():
    """Тестирует создание объектов основных классов."""
    print("\n🔍 Тестирование создания объектов...")

    try:
        # Тест создания TeachAIEngine
        print("  🏗️ Создание TeachAIEngine...")
        from engine import TeachAIEngine

        engine = TeachAIEngine()
        print("    ✅ TeachAIEngine создан успешно")

        # Тест создания ExamplesGenerator
        print("  🏗️ Создание ExamplesGenerator...")
        from examples_generator import ExamplesGenerator

        examples_gen = ExamplesGenerator("test_api_key")
        print("    ✅ ExamplesGenerator создан успешно")

        # Тест создания ExamplesGeneration
        print("  🏗️ Создание ExamplesGeneration...")
        from examples_generation import ExamplesGeneration

        examples_gen_module = ExamplesGeneration("test_api_key")
        print("    ✅ ExamplesGeneration создан успешно")

        # Тест создания ExamplesValidation
        print("  🏗️ Создание ExamplesValidation...")
        from examples_validation import ExamplesValidation

        examples_val = ExamplesValidation("test_api_key")
        print("    ✅ ExamplesValidation создан успешно")

        print("✅ Все объекты создаются корректно!")
        return True

    except Exception as e:
        print(f"❌ Ошибка создания объекта: {str(e)}")
        print(f"🔍 Детали: {traceback.format_exc()}")
        return False


def test_delegation():
    """Тестирует делегирование методов в ExamplesGenerator."""
    print("\n🔍 Тестирование делегирования методов...")

    try:
        from examples_generator import ExamplesGenerator

        # Создаем объект
        generator = ExamplesGenerator("test_api_key")

        # Тестируем делегирование методов
        print("  🔄 Тест делегирования _determine_course_subject...")
        result = generator._determine_course_subject({}, "Python урок", ["python"])
        print(f"    ✅ Результат: {result}")

        print("  🔄 Тест делегирования _validate_examples_relevance...")
        result = generator._validate_examples_relevance("print('Hello')", "Python")
        print(f"    ✅ Результат: {result}")

        print("  🔄 Тест делегирования _create_fallback_python_example...")
        result = generator._create_fallback_python_example("Тестовый урок")
        print(f"    ✅ Fallback пример создан (длина: {len(result)} символов)")

        print("✅ Все делегирующие методы работают корректно!")
        return True

    except Exception as e:
        print(f"❌ Ошибка делегирования: {str(e)}")
        print(f"🔍 Детали: {traceback.format_exc()}")
        return False


def main():
    """Основная функция тестирования."""
    print("🚀 Тестирование системы TeachAI после рефакторинга")
    print("=" * 60)

    # Тестируем импорты
    if not test_imports():
        print("\n❌ Тест импортов провален!")
        return False

    # Тестируем создание объектов
    if not test_objects_creation():
        print("\n❌ Тест создания объектов провален!")
        return False

    # Тестируем делегирование
    if not test_delegation():
        print("\n❌ Тест делегирования провален!")
        return False

    print("\n" + "=" * 60)
    print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("✅ Система TeachAI готова к запуску!")
    print("\n💡 Для запуска используйте:")
    print("   - Jupyter Notebook: TeachAI.ipynb")
    print("   - Или: python main.py")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
