"""
Тестирование демонстрационных ячеек.
Запустите этот файл в Jupyter Notebook для проверки работы DemoCellWidget.
"""

# Импортируем необходимые модули
from cell_widget_base import CellWidgetBase
from demo_cell_widget import DemoCellWidget, create_demo_cell
from IPython.display import display
import ipywidgets as widgets


def test_basic_demo_cell():
    """Тест 1: Простая демонстрационная ячейка"""
    print("=== Тест 1: Простая демонстрационная ячейка ===")

    code = """# Простой пример с переменными
x = 10
y = 20
result = x + y
print(f"x = {x}")
print(f"y = {y}")
print(f"x + y = {result}")
result"""

    demo1 = DemoCellWidget(
        code=code,
        title="Пример 1: Работа с переменными",
        description="Этот пример показывает создание переменных и их сложение",
    )

    display(demo1)
    return demo1


def test_loop_demo_cell():
    """Тест 2: Демонстрация с циклом"""
    print("=== Тест 2: Демонстрация с циклом ===")

    code = """# Пример с циклом
numbers = [1, 2, 3, 4, 5]
squares = []

for num in numbers:
    square = num ** 2
    squares.append(square)
    print(f"{num}² = {square}")

print(f"Исходный список: {numbers}")
print(f"Квадраты: {squares}")
squares"""

    demo2 = DemoCellWidget(
        code=code,
        title="Пример 2: Цикл и список",
        description="Демонстрация работы с циклами и списками",
    )

    display(demo2)
    return demo2


def test_function_demo_cell():
    """Тест 3: Демонстрация с функцией"""
    print("=== Тест 3: Демонстрация с функцией ===")

    code = """# Пример с функцией
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

# Тестируем функцию
numbers = [3, 5, 7]
for num in numbers:
    fact = factorial(num)
    print(f"Факториал {num}! = {fact}")

factorial(5)"""

    demo3 = DemoCellWidget(
        code=code,
        title="Пример 3: Рекурсивная функция",
        description="Вычисление факториала с помощью рекурсии",
    )

    display(demo3)
    return demo3


def test_hidden_code_demo():
    """Тест 4: Демонстрация со скрытым кодом"""
    print("=== Тест 4: Демонстрация со скрытым кодом ===")

    code = """# Секретный код для демонстрации
import random

print("🎲 Генератор случайных чисел")
print("=" * 30)

for i in range(5):
    number = random.randint(1, 100)
    print(f"Случайное число {i+1}: {number}")

print("=" * 30)
print("Генерация завершена!")"""

    demo4 = DemoCellWidget(
        code=code,
        title="Пример 4: Скрытый код",
        description="Код скрыт по умолчанию, но можно показать кнопкой",
        show_code=False,  # Скрываем код по умолчанию
    )

    display(demo4)
    return demo4


def test_auto_run_demo():
    """Тест 5: Автоматический запуск"""
    print("=== Тест 5: Автоматический запуск ===")

    code = """# Код с автоматическим запуском
import datetime

now = datetime.datetime.now()
print("🕒 Текущее время и дата:")
print(f"Дата: {now.strftime('%d.%m.%Y')}")
print(f"Время: {now.strftime('%H:%M:%S')}")
print(f"День недели: {now.strftime('%A')}")

now.strftime('%d.%m.%Y %H:%M:%S')"""

    demo5 = DemoCellWidget(
        code=code,
        title="Пример 5: Автозапуск",
        description="Этот код запустится автоматически при создании ячейки",
        auto_run=True,  # Автоматический запуск
    )

    display(demo5)
    return demo5


def test_error_demo():
    """Тест 6: Демонстрация с ошибкой"""
    print("=== Тест 6: Демонстрация с ошибкой ===")

    code = """# Код с преднамеренной ошибкой
numbers = [1, 2, 3, 4, 5]
print("Исходный список:", numbers)

# Попытка обратиться к несуществующему индексу
print("Элемент с индексом 10:", numbers[10])  # Это вызовет ошибку

print("Эта строка не выполнится")"""

    demo6 = DemoCellWidget(
        code=code,
        title="Пример 6: Обработка ошибок",
        description="Этот пример показывает, как отображаются ошибки выполнения",
    )

    display(demo6)
    return demo6


def test_using_helper_function():
    """Тест 7: Использование функции-помощника"""
    print("=== Тест 7: Функция-помощник create_demo_cell ===")

    code = """# Пример работы со словарями
person = {
    'name': 'Анна',
    'age': 25,
    'city': 'Москва',
    'profession': 'Программист'
}

print("Информация о человеке:")
for key, value in person.items():
    print(f"{key.capitalize()}: {value}")

# Добавляем новую информацию
person['experience'] = 3
print(f"\\nОпыт работы: {person['experience']} года")
person"""

    # Используем функцию-помощник
    demo7 = create_demo_cell(
        code=code,
        title="Пример 7: Словари",
        description="Создано с помощью функции create_demo_cell",
    )

    display(demo7)
    return demo7


def test_dynamic_code_change():
    """Тест 8: Динамическое изменение кода"""
    print("=== Тест 8: Динамическое изменение кода ===")

    initial_code = """# Начальный код
print("Привет, мир!")
print("Это начальная версия кода")"""

    demo8 = DemoCellWidget(
        code=initial_code,
        title="Пример 8: Изменяемый код",
        description="Демонстрация изменения кода программно",
    )

    display(demo8)

    # Создаем кнопку для изменения кода
    change_button = widgets.Button(description="🔄 Изменить код", button_style="warning")

    def change_code(button):
        new_code = """# Обновленный код
import math

radius = 5
area = math.pi * radius ** 2
circumference = 2 * math.pi * radius

print(f"Радиус окружности: {radius}")
print(f"Площадь: {area:.2f}")
print(f"Длина окружности: {circumference:.2f}")
area"""

        demo8.set_code(new_code)
        print("Код обновлен! Теперь можно запустить новый код.")

    change_button.on_click(change_code)
    display(change_button)

    return demo8


def run_all_tests():
    """Запуск всех тестов демонстрационных ячеек"""
    print("🧪 ТЕСТИРОВАНИЕ ДЕМОНСТРАЦИОННЫХ ЯЧЕЕК")
    print("=" * 50)

    demos = []

    # Запускаем все тесты
    demos.append(test_basic_demo_cell())
    print()
    demos.append(test_loop_demo_cell())
    print()
    demos.append(test_function_demo_cell())
    print()
    demos.append(test_hidden_code_demo())
    print()
    demos.append(test_auto_run_demo())
    print()
    demos.append(test_error_demo())
    print()
    demos.append(test_using_helper_function())
    print()
    demos.append(test_dynamic_code_change())

    print("\n" + "=" * 50)
    print("✅ Все тесты созданы!")
    print("Попробуйте взаимодействовать с ячейками выше:")
    print("- Нажимайте кнопки 'Запустить код'")
    print("- Переключайте видимость кода")
    print("- Смотрите на индикаторы статуса")

    return demos


# Если файл запускается напрямую
if __name__ == "__main__":
    demos = run_all_tests()
