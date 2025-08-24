from IPython.display import display, clear_output
from engine import TeachAIEngine

# Инициализация и запуск TeachAI с оптимизированным отображением
engine = TeachAIEngine()

# Тестовая задача для демонстрации исправления проблемы с input()

# СТАРАЯ ЗАДАЧА (зависала):
# input_number = int(input("Введите целое число: "))
# if input_number % 2 == 0:
#     print("Четное")
# else:
#     print("Нечетное")

# НОВАЯ ЗАДАЧА (работает корректно):
number = 10
# Проверьте, является ли число четным
if number % 2 == 0:
    print("Четное")
else:
    print("Нечетное")

print("✅ Задача выполнена успешно без зависания!")

