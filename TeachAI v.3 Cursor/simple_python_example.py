#!/usr/bin/env python3
"""
Простой пример Python кода без внешних зависимостей.
Демонстрирует базовые возможности Python.
"""

def demonstrate_basic_python():
    """Демонстрирует базовые возможности Python."""
    
    print("🐍 ДЕМОНСТРАЦИЯ БАЗОВЫХ ВОЗМОЖНОСТЕЙ PYTHON")
    print("=" * 50)
    
    # 1. Работа со списками
    print("\n📋 1. Работа со списками:")
    numbers = [1, 2, 3, 4, 5]
    print(f"Исходный список: {numbers}")
    
    # Добавление элемента
    numbers.append(6)
    print(f"После добавления 6: {numbers}")
    
    # Фильтрация четных чисел
    even_numbers = [x for x in numbers if x % 2 == 0]
    print(f"Четные числа: {even_numbers}")
    
    # 2. Работа со словарями
    print("\n📚 2. Работа со словарями:")
    student = {
        "name": "Иван",
        "age": 20,
        "subjects": ["Математика", "Физика", "Программирование"]
    }
    print(f"Информация о студенте: {student}")
    
    # Добавление нового предмета
    student["subjects"].append("История")
    print(f"После добавления предмета: {student['subjects']}")
    
    # 3. Функции и генераторы
    print("\n⚙️ 3. Функции и генераторы:")
    
    def fibonacci(n):
        """Генерирует числа Фибоначчи до n."""
        a, b = 0, 1
        count = 0
        while count < n:
            yield a
            a, b = b, a + b
            count += 1
    
    print("Первые 10 чисел Фибоначчи:")
    fib_list = list(fibonacci(10))
    print(fib_list)
    
    # 4. Обработка исключений
    print("\n🛡️ 4. Обработка исключений:")
    
    def safe_divide(a, b):
        """Безопасное деление с обработкой ошибок."""
        try:
            result = a / b
            return result
        except ZeroDivisionError:
            return "Ошибка: деление на ноль!"
        except TypeError:
            return "Ошибка: неверный тип данных!"
    
    print(f"10 / 2 = {safe_divide(10, 2)}")
    print(f"10 / 0 = {safe_divide(10, 0)}")
    print(f"10 / 'a' = {safe_divide(10, 'a')}")
    
    # 5. Работа с файлами
    print("\n📁 5. Работа с файлами:")
    
    # Создаем временный файл
    filename = "temp_demo.txt"
    
    try:
        # Запись в файл
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("Это демонстрационный файл\n")
            f.write("Создан для показа работы с файлами\n")
        
        print(f"Файл {filename} создан и заполнен")
        
        # Чтение из файла
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"Содержимое файла:\n{content}")
        
        # Удаляем временный файл
        import os
        os.remove(filename)
        print(f"Временный файл {filename} удален")
        
    except Exception as e:
        print(f"Ошибка при работе с файлом: {e}")
    
    print("\n🎉 Демонстрация завершена!")
    print("Этот код использует только встроенные возможности Python!")

if __name__ == "__main__":
    demonstrate_basic_python() 