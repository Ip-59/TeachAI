#!/usr/bin/env python3
"""
Упрощенная диагностика TeachAI 2
Проверяет только базовые вещи без сложных импортов
"""

import os
import sys

print("🔍 УПРОЩЕННАЯ ДИАГНОСТИКА TEACHAI 2")
print("=" * 40)

# 1. Проверка Python версии
print(f"1. Python версия: {sys.version}")

# 2. Проверка текущей директории
print(f"2. Текущая директория: {os.getcwd()}")

# 3. Проверка файлов проекта
required_files = [
    "engine.py",
    "state_manager.py",
    "content_generator.py",
    "lesson_interface.py",
    "lesson_interactive_handlers.py",
    "assessment_interface.py",
    "interface_facade.py",
    "teachai.ipynb",
]

print("\n3. Проверка файлов проекта:")
missing_files = []
for file in required_files:
    if os.path.exists(file):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file}")
        missing_files.append(file)

# 4. Проверка .env файла
print("\n4. Проверка .env файла:")
if os.path.exists(".env"):
    print("   ✅ .env файл существует")
    try:
        with open(".env", "r") as f:
            content = f.read()
        if "OPENAI_API_KEY" in content:
            print("   ✅ OPENAI_API_KEY найден в .env")
            # Проверяем значение ключа
            for line in content.split("\n"):
                if line.startswith("OPENAI_API_KEY="):
                    key_value = line.split("=", 1)[1].strip()
                    if key_value and key_value != "ваш-ключ-здесь":
                        print(f"   ✅ API ключ установлен (длина: {len(key_value)})")
                    else:
                        print("   ❌ API ключ не настроен (используется шаблон)")
        else:
            print("   ❌ OPENAI_API_KEY не найден в .env")
    except Exception as e:
        print(f"   ❌ Ошибка чтения .env: {e}")
else:
    print("   ❌ .env файл не найден")

# 5. Проверка базовых импортов
print("\n5. Проверка базовых модулей:")
test_modules = [
    ("os", "os"),
    ("sys", "sys"),
    ("logging", "logging"),
    ("ipywidgets", "ipywidgets"),
    ("dotenv", "python-dotenv"),
]

for module_name, package_name in test_modules:
    try:
        __import__(module_name)
        print(f"   ✅ {module_name}")
    except ImportError:
        print(f"   ❌ {module_name} (установите: pip install {package_name})")

# 6. Проверка OpenAI
print("\n6. Проверка OpenAI:")
try:
    import openai

    print("   ✅ openai модуль доступен")
except ImportError:
    print("   ❌ openai модуль не установлен (pip install openai)")

# 7. Попытка импорта модулей проекта
print("\n7. Проверка модулей проекта:")
project_modules = ["engine", "state_manager", "content_generator"]

for module in project_modules:
    if f"{module}.py" in missing_files:
        print(f"   ⏭️ {module} (файл отсутствует)")
        continue

    try:
        # Добавляем текущую директорию в путь
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())

        __import__(module)
        print(f"   ✅ {module}")
    except Exception as e:
        print(f"   ❌ {module}: {str(e)}")

# Итоговый результат
print("\n" + "=" * 40)
print("📊 РЕЗУЛЬТАТ ПРОВЕРКИ:")

if missing_files:
    print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
    print("РЕШЕНИЕ: Убедитесь что все файлы проекта в текущей директории")
else:
    print("✅ Все файлы проекта найдены")

if not os.path.exists(".env"):
    print("❌ Нет .env файла")
    print("РЕШЕНИЕ: Создайте .env файл с OPENAI_API_KEY=ваш-ключ")
else:
    print("✅ .env файл настроен")

print("\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
print("1. Устраните отмеченные ❌ проблемы")
print("2. Установите недостающие модули: pip install openai python-dotenv ipywidgets")
print("3. Настройте API ключ в .env файле")
print("4. Попробуйте запустить простой тест системы")

print("\n" + "=" * 40)
