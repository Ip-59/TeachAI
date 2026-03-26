"""
Запуск TeachAI без Jupyter Notebook
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

from engine import TeachAIEngine


def main():
    """Запуск TeachAI"""
    print("🚀 Запуск TeachAI...")
    print("=" * 50)

    # Создаем экземпляр движка
    engine = TeachAIEngine()

    # Инициализируем систему
    if engine.initialize():
        print("✅ Система TeachAI успешно инициализирована")

        # Запускаем интерфейс
        interface_element = engine.start()

        # Проверяем, что интерфейс создан
        if interface_element:
            print("✅ Интерфейс создан успешно!")
            print("🎯 TeachAI готов к работе!")

            # Здесь можно добавить логику для работы с интерфейсом
            print("\n📋 Доступные функции:")
            print("- Генерация уроков")
            print("- Интерактивные примеры")
            print("- Оценка знаний")
            print("- MCP интеграция")

        else:
            print("❌ Интерфейс не был создан")
    else:
        print("❌ Ошибка при инициализации системы TeachAI")


if __name__ == "__main__":
    main()
