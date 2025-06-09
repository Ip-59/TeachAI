"""
ИСПРАВЛЕННЫЙ диагностический скрипт для выявления причины проблемы #121
Запустите этот код в Jupyter Notebook для диагностики
"""

import os
import json
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("diagnostic")


def diagnose_state_file():
    """Диагностика файла state.json"""
    print("=== ДИАГНОСТИКА ФАЙЛА STATE.JSON ===\n")

    # Исправленный путь к файлу
    state_file = os.path.join("data", "state.json")

    # 1. Проверка существования файла
    if os.path.exists(state_file):
        print(f"✅ Файл {state_file} существует")
        print(f"   Размер: {os.path.getsize(state_file)} байт")
        print(f"   Путь: {os.path.abspath(state_file)}\n")
    else:
        print(f"❌ Файл {state_file} НЕ существует")
        print(f"   Ожидаемый путь: {os.path.abspath(state_file)}\n")
        return

    # 2. Чтение и анализ содержимого
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state_data = json.load(f)

        print("✅ Файл успешно прочитан как JSON")
        print(f"   Ключи верхнего уровня: {list(state_data.keys())}\n")

        # 3. Проверка структуры user (ИСПРАВЛЕНО)
        if "user" in state_data:
            user = state_data["user"]
            print("📋 Данные user:")
            print(f"   - name: {user.get('name', 'НЕ НАЙДЕНО')}")
            print(
                f"   - total_study_hours: {user.get('total_study_hours', 'НЕ НАЙДЕНО')}"
            )
            print(
                f"   - lesson_duration_minutes: {user.get('lesson_duration_minutes', 'НЕ НАЙДЕНО')}"
            )
            print(
                f"   - communication_style: {user.get('communication_style', 'НЕ НАЙДЕНО')}\n"
            )
        else:
            print("❌ Ключ 'user' НЕ НАЙДЕН в state.json\n")

        # 4. Проверка learning (ИСПРАВЛЕНО)
        if "learning" in state_data:
            learning = state_data["learning"]
            print("📊 Данные learning:")
            print(
                f"   - current_lesson: {learning.get('current_lesson', 'НЕ НАЙДЕНО')}"
            )
            print(f"   - Ключи learning: {list(learning.keys())}\n")
        else:
            print("❌ Ключ 'learning' НЕ НАЙДЕН в state.json\n")

        # 5. Проверка course_plan (ИСПРАВЛЕНО)
        if "course_plan" in state_data:
            course_plan = state_data["course_plan"]
            print("📚 Данные course_plan:")
            if course_plan:
                print(f"   - title: {course_plan.get('title', 'НЕ НАЙДЕНО')}")
                print(f"   - sections: {len(course_plan.get('sections', []))} разделов")
            else:
                print("   - course_plan пустой")
            print()
        else:
            print("❌ Ключ 'course_plan' НЕ НАЙДЕН в state.json\n")

    except json.JSONDecodeError as e:
        print(f"❌ Ошибка чтения JSON: {e}\n")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}\n")


def test_has_user_profile_logic():
    """Тестирование логики проверки профиля"""
    print("=== ТЕСТИРОВАНИЕ ЛОГИКИ has_user_profile ===\n")

    # Эмуляция логики из engine.py
    try:
        from state_manager import StateManager

        # Создаем StateManager с правильным путем
        state_file_path = os.path.join("data", "state.json")
        sm = StateManager(state_file=state_file_path)

        # Проверяем загруженное состояние
        print("📋 Загруженное состояние StateManager:")
        print(f"   - Ключи состояния: {list(sm.state.keys())}")

        # ИСПРАВЛЕНО: Используем правильный метод get_user_data()
        user_data = sm.get_user_data()
        print(f"\n📋 get_user_data() вернул:")
        print(f"   - Тип: {type(user_data)}")
        print(f"   - Содержимое: {user_data}")

        # Проверка условий из engine.py
        print("\n🔍 Проверка условий has_user_profile:")

        # Условие 1: user_data не пустые
        condition1 = bool(user_data)
        print(f"   1. user_data не пустые: {condition1}")

        if user_data:
            # Условие 2: name существует и не пустое
            name = user_data.get("name", "")
            condition2 = bool(name) and name != "Введите ваше имя"
            print(f"   2. name валидно: {condition2} (name='{name}')")

            # Условие 3: total_study_hours существует
            condition3 = (
                "total_study_hours" in user_data and user_data["total_study_hours"]
            )
            print(f"   3. total_study_hours: {condition3}")

            # Условие 4: lesson_duration_minutes существует
            condition4 = (
                "lesson_duration_minutes" in user_data
                and user_data["lesson_duration_minutes"]
            )
            print(f"   4. lesson_duration_minutes: {condition4}")

            # Условие 5: communication_style существует
            condition5 = (
                "communication_style" in user_data and user_data["communication_style"]
            )
            print(f"   5. communication_style: {condition5}")

            # Итоговый результат
            has_profile = (
                condition1 and condition2 and condition3 and condition4 and condition5
            )
        else:
            condition2 = condition3 = condition4 = condition5 = False
            print(f"   2-5. Остальные условия: False (user_data пустые)")
            has_profile = False

        print(f"\n✅ Итоговый результат has_user_profile: {has_profile}")

        # Дополнительно: проверяем learning_progress
        print(f"\n📊 Дополнительно - learning_progress:")
        learning_progress = sm.get_learning_progress()
        print(f"   - learning_progress: {learning_progress}")

    except ImportError as e:
        print(f"❌ Ошибка импорта StateManager: {e}")
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback

        traceback.print_exc()


def test_state_manager_creation():
    """Тестирование создания StateManager и файла состояния"""
    print("=== ТЕСТИРОВАНИЕ СОЗДАНИЯ STATE MANAGER ===\n")

    try:
        from state_manager import StateManager

        # Создаем StateManager
        print("📋 Создание StateManager...")
        state_file_path = os.path.join("data", "state.json")
        sm = StateManager(state_file=state_file_path)

        # Проверяем что файл создался
        if os.path.exists(state_file_path):
            print(f"✅ Файл {state_file_path} создан")

            # Читаем содержимое
            with open(state_file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
            print(f"   - Структура: {list(content.keys())}")
            print(f"   - user пустой: {not bool(content.get('user', {}))}")
        else:
            print(f"❌ Файл {state_file_path} НЕ создан")

        # Создаем тестовый профиль
        print("\n📝 Создание тестового профиля...")
        test_profile = {
            "name": "Тестовый Пользователь",
            "total_study_hours": 10,
            "lesson_duration_minutes": 30,
            "communication_style": "Дружелюбный",
        }

        result = sm.save_user_profile(test_profile)
        print(f"   - Сохранение: {'✅ успешно' if result else '❌ ошибка'}")

        # Проверяем что профиль сохранился
        saved_profile = sm.get_user_data()
        print(f"   - Загружено: {saved_profile}")

        # Эмулируем проверку has_user_profile
        has_profile_result = test_has_profile_with_data(saved_profile)
        print(f"   - has_user_profile результат: {has_profile_result}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback

        traceback.print_exc()


def test_has_profile_with_data(user_data):
    """Тестирует логику has_user_profile с реальными данными"""
    if not user_data:
        return False

    required_fields = [
        "name",
        "total_study_hours",
        "lesson_duration_minutes",
        "communication_style",
    ]

    for field in required_fields:
        if field not in user_data or not user_data[field]:
            return False

    # Проверка на placeholder значения
    if user_data.get("name") == "Введите ваше имя":
        return False

    return True


def suggest_fixes():
    """Предложения по исправлению"""
    print("\n=== РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ ===\n")

    print("1. Если state.json не создается автоматически:")
    print("   - Проверьте права на запись в папку data/")
    print("   - Убедитесь что StateManager.save_state() вызывается при инициализации\n")

    print("2. Если профиль не распознается:")
    print("   - Убедитесь что все обязательные поля заполнены")
    print("   - Проверьте что name != 'Введите ваше имя'")
    print("   - Проверьте логику в engine.has_user_profile()\n")

    print("3. Исправления в коде:")
    print("   - В engine.py использовать get_user_data() вместо get_user_profile()")
    print("   - Убедиться что StateManager сохраняет файл при создании")
    print("   - Проверить все пути к файлам (должны быть data/state.json)\n")


# Запуск диагностики
if __name__ == "__main__":
    diagnose_state_file()
    print("\n" + "=" * 50 + "\n")
    test_state_manager_creation()
    print("\n" + "=" * 50 + "\n")
    test_has_user_profile_logic()
    print("\n" + "=" * 50 + "\n")
    suggest_fixes()
