"""
Фабрика для создания интерактивных ячеек.
Содержит функции-помощники для быстрого создания ячеек.
"""

from typing import Any, Dict, Optional
from interactive_cell_widget import InteractiveCellWidget


def create_interactive_cell(
    task_description: str,
    expected_result: Any,
    check_type: str = "exact",
    initial_code: str = "",
    title: Optional[str] = None,
    description: Optional[str] = None,
    cell_id: Optional[str] = None,
    check_kwargs: Optional[Dict[str, Any]] = None,
    max_attempts: Optional[int] = None,
    show_solution: bool = False,
    solution_code: str = "",
) -> InteractiveCellWidget:
    """
    Функция-помощник для быстрого создания интерактивной ячейки.

    Args:
        task_description: Описание задания
        expected_result: Ожидаемый результат
        check_type: Тип проверки
        initial_code: Начальный код
        title: Заголовок ячейки
        description: Описание ячейки
        cell_id: Уникальный идентификатор ячейки
        check_kwargs: Параметры проверки
        max_attempts: Максимум попыток
        show_solution: Показывать кнопку решения
        solution_code: Код решения

    Returns:
        Экземпляр InteractiveCellWidget
    """
    kwargs = {
        "task_description": task_description,
        "expected_result": expected_result,
        "check_type": check_type,
        "initial_code": initial_code,
        "show_solution": show_solution,
        "solution_code": solution_code,
    }

    if title is not None:
        kwargs["title"] = title
    if description is not None:
        kwargs["description"] = description
    if cell_id is not None:
        kwargs["cell_id"] = cell_id
    if check_kwargs is not None:
        kwargs["check_kwargs"] = check_kwargs
    if max_attempts is not None:
        kwargs["max_attempts"] = max_attempts

    return InteractiveCellWidget(**kwargs)


def create_simple_interactive_cell(
    task_description: str,
    expected_result: Any,
    initial_code: str = "",
    cell_id: Optional[str] = None,
) -> InteractiveCellWidget:
    """
    Создает простую интерактивную ячейку с минимальными параметрами.

    Args:
        task_description: Описание задания
        expected_result: Ожидаемый результат
        initial_code: Начальный код
        cell_id: Уникальный идентификатор ячейки

    Returns:
        Экземпляр InteractiveCellWidget
    """
    kwargs = {
        "task_description": task_description,
        "expected_result": expected_result,
        "initial_code": initial_code,
    }

    if cell_id is not None:
        kwargs["cell_id"] = cell_id

    return InteractiveCellWidget(**kwargs)


def create_interactive_cell_with_solution(
    task_description: str,
    expected_result: Any,
    solution_code: str,
    initial_code: str = "",
    cell_id: Optional[str] = None,
    title: Optional[str] = None,
) -> InteractiveCellWidget:
    """
    Создает интерактивную ячейку с возможностью показа решения.

    Args:
        task_description: Описание задания
        expected_result: Ожидаемый результат
        solution_code: Код решения
        initial_code: Начальный код
        cell_id: Уникальный идентификатор ячейки
        title: Заголовок ячейки

    Returns:
        Экземпляр InteractiveCellWidget
    """
    kwargs = {
        "task_description": task_description,
        "expected_result": expected_result,
        "solution_code": solution_code,
        "initial_code": initial_code,
        "show_solution": True,
    }

    if cell_id is not None:
        kwargs["cell_id"] = cell_id
    if title is not None:
        kwargs["title"] = title

    return InteractiveCellWidget(**kwargs)


def create_limited_attempts_cell(
    task_description: str,
    expected_result: Any,
    max_attempts: int,
    initial_code: str = "",
    cell_id: str = None,
    title: str = None,
) -> InteractiveCellWidget:
    """
    Создает интерактивную ячейку с ограничением попыток.

    Args:
        task_description: Описание задания
        expected_result: Ожидаемый результат
        max_attempts: Максимальное количество попыток
        initial_code: Начальный код
        cell_id: Уникальный идентификатор ячейки
        title: Заголовок ячейки

    Returns:
        Экземпляр InteractiveCellWidget
    """
    return InteractiveCellWidget(
        task_description=task_description,
        expected_result=expected_result,
        max_attempts=max_attempts,
        initial_code=initial_code,
        cell_id=cell_id,
        title=title,
    )


def create_custom_check_cell(
    task_description: str,
    expected_result: Any,
    check_type: str,
    check_kwargs: Dict[str, Any],
    initial_code: str = "",
    cell_id: str = None,
    title: str = None,
) -> InteractiveCellWidget:
    """
    Создает интерактивную ячейку с кастомной проверкой.

    Args:
        task_description: Описание задания
        expected_result: Ожидаемый результат
        check_type: Тип проверки
        check_kwargs: Параметры проверки
        initial_code: Начальный код
        cell_id: Уникальный идентификатор ячейки
        title: Заголовок ячейки

    Returns:
        Экземпляр InteractiveCellWidget
    """
    return InteractiveCellWidget(
        task_description=task_description,
        expected_result=expected_result,
        check_type=check_type,
        check_kwargs=check_kwargs,
        initial_code=initial_code,
        cell_id=cell_id,
        title=title,
    )
