"""
Логика выполнения и проверки кода для интерактивной ячейки.
Содержит функции для выполнения кода студента и проверки результатов.
"""

import time
from typing import Any, Dict, Tuple, Optional
from result_checker import CheckResult, check_result
from control_tasks_logger import log_attempt, get_cell_stats, is_cell_completed


def execute_student_code(
    student_code: str, execution_namespace: Dict[str, Any]
) -> Tuple[Any, str, bool]:
    """
    Выполняет код студента и возвращает результат.

    Args:
        student_code: Код студента для выполнения
        execution_namespace: Пространство имен для выполнения

    Returns:
        Кортеж (результат, вывод, успех_выполнения)
    """
    try:
        # Выполняем код студента
        exec(student_code, execution_namespace)

        # Ищем результат в пространстве имен
        result = None
        result_vars = [
            "result",
            "answer",
            "output",
            "res",
            "squares",
            "numbers",
            "data",
            "values",
        ]

        # Ищем переменные по имени
        for var_name in result_vars:
            if var_name in execution_namespace:
                result = execution_namespace[var_name]
                break

        return result, "", True

    except Exception as e:
        return None, str(e), False


def find_result_in_namespace(
    execution_namespace: Dict[str, Any], expected_result: Any
) -> Any:
    """
    Ищет результат в пространстве имен по типу ожидаемого результата.

    Args:
        execution_namespace: Пространство имен выполнения
        expected_result: Ожидаемый результат для определения типа

    Returns:
        Найденный результат или None
    """
    if execution_namespace:
        expected_type = type(expected_result)
        for var_name, var_value in execution_namespace.items():
            # Игнорируем встроенные переменные и импорты
            if (
                not var_name.startswith("_")
                and not var_name in ["__builtins__"]
                and type(var_value) == expected_type
                and var_name not in ["print", "len", "range", "list", "dict", "set"]
            ):
                return var_value

    return None


def check_execution_result(
    result: Any, expected_result: Any, check_type: str, check_kwargs: Dict[str, Any]
) -> CheckResult:
    """
    Проверяет результат выполнения кода.

    Args:
        result: Результат выполнения
        expected_result: Ожидаемый результат
        check_type: Тип проверки
        check_kwargs: Дополнительные параметры проверки

    Returns:
        Объект результата проверки
    """
    return check_result(result, expected_result, check_type, **check_kwargs)


def log_execution_attempt(
    cell_id: str,
    student_code: str,
    execution_result: Any,
    execution_output: str,
    execution_success: bool,
    check_result_obj: CheckResult,
    execution_time_ms: float,
) -> str:
    """
    Логирует попытку выполнения кода.

    Args:
        cell_id: Идентификатор ячейки
        student_code: Код студента
        execution_result: Результат выполнения
        execution_output: Вывод выполнения
        execution_success: Успешность выполнения
        check_result_obj: Результат проверки
        execution_time_ms: Время выполнения в миллисекундах

    Returns:
        Идентификатор попытки
    """
    return log_attempt(
        cell_id=cell_id,
        student_code=student_code,
        execution_result=execution_result,
        execution_output=execution_output,
        execution_success=execution_success,
        check_result=check_result_obj,
        execution_time_ms=execution_time_ms,
    )


def get_cell_attempt_count(cell_id: str) -> int:
    """
    Возвращает количество попыток для данной ячейки.

    Args:
        cell_id: Идентификатор ячейки

    Returns:
        Количество попыток
    """
    stats = get_cell_stats(cell_id)
    return stats["total_attempts"] if stats else 0


def check_attempt_limit(cell_id: str, max_attempts: Optional[int]) -> bool:
    """
    Проверяет, не превышен ли лимит попыток.

    Args:
        cell_id: Идентификатор ячейки
        max_attempts: Максимальное количество попыток

    Returns:
        True если лимит не превышен, False если превышен
    """
    if max_attempts is None:
        return True

    current_attempts = get_cell_attempt_count(cell_id)
    return current_attempts < max_attempts


def is_cell_task_completed(cell_id: str) -> bool:
    """
    Проверяет, выполнена ли ячейка.

    Args:
        cell_id: Идентификатор ячейки

    Returns:
        True если ячейка выполнена, False иначе
    """
    return is_cell_completed(cell_id)


def get_cell_statistics(cell_id: str) -> Optional[Dict[str, Any]]:
    """
    Возвращает статистику ячейки.

    Args:
        cell_id: Идентификатор ячейки

    Returns:
        Словарь со статистикой или None
    """
    return get_cell_stats(cell_id)
