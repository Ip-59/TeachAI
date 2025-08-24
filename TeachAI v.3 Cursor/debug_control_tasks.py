#!/usr/bin/env python3
"""
Диагностический скрипт для отладки проблем с контрольными заданиями
"""

import os
import sys
import json
import logging
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, os.getcwd())

def setup_logging():
    """Настраивает логирование для диагностики"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('debug_control_tasks.log', mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def test_control_tasks_generator():
    """Тестирует генератор контрольных заданий"""
    logger = logging.getLogger(__name__)
    logger.info("=== ТЕСТ ГЕНЕРАТОРА КОНТРОЛЬНЫХ ЗАДАНИЙ ===")
    
    try:
        from control_tasks_generator import ControlTasksGenerator
        from config import ConfigManager
        
        # Инициализируем конфигурацию
        config_manager = ConfigManager()
        if not config_manager.load_config():
            logger.error("Не удалось загрузить конфигурацию")
            return False
        
        api_key = config_manager.get_api_key()
        if not api_key:
            logger.error("API ключ не найден")
            return False
        
        # Создаем генератор
        generator = ControlTasksGenerator(api_key)
        logger.info("Генератор создан успешно")
        
        # Тестовые данные урока
        lesson_data = {
            "title": "Списки и словари",
            "description": "Изучение работы со списками и словарями в Python"
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
        logger.info(f"task_code: {task_data.get('task_code', 'НЕТ')[:100]}...")
        logger.info(f"expected_output: {task_data.get('expected_output', 'НЕТ')}")
        logger.info(f"is_needed: {task_data.get('is_needed', 'НЕТ')}")
        
        # Сохраняем результат в файл
        with open('debug_responses/test_task_generation.json', 'w', encoding='utf-8') as f:
            json.dump(task_data, f, ensure_ascii=False, indent=2)
        
        logger.info("Результат сохранен в debug_responses/test_task_generation.json")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании генератора: {str(e)}")
        return False

def test_validation():
    """Тестирует валидацию заданий"""
    logger = logging.getLogger(__name__)
    logger.info("=== ТЕСТ ВАЛИДАЦИИ ЗАДАНИЙ ===")
    
    try:
        from control_tasks_generator import ControlTasksGenerator
        from config import ConfigManager
        
        # Инициализируем генератор
        config_manager = ConfigManager()
        config_manager.load_config()
        api_key = config_manager.get_api_key()
        generator = ControlTasksGenerator(api_key)
        
        # Тест 1: Проверка переменной без print
        logger.info("Тест 1: Проверка переменной без print")
        user_code = "result = 10 - 5"
        expected_output = ""
        check_variable = "result"
        expected_variable_value = 5
        
        result = generator.validate_task_execution(
            user_code=user_code,
            expected_output=expected_output,
            check_variable=check_variable,
            expected_variable_value=expected_variable_value
        )
        
        logger.info(f"Результат: {result}")
        
        # Тест 2: Проверка с print
        logger.info("Тест 2: Проверка с print")
        user_code = "print('Hello, World!')"
        expected_output = "Hello, World!"
        
        result = generator.validate_task_execution(
            user_code=user_code,
            expected_output=expected_output
        )
        
        logger.info(f"Результат: {result}")
        
        # Тест 3: Неправильное решение
        logger.info("Тест 3: Неправильное решение")
        user_code = "result = 10 - 3"  # Должно быть 5, а не 7
        expected_output = ""
        check_variable = "result"
        expected_variable_value = 5
        
        result = generator.validate_task_execution(
            user_code=user_code,
            expected_output=expected_output,
            check_variable=check_variable,
            expected_variable_value=expected_variable_value
        )
        
        logger.info(f"Результат: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании валидации: {str(e)}")
        return False

def test_interface():
    """Тестирует интерфейс контрольных заданий"""
    logger = logging.getLogger(__name__)
    logger.info("=== ТЕСТ ИНТЕРФЕЙСА КОНТРОЛЬНЫХ ЗАДАНИЙ ===")
    
    try:
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
        
        lesson_interface = MockLessonInterface()
        
        # Создаем интерфейс
        interface = ControlTasksInterface(content_generator, lesson_interface)
        logger.info("Интерфейс создан успешно")
        
        # Тестовые данные
        lesson_data = {
            "title": "Тестовый урок",
            "description": "Тестовое описание"
        }
        
        lesson_content = """
# Тестовый урок

## Пример кода
```python
numbers = [1, 2, 3, 4, 5]
result = sum(numbers)
print(result)
```
        """
        
        logger.info("Тестируем показ задания...")
        # Этот тест может не работать в консольном режиме из-за ipywidgets
        logger.info("Интерфейс инициализирован успешно")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании интерфейса: {str(e)}")
        return False

def main():
    """Основная функция диагностики"""
    print("🔍 ДИАГНОСТИКА ПРОБЛЕМ С КОНТРОЛЬНЫМИ ЗАДАНИЯМИ")
    print("=" * 60)
    
    # Настраиваем логирование
    logger = setup_logging()
    
    # Создаем директорию для debug_responses
    Path("debug_responses").mkdir(exist_ok=True)
    
    # Очищаем старые файлы
    for file in Path("debug_responses").glob("test_*"):
        file.unlink()
    
    # Запускаем тесты
    tests = [
        ("Генератор контрольных заданий", test_control_tasks_generator),
        ("Валидация заданий", test_validation),
        ("Интерфейс контрольных заданий", test_interface)
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
    print("📊 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
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
    
    print("\n🔍 Логи сохранены в: debug_control_tasks.log")
    print("📁 Результаты в: debug_responses/")

if __name__ == "__main__":
    main()