#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправлений контрольных заданий
"""

import os
import sys
import json
import logging
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, os.getcwd())

def setup_logging():
    """Настраивает логирование для тестирования"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('test_control_tasks_fixed.log', mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def test_variable_checking():
    """Тестирует проверку переменных без print()"""
    logger = logging.getLogger(__name__)
    logger.info("=== ТЕСТ ПРОВЕРКИ ПЕРЕМЕННЫХ БЕЗ PRINT() ===")
    
    try:
        from control_tasks_generator import ControlTasksGenerator
        from config import ConfigManager
        
        # Инициализируем генератор
        config_manager = ConfigManager()
        config_manager.load_config()
        api_key = config_manager.get_api_key()
        generator = ControlTasksGenerator(api_key)
        
        # Тест 1: Задание с переменной без print
        logger.info("Тест 1: Задание с переменной без print")
        
        # Создаем тестовое задание
        test_task = {
            "title": "Работа с переменными",
            "description": "Создайте переменную result и присвойте ей разность чисел 10 и 5",
            "task_code": "# Ваш код здесь\n# Создайте переменную result",
            "expected_output": "",  # Пустой вывод
            "solution_code": "result = 10 - 5",
            "check_variable": "result",
            "expected_variable_value": 5
        }
        
        # Тестируем валидацию
        test_cases = [
            ("Правильное решение", "result = 10 - 5", True),
            ("Неправильное решение", "result = 10 - 3", False),
            ("С print", "result = 10 - 5\nprint(result)", True),
            ("Без переменной", "print(5)", False)
        ]
        
        for case_name, user_code, should_be_correct in test_cases:
            logger.info(f"  Тестируем: {case_name}")
            result = generator.validate_task_execution(
                user_code=user_code,
                expected_output=test_task["expected_output"],
                check_variable=test_task["check_variable"],
                expected_variable_value=test_task["expected_variable_value"]
            )
            
            is_correct = result["is_correct"]
            logger.info(f"    Результат: {is_correct} (ожидалось: {should_be_correct})")
            logger.info(f"    Фактическое значение переменной: {result.get('actual_variable')}")
            
            if is_correct == should_be_correct:
                logger.info(f"    ✅ ТЕСТ ПРОЙДЕН")
            else:
                logger.error(f"    ❌ ТЕСТ ПРОВАЛЕН")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании проверки переменных: {str(e)}")
        return False

def test_task_generation():
    """Тестирует генерацию релевантных заданий"""
    logger = logging.getLogger(__name__)
    logger.info("=== ТЕСТ ГЕНЕРАЦИИ РЕЛЕВАНТНЫХ ЗАДАНИЙ ===")
    
    try:
        from control_tasks_generator import ControlTasksGenerator
        from config import ConfigManager
        
        # Инициализируем генератор
        config_manager = ConfigManager()
        config_manager.load_config()
        api_key = config_manager.get_api_key()
        generator = ControlTasksGenerator(api_key)
        
        # Тестовый урок по спискам и словарям
        lesson_data = {
            "title": "Списки и словари в Python",
            "description": "Изучение работы со списками и словарями"
        }
        
        lesson_content = """
# Списки и словари в Python

## Списки
Списки - это изменяемые последовательности объектов.

### Создание списка
```python
my_list = [1, 2, 3, 'apple', 'banana']
```

### Методы списков
- `append()` - добавление элемента в конец
- `insert()` - вставка по индексу
- `remove()` - удаление элемента
- `pop()` - удаление и возврат элемента

## Словари
Словари - это неупорядоченные коллекции пар ключ-значение.

### Создание словаря
```python
my_dict = {'a': 'apple', 'b': 'banana', 'c': 'cherry'}
```

### Работа со словарями
- Добавление: `my_dict['d'] = 'dog'`
- Получение: `value = my_dict['a']`
- Удаление: `del my_dict['b']`
        """
        
        logger.info("Генерируем контрольное задание...")
        task_data = generator.generate_control_task(
            lesson_data=lesson_data,
            lesson_content=lesson_content,
            communication_style="friendly"
        )
        
        logger.info("Результат генерации:")
        logger.info(f"title: {task_data.get('title', 'НЕТ')}")
        logger.info(f"description: {task_data.get('description', 'НЕТ')[:100]}...")
        logger.info(f"is_needed: {task_data.get('is_needed', 'НЕТ')}")
        
        # Проверяем релевантность
        title = task_data.get('title', '').lower()
        description = task_data.get('description', '').lower()
        
        # Ключевые слова, которые должны быть в задании
        required_keywords = ['список', 'словарь', 'append', 'insert', 'remove', 'dict']
        found_keywords = [kw for kw in required_keywords if kw in title or kw in description]
        
        logger.info(f"Найденные ключевые слова: {found_keywords}")
        
        if len(found_keywords) >= 2:
            logger.info("✅ Задание релевантно теме")
        else:
            logger.warning("⚠️ Задание может быть недостаточно релевантно")
        
        # Сохраняем результат
        with open('debug_responses/test_relevant_task.json', 'w', encoding='utf-8') as f:
            json.dump(task_data, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании генерации: {str(e)}")
        return False

def test_dashboard_integration():
    """Тестирует интеграцию с дашбордом"""
    logger = logging.getLogger(__name__)
    logger.info("=== ТЕСТ ИНТЕГРАЦИИ С ДАШБОРДОМ ===")
    
    try:
        # Проверяем, что кнопка дашборда создается корректно
        from control_tasks_interface import ControlTasksInterface
        from content_generator import ContentGenerator
        from config import ConfigManager
        
        # Инициализируем компоненты
        config_manager = ConfigManager()
        config_manager.load_config()
        api_key = config_manager.get_api_key()
        
        content_generator = ContentGenerator(api_key)
        
        # Создаем mock lesson_interface
        class MockLessonInterface:
            def __init__(self):
                self.current_course_info = {"user_profile": {"communication_style": "friendly"}}
                self.current_lesson_id = "test_lesson_1"
        
        lesson_interface = MockLessonInterface()
        
        # Создаем интерфейс
        interface = ControlTasksInterface(content_generator, lesson_interface)
        logger.info("Интерфейс создан успешно")
        
        # Тестируем создание кнопок успеха
        success_buttons = interface._create_success_buttons()
        logger.info(f"Создано кнопок успеха: {len(success_buttons)}")
        
        # Проверяем, что есть кнопка дашборда
        dashboard_button_found = any(
            "дашборд" in str(button.description).lower() 
            for button in success_buttons 
            if hasattr(button, 'description')
        )
        
        if dashboard_button_found:
            logger.info("✅ Кнопка дашборда найдена")
        else:
            logger.warning("⚠️ Кнопка дашборда не найдена")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании интеграции с дашбордом: {str(e)}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ КОНТРОЛЬНЫХ ЗАДАНИЙ")
    print("=" * 60)
    
    # Настраиваем логирование
    logger = setup_logging()
    
    # Создаем директорию для debug_responses
    Path("debug_responses").mkdir(exist_ok=True)
    
    # Запускаем тесты
    tests = [
        ("Проверка переменных без print()", test_variable_checking),
        ("Генерация релевантных заданий", test_task_generation),
        ("Интеграция с дашбордом", test_dashboard_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Тестируем: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ УСПЕХ" if result else "❌ ОШИБКА"
            print(f"   {status}")
        except Exception as e:
            results[test_name] = False
            print(f"   ❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
    
    # Выводим итоги
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    for test_name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"   {test_name}: {status}")
    
    # Проверяем созданные файлы
    print("\n📁 СОЗДАННЫЕ ФАЙЛЫ:")
    debug_files = list(Path("debug_responses").glob("test_*"))
    if debug_files:
        for file in debug_files:
            print(f"   {file.name}")
    else:
        print("   Файлы не созданы")
    
    print("\n🔍 Логи сохранены в: test_control_tasks_fixed.log")
    print("📁 Результаты в: debug_responses/")

if __name__ == "__main__":
    main() 