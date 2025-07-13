#!/usr/bin/env python3
"""
Тест исправлений системы релевантности вопросов.
Проверяет, что вопросы о программировании правильно определяются как релевантные.
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


def test_relevance_fix():
    """Тестирует исправления системы релевантности."""

    print("🧪 Тестирование исправлений системы релевантности")
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
        print("✅ Компоненты инициализированы")

        # Тестовые данные урока об операторах сравнения
        lesson_content = """
        <h1>Операторы сравнения в Python</h1>
        <p>В этом уроке мы изучим операторы сравнения в Python.</p>
        <h2>Основные операторы</h2>
        <p>Python поддерживает следующие операторы сравнения:</p>
        <ul>
            <li>== (равно)</li>
            <li>!= (не равно)</li>
            <li>< (меньше)</li>
            <li>> (больше)</li>
            <li><= (меньше или равно)</li>
            <li>>= (больше или равно)</li>
        </ul>
        """

        lesson_data = {
            "title": "Операторы сравнения в Python",
            "description": "Изучение операторов сравнения в Python: ==, !=, <, >, <=, >=",
            "keywords": [
                "Python",
                "операторы",
                "сравнение",
                "==",
                "!=",
                "<",
                ">",
                "<=",
                ">=",
            ],
        }

        print("📚 Тестовый урок загружен")

        # Тестовые вопросы (включая проблемный случай)
        test_questions = [
            {
                "question": "=! - это тоже оператор не равно?",
                "expected": "релевантный",
                "description": "Вопрос об операторе не равно (проблемный случай)",
            },
            {
                "question": "Как работает оператор != в Python?",
                "expected": "релевантный",
                "description": "Вопрос об операторе не равно",
            },
            {
                "question": "Какие операторы сравнения есть в Python?",
                "expected": "релевантный",
                "description": "Вопрос об операторах сравнения",
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
        ]

        print("\n🔍 Тестирование исправленной системы релевантности:")
        print("-" * 60)

        passed_tests = 0
        total_tests = len(test_questions)

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

                print(
                    f"   Результат: {'✅ релевантный' if is_relevant else '❌ нерелевантный'}"
                )
                print(f"   Уверенность: {confidence}%")
                print(f"   Причина: {reason}")

                # Проверяем соответствие ожиданиям
                actual = "релевантный" if is_relevant else "нерелевантный"
                if actual == expected:
                    print(f"   ✅ ТЕСТ ПРОЙДЕН")
                    passed_tests += 1
                else:
                    print(
                        f"   ❌ ТЕСТ НЕ ПРОЙДЕН (ожидалось: {expected}, получено: {actual})"
                    )

            except Exception as e:
                print(f"   ❌ ОШИБКА: {str(e)}")

        print("\n" + "=" * 60)
        print(
            f"📊 Результаты тестирования: {passed_tests}/{total_tests} тестов пройдено"
        )

        if passed_tests == total_tests:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система релевантности исправлена.")
        else:
            print("⚠️ Некоторые тесты не пройдены. Требуется дополнительная настройка.")

        return passed_tests == total_tests

    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        return False


if __name__ == "__main__":
    test_relevance_fix()
