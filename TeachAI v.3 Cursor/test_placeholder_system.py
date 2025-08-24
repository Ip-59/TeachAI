#!/usr/bin/env python3
"""
Тест новой системы плейсхолдеров для блоков кода
"""

import sys
import logging
from pathlib import Path

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_placeholder_system():
    """Тестирует систему плейсхолдеров для блоков кода"""
    try:
        print("🧪 Тестирование системы плейсхолдеров для блоков кода...")
        
        # Импортируем ContentFormatter
        from content_formatter import ContentFormatter
        
        # Создаем форматтер
        formatter = ContentFormatter()
        
        # Тестовый контент с блоками кода
        test_content = """# Тест системы плейсхолдеров

Этот урок тестирует новую систему обработки блоков кода.

## Блок кода Python

```python
def hello_world():
    print("Hello, World!")
    return "Success"

result = hello_world()
print(f"Результат: {result}")
```

## Блок кода без указания языка

```
Это простой блок кода
без указания языка
```

## Inline код

Вот пример `inline кода` в тексте.

## Еще один блок кода

```python
import numpy as np

# Создаем массив
arr = np.array([1, 2, 3, 4, 5])
print(f"Массив: {arr}")
print(f"Сумма: {np.sum(arr)}")
```

Конец урока.
"""
        
        print("📝 Тестовый контент:")
        print(test_content)
        print("\n" + "="*50 + "\n")
        
        # Форматируем контент
        print("🎨 Форматирование контента...")
        formatted_content = formatter.format_lesson_content(test_content, "Тест плейсхолдеров")
        
        print("✅ Отформатированный HTML:")
        print(formatted_content)
        
        # Проверяем ключевые элементы
        checks = [
            ("<h1>", "Заголовок H1"),
            ("<h2>", "Заголовок H2"),
            ("<pre>", "Блоки кода (pre)"),
            ("<code>", "Inline код"),
            ("__CODE_BLOCK_", "Плейсхолдеры блоков кода"),
        ]
        
        print("\n🔍 Проверка элементов HTML:")
        for check, description in checks:
            if check in formatted_content:
                print(f"✅ {description}: найдено")
            else:
                print(f"❌ {description}: НЕ найдено")
        
        # Проверяем специфические проблемы
        if "``<code>" in formatted_content:
            print("❌ ПРОБЛЕМА: Неправильная обработка блоков кода")
        else:
            print("✅ Блоки кода обрабатываются правильно")
            
        if "__CODE_BLOCK_" in formatted_content:
            print("❌ ПРОБЛЕМА: Плейсхолдеры не заменены на HTML")
        else:
            print("✅ Плейсхолдеры успешно заменены на HTML")
            
        # Проверяем количество блоков кода
        pre_count = formatted_content.count("<pre>")
        print(f"📊 Найдено блоков кода: {pre_count}")
        
        if pre_count >= 3:  # Ожидаем минимум 3 блока кода
            print("✅ Все блоки кода обработаны")
        else:
            print(f"❌ Ожидали минимум 3 блока кода, найдено {pre_count}")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔬 Начинаем тестирование системы плейсхолдеров...\n")
    
    # Тест системы плейсхолдеров
    test_placeholder_system()
    
    print("\n✅ Тестирование завершено!")
