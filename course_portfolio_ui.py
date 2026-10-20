"""UI портфеля курсов: список, открыть, удалить, начать ещё один."""

from __future__ import annotations

import html
import logging
from typing import Any, Callable, Optional

import ipywidgets as widgets
from IPython.display import clear_output, display

logger = logging.getLogger(__name__)

DisplayCallback = Callable[[Any], None]


def _is_engine(obj: Any) -> bool:
    return obj is not None and hasattr(obj, "startup_dashboard") and hasattr(
        obj, "initialize"
    )


def resolve_engine(host: Any) -> Any:
    """Ищет TeachAIEngine у виджета/интерфейса."""
    if _is_engine(host):
        return host
    if host is None:
        return None
    for attr in ("engine", "interface"):
        candidate = getattr(host, attr, None)
        if _is_engine(candidate):
            return candidate
        nested = getattr(candidate, "engine", None) if candidate is not None else None
        if _is_engine(nested):
            return nested
    return None


def _display_callback_for(engine: Any) -> DisplayCallback:
    def _cb(widget: Any) -> None:
        try:
            clear_output(wait=False)
            if widget is not None:
                display(widget)
        except Exception as exc:
            logger.error("Ошибка отображения: %s", exc)

    return _cb


def display_engine_dashboard(engine: Any) -> None:
    """Перерисовывает стартовый дашборд с портфелем."""
    widget = engine_dashboard_widget(engine)
    if widget is not None:
        clear_output(wait=True)
        display(widget)


def engine_dashboard_widget(engine: Any) -> Any:
    """Собирает дашборд и вешает обработчики (продолжить + портфель)."""
    if engine.startup_dashboard is None:
        from startup_dashboard import StartupDashboard

        engine.startup_dashboard = StartupDashboard(
            engine.state_manager, getattr(engine, "content_generator", None)
        )
    else:
        engine.startup_dashboard.state_manager = engine.state_manager
        cg = getattr(engine, "content_generator", None)
        if cg is not None:
            engine.startup_dashboard.content_generator = cg

    widget = engine.startup_dashboard.show_dashboard()
    callback = _display_callback_for(engine)
    engine.startup_dashboard.setup_continue_button_handler(engine, callback)
    panel = getattr(engine.startup_dashboard, "portfolio_panel", None)
    if panel is not None:
        panel.attach(engine, callback)
    return widget


def show_courses_home(host: Any) -> None:
    """«Назад к курсам»: дашборд портфеля или выбор курса."""
    engine = resolve_engine(host)
    if engine is not None and getattr(engine, "state_manager", None):
        display_engine_dashboard(engine)
        return
    facade = getattr(host, "interface", None)
    if facade is not None and hasattr(facade, "show_course_selection"):
        clear_output(wait=True)
        display(facade.show_course_selection())
        return
    logger.warning("show_courses_home: нет engine и нет фасада выбора курса")


def ensure_engine_ready(engine: Any, display_callback: Optional[DisplayCallback]) -> bool:
    """Ленивая initialize(), как кнопка «Продолжить обучение»."""
    if getattr(engine, "is_ready", False):
        return True
    logger.info("Инициализация компонентов для портфеля курсов...")
    if display_callback:
        display_callback(
            widgets.HTML(value="<p>⏳ Инициализация компонентов...</p>")
        )
    if not engine.initialize():
        if display_callback:
            display_callback(
                widgets.HTML(
                    value=(
                        "<p>Не удалось инициализировать систему. "
                        "Проверьте ключи API в .env.</p>"
                    )
                )
            )
        return False
    return True


class CoursePortfolioPanel:
    """Блок «Мои курсы» для дашборда."""

    def __init__(self, state_manager: Any) -> None:
        self.state_manager = state_manager
        self.engine: Any = None
        self.display_callback: Optional[DisplayCallback] = None
        self.widget = widgets.VBox(layout=widgets.Layout(width="100%", margin="0 0 16px 0"))
        self.rebuild()

    def attach(self, engine: Any, display_callback: DisplayCallback) -> None:
        self.engine = engine
        self.display_callback = display_callback

    def rebuild(self) -> None:
        rows = self.state_manager.list_user_courses()
        header = widgets.HTML(
            value=(
                "<h3 style='margin:0 0 8px 0;color:#2c3e50;'>Мои курсы</h3>"
                "<p style='margin:0 0 10px 0;color:#6c757d;font-size:13px;'>"
                "Можно начать ещё один курс — текущий сохранится. "
                "Переключение не удаляет прогресс.</p>"
            )
        )
        children: list[Any] = [header]
        if not rows:
            children.append(
                widgets.HTML(
                    value=(
                        "<p style='color:#6c757d;'>Пока нет сохранённых курсов. "
                        "Нажмите «Начать ещё один курс» или «Продолжить обучение».</p>"
                    )
                )
            )
        else:
            for row in rows:
                children.append(self._make_row(row))
        new_btn = widgets.Button(
            description="➕ Начать ещё один курс",
            button_style="primary",
            layout=widgets.Layout(width="auto", margin="8px 0 0 0"),
        )
        new_btn.on_click(lambda _b: self._on_new_course())
        children.append(new_btn)
        self.widget.children = tuple(children)

    def _make_row(self, row: dict[str, Any]) -> widgets.HBox:
        cid = row["course_id"]
        title = html.escape(str(row.get("title") or cid))
        status = row.get("status") or "active"
        percent = float(row.get("progress_percent") or 0)
        active = " · текущий" if row.get("is_active") else ""
        source = "свой" if row.get("source") == "user" else "каталог"
        badge = "завершён" if status == "completed" else "в процессе"
        info = widgets.HTML(
            value=(
                f"<div style='padding:8px 0;'><strong>{title}</strong>"
                f"<br><span style='color:#6c757d;font-size:13px;'>"
                f"{badge}{active} · {source} · {percent:.0f}%</span></div>"
            )
        )
        open_btn = widgets.Button(
            description="Продолжить" if row.get("is_active") else "Открыть",
            button_style="success",
            layout=widgets.Layout(width="120px", margin="4px"),
        )
        del_btn = widgets.Button(
            description="Удалить",
            button_style="danger",
            layout=widgets.Layout(width="140px", margin="4px"),
        )
        pending = {"confirm": False}

        open_btn.on_click(lambda _b, course_id=cid: self._on_open(course_id))

        def on_delete(_b, course_id=cid, button=del_btn) -> None:
            if not pending["confirm"]:
                pending["confirm"] = True
                button.description = "Точно удалить?"
                return
            self._on_delete(course_id)

        del_btn.on_click(on_delete)
        return widgets.HBox(
            [info, open_btn, del_btn],
            layout=widgets.Layout(
                width="100%",
                justify_content="space-between",
                align_items="center",
                border="1px solid #ecf0f1",
                padding="4px 8px",
                margin="4px 0",
            ),
        )

    def _on_open(self, course_id: str) -> None:
        if not self.state_manager.switch_course(course_id):
            logger.warning("Не удалось переключить курс %s", course_id)
            return
        self._proceed_active()

    def _on_delete(self, course_id: str) -> None:
        if not self.state_manager.delete_user_course(course_id):
            logger.warning("Не удалось удалить курс %s", course_id)
            return
        if self.engine is not None:
            display_engine_dashboard(self.engine)
        else:
            self.rebuild()

    def _on_new_course(self) -> None:
        engine = self.engine
        if engine is None:
            logger.warning("Нет engine — нельзя открыть выбор курса")
            return
        if not ensure_engine_ready(engine, self.display_callback):
            return
        if not engine.interface:
            logger.error("engine.interface не готов")
            return
        widget = engine.interface.show_course_selection()
        if self.display_callback:
            self.display_callback(widget)
        else:
            clear_output(wait=True)
            display(widget)

    def _proceed_active(self) -> None:
        engine = self.engine
        if engine is None:
            self.rebuild()
            return
        if not ensure_engine_ready(engine, self.display_callback):
            return
        dash = engine.startup_dashboard
        nxt = dash.get_next_lesson_interface(engine)
        if self.display_callback:
            self.display_callback(nxt)
        else:
            clear_output(wait=True)
            display(nxt)


def build_portfolio_panel(state_manager: Any) -> CoursePortfolioPanel:
    """Фабрика панели для вставки в дашборд."""
    return CoursePortfolioPanel(state_manager)
