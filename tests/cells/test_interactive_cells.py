"""
Тестирование интерактивных ячеек для контрольных заданий.
Запустите этот файл в Jupyter Notebook для проверки работы InteractiveCellWidget.
"""

# Импортируем необходимые модули
from cell_widget_base import CellWidgetBase
from interactive_cell_widget import InteractiveCellWidget, create_interactive_cell
from result_checker import CheckResult, check_result
from control_tasks_logger import get_cell_stats, is_cell_completed, default_logger
from IPython.display import display
import ipywidgets as widgets


def test_basic_math_task():
    """Тест 1: Простая математическая задача"""
    print("=== Тест 1: Простая математическая задача ===")

    task = create_interactive_cell(
        task_description="Вычислите сумму чисел 15 и 27. Сохраните результат в переменную 'result'.",
        expected_result=42,
        check_type="exact",
        initial_code="# Вычислите сумму 15 + 27\nresult = ",
        title="Задача 1: Сложение чисел",
        cell_id="math_task_1",
    )

    display(task)
    return task


def test_list_manipulation():
    """Тест 2: Работа со списками"""
    print("=== Тест 2: Работа со списками ===")

    task = create_interactive_cell(
        task_description="Создайте список квадратов чисел от 1 до 5. Результат должен быть [1, 4, 9, 16, 25]. В конце добавьте строку 'squares' чтобы вернуть результат.",
        expected_result=[1, 4, 9, 16, 25],
        check_type="list",
        initial_code="""# Создайте список квадратов
squares = []
# Ваш код здесь
for i in range(1, 6):  # подсказка: от 1 до 5 включительно
    # добавьте квадрат числа i в список
    pass

squares  # эта строка возвращает результат""",
        title="Задача 2: Список квадратов",
        cell_id="list_task_1",
    )

    display(task)
    return task


def test_function_creation():
    """Тест 3: Создание функции"""
    print("=== Тест 3: Создание функции ===")

    # Тестовые случаи для функции
    test_cases = [
        ((5,), 120),  # 5! = 120
        ((3,), 6),  # 3! = 6
        ((1,), 1),  # 1! = 1
        ((0,), 1),  # 0! = 1
    ]

    task = create_interactive_cell(
        task_description="Создайте функцию factorial(n), которая вычисляет факториал числа n.",
        expected_result=None,  # Будет проверяться функция
        check_type="function",
        check_kwargs={"test_cases": test_cases},
        initial_code="""def factorial(n):
    # Ваш код здесь
    pass

factorial""",
        title="Задача 3: Функция факториала",
        cell_id="function_task_1",
    )

    display(task)
    return task


def test_numeric_precision():
    """Тест 4: Числовая точность"""
    print("=== Тест 4: Числовая точность ===")

    task = create_interactive_cell(
        task_description="Вычислите площадь круга радиусом 3. Используйте π = 3.14159.",
        expected_result=28.27431,
        check_type="numeric",
        check_kwargs={"tolerance": 1e-3},
        initial_code="""import math

radius = 3
pi = 3.14159
# Вычислите площадь круга
area =

area""",
        title="Задача 4: Площадь круга",
        cell_id="numeric_task_1",
    )

    display(task)
    return task


def test_string_processing():
    """Тест 5: Обработка строк"""
    print("=== Тест 5: Обработка строк ===")

    task = create_interactive_cell(
        task_description="Преобразуйте строку 'Hello World' в верхний регистр и получите 'HELLO WORLD'.",
        expected_result="HELLO WORLD",
        check_type="exact",
        initial_code="""text = "Hello World"
# Преобразуйте в верхний регистр
result =

result""",
        title="Задача 5: Преобразование строки",
        cell_id="string_task_1",
        max_attempts=3,
    )

    display(task)
    return task


def test_with_solution():
    """Тест 6: Задача с показом решения"""
    print("=== Тест 6: Задача с показом решения ===")

    task = create_interactive_cell(
        task_description="Найдите максимальное число в списке [3, 1, 4, 1, 5, 9, 2, 6].",
        expected_result=9,
        check_type="exact",
        initial_code="""numbers = [3, 1, 4, 1, 5, 9, 2, 6]
# Найдите максимальное число
max_number =

max_number""",
        title="Задача 6: Максимум в списке",
        cell_id="max_task_1",
        show_solution=True,
        solution_code="""numbers = [3, 1, 4, 1, 5, 9, 2, 6]
# Найдите максимальное число
max_number = max(numbers)

max_number""",
    )

    display(task)
    return task


def test_complex_logic():
    """Тест 7: Сложная логическая задача"""
    print("=== Тест 7: Сложная логическая задача ===")

    task = create_interactive_cell(
        task_description="""Создайте список всех четных чисел от 2 до 20 включительно.
        Список должен содержать: [2, 4, 6, 8, 10, 12, 14, 16, 18, 20].""",
        expected_result=[2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        check_type="list",
        check_kwargs={"order_matters": True},
        initial_code="""# Создайте список четных чисел от 2 до 20
even_numbers = []

# Ваш код здесь

even_numbers""",
        title="Задача 7: Четные числа",
        cell_id="logic_task_1",
    )

    display(task)
    return task


def test_error_handling():
    """Тест 8: Обработка ошибок"""
    print("=== Тест 8: Задача с возможными ошибками ===")

    task = create_interactive_cell(
        task_description="Разделите число 100 на число 5 и сохраните результат в переменную 'result'.",
        expected_result=20.0,
        check_type="numeric",
        check_kwargs={"tolerance": 1e-6},
        initial_code="""# Выполните деление
numerator = 100
denominator = 5
result =

result""",
        title="Задача 8: Деление чисел",
        cell_id="division_task_1",
    )

    display(task)
    return task


def test_statistics_display():
    """Тест 9: Демонстрация статистики"""
    print("=== Тест 9: Статистика по задачам ===")

    # Создаем виджет для отображения общей статистики
    stats_widget = widgets.HTML()

    def update_stats():
        overall_stats = default_logger.get_overall_stats()

        stats_html = f"""
        <div style='background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 10px 0;'>
            <h4 style='margin-top: 0; color: #1976d2;'>📊 Общая статистика</h4>
            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;'>
                <div>
                    <strong>Всего задач:</strong> {overall_stats['total_cells']}<br>
                    <strong>Выполнено:</strong> {overall_stats['completed_cells']}<br>
                    <strong>Процент выполнения:</strong> {overall_stats['completion_rate']:.1%}
                </div>
                <div>
                    <strong>Всего попыток:</strong> {overall_stats['total_attempts']}<br>
                    <strong>Успешность:</strong> {overall_stats['success_rate']:.1%}<br>
                    <strong>Среднее время:</strong> {overall_stats['average_execution_time_ms']:.1f} мс
                </div>
            </div>
        </div>
        """

        stats_widget.value = stats_html

    # Кнопка для обновления статистики
    refresh_button = widgets.Button(
        description="🔄 Обновить статистику", button_style="info"
    )

    def on_refresh(button):
        update_stats()

    refresh_button.on_click(on_refresh)

    # Показываем начальную статистику
    update_stats()

    display(widgets.VBox([refresh_button, stats_widget]))

    return stats_widget


def test_cell_management():
    """Тест 10: Управление ячейками"""
    print("=== Тест 10: Управление ячейками ===")

    # Создаем виджеты управления
    cell_selector = widgets.Dropdown(
        options=[], description="Ячейка:", style={"description_width": "80px"}
    )

    info_area = widgets.HTML()

    clear_button = widgets.Button(
        description="🗑 Очистить данные ячейки", button_style="danger"
    )

    clear_all_button = widgets.Button(
        description="🗑 Очистить все данные", button_style="danger"
    )

    refresh_list_button = widgets.Button(
        description="🔄 Обновить список", button_style="info"
    )

    def update_cell_list():
        cell_ids = list(default_logger.log_data["cell_stats"].keys())
        if cell_ids:
            cell_selector.options = cell_ids
        else:
            cell_selector.options = []
            cell_selector.value = None

    def on_cell_selected(change):
        if change["new"]:
            cell_id = change["new"]
            stats = get_cell_stats(cell_id)
            completed = is_cell_completed(cell_id)

            # Правильно форматируем лучший результат
            best_score_text = f"{stats['best_score']:.1%}" if stats else "N/A"

            info_html = f"""
            <div style='background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 5px 0;'>
                <strong>Ячейка:</strong> {cell_id}<br>
                <strong>Статус:</strong> {'✅ Выполнена' if completed else '⏳ В процессе'}<br>
                <strong>Попыток:</strong> {stats['total_attempts'] if stats else 0}<br>
                <strong>Успешных:</strong> {stats['successful_attempts'] if stats else 0}<br>
                <strong>Лучший результат:</strong> {best_score_text}
            </div>
            """
            info_area.value = info_html

    def on_refresh_list(button):
        update_cell_list()
        info_area.value = (
            "<div style='color: blue; font-weight: bold;'>🔄 Список ячеек обновлен</div>"
        )

    def on_clear_cell(button):
        if cell_selector.value:
            cell_id = cell_selector.value
            default_logger.clear_cell_data(cell_id)
            update_cell_list()
            # Очищаем выбор и информацию
            cell_selector.value = None
            info_area.value = f"<div style='color: green; font-weight: bold;'>✅ Данные ячейки '{cell_id}' очищены</div>"

    def on_clear_all(button):
        # Простое подтверждение через смену описания кнопки
        if button.description == "🗑 Очистить все данные":
            button.description = "⚠️ Подтвердить очистку"
            button.button_style = "warning"
            info_area.value = "<div style='color: orange; font-weight: bold;'>⚠️ Нажмите ещё раз для подтверждения полной очистки данных</div>"
        else:
            # Подтверждение получено, очищаем данные
            default_logger.clear_all_data()
            update_cell_list()
            # Возвращаем кнопку в исходное состояние
            button.description = "🗑 Очистить все данные"
            button.button_style = "danger"
            # Очищаем выбор и информацию
            cell_selector.value = None
            info_area.value = "<div style='color: green; font-weight: bold;'>✅ Все данные очищены</div>"

    # Привязка событий
    cell_selector.observe(on_cell_selected, names="value")
    refresh_list_button.on_click(on_refresh_list)
    clear_button.on_click(on_clear_cell)
    clear_all_button.on_click(on_clear_all)

    # Обновляем список ячеек
    update_cell_list()

    management_widget = widgets.VBox(
        [
            widgets.HTML("<h4>🔧 Управление данными ячеек</h4>"),
            widgets.HBox([cell_selector, refresh_list_button]),
            info_area,
            widgets.HBox([clear_button, clear_all_button]),
        ]
    )

    display(management_widget)

    return management_widget


def run_all_tests():
    """Запуск всех тестов интерактивных ячеек"""
    print("🧪 ТЕСТИРОВАНИЕ ИНТЕРАКТИВНЫХ ЯЧЕЕК")
    print("=" * 50)

    tasks = []

    # Запускаем все тесты
    tasks.append(test_basic_math_task())
    print()
    tasks.append(test_list_manipulation())
    print()
    tasks.append(test_function_creation())
    print()
    tasks.append(test_numeric_precision())
    print()
    tasks.append(test_string_processing())
    print()
    tasks.append(test_with_solution())
    print()
    tasks.append(test_complex_logic())
    print()
    tasks.append(test_error_handling())
    print()

    # Показываем статистику и управление
    stats_widget = test_statistics_display()
    print()
    management_widget = test_cell_management()

    print("\n" + "=" * 50)
    print("✅ Все тесты созданы!")
    print("\nИнструкции для тестирования:")
    print("1. Решите задачи выше, вводя код в редакторы")
    print("2. Нажимайте '🚀 Выполнить' для проверки")
    print("3. Используйте '💡 Решение' если застряли")
    print("4. Смотрите статистику и управляйте данными")
    print("5. Проверьте различные типы ошибок и ситуаций")

    return {
        "tasks": tasks,
        "stats_widget": stats_widget,
        "management_widget": management_widget,
    }


# Если файл запускается напрямую
if __name__ == "__main__":
    result = run_all_tests()
