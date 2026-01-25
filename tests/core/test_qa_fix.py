"""
Простой тест для проверки исправления ошибки с вопросами.
Проверяет, что система вопросов работает без ошибки 'course'.
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_generator import ContentGenerator
from config import ConfigManager


def test_qa_fix():
    """Тестирует исправление ошибки с вопросами."""

    print("🧪 Тестирование исправления ошибки с вопросами")
    print("=" * 60)

    try:
        # Инициализируем компоненты
        config = ConfigManager()
        config.load_config()
        api_key = config.get_api_key()

        if not api_key:
            print("❌ API ключ не найден. Проверьте .env файл")
            return False

        content_generator = ContentGenerator(api_key)

        print("✅ ContentGenerator инициализирован")

        # Тестовые данные
        test_data = {
            "course": "Основы Python",
            "section": "Основы Python и синтаксис",
            "topic": "Введение в Python",
            "lesson": "Основы синтаксиса",
            "user_question": "Как создать переменную в Python?",
            "lesson_content": """
            <h1>Основы синтаксиса Python</h1>
            <p>В этом уроке мы изучим основные элементы синтаксиса языка Python.</p>

            <h2>Переменные</h2>
            <p>Переменные в Python создаются с помощью оператора присваивания =</p>
            <pre><code>name = "Иван"
age = 25
height = 1.75</code></pre>
            """,
            "user_name": "Тестовый пользователь",
            "communication_style": "friendly",
        }

        print("📚 Тестовые данные подготовлены")

        # Тестируем генерацию ответа на вопрос
        print("\n🔍 Тестирование генерации ответа на вопрос:")
        print("-" * 60)

        try:
            answer = content_generator.answer_question(
                course=test_data["course"],
                section=test_data["section"],
                topic=test_data["topic"],
                lesson=test_data["lesson"],
                user_question=test_data["user_question"],
                lesson_content=test_data["lesson_content"],
                user_name=test_data["user_name"],
                communication_style=test_data["communication_style"],
            )

            print(f"✅ Ответ успешно сгенерирован!")
            print(f"📝 Длина ответа: {len(answer)} символов")
            print(f"🔍 Первые 100 символов: {answer[:100]}...")

        except Exception as e:
            print(f"❌ ОШИБКА при генерации ответа: {str(e)}")
            return False

        # Тестируем проверку релевантности
        print("\n🔍 Тестирование проверки релевантности:")
        print("-" * 60)

        lesson_data = {
            "title": "Основы синтаксиса Python",
            "description": "Изучение базовых элементов синтаксиса языка Python",
            "keywords": ["Python", "синтаксис", "переменные"],
        }

        try:
            relevance_result = content_generator.check_question_relevance(
                test_data["user_question"], test_data["lesson_content"], lesson_data
            )

            print(f"✅ Проверка релевантности выполнена!")
            print(
                f"📊 Результат: {'релевантный' if relevance_result['is_relevant'] else 'нерелевантный'}"
            )
            print(f"🎯 Уверенность: {relevance_result['confidence']}%")

        except Exception as e:
            print(f"❌ ОШИБКА при проверке релевантности: {str(e)}")
            return False

        print("\n" + "=" * 60)
        print("🎉 Тестирование завершено успешно!")
        print("✅ Ошибка с вопросами исправлена")
        print("✅ Система вопросов работает корректно")

        return True

    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        return False


if __name__ == "__main__":
    test_qa_fix()
