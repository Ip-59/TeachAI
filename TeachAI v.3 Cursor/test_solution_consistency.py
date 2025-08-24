#!/usr/bin/env python3
"""
Тестовый скрипт для проверки соответствия эталонного решения и expected_output
"""

import io
from contextlib import redirect_stdout

def test_solution_consistency():
    """Тестирует соответствие эталонного решения и expected_output"""
    
    # Тестовые случаи из реальной проблемы
    test_cases = [
        {
            "name": "Проблемный случай из пользователя",
            "solution_code": """my_list = [1, 2, 3, 'apple', 'banana', 'cherry']
my_dict = {'name': 'Alice', 'age': 30, 'city': 'New York'}
my_list.append(4)
my_list.insert(3, 'orange')  # Неправильно! Должно быть insert(2, 'orange')
my_list.remove('banana')
my_dict['email'] = 'alice@example.com'
print(my_list)
print(my_dict)""",
            "expected_output": "[1, 2, 3, 'orange', 'apple', 'cherry', 4]\n{'name': 'Alice', 'city': 'New York', 'email': 'alice@example.com'}"
        },
        {
            "name": "Правильное решение",
            "solution_code": """my_list = [1, 2, 3, 'apple', 'banana', 'cherry']
my_dict = {'name': 'Alice', 'age': 30, 'city': 'New York'}
my_list.append(4)
my_list.insert(2, 'orange')  # Правильно! Индекс 2
my_list.remove('banana')
my_dict['email'] = 'alice@example.com'
print(my_list)
print(my_dict)""",
            "expected_output": "[1, 2, 'orange', 3, 'apple', 'cherry', 4]\n{'name': 'Alice', 'age': 30, 'city': 'New York', 'email': 'alice@example.com'}"
        }
    ]
    
    print("🧪 ТЕСТИРОВАНИЕ СООТВЕТСТВИЯ ЭТАЛОННОГО РЕШЕНИЯ")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Тест {i}: {test_case['name']}")
        print("-" * 40)
        
        # Выполняем эталонное решение
        try:
            output_buffer = io.StringIO()
            local_vars = {}
            with redirect_stdout(output_buffer):
                exec(test_case["solution_code"], {}, local_vars)
            actual_output = output_buffer.getvalue().strip()
            
            print(f"Ожидаемый вывод: '{test_case['expected_output']}'")
            print(f"Фактический вывод: '{actual_output}'")
            
            # Проверяем соответствие
            is_consistent = actual_output == test_case["expected_output"].strip()
            
            if is_consistent:
                print("✅ СООТВЕТСТВИЕ: Да")
            else:
                print("❌ СООТВЕТСТВИЕ: Нет")
                print("   ⚠️ Проблема: expected_output не соответствует реальному выводу solution_code")
                
                # Показываем разницу
                print("\n🔍 Анализ:")
                expected_lines = test_case["expected_output"].strip().split('\n')
                actual_lines = actual_output.split('\n')
                
                print(f"   Ожидалось строк: {len(expected_lines)}")
                print(f"   Получено строк: {len(actual_lines)}")
                
                for j, (expected, actual) in enumerate(zip(expected_lines, actual_lines)):
                    if expected != actual:
                        print(f"   Строка {j+1}:")
                        print(f"     Ожидалось: '{expected}'")
                        print(f"     Получено:  '{actual}'")
                
        except Exception as e:
            print(f"❌ ОШИБКА выполнения: {str(e)}")
    
    print("\n" + "=" * 60)
    print("📊 ВЫВОДЫ:")
    print("1. Проблема в том, что AI генерирует неправильный эталонный код")
    print("2. Нужно добавить проверку соответствия solution_code и expected_output")
    print("3. Исправления уже применены в control_tasks_generator.py")

if __name__ == "__main__":
    test_solution_consistency()