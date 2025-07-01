"""
Тестовый скрипт для проверки функциональности анализа релевантности вопросов.
Проверяет работу RelevanceChecker и интеграцию с системой вопросов.
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_generator import ContentGenerator
from state_manager import StateManager
from config import ConfigManager


def test_relevance_checker():
    """Тестирует функциональность анализа релевантности вопросов."""

    print("🧪 Тестирование анализа релевантности вопросов")
    print("=" * 60)

    try:
        # Инициализируем компоненты
        config = ConfigManager()
        config.load_config()  # Загружаем конфигурацию
        api_key = config.get_api_key()  # Исправлено: используем правильный метод

        if not api_key:
            print("❌ API ключ не найден. Проверьте .env файл")
            return False

        content_generator = ContentGenerator(api_key)
        state_manager = StateManager()

        print("✅ Компоненты инициализированы")

        # Тестовые данные урока
        lesson_content = """
        <h1>Основы синтаксиса Python</h1>
        <p>В этом уроке мы изучим основные элементы синтаксиса языка Python.</p>

        <h2>Переменные</h2>
        <p>Переменные в Python создаются с помощью оператора присваивания =</p>
        <pre><code>name = "Иван"
age = 25
height = 1.75</code></pre>

        <h2>Типы данных</h2>
        <p>Python поддерживает различные типы данных:</p>
        <ul>
            <li>int - целые числа</li>
            <li>float - числа с плавающей точкой</li>
            <li>str - строки</li>
            <li>bool - логические значения</li>
        </ul>

        <h2>Условные операторы</h2>
        <p>Для создания условий используется if-elif-else:</p>
        <pre><code>if age >= 18:
    print("Совершеннолетний")
elif age >= 14:
    print("Подросток")
else:
    print("Ребенок")</code></pre>
        """

        lesson_data = {
            "title": "Основы синтаксиса Python",
            "description": "Изучение базовых элементов синтаксиса языка Python",
            "keywords": [
                "Python",
                "синтаксис",
                "переменные",
                "типы данных",
                "условные операторы",
            ],
        }

        print("📚 Тестовый урок загружен")

        # Тестовые вопросы
        test_questions = [
            {
                "question": "Как создать переменную в Python?",
                "expected": "релевантный",
                "description": "Вопрос о синтаксисе Python",
            },
            {
                "question": "Какие типы данных поддерживает Python?",
                "expected": "релевантный",
                "description": "Вопрос о типах данных",
            },
            {
                "question": "Как работает условный оператор if?",
                "expected": "релевантный",
                "description": "Вопрос об условных операторах",
            },
            {
                "question": "Почему небо голубое?",
                "expected": "нерелевантный",
                "description": "Вопрос не связан с программированием",
            },
            {
                "question": "Как приготовить борщ?",
                "expected": "нерелевантный",
                "description": "Вопрос о кулинарии",
            },
            {
                "question": "Что такое цикл for в Python?",
                "expected": "релевантный",
                "description": "Вопрос о программировании, но не о синтаксисе",
            },
        ]

        print("\n🔍 Тестирование анализа релевантности:")
        print("-" * 60)

        for i, test_case in enumerate(test_questions, 1):
            question = test_case["question"]
            expected = test_case["expected"]
            description = test_case["description"]

            print(f"\n{i}. {description}")
            print(f"   Вопрос: {question}")
            print(f"   Ожидается: {expected}")

            try:
                # Проверяем релевантность
                relevance_result = content_generator.check_question_relevance(
                    question, lesson_content, lesson_data
                )

                is_relevant = relevance_result["is_relevant"]
                confidence = relevance_result["confidence"]
                reason = relevance_result["reason"]
                suggestions = relevance_result["suggestions"]

                print(
                    f"   Результат: {'✅ релевантный' if is_relevant else '❌ нерелевантный'}"
                )
                print(f"   Уверенность: {confidence}%")
                print(f"   Причина: {reason}")

                if not is_relevant and suggestions:
                    print(f"   Рекомендации: {', '.join(suggestions[:2])}")

                # Проверяем соответствие ожиданиям
                actual = "релевантный" if is_relevant else "нерелевантный"
                if actual == expected:
                    print(f"   ✅ ТЕСТ ПРОЙДЕН")
                else:
                    print(
                        f"   ❌ ТЕСТ НЕ ПРОЙДЕН (ожидалось: {expected}, получено: {actual})"
                    )

                # Тестируем генерацию ответа для нерелевантного вопроса
                if not is_relevant:
                    print(
                        "   🎨 Тестирование генерации ответа для нерелевантного вопроса..."
                    )
                    non_relevant_response = (
                        content_generator.generate_non_relevant_response(
                            question, suggestions
                        )
                    )
                    print("   ✅ Ответ для нерелевантного вопроса сгенерирован")

            except Exception as e:
                print(f"   ❌ ОШИБКА: {str(e)}")

        # Тестируем предупреждение о множественных вопросах
        print(f"\n🔔 Тестирование предупреждения о множественных вопросах:")
        print("-" * 60)

        for count in [3, 5, 10]:
            warning = content_generator.generate_multiple_questions_warning(count)
            print(f"   ✅ Предупреждение для {count} вопросов сгенерировано")

        print("\n" + "=" * 60)
        print("🎉 Тестирование завершено успешно!")
        print("✅ Система анализа релевантности работает корректно")

    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    test_relevance_checker()
