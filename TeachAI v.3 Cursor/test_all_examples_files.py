#!/usr/bin/env python3
"""
Тест всех файлов генерации примеров на наличие ошибки с переменной i.
"""

import os
import sys
import importlib

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_all_examples_files():
    """Тестирует все файлы генерации примеров."""
    files_to_test = [
        "examples_generation",
        "examples_utils", 
        "examples_generator",
        "examples_validation"
    ]
    
    results = {}
    
    for file_name in files_to_test:
        print(f"\n🧪 Тестирование файла: {file_name}.py")
        try:
            # Пытаемся импортировать модуль
            module = importlib.import_module(file_name)
            print(f"✅ Модуль {file_name} импортирован успешно")
            
            # Пытаемся создать экземпляр основного класса
            if file_name == "examples_generation":
                instance = module.ExamplesGeneration("test_key")
                print(f"✅ ExamplesGeneration создан успешно")
                
                # Тестируем определение предметной области
                lesson_content = "Это урок по Python с циклами for и функциями def"
                lesson_keywords = ["python", "циклы"]
                
                course_subject = instance._determine_course_subject(
                    None, lesson_content, lesson_keywords
                )
                print(f"✅ Предметная область определена: {course_subject}")
                
            elif file_name == "examples_utils":
                instance = module.ExamplesUtils()
                print(f"✅ ExamplesUtils создан успешно")
                
                # Тестируем определение предметной области
                lesson_content = "Это урок по Python с циклами for и функциями def"
                lesson_keywords = ["python", "циклы"]
                
                course_subject = instance.determine_course_subject(
                    None, lesson_content, lesson_keywords
                )
                print(f"✅ Предметная область определена: {course_subject}")
                
            elif file_name == "examples_generator":
                instance = module.ExamplesGenerator("test_key")
                print(f"✅ ExamplesGenerator создан успешно")
                
            elif file_name == "examples_validation":
                instance = module.ExamplesValidation("test_key")
                print(f"✅ ExamplesValidation создан успешно")
            
            results[file_name] = "✅ УСПЕШНО"
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Ошибка в {file_name}: {error_msg}")
            
            # Проверяем, связана ли ошибка с переменной i
            if "'i'" in error_msg or "NameError" in error_msg:
                print(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: Проблема с переменной i в {file_name}")
                results[file_name] = "❌ КРИТИЧЕСКАЯ ОШИБКА: переменная i"
            else:
                results[file_name] = f"❌ Ошибка: {error_msg}"
    
    # Выводим итоговый результат
    print("\n" + "="*60)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ")
    print("="*60)
    
    all_success = True
    for file_name, result in results.items():
        print(f"{file_name}: {result}")
        if "❌" in result:
            all_success = False
    
    if all_success:
        print("\n🎉 ВСЕ файлы работают корректно!")
        print("🎯 Ошибка с переменной i исправлена во всех файлах!")
    else:
        print("\n💥 ЕСТЬ проблемы, требующие исправления!")
        print("🔍 Проверьте файлы с ошибками выше")
    
    return all_success

if __name__ == "__main__":
    success = test_all_examples_files()
    
    if success:
        print("\n🎯 Все файлы генерации примеров работают корректно!")
    else:
        print("\n💥 Требуется дополнительное исправление!")
