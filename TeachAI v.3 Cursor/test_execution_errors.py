#!/usr/bin/env python3
"""
Тестовый скрипт для проверки обработки ошибок исполнения кода
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from control_tasks_generator import ControlTasksGenerator
from config import ConfigManager

def test_execution_errors():
    """Тестирует обработку ошибок исполнения кода"""
    
    print("🧪 ТЕСТИРОВАНИЕ ОБРАБОТКИ ОШИБОК ИСПОЛНЕНИЯ")
    print("=" * 60)
    
    # Инициализируем генератор
    config = ConfigManager()
    config.load_config()
    api_key = config.get_api_key()
    if not api_key:
        print("❌ API ключ не найден. Пропускаем тест.")
        return
    generator = ControlTasksGenerator(api_key)
    
    # Тестовые случаи с ошибками
    test_cases = [
        {
            "name": "Синтаксическая ошибка",
            "user_code": "x = 5\nif x > 0:\n    print('Положительное')\nelse\n    print('Не положительное')",  # Отсутствует двоеточие
            "expected_output": "Положительное",
            "expected_error": "SyntaxError"
        },
        {
            "name": "Ошибка имени переменной",
            "user_code": "x = 5\nif x > 0:\n    print(y)",  # y не определена
            "expected_output": "Положительное",
            "expected_error": "NameError"
        },
        {
            "name": "Ошибка деления на ноль",
            "user_code": "x = 5\nresult = x / 0\nprint(result)",
            "expected_output": "Положительное",
            "expected_error": "ZeroDivisionError"
        },
        {
            "name": "Правильный код",
            "user_code": "x = 5\nif x > 0:\n    print('Положительное')\nelse:\n    print('Не положительное')",
            "expected_output": "Положительное",
            "expected_error": None
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Тест {i}: {test_case['name']}")
        print("-" * 40)
        
        print(f"Код: {test_case['user_code']}")
        print(f"Ожидаемый вывод: '{test_case['expected_output']}'")
        
        # Тестируем валидацию
        result = generator.validate_task_execution(
            test_case["user_code"],
            test_case["expected_output"]
        )
        
        print(f"Результат валидации:")
        print(f"  is_correct: {result['is_correct']}")
        print(f"  actual_output: '{result['actual_output']}'")
        print(f"  error_message: '{result['error_message']}'")
        
        # Проверяем, что ошибка обрабатывается правильно
        if test_case["expected_error"]:
            if test_case["expected_error"] in result["error_message"]:
                print(f"✅ Ошибка {test_case['expected_error']} правильно обработана")
            else:
                print(f"❌ Ошибка {test_case['expected_error']} не найдена в error_message")
        else:
            if result["error_message"]:
                print(f"❌ Неожиданная ошибка: {result['error_message']}")
            else:
                print(f"✅ Код выполнен без ошибок")
    
    print("\n" + "=" * 60)
    print("📊 ВЫВОДЫ:")
    print("1. Ошибки исполнения должны возвращаться в error_message")
    print("2. Интерфейс должен показывать error_message пользователю")
    print("3. Теперь пользователь будет видеть точную причину сбоя")

if __name__ == "__main__":
    test_execution_errors() 