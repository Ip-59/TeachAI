"""
Базовый класс для виджетов ячеек в образовательной системе.
Содержит общую функциональность для демонстрационных и интерактивных ячеек.
"""

import ipywidgets as widgets
from IPython.display import display, clear_output
import sys
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Optional, Dict, Tuple


class CellWidgetBase(widgets.VBox):
    """
    Базовый класс для всех типов ячеек (демонстрационных и интерактивных).
    Предоставляет общую функциональность для выполнения кода и отображения результатов.
    """

    def __init__(
        self, cell_id: Optional[str] = None, title: Optional[str] = None, description: Optional[str] = None, **kwargs
    ):
        """
        Инициализация базового виджета ячейки.

        Args:
            cell_id: Уникальный идентификатор ячейки
            title: Заголовок ячейки
            description: Описание/инструкция для ячейки
        """
        super().__init__(**kwargs)

        self.cell_id = cell_id or f"cell_{id(self)}"
        self.title = title
        self.description = description

        # Контейнер для вывода результатов выполнения кода
        self.output_area = widgets.Output()

        # Пространство имен для выполнения кода
        self.execution_namespace = {}

        # Стили для различных элементов
        self._init_styles()

        # Создание базовой структуры виджета
        self._create_base_layout()

    def _init_styles(self):
        """Инициализация стилей для элементов интерфейса."""
        self.title_style = {
            "description_width": "0px",
            "font_weight": "bold",
            "font_size": "16px",
        }

        self.description_style = {
            "description_width": "0px",
            "font_size": "14px",
            "color": "#666",
        }

        self.button_style = {"button_color": "#4CAF50", "font_weight": "bold"}

        self.error_style = {"color": "red", "font_weight": "bold"}

        self.success_style = {"color": "green", "font_weight": "bold"}

    def _create_base_layout(self):
        """Создание базовой структуры виджета."""
        children = []

        # Добавляем заголовок, если есть
        if self.title:
            title_widget = widgets.HTML(
                value=f"<h3>{self.title}</h3>",
                layout=widgets.Layout(margin="0 0 5px 0"),
            )
            children.append(title_widget)

        # Добавляем описание, если есть
        if self.description:
            description_widget = widgets.HTML(
                value=f"<div style='margin-bottom: 8px; color: #666;'>{self.description}</div>",
                layout=widgets.Layout(margin="0 0 5px 0"),
            )
            children.append(description_widget)

        # Базовые дочерние элементы (будут переопределены в наследниках)
        children.extend(self._get_specific_widgets())

        # Область вывода результатов
        children.append(self.output_area)

        self.children = children

        # Стиль для всего контейнера
        self.layout = widgets.Layout(
            border="1px solid #ddd", padding="10px", margin="5px 0", border_radius="5px"
        )

    def _get_specific_widgets(self) -> list:
        """
        Возвращает специфичные для типа ячейки виджеты.
        Должен быть переопределен в наследниках.
        """
        return []

    def execute_code(self, code: str) -> Tuple[Any, str, bool]:
        """
        Выполняет Python код в дочернем процессе (D9) и возвращает результат.

        Args:
            code: Строка с Python кодом для выполнения

        Returns:
            Кортеж (результат, вывод, успешность_выполнения)
        """
        if not code.strip():
            return None, "Пустой код", False

        from code_sandbox import run_student_code

        if not hasattr(self, "execution_namespace") or self.execution_namespace is None:
            self.execution_namespace = {}

        sandbox = run_student_code(
            code,
            initial_vars=self.execution_namespace,
            capture_variables=True,
            eval_last_expression=True,
        )
        self._last_sandbox_images = list(sandbox.images or [])
        if sandbox.timed_out:
            return None, sandbox.error or "Код выполнялся слишком долго, возможно, бесконечный цикл", False
        if sandbox.variables:
            self.execution_namespace.update(sandbox.variables)

        output = sandbox.stdout or ""
        if sandbox.stderr:
            output = f"{output}\n{sandbox.stderr}" if output else sandbox.stderr

        if not sandbox.success:
            return None, (sandbox.error or output or "Ошибка выполнения"), False

        return sandbox.result, output, True

    def display_result(self, result: Any, output: str, success: bool):
        """
        Отображает результат выполнения кода в области вывода.

        Args:
            result: Результат выполнения кода
            output: Текстовый вывод (stdout/stderr)
            success: Флаг успешности выполнения
        """
        with self.output_area:
            clear_output(wait=True)

            if not success:
                # Ошибка выполнения
                print(f"❌ Ошибка выполнения:\n{output}")
            else:
                # Успешное выполнение
                result_lines = []
                
                if output.strip():
                    result_lines.append(f"📤 Вывод:\n{output}")

                if result is not None:
                    result_lines.append(f"📊 Результат: {result}")

                if not output.strip() and result is None:
                    result_lines.append("✅ Код выполнен успешно (без вывода)")
                
                # Выводим все одной командой
                if result_lines:
                    print("\n".join(result_lines))

            from code_sandbox import display_images

            display_images(getattr(self, "_last_sandbox_images", None))

    def clear_output(self):
        """Очищает область вывода результатов."""
        with self.output_area:
            clear_output(wait=True)

    def set_title(self, title: str):
        """Устанавливает новый заголовок ячейки."""
        self.title = title
        self._create_base_layout()

    def set_description(self, description: str):
        """Устанавливает новое описание ячейки."""
        self.description = description
        self._create_base_layout()

    def get_cell_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о ячейке.

        Returns:
            Словарь с информацией о ячейке
        """
        return {
            "cell_id": self.cell_id,
            "title": self.title,
            "description": self.description,
            "type": self.__class__.__name__,
        }
