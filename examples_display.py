"""Сборка виджетов Jupyter для отображения примеров."""

from __future__ import annotations

import html
import io
from contextlib import redirect_stdout
from typing import Any, List

import ipywidgets as widgets

from examples_html_utils import extract_example_sections, looks_like_python_code, strip_examples_wrapper


def _create_fallback_code_widget(code: str) -> widgets.VBox:
    """Интерактивная ячейка, если demo_cell_widget недоступен."""
    code_area = widgets.Textarea(
        value=code,
        layout=widgets.Layout(width="100%", height="180px"),
    )
    run_button = widgets.Button(
        description="▶ Запустить",
        button_style="success",
        layout=widgets.Layout(width="160px", margin="8px 0"),
    )
    output = widgets.Output(layout=widgets.Layout(margin="8px 0"))

    def _on_run(_button: widgets.Button) -> None:
        output.clear_output(wait=True)
        with output:
            buffer = io.StringIO()
            try:
                with redirect_stdout(buffer):
                    exec(code_area.value, {})
                text = buffer.getvalue()
                if text.strip():
                    print(text)
                else:
                    print("Код выполнен успешно.")
            except Exception as exc:
                print(f"Ошибка: {exc}")

    run_button.on_click(_on_run)
    return widgets.VBox([code_area, run_button, output])


def _create_code_widget(code: str, cell_adapter: Any) -> widgets.Widget | None:
    """Создаёт demo-ячейку или fallback с редактором и кнопкой запуска."""
    if not looks_like_python_code(code):
        return None

    if getattr(cell_adapter, "cells_available", False):
        demo_cells = cell_adapter.create_demo_cells([{"code": code}])
        if demo_cells:
            return demo_cells[0]

    return _create_fallback_code_widget(code)


def build_examples_widgets(styled_html: str, cell_adapter: Any) -> List[widgets.Widget]:
    """
    Строит виджеты для блока «Показать примеры» из HTML, собранного из JSON.

    Args:
        styled_html: HTML после render_examples_json_to_html + стилей.
        cell_adapter: Адаптер для создания интерактивных code-ячеек.

    Returns:
        Список виджетов для examples_container.
    """
    widgets_to_display: List[widgets.Widget] = [
        widgets.HTML(value="<h3>Практические примеры</h3>")
    ]

    sections = extract_example_sections(strip_examples_wrapper(styled_html))
    rendered_count = 0

    for section in sections:
        title = section.get("title", "").strip()
        description = section.get("description", "").strip()
        code = section.get("code", "").strip()
        code_widget = _create_code_widget(code, cell_adapter)
        if code_widget is None:
            continue

        if title:
            widgets_to_display.append(
                widgets.HTML(value=f"<h4>{html.escape(title)}</h4>")
            )
        if description and not any(
            phrase in description.lower()
            for phrase in (
                "в этом примере мы",
                "здесь мы создадим",
                "мы создадим",
            )
        ):
            widgets_to_display.append(
                widgets.HTML(value=f"<p>{html.escape(description)}</p>")
            )
        widgets_to_display.append(code_widget)
        rendered_count += 1

    if rendered_count == 0:
        widgets_to_display.append(
            widgets.HTML(
                value=(
                    "<p style='color:#721c24;'>"
                    "Не удалось показать исполняемые примеры. "
                    "Нажмите «Показать примеры» ещё раз."
                    "</p>"
                )
            )
        )

    return widgets_to_display
