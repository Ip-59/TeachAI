#!/usr/bin/env python3
"""
Простой тест базовой функциональности TeachAI 2
Тестирует систему пошагово без сложных зависимостей
"""

import os
import sys


def test_api_key():
    """Тестирует API ключ OpenAI."""
    print("🔑 Тест API ключа...")

    # Проверяем .env файл
    if not os.path.exists(".env"):
        print("   ❌ .env файл не найден")
        return False

    try:
        # Загружаем переменные окружения
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("OPENAI_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    if key and key != "ваш-ключ-здесь":
                        print(f"   ✅ API ключ найден (длина: {len(key)})")

                        # Устанавливаем переменную окружения
                        os.environ["OPENAI_API_KEY"] = key
                        return True
                    else:
                        print("   ❌ API ключ не настроен")
                        return False

        print("   ❌ OPENAI_API_KEY не найден в .env")
        return False

    except Exception as e:
        print(f"   ❌ Ошибка чтения .env: {e}")
        return False


def test_openai_connection():
    """Тестирует подключение к OpenAI."""
    print("🌐 Тест подключения к OpenAI...")

    try:
        import openai

        print("   ✅ openai модуль загружен")
    except ImportError:
        print("   ❌ openai модуль не установлен")
        print("   УСТАНОВИТЕ: pip install openai")
        return False

    # Проверяем API ключ
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("   ❌ API ключ не загружен")
        return False

    try:
        # Минимальный тест API
        openai.api_key = api_key

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=5,
        )

        print("   ✅ API подключение работает")
        return True

    except Exception as e:
        error_str = str(e).lower()

        if "authentication" in error_str or "api key" in error_str:
            print("   ❌ Неверный API ключ")
            print("   РЕШЕНИЕ: Проверьте ключ на https://platform.openai.com/api-keys")
        elif "rate limit" in error_str:
            print("   ⚠️ Превышен лимит запросов")
            print("   РЕШЕНИЕ: Подождите несколько минут")
        elif "connection" in error_str:
            print("   ❌ Проблема с интернет соединением")
            print("   РЕШЕНИЕ: Проверьте интернет и статус OpenAI")
        else:
            print(f"   ❌ Ошибка API: {e}")

        return False


def test_engine_init():
    """Тестирует инициализацию engine."""
    print("⚙️ Тест инициализации engine...")

    # Добавляем текущую директорию в путь
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())

    try:
        from engine import TeachAIEngine

        print("   ✅ engine модуль импортирован")
    except ImportError as e:
        print(f"   ❌ Ошибка импорта engine: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Ошибка в engine модуле: {e}")
        return False

    try:
        engine = TeachAIEngine()
        print("   ✅ TeachAIEngine создан")
    except Exception as e:
        print(f"   ❌ Ошибка создания engine: {e}")
        return False

    try:
        result = engine.initialize()
        if result.get("success"):
            print("   ✅ Engine инициализирован")
            return True
        else:
            print(
                f"   ❌ Ошибка инициализации: {result.get('error', 'Неизвестная ошибка')}"
            )
            return False
    except Exception as e:
        print(f"   ❌ Исключение при инициализации: {e}")
        return False


def test_lesson_generation():
    """Тестирует генерацию урока."""
    print("📚 Тест генерации урока...")

    try:
        from content_generator import ContentGenerator

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("   ❌ API ключ недоступен")
            return False

        generator = ContentGenerator(api_key)
        print("   ✅ ContentGenerator создан")

        # Простой тест генерации
        lesson_content = generator.generate_lesson_content(
            lesson_data={"title": "Тест", "id": "test"},
            user_data={"name": "Тест", "communication_style": "friendly"},
            course_context={"course_name": "Тест курс"},
        )

        if lesson_content:
            print("   ✅ Урок сгенерирован")
            print(f"   📄 Тип результата: {type(lesson_content)}")
            if isinstance(lesson_content, dict) and "content" in lesson_content:
                content_length = (
                    len(lesson_content["content"]) if lesson_content["content"] else 0
                )
                print(f"   📄 Длина контента: {content_length} символов")
            return True
        else:
            print("   ❌ Пустой результат генерации")
            return False

    except Exception as e:
        error_str = str(e).lower()

        if "connection" in error_str:
            print("   ❌ Ошибка подключения к API")
        elif "rate limit" in error_str:
            print("   ❌ Превышен лимит запросов")
        elif "authentication" in error_str:
            print("   ❌ Ошибка аутентификации API")
        else:
            print(f"   ❌ Ошибка генерации: {e}")

        return False


def main():
    """Главная функция тестирования."""
    print("🧪 ПРОСТОЙ ТЕСТ TEACHAI 2")
    print("=" * 30)

    tests = [
        ("API ключ", test_api_key),
        ("OpenAI подключение", test_openai_connection),
        ("Инициализация engine", test_engine_init),
        ("Генерация урока", test_lesson_generation),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print()  # Пустая строка между тестами
        except Exception as e:
            print(f"   💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
            results.append((test_name, False))
            print()

    # Итоговый отчет
    print("=" * 30)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТОВ:")

    passed = 0
    for test_name, result in results:
        status = "✅ ПРОШЕЛ" if result else "❌ ПРОВАЛЕН"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1

    print(f"\nПрошло тестов: {passed}/{len(results)}")

    if passed == len(results):
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ! Система готова к работе.")
    elif passed >= len(results) // 2:
        print("⚠️ Часть тестов прошла. Устраните провалы.")
    else:
        print("❌ Большинство тестов провалено. Требуется настройка.")

    print("\n🎯 ЧТО ДЕЛАТЬ ДАЛЬШЕ:")
    if passed == len(results):
        print("1. Запустите teachai.ipynb")
        print("2. Протестируйте интерактивные функции")
    else:
        print("1. Устраните провалившиеся тесты")
        print("2. Установите недостающие модули")
        print("3. Настройте API ключ")
        print("4. Перезапустите тест")


if __name__ == "__main__":
    main()
