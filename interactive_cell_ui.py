"""
UI компоненты для интерактивной ячейки.
Содержит функции создания и управления виджетами интерфейса.
"""

import ipywidgets as widgets
from typing import List, Optional


def create_task_widget(task_description: str) -> widgets.HTML:
    """
    Создает виджет с описанием задания.

    Args:
        task_description: Описание задания для студента

    Returns:
        HTML виджет с описанием задания
    """
    return widgets.HTML(
        value=f"<div style='background: #f8f9fa; padding: 10px; border-left: 4px solid #007bff; margin: 5px 0;'>"
        f"<strong>📝 Задание:</strong><br>{task_description}</div>",
        layout=widgets.Layout(margin="0 0 10px 0"),
    )


def create_code_editor(initial_code: str = "") -> widgets.Textarea:
    """
    Создает редактор кода.

    Args:
        initial_code: Начальный код в редакторе

    Returns:
        Textarea виджет для редактирования кода
    """
    return widgets.Textarea(
        value=initial_code,
        description="Ваш код:",
        placeholder="Введите ваш Python код здесь...",
        layout=widgets.Layout(width="100%", height="150px", font_family="monospace"),
        style={"description_width": "80px"},
    )


def create_run_button() -> widgets.Button:
    """Создает кнопку выполнения кода."""
    return widgets.Button(
        description="🚀 Выполнить",
        button_style="primary",
        tooltip="Выполнить код и проверить результат",
        layout=widgets.Layout(width="120px"),
    )


def create_clear_button() -> widgets.Button:
    """Создает кнопку очистки кода."""
    return widgets.Button(
        description="🗑 Очистить",
        button_style="warning",
        tooltip="Очистить редактор кода",
        layout=widgets.Layout(width="120px"),
    )


def create_reset_button() -> widgets.Button:
    """Создает кнопку сброса кода."""
    return widgets.Button(
        description="🔄 Сброс",
        button_style="info",
        tooltip="Вернуть начальный код",
        layout=widgets.Layout(width="120px"),
    )


def create_solution_button() -> widgets.Button:
    """Создает кнопку показа решения."""
    return widgets.Button(
        description="💡 Решение",
        button_style="success",
        tooltip="Показать решение задачи",
        layout=widgets.Layout(width="120px"),
    )


def create_status_widget() -> widgets.HTML:
    """Создает виджет статуса."""
    return widgets.HTML(
        value="<div style='color: #666; font-style: italic;'>Готов к выполнению</div>",
        layout=widgets.Layout(margin="5px 0"),
    )


def create_result_widget() -> widgets.HTML:
    """Создает виджет результата."""
    return widgets.HTML(value="", layout=widgets.Layout(margin="5px 0"))


def create_stats_widget() -> widgets.HTML:
    """Создает виджет статистики."""
    return widgets.HTML(value="", layout=widgets.Layout(margin="5px 0"))


def create_button_row(
    run_button: widgets.Button,
    clear_button: widgets.Button,
    reset_button: widgets.Button,
    solution_button: Optional[widgets.Button] = None,
) -> widgets.HBox:
    """
    Создает строку с кнопками управления.

    Args:
        run_button: Кнопка выполнения
        clear_button: Кнопка очистки
        reset_button: Кнопка сброса
        solution_button: Кнопка решения (опционально)

    Returns:
        HBox контейнер с кнопками
    """
    buttons = [run_button, clear_button, reset_button]

    if solution_button:
        buttons.append(solution_button)

    return widgets.HBox(buttons, layout=widgets.Layout(margin="5px 0"))


def update_task_widget(task_widget: widgets.HTML, task_description: str) -> None:
    """
    Обновляет виджет с описанием задания.

    Args:
        task_widget: Виджет для обновления
        task_description: Новое описание задания
    """
    task_widget.value = (
        f"<div style='background: #f8f9fa; padding: 10px; border-left: 4px solid #007bff; margin: 5px 0;'>"
        f"<strong>📝 Задание:</strong><br>{task_description}</div>"
    )


def update_status_widget(
    status_widget: widgets.HTML, message: str, status_type: str = "info"
) -> None:
    """
    Обновляет виджет статуса.

    Args:
        status_widget: Виджет статуса для обновления
        message: Сообщение для отображения
        status_type: Тип статуса ('info', 'success', 'error', 'warning', 'running')
    """
    color_map = {
        "info": "#17a2b8",
        "success": "#28a745",
        "error": "#dc3545",
        "warning": "#ffc107",
        "running": "#6f42c1",
    }

    color = color_map.get(status_type, "#666")
    status_widget.value = (
        f"<div style='color: {color}; font-weight: bold;'>{message}</div>"
    )


def update_result_widget(
    result_widget: widgets.HTML, check_result_obj, execution_time_ms: float
) -> None:
    """
    Обновляет виджет результата.

    Args:
        result_widget: Виджет результата для обновления
        check_result_obj: Объект результата проверки
        execution_time_ms: Время выполнения в миллисекундах
    """
    if check_result_obj.passed:
        status_color = "#28a745"  # Зеленый
        status_icon = "✅"
        status_text = "ЗАЧЁТ"
    else:
        status_color = "#dc3545"  # Красный
        status_icon = "❌"
        status_text = "НЕ ЗАЧЁТ"

    result_html = f"""
    <div style='border: 2px solid {status_color}; border-radius: 8px; padding: 12px; margin: 8px 0; background: {"#d4edda" if check_result_obj.passed else "#f8d7da"}'>
        <div style='font-weight: bold; font-size: 16px; color: {status_color}; margin-bottom: 8px;'>
            {status_icon} {status_text}
        </div>
        <div style='margin-bottom: 6px;'>
            <strong>Результат:</strong> {check_result_obj.message}
        </div>
        <div style='font-size: 12px; color: #666;'>
            Оценка: {check_result_obj.score:.1%} | Время выполнения: {execution_time_ms:.1f} мс
        </div>
    </div>
    """

    result_widget.value = result_html


def update_stats_widget(stats_widget: widgets.HTML, stats: dict) -> None:
    """
    Обновляет виджет статистики.

    Args:
        stats_widget: Виджет статистики для обновления
        stats: Словарь со статистикой
    """
    if stats:
        completed_icon = "✅" if stats["successful_attempts"] > 0 else "⏳"
        stats_html = f"""
        <div style='background: #f8f9fa; padding: 8px; border-radius: 4px; font-size: 12px; color: #666;'>
            {completed_icon} Попыток: {stats['total_attempts']} |
            Успешных: {stats['successful_attempts']} |
            Лучший результат: {stats['best_score']:.1%} |
            Средний результат: {stats['average_score']:.1%}
        </div>
        """
        stats_widget.value = stats_html
