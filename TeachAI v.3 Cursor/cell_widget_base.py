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
        self, cell_id: str = None, title: str = None, description: str = None, **kwargs
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
        Выполняет Python код и возвращает результат.

        Args:
            code: Строка с Python кодом для выполнения

        Returns:
            Кортеж (результат, вывод, успешность_выполнения)
        """
        if not code.strip():
            return None, "Пустой код", False

        # Захват stdout и stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        result = None
        success = True

        try:
            # Перенаправляем вывод
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture

            # Используем персистентное пространство имен для ячейки
            if not hasattr(self, "execution_namespace") or not self.execution_namespace:
                self.execution_namespace = {}
                # Добавляем основные встроенные функции
                self.execution_namespace.update(__builtins__)

            # Выполняем код в персистентном пространстве имен
            exec(code, self.execution_namespace, self.execution_namespace)

            # Пытаемся получить результат из последней строки (если это выражение)
            lines = code.strip().split("\n")
            if lines:
                last_line = lines[-1].strip()
                if (
                    last_line
                    and not last_line.startswith(
                        (
                            "print",
                            "import",
                            "from",
                            "def",
                            "class",
                            "if",
                            "for",
                            "while",
                            "try",
                            "with",
                            "#",
                        )
                    )
                    and "=" not in last_line
                    and not last_line.endswith(":")
                    and "+=" not in last_line
                    and "-=" not in last_line
                    and "*=" not in last_line
                    and "append(" not in last_line
                ):
                    try:
                        result = eval(last_line, self.execution_namespace)
                    except:
                        pass

        except Exception as e:
            success = False
            stderr_capture.write(f"Ошибка: {str(e)}\n")
            stderr_capture.write(traceback.format_exc())

        finally:
            # Восстанавливаем stdout и stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        # Получаем захваченный вывод
        stdout_content = stdout_capture.getvalue()
        stderr_content = stderr_capture.getvalue()

        output = stdout_content
        if stderr_content:
            output += f"\n{stderr_content}" if output else stderr_content

        return result, output, success

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
                print("❌ Ошибка выполнения:")
                print(output)
            else:
                # Успешное выполнение
                if output.strip():
                    print("📤 Вывод:")
                    print(output)

                if result is not None:
                    print(f"📊 Результат: {result}")

                if not output.strip() and result is None:
                    print("✅ Код выполнен успешно (без вывода)")

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
