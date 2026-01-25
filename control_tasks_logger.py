"""
Модуль логирования контрольных заданий для интерактивных ячеек.
Записывает попытки решения студентов и статистику выполнения.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from result_checker import CheckResult


@dataclass
class AttemptLog:
    """Лог одной попытки решения задания."""

    attempt_id: str
    cell_id: str
    student_code: str
    execution_result: Any
    execution_output: str
    execution_success: bool
    check_result: Dict[str, Any]  # Результат проверки
    timestamp: str
    execution_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует лог в словарь для сериализации."""
        return asdict(self)


@dataclass
class CellStats:
    """Статистика по ячейке с заданием."""

    cell_id: str
    total_attempts: int
    successful_attempts: int
    first_success_attempt: Optional[int]
    last_attempt_timestamp: str
    best_score: float
    average_score: float
    total_execution_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует статистику в словарь."""
        return asdict(self)


class ControlTasksLogger:
    """Система логирования контрольных заданий."""

    def __init__(self, log_file: str = "control_tasks_log.json"):
        """
        Инициализация логгера.

        Args:
            log_file: Путь к файлу лога
        """
        self.log_file = log_file
        self.log_data = self._load_log_file()

    def _load_log_file(self) -> Dict[str, Any]:
        """Загружает данные из файла лога."""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Проверяем структуру данных
                if not isinstance(data, dict):
                    data = self._create_empty_log()

                # Добавляем отсутствующие поля
                if "version" not in data:
                    data["version"] = "1.0"
                if "created_at" not in data:
                    data["created_at"] = datetime.now().isoformat()
                if "attempts" not in data:
                    data["attempts"] = []
                if "cell_stats" not in data:
                    data["cell_stats"] = {}

                return data

            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ Ошибка загрузки лога: {e}. Создается новый файл.")
                return self._create_empty_log()
        else:
            return self._create_empty_log()

    def _create_empty_log(self) -> Dict[str, Any]:
        """Создает пустую структуру лога."""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "attempts": [],
            "cell_stats": {},
        }

    def _save_log_file(self):
        """Сохраняет данные в файл лога."""
        try:
            self.log_data["last_updated"] = datetime.now().isoformat()

            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(self.log_data, f, ensure_ascii=False, indent=2)

        except IOError as e:
            print(f"❌ Ошибка сохранения лога: {e}")

    def log_attempt(
        self,
        cell_id: str,
        student_code: str,
        execution_result: Any,
        execution_output: str,
        execution_success: bool,
        check_result: CheckResult,
        execution_time_ms: float,
    ) -> str:
        """
        Записывает попытку решения задания.

        Args:
            cell_id: Идентификатор ячейки
            student_code: Код студента
            execution_result: Результат выполнения
            execution_output: Текстовый вывод
            execution_success: Успешность выполнения
            check_result: Результат проверки
            execution_time_ms: Время выполнения в миллисекундах

        Returns:
            str: Идентификатор попытки
        """
        # Создаем уникальный ID попытки
        attempt_id = f"{cell_id}_{len(self.log_data['attempts']) + 1}_{int(datetime.now().timestamp())}"

        # Сериализуем результат выполнения
        try:
            serialized_result = json.dumps(execution_result, default=str)
        except:
            serialized_result = str(execution_result)

        # Создаем лог попытки
        attempt_log = AttemptLog(
            attempt_id=attempt_id,
            cell_id=cell_id,
            student_code=student_code,
            execution_result=serialized_result,
            execution_output=execution_output,
            execution_success=execution_success,
            check_result={
                "passed": check_result.passed,
                "message": check_result.message,
                "score": check_result.score,
                "details": check_result.details,
            },
            timestamp=datetime.now().isoformat(),
            execution_time_ms=execution_time_ms,
        )

        # Добавляем в лог
        self.log_data["attempts"].append(attempt_log.to_dict())

        # Обновляем статистику по ячейке
        self._update_cell_stats(cell_id, check_result, execution_time_ms)

        # Сохраняем файл
        self._save_log_file()

        return attempt_id

    def _update_cell_stats(
        self, cell_id: str, check_result: CheckResult, execution_time_ms: float
    ):
        """Обновляет статистику по ячейке."""
        if cell_id not in self.log_data["cell_stats"]:
            # Создаем новую статистику
            self.log_data["cell_stats"][cell_id] = CellStats(
                cell_id=cell_id,
                total_attempts=0,
                successful_attempts=0,
                first_success_attempt=None,
                last_attempt_timestamp=datetime.now().isoformat(),
                best_score=0.0,
                average_score=0.0,
                total_execution_time_ms=0.0,
            ).to_dict()

        stats = self.log_data["cell_stats"][cell_id]

        # Обновляем счетчики
        stats["total_attempts"] += 1
        stats["total_execution_time_ms"] += execution_time_ms
        stats["last_attempt_timestamp"] = datetime.now().isoformat()

        if check_result.passed:
            stats["successful_attempts"] += 1
            if stats["first_success_attempt"] is None:
                stats["first_success_attempt"] = stats["total_attempts"]

        # Обновляем лучший результат
        if check_result.score > stats["best_score"]:
            stats["best_score"] = check_result.score

        # Пересчитываем средний результат
        cell_attempts = [
            a for a in self.log_data["attempts"] if a["cell_id"] == cell_id
        ]
        if cell_attempts:
            total_score = sum(a["check_result"]["score"] for a in cell_attempts)
            stats["average_score"] = total_score / len(cell_attempts)

    def get_cell_stats(self, cell_id: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает статистику по ячейке.

        Args:
            cell_id: Идентификатор ячейки

        Returns:
            Словарь со статистикой или None
        """
        return self.log_data["cell_stats"].get(cell_id)

    def get_cell_attempts(self, cell_id: str) -> List[Dict[str, Any]]:
        """
        Возвращает все попытки по ячейке.

        Args:
            cell_id: Идентификатор ячейки

        Returns:
            Список попыток
        """
        return [a for a in self.log_data["attempts"] if a["cell_id"] == cell_id]

    def get_last_attempt(self, cell_id: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает последнюю попытку по ячейке.

        Args:
            cell_id: Идентификатор ячейки

        Returns:
            Словарь с последней попыткой или None
        """
        attempts = self.get_cell_attempts(cell_id)
        return attempts[-1] if attempts else None

    def get_successful_attempt(self, cell_id: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает первую успешную попытку по ячейке.

        Args:
            cell_id: Идентификатор ячейки

        Returns:
            Словарь с успешной попыткой или None
        """
        attempts = self.get_cell_attempts(cell_id)
        for attempt in attempts:
            if attempt["check_result"]["passed"]:
                return attempt
        return None

    def is_cell_completed(self, cell_id: str) -> bool:
        """
        Проверяет, выполнена ли ячейка успешно.

        Args:
            cell_id: Идентификатор ячейки

        Returns:
            True, если есть успешная попытка
        """
        return self.get_successful_attempt(cell_id) is not None

    def get_overall_stats(self) -> Dict[str, Any]:
        """Возвращает общую статистику по всем заданиям."""
        total_cells = len(self.log_data["cell_stats"])
        completed_cells = sum(
            1
            for stats in self.log_data["cell_stats"].values()
            if stats["successful_attempts"] > 0
        )
        total_attempts = len(self.log_data["attempts"])

        if total_attempts > 0:
            successful_attempts = sum(
                1 for a in self.log_data["attempts"] if a["check_result"]["passed"]
            )
            success_rate = successful_attempts / total_attempts
            avg_execution_time = (
                sum(a["execution_time_ms"] for a in self.log_data["attempts"])
                / total_attempts
            )
        else:
            success_rate = 0.0
            avg_execution_time = 0.0

        return {
            "total_cells": total_cells,
            "completed_cells": completed_cells,
            "completion_rate": completed_cells / total_cells
            if total_cells > 0
            else 0.0,
            "total_attempts": total_attempts,
            "success_rate": success_rate,
            "average_execution_time_ms": avg_execution_time,
            "log_file_size_kb": os.path.getsize(self.log_file) / 1024
            if os.path.exists(self.log_file)
            else 0,
        }

    def export_stats(self, format: str = "json") -> str:
        """
        Экспортирует статистику в указанном формате.

        Args:
            format: Формат экспорта ('json', 'csv')

        Returns:
            Строка с данными в указанном формате
        """
        if format == "json":
            stats_data = {
                "overall_stats": self.get_overall_stats(),
                "cell_stats": self.log_data["cell_stats"],
                "exported_at": datetime.now().isoformat(),
            }
            return json.dumps(stats_data, ensure_ascii=False, indent=2)

        elif format == "csv":
            # Простой CSV экспорт статистики по ячейкам
            lines = [
                "cell_id,total_attempts,successful_attempts,best_score,average_score"
            ]

            for cell_id, stats in self.log_data["cell_stats"].items():
                line = f"{cell_id},{stats['total_attempts']},{stats['successful_attempts']},{stats['best_score']:.3f},{stats['average_score']:.3f}"
                lines.append(line)

            return "\n".join(lines)

        else:
            raise ValueError(f"Неподдерживаемый формат: {format}")

    def clear_cell_data(self, cell_id: str):
        """
        Очищает данные по конкретной ячейке.

        Args:
            cell_id: Идентификатор ячейки
        """
        # Удаляем попытки
        self.log_data["attempts"] = [
            a for a in self.log_data["attempts"] if a["cell_id"] != cell_id
        ]

        # Удаляем статистику
        if cell_id in self.log_data["cell_stats"]:
            del self.log_data["cell_stats"][cell_id]

        # Сохраняем изменения
        self._save_log_file()

    def clear_all_data(self):
        """Очищает все данные лога."""
        self.log_data = self._create_empty_log()
        self._save_log_file()


# Глобальный экземпляр логгера
default_logger = ControlTasksLogger()


def log_attempt(
    cell_id: str,
    student_code: str,
    execution_result: Any,
    execution_output: str,
    execution_success: bool,
    check_result: CheckResult,
    execution_time_ms: float,
) -> str:
    """
    Функция-помощник для быстрого логирования попытки.

    Args:
        cell_id: Идентификатор ячейки
        student_code: Код студента
        execution_result: Результат выполнения
        execution_output: Текстовый вывод
        execution_success: Успешность выполнения
        check_result: Результат проверки
        execution_time_ms: Время выполнения

    Returns:
        Идентификатор попытки
    """
    return default_logger.log_attempt(
        cell_id,
        student_code,
        execution_result,
        execution_output,
        execution_success,
        check_result,
        execution_time_ms,
    )


def get_cell_stats(cell_id: str) -> Optional[Dict[str, Any]]:
    """Функция-помощник для получения статистики по ячейке."""
    return default_logger.get_cell_stats(cell_id)


def is_cell_completed(cell_id: str) -> bool:
    """Функция-помощник для проверки выполнения ячейки."""
    return default_logger.is_cell_completed(cell_id)
