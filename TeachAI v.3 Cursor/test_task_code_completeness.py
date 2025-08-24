#!/usr/bin/env python3
"""
Тестовый скрипт для проверки полноты task_code
"""

import re

def test_task_code_completeness():
    """Тестирует полноту task_code"""
    
    # Тестовые случаи
    test_cases = [
        {
            "name": "Правильный случай - все данные указаны",
            "description": "Дан список my_list = [1, 2, 3, 'apple', 'banana'] и словарь my_dict = {'a': 'apple', 'b': 'banana', 'c': 'cherry'}. Добавьте элемент 'orange' в конец списка.",
            "task_code": "my_list = [1, 2, 3, 'apple', 'banana']\nmy_dict = {'a': 'apple', 'b': 'banana', 'c': 'cherry'}\n# Ваш код здесь",
            "expected": "✅ Полный"
        },
        {
            "name": "Проблемный случай - отсутствуют данные в task_code",
            "description": "Дан список my_list = [1, 2, 3, 'apple', 'banana'] и словарь my_dict = {'a': 'apple', 'b': 'banana', 'c': 'cherry'}. Добавьте элемент 'orange' в конец списка.",
            "task_code": "# Ваш код здесь\n# Создайте список и словарь",
            "expected": "❌ Неполный"
        },
        {
            "name": "Частично неполный - отсутствует словарь",
            "description": "Дан список my_list = [1, 2, 3, 'apple', 'banana'] и словарь my_dict = {'a': 'apple', 'b': 'banana', 'c': 'cherry'}. Добавьте элемент 'orange' в конец списка.",
            "task_code": "my_list = [1, 2, 3, 'apple', 'banana']\n# Ваш код здесь",
            "expected": "❌ Неполный"
        }
    ]
    
    print("🧪 ТЕСТИРОВАНИЕ ПОЛНОТЫ TASK_CODE")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Тест {i}: {test_case['name']}")
        print("-" * 40)
        
        description = test_case["description"]
        task_code = test_case["task_code"]
        
        print(f"Description: {description}")
        print(f"Task_code: {task_code}")
        
        # Проверяем полноту
        missing_data = check_task_code_completeness(description, task_code)
        
        if missing_data:
            print(f"❌ НЕПОЛНЫЙ TASK_CODE:")
            for item in missing_data:
                print(f"   - Отсутствует: {item}")
            print(f"   ⚠️ Проблема: Студент не получит начальные данные!")
        else:
            print(f"✅ ПОЛНЫЙ TASK_CODE")
            print(f"   ✅ Все начальные данные указаны")
        
        print(f"Ожидаемый результат: {test_case['expected']}")
    
    print("\n" + "=" * 60)
    print("📊 ВЫВОДЫ:")
    print("1. task_code должен содержать ВСЕ начальные данные из description")
    print("2. Если в description упоминается 'список my_list = [1, 2, 3]'")
    print("   то в task_code должно быть 'my_list = [1, 2, 3]'")
    print("3. Исправления уже применены в control_tasks_generator.py")

def check_task_code_completeness(description, task_code):
    """Проверяет полноту task_code"""
    missing_data = []
    
    # Ищем упоминания списков и словарей в description
    list_patterns = [
        r"список\s+(\w+)\s*=\s*\[([^\]]+)\]",
        r"(\w+)\s*=\s*\[([^\]]+)\].*список",
        r"список\s+(\w+).*=\s*\[([^\]]+)\]"
    ]
    
    dict_patterns = [
        r"словарь\s+(\w+)\s*=\s*\{([^}]+)\}",
        r"(\w+)\s*=\s*\{([^}]+)\}.*словарь",
        r"словарь\s+(\w+).*=\s*\{([^}]+)\}"
    ]
    
    # Проверяем списки
    for pattern in list_patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        for var_name, var_content in matches:
            if f"{var_name} = [" not in task_code:
                missing_data.append(f"Список {var_name} = [{var_content}]")
    
    # Проверяем словари
    for pattern in dict_patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        for var_name, var_content in matches:
            if f"{var_name} = {{" not in task_code:
                missing_data.append(f"Словарь {var_name} = {{{var_content}}}")
    
    return missing_data

if __name__ == "__main__":
    test_task_code_completeness()