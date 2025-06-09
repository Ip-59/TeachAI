"""
Модуль проверки результатов выполнения кода для интерактивных ячеек.
Содержит различные типы проверок для контрольных заданий.
"""

import math
import inspect
from typing import Any, Dict, List, Tuple, Union, Callable, Optional
from abc import ABC, abstractmethod


class CheckResult:
    """Результат проверки выполнения задания."""

    def __init__(
        self,
        passed: bool,
        message: str = "",
        score: float = 0.0,
        details: Dict[str, Any] = None,
    ):
        """
        Инициализация результата проверки.

        Args:
            passed: Прошел ли тест
            message: Сообщение для студента
            score: Оценка от 0.0 до 1.0
            details: Дополнительные детали проверки
        """
        self.passed = passed
        self.message = message
        self.score = score
        self.details = details or {}

    def __str__(self):
        status = "✅ ЗАЧЁТ" if self.passed else "❌ НЕ ЗАЧЁТ"
        return f"{status}: {self.message}"


class BaseChecker(ABC):
    """Базовый класс для всех типов проверок."""

    @abstractmethod
    def check(self, result: Any, expected: Any, **kwargs) -> CheckResult:
        """
        Выполняет проверку результата.

        Args:
            result: Полученный результат выполнения кода
            expected: Ожидаемый результат
            **kwargs: Дополнительные параметры

        Returns:
            CheckResult: Результат проверки
        """
        pass


class ExactChecker(BaseChecker):
    """Проверка точного совпадения результатов."""

    def check(self, result: Any, expected: Any, **kwargs) -> CheckResult:
        """Проверяет точное совпадение результатов."""
        if result == expected:
            return CheckResult(
                passed=True, message=f"Правильно! Результат: {result}", score=1.0
            )
        else:
            return CheckResult(
                passed=False,
                message=f"Неверно. Получен: {result}, ожидался: {expected}",
                score=0.0,
                details={"result": result, "expected": expected},
            )


class NumericChecker(BaseChecker):
    """Проверка числовых результатов с допустимой погрешностью."""

    def check(
        self, result: Any, expected: Any, tolerance: float = 1e-9, **kwargs
    ) -> CheckResult:
        """
        Проверяет числовые результаты с учетом погрешности.

        Args:
            result: Полученный результат
            expected: Ожидаемый результат
            tolerance: Допустимая погрешность
        """
        try:
            result_num = float(result)
            expected_num = float(expected)

            if math.isclose(
                result_num, expected_num, rel_tol=tolerance, abs_tol=tolerance
            ):
                return CheckResult(
                    passed=True,
                    message=f"Правильно! Результат: {result_num}",
                    score=1.0,
                )
            else:
                diff = abs(result_num - expected_num)
                return CheckResult(
                    passed=False,
                    message=f"Неверно. Получен: {result_num}, ожидался: {expected_num} (разница: {diff:.6f})",
                    score=0.0,
                    details={
                        "result": result_num,
                        "expected": expected_num,
                        "difference": diff,
                        "tolerance": tolerance,
                    },
                )
        except (ValueError, TypeError) as e:
            return CheckResult(
                passed=False, message=f"Ошибка преобразования к числу: {e}", score=0.0
            )


class ListChecker(BaseChecker):
    """Проверка списков и последовательностей."""

    def check(
        self, result: Any, expected: Any, order_matters: bool = True, **kwargs
    ) -> CheckResult:
        """
        Проверяет списки и последовательности.

        Args:
            result: Полученный список
            expected: Ожидаемый список
            order_matters: Важен ли порядок элементов
        """
        # Проверяем, что результат не None
        if result is None:
            return CheckResult(
                passed=False,
                message="Результат не найден. Убедитесь, что ваш код возвращает список (добавьте строку с именем переменной в конце).",
                score=0.0,
            )

        try:
            result_list = list(result)
            expected_list = list(expected)

            if order_matters:
                if result_list == expected_list:
                    return CheckResult(
                        passed=True,
                        message=f"Правильно! Список: {result_list}",
                        score=1.0,
                    )
                else:
                    return CheckResult(
                        passed=False,
                        message=f"Неверный порядок или содержимое. Получен: {result_list}, ожидался: {expected_list}",
                        score=0.0,
                        details={"result": result_list, "expected": expected_list},
                    )
            else:
                # Проверяем только содержимое, порядок не важен
                if sorted(result_list) == sorted(expected_list):
                    return CheckResult(
                        passed=True,
                        message=f"Правильно! Список содержит нужные элементы: {result_list}",
                        score=1.0,
                    )
                else:
                    missing = set(expected_list) - set(result_list)
                    extra = set(result_list) - set(expected_list)
                    message = f"Неверное содержимое списка. Получен: {result_list}"

                    if missing:
                        message += f", отсутствуют: {list(missing)}"
                    if extra:
                        message += f", лишние: {list(extra)}"

                    return CheckResult(
                        passed=False,
                        message=message,
                        score=0.0,
                        details={
                            "result": result_list,
                            "expected": expected_list,
                            "missing": list(missing),
                            "extra": list(extra),
                        },
                    )

        except (TypeError, ValueError) as e:
            return CheckResult(
                passed=False,
                message=f"Ошибка преобразования к списку: {e}. Убедитесь, что возвращаете итерируемый объект.",
                score=0.0,
            )


class FunctionChecker(BaseChecker):
    """Проверка функций по набору тестовых случаев."""

    def check(
        self, result: Any, expected: Any, test_cases: List[Tuple] = None, **kwargs
    ) -> CheckResult:
        """
        Проверяет функцию по набору тестовых случаев.

        Args:
            result: Функция для проверки
            expected: Ожидаемая функция или список ожидаемых результатов
            test_cases: Список кортежей (args, expected_result)
        """
        if not callable(result):
            return CheckResult(
                passed=False, message="Результат должен быть функцией", score=0.0
            )

        if not test_cases:
            return CheckResult(
                passed=False,
                message="Не указаны тестовые случаи для проверки функции",
                score=0.0,
            )

        passed_tests = 0
        total_tests = len(test_cases)
        errors = []

        for i, test_case in enumerate(test_cases):
            try:
                if len(test_case) == 2:
                    args, expected_result = test_case
                    kwargs_test = {}
                else:
                    args, kwargs_test, expected_result = test_case

                # Вызываем функцию
                if isinstance(args, tuple):
                    actual_result = result(*args, **kwargs_test)
                else:
                    actual_result = result(args, **kwargs_test)

                # Проверяем результат
                if actual_result == expected_result:
                    passed_tests += 1
                else:
                    errors.append(
                        f"Тест {i+1}: получен {actual_result}, ожидался {expected_result}"
                    )

            except Exception as e:
                errors.append(f"Тест {i+1}: ошибка выполнения - {e}")

        score = passed_tests / total_tests
        passed = score == 1.0

        if passed:
            message = f"Отлично! Все {total_tests} тестов пройдены"
        else:
            message = f"Пройдено {passed_tests} из {total_tests} тестов. Ошибки: {'; '.join(errors[:3])}"
            if len(errors) > 3:
                message += f" и ещё {len(errors) - 3}..."

        return CheckResult(
            passed=passed,
            message=message,
            score=score,
            details={
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "errors": errors,
            },
        )


class OutputChecker(BaseChecker):
    """Проверка текстового вывода программы."""

    def check(
        self,
        result: Any,
        expected: Any,
        ignore_whitespace: bool = True,
        ignore_case: bool = False,
        **kwargs,
    ) -> CheckResult:
        """
        Проверяет текстовый вывод программы.

        Args:
            result: Полученный вывод
            expected: Ожидаемый вывод
            ignore_whitespace: Игнорировать пробелы и переносы строк
            ignore_case: Игнорировать регистр
        """
        try:
            result_str = str(result).strip() if ignore_whitespace else str(result)
            expected_str = str(expected).strip() if ignore_whitespace else str(expected)

            if ignore_case:
                result_str = result_str.lower()
                expected_str = expected_str.lower()

            if ignore_whitespace:
                # Нормализуем пробелы
                result_str = " ".join(result_str.split())
                expected_str = " ".join(expected_str.split())

            if result_str == expected_str:
                return CheckResult(passed=True, message=f"Правильный вывод!", score=1.0)
            else:
                return CheckResult(
                    passed=False,
                    message=f"Неверный вывод. Получен: '{result_str}', ожидался: '{expected_str}'",
                    score=0.0,
                    details={"result": result_str, "expected": expected_str},
                )

        except Exception as e:
            return CheckResult(
                passed=False, message=f"Ошибка при проверке вывода: {e}", score=0.0
            )


class ResultChecker:
    """Главный класс для проверки результатов выполнения заданий."""

    def __init__(self):
        """Инициализация системы проверки результатов."""
        self.checkers = {
            "exact": ExactChecker(),
            "numeric": NumericChecker(),
            "list": ListChecker(),
            "function": FunctionChecker(),
            "output": OutputChecker(),
        }

    def check_result(
        self, result: Any, expected: Any, check_type: str = "exact", **kwargs
    ) -> CheckResult:
        """
        Выполняет проверку результата по указанному типу.

        Args:
            result: Полученный результат
            expected: Ожидаемый результат
            check_type: Тип проверки ('exact', 'numeric', 'list', 'function', 'output')
            **kwargs: Дополнительные параметры для конкретного типа проверки

        Returns:
            CheckResult: Результат проверки
        """
        if check_type not in self.checkers:
            return CheckResult(
                passed=False,
                message=f"Неизвестный тип проверки: {check_type}",
                score=0.0,
            )

        checker = self.checkers[check_type]
        return checker.check(result, expected, **kwargs)

    def add_checker(self, name: str, checker: BaseChecker):
        """
        Добавляет новый тип проверки.

        Args:
            name: Название типа проверки
            checker: Экземпляр проверяющего класса
        """
        self.checkers[name] = checker

    def get_available_checkers(self) -> List[str]:
        """Возвращает список доступных типов проверок."""
        return list(self.checkers.keys())


# Экземпляр для глобального использования
default_checker = ResultChecker()


def check_result(
    result: Any, expected: Any, check_type: str = "exact", **kwargs
) -> CheckResult:
    """
    Функция-помощник для быстрой проверки результатов.

    Args:
        result: Полученный результат
        expected: Ожидаемый результат
        check_type: Тип проверки
        **kwargs: Дополнительные параметры

    Returns:
        CheckResult: Результат проверки
    """
    return default_checker.check_result(result, expected, check_type, **kwargs)
