"""
Виджет демонстрационной ячейки для показа примеров кода.
Код отображается только для чтения с возможностью запуска.
"""

import ipywidgets as widgets
from cell_widget_base import CellWidgetBase
from typing import Optional


class DemoCellWidget(CellWidgetBase):
    """
    Демонстрационная ячейка с кодом только для чтения.
    Используется для показа примеров кода, которые студент может запустить и посмотреть результат.
    """

    def __init__(
        self,
        code: str,
        cell_id: str = None,
        title: str = None,
        description: str = None,
        show_code: bool = True,
        auto_run: bool = False,
        **kwargs,
    ):
        """
        Инициализация демонстрационной ячейки.

        Args:
            code: Python код для демонстрации
            cell_id: Уникальный идентификатор ячейки
            title: Заголовок ячейки
            description: Описание/инструкция для ячейки
            show_code: Показывать ли код (по умолчанию True)
            auto_run: Автоматически запускать код при создании (по умолчанию False)
        """
        self.code = code
        self.show_code = show_code
        self.auto_run = auto_run

        # Создаем виджеты до вызова родительского конструктора
        self._create_widgets()

        super().__init__(
            cell_id=cell_id, title=title, description=description, **kwargs
        )

        # Автоматический запуск, если указан
        if self.auto_run:
            self._run_code()

    def _create_widgets(self):
        """Создание специфичных для демонстрационной ячейки виджетов."""

        # Область с кодом (только для чтения)
        if self.show_code:
            self.code_display = widgets.HTML(
                value=self._format_code_html(),
                layout=widgets.Layout(width="100%", margin="0 0 5px 0"),
            )

        # Кнопка запуска
        self.run_button = widgets.Button(
            description="▶ Запустить код",
            tooltip="Запустить демонстрационный код",
            button_style="info",
            layout=widgets.Layout(width="auto", margin="0 5px 5px 0"),
        )

        # Привязываем обработчик события
        self.run_button.on_click(self._on_run_clicked)

        # Кнопка для переключения видимости кода
        if self.show_code:
            self.toggle_code_button = widgets.Button(
                description="🙈 Скрыть код",
                tooltip="Показать/скрыть код",
                button_style="",
                layout=widgets.Layout(width="auto", margin="0 0 5px 0"),
            )
            self.toggle_code_button.on_click(self._on_toggle_code_clicked)

        # Индикатор состояния
        self.status_label = widgets.HTML(
            value="<i>Готов к запуску</i>", layout=widgets.Layout(margin="0 0 5px 0")
        )

    def _get_specific_widgets(self) -> list:
        """Возвращает специфичные для демонстрационной ячейки виджеты."""
        widgets_list = []

        # Добавляем область с кодом, если нужно показывать
        if self.show_code and hasattr(self, "code_display"):
            widgets_list.append(self.code_display)

        # Контейнер с кнопками
        buttons = [self.run_button]
        if self.show_code and hasattr(self, "toggle_code_button"):
            buttons.append(self.toggle_code_button)

        button_box = widgets.HBox(
            children=buttons, layout=widgets.Layout(margin="0 0 5px 0")
        )
        widgets_list.append(button_box)

        # Статус
        widgets_list.append(self.status_label)

        return widgets_list

    def _format_code_html(self) -> str:
        """Форматирует код для отображения в HTML с подсветкой синтаксиса."""
        # Экранируем HTML символы
        escaped_code = (
            self.code.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

        # Простая подсветка синтаксиса Python
        return f"""
        <div style="
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 0;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            overflow-x: auto;
            margin-bottom: 5px;
        ">
            <div style="
                background-color: #e9ecef;
                color: #495057;
                font-size: 12px;
                font-weight: bold;
                padding: 8px 12px;
                border-bottom: 1px solid #dee2e6;
                margin: 0;
            ">
                🐍 Демонстрационный код:
            </div>
            <pre style="
                color: #495057;
                margin: 0;
                padding: 12px;
                background: transparent;
                border: none;
                font-family: inherit;
                font-size: inherit;
                line-height: 1.4;
                white-space: pre;
                overflow-x: auto;
            ">{escaped_code}</pre>
        </div>
        """

    def _on_run_clicked(self, button):
        """Обработчик клика по кнопке запуска."""
        self._run_code()

    def _on_toggle_code_clicked(self, button):
        """Обработчик клика по кнопке переключения видимости кода."""
        self._toggle_code_visibility()

    def _run_code(self):
        """Запускает демонстрационный код."""
        # Обновляем статус
        self.status_label.value = "<span style='color: orange;'>⏳ Выполняется...</span>"

        # Очищаем предыдущий вывод
        self.clear_output()

        # Выполняем код
        result, output, success = self.execute_code(self.code)

        # Отображаем результат
        self.display_result(result, output, success)

        # Обновляем статус
        if success:
            self.status_label.value = (
                "<span style='color: green;'>✅ Выполнено успешно</span>"
            )
        else:
            self.status_label.value = (
                "<span style='color: red;'>❌ Ошибка выполнения</span>"
            )

    def _toggle_code_visibility(self):
        """Переключает видимость кода."""
        if not hasattr(self, "code_display"):
            return

        current_children = list(self.children)

        if self.code_display in current_children:
            # Скрываем код
            current_children.remove(self.code_display)
            self.toggle_code_button.description = "👁 Показать код"
            self.toggle_code_button.tooltip = "Показать код"
        else:
            # Показываем код (вставляем после заголовка/описания, но перед кнопками)
            insert_index = 0

            # Ищем позицию для вставки (после заголовка и описания)
            for i, child in enumerate(current_children):
                if isinstance(child, widgets.HTML) and (
                    "h3>" in child.value or "color: #666" in child.value
                ):
                    insert_index = i + 1
                elif isinstance(child, widgets.HBox):  # Это контейнер с кнопками
                    break

            current_children.insert(insert_index, self.code_display)
            self.toggle_code_button.description = "🙈 Скрыть код"
            self.toggle_code_button.tooltip = "Скрыть код"

        self.children = current_children

    def set_code(self, code: str):
        """
        Устанавливает новый код для демонстрации.

        Args:
            code: Новый Python код
        """
        self.code = code
        if hasattr(self, "code_display"):
            self.code_display.value = self._format_code_html()
        self.status_label.value = "<i>Готов к запуску (код обновлен)</i>"
        self.clear_output()

    def get_code(self) -> str:
        """
        Возвращает текущий код демонстрации.

        Returns:
            Строка с кодом
        """
        return self.code

    def run(self):
        """Программный запуск кода (альтернатива клику по кнопке)."""
        self._run_code()

    def get_cell_info(self) -> dict:
        """Возвращает расширенную информацию о демонстрационной ячейке."""
        info = super().get_cell_info()
        info.update(
            {
                "code": self.code,
                "show_code": self.show_code,
                "auto_run": self.auto_run,
                "code_length": len(self.code),
                "code_lines": len(self.code.split("\n")),
            }
        )
        return info


def create_demo_cell(
    code: str,
    title: str = None,
    description: str = None,
    show_code: bool = True,
    auto_run: bool = False,
) -> DemoCellWidget:
    """
    Функция-помощник для быстрого создания демонстрационной ячейки.

    Args:
        code: Python код для демонстрации
        title: Заголовок ячейки
        description: Описание ячейки
        show_code: Показывать ли код
        auto_run: Автоматически запускать код

    Returns:
        Экземпляр DemoCellWidget
    """
    return DemoCellWidget(
        code=code,
        title=title,
        description=description,
        show_code=show_code,
        auto_run=auto_run,
    )
