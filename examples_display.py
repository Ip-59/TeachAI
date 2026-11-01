"""Сборка виджетов Jupyter для отображения примеров.

Источник данных — list[dict] {"title", "description", "code"}.
HTML-парсинг полностью удалён: код приходит из структурированных данных
и попадает в виджет без потерь.
"""

from __future__ import annotations

import html
import time
from typing import Any, Dict, List

import ipywidgets as widgets

from examples_code_fixes import sanitize_examples
from examples_html_utils import (
    NO_CODE_NOTICE,
    is_examples_notice,
    is_stub_only_description,
    looks_like_python_code,
)


def format_example_run_html(stdout: str, stderr: str, result: Any) -> str:
    """HTML блока «Результат запуска» под кнопкой примера.

    Args:
        stdout: Текст, который программа напечатала.
        stderr: Предупреждения, если выполнение само не упало.
        result: Значение последней строки, как в ячейке Jupyter. None — не показывать.

    Returns:
        Фрагмент HTML. Пустой вывод тоже занимает место на экране.
    """
    chunks: List[str] = []
    out = (stdout or "").strip()
    err = (stderr or "").strip()
    if out:
        chunks.append(
            "<pre style='white-space:pre-wrap;margin:8px 0;'>"
            f"{html.escape(out)}</pre>"
        )
    if result is not None:
        shown = result if isinstance(result, str) else repr(result)
        chunks.append(
            "<pre style='white-space:pre-wrap;margin:8px 0;'>"
            f"{html.escape(shown)}</pre>"
        )
    if err:
        chunks.append(
            "<pre style='white-space:pre-wrap;margin:8px 0;color:#6c757d;'>"
            f"{html.escape(err)}</pre>"
        )
    if not chunks:
        chunks.append("<p style='margin:8px 0;'>Код выполнен, вывода нет.</p>")
    return (
        "<div style='background:#f8f9fa;border:1px solid #dee2e6;"
        "border-radius:6px;padding:10px;margin:8px 0;'>"
        "<strong>Результат запуска</strong>"
        f"{''.join(chunks)}</div>"
    )


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
    # Не widgets.Output: его поток в Jupyter дописывается по числу активных
    # областей вывода, и один щелчок печатает результат несколько раз.
    # Текст пишем в .value виджета, который уже стоит в дереве: так блок
    # не пропадает, в отличие от подмены children пустого контейнера.
    result_html = widgets.HTML(value="")
    images_box = widgets.VBox()
    busy_until = {"t": 0.0}

    def _on_run(_button: widgets.Button) -> None:
        now = time.monotonic()
        if now < busy_until["t"]:
            return
        busy_until["t"] = now + 1.0
        try:
            from code_sandbox import image_widgets, run_student_code

            sandbox = run_student_code(
                code_area.value,
                capture_variables=False,
                eval_last_expression=True,
            )
            imgs = tuple(image_widgets(sandbox.images))
            if sandbox.timed_out or not sandbox.success:
                msg = sandbox.error or sandbox.stderr or "Ошибка выполнения кода"
                result_html.value = (
                    "<div style='background:#f8d7da;border:1px solid #f5c6cb;"
                    "border-radius:6px;padding:10px;margin:8px 0;'>"
                    "<strong>Результат запуска</strong>"
                    "<pre style='white-space:pre-wrap;margin:8px 0;color:#721c24;'>"
                    f"{html.escape(msg)}</pre></div>"
                )
            else:
                result_html.value = format_example_run_html(
                    sandbox.stdout, sandbox.stderr, sandbox.result
                )
            images_box.children = imgs
        except Exception as exc:
            images_box.children = ()
            result_html.value = (
                "<div style='background:#f8d7da;border:1px solid #f5c6cb;"
                "border-radius:6px;padding:10px;margin:8px 0;'>"
                "<strong>Результат запуска</strong>"
                "<pre style='white-space:pre-wrap;margin:8px 0;color:#721c24;'>"
                f"{html.escape(str(exc))}</pre></div>"
            )

    run_button.on_click(_on_run)
    return widgets.VBox([code_area, run_button, result_html, images_box])


def _create_code_widget(code: str, cell_adapter: Any) -> widgets.Widget | None:
    """Создаёт demo-ячейку или fallback с редактором и кнопкой запуска."""
    if not looks_like_python_code(code):
        return None

    if getattr(cell_adapter, "cells_available", False):
        demo_cells = cell_adapter.create_demo_cells([{"code": code}])
        if demo_cells:
            return demo_cells[0]

    return _create_fallback_code_widget(code)


def _notice_widget(text: str) -> widgets.HTML:
    """Обычное сообщение: по уроку нет запускаемого примера."""
    safe = html.escape(text)
    return widgets.HTML(
        value=(
            "<div style='background:#e7f3ff;border:1px solid #b8daff;"
            "border-radius:8px;padding:16px;margin:8px 0;'>"
            "<p style='color:#004085;margin:0;line-height:1.5;'>"
            f"{safe}</p></div>"
        )
    )


def build_examples_widgets(
    examples_data: List[Dict[str, str]],
    cell_adapter: Any,
) -> List[widgets.Widget]:
    """Строит виджеты для блока «Показать примеры» из list[dict].

    Args:
        examples_data: Список словарей {"title", "description", "code"}.
        cell_adapter: Адаптер для создания интерактивных code-ячеек.

    Returns:
        Список виджетов для examples_container.
    """
    if is_examples_notice(examples_data):
        return [_notice_widget(str(examples_data.get("notice") or NO_CODE_NOTICE))]

    widgets_to_display: List[widgets.Widget] = [
        widgets.HTML(value="<h3>Практические примеры</h3>")
    ]

    if not isinstance(examples_data, list):
        widgets_to_display.append(
            widgets.HTML(
                value=(
                    "<p style='color:#721c24;'>"
                    "Не удалось показать примеры: неверный формат данных."
                    "</p>"
                )
            )
        )
        return widgets_to_display

    examples_data = sanitize_examples(examples_data)

    rendered_count = 0
    for index, example in enumerate(examples_data, start=1):
        if not isinstance(example, dict):
            continue
        code = (example.get("code") or "").strip()
        code_widget = _create_code_widget(code, cell_adapter)
        if code_widget is None:
            continue

        title = (example.get("title") or f"Пример {index}").strip()
        description = (example.get("description") or "").strip()

        widgets_to_display.append(
            widgets.HTML(value=f"<h4>{html.escape(title)}</h4>")
        )
        if description and not is_stub_only_description(description):
            from student_content import render_student_content

            widgets_to_display.append(
                widgets.HTML(value=render_student_content(description, css=False))
            )
        widgets_to_display.append(code_widget)
        rendered_count += 1

    if rendered_count == 0:
        widgets_to_display.append(_notice_widget(NO_CODE_NOTICE))

    return widgets_to_display
