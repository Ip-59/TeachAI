"""UI выбора курса: каталог или своё название."""

from __future__ import annotations

import html
import logging
import time

import ipywidgets as widgets
from IPython.display import clear_output, display

logger = logging.getLogger(__name__)


def build_course_selection(setup) -> widgets.VBox:
    """
    Собирает экран выбора курса.

    Args:
        setup: ``SetupInterface`` (state, генератор, логгер, assessment).
    """
    try:
        courses = setup.state_manager.get_all_courses()
        if not courses:
            return setup._create_courses_error_interface()

        from project_identity import scope_banner_html

        header = setup.utils.create_header("Выбор курса")
        description = widgets.HTML(
            value=(
                scope_banner_html()
                + "<p>Сначала тема курса, затем общее время именно этого курса, "
                "затем длительность одного занятия. Эти два числа не переносятся "
                "на следующий курс. Каталог — Python и AI/ML; своё название тоже "
                "должно быть из этой области. Уже начатый курс открывается с дашборда "
                "или кнопкой «Продолжить» — его время не спрашивается заново.</p>"
            )
        )

        source_radio = widgets.RadioButtons(
            options=[
                ("Курс из списка", "catalog"),
                ("Своё название курса", "custom"),
            ],
            value="catalog",
            description="",
            layout=widgets.Layout(width="100%", margin="4px 0"),
        )

        course_dropdown = widgets.Dropdown(
            options=[(course["title"], course["id"]) for course in courses],
            description="Выберите курс:",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="500px"),
        )
        course_description = widgets.HTML(value="")

        custom_title = widgets.Text(
            description="Название:",
            placeholder="Например: Основы pandas для аналитика",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="520px"),
        )
        custom_desc = widgets.Textarea(
            description="Описание (необязательно):",
            placeholder="Кратко, чему должен научить курс",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="520px", height="80px"),
        )
        custom_box = widgets.VBox(
            [custom_title, custom_desc],
            layout=widgets.Layout(display="none", gap="8px"),
        )
        catalog_box = widgets.VBox(
            [course_dropdown, course_description],
            layout=widgets.Layout(display="flex"),
        )

        def _catalog_html(course: dict) -> str:
            return (
                '<div style="padding: 15px; background-color: #f8f9fa; '
                'border-radius: 8px; margin: 15px 0; border: 1px solid #dee2e6;">'
                '<h3 style="margin-top: 0; color: #495057;">Описание курса</h3>'
                f"<p><strong>Описание:</strong> {html.escape(str(course.get('description', '')))}</p>"
                f"<p><strong>Требования:</strong> {html.escape(str(course.get('prerequisites', 'Не указаны')))}</p>"
                f"<p><strong>Сложность:</strong> {html.escape(str(course.get('difficulty', 'Не указана')))}</p>"
                "</div>"
            )

        def _refresh_start_label() -> None:
            from course_portfolio import has_course, schedule_of

            catalog_id = course_dropdown.value
            continuing = source_radio.value == "catalog" and has_course(
                setup.state_manager.state, catalog_id
            )
            if continuing:
                start_button.description = "Продолжить этот курс"
                schedule_box.layout.display = "none"
                saved = schedule_of(setup.state_manager.state, catalog_id)
                if saved:
                    saved_schedule.value = (
                        "<p style='margin:8px 0;color:#495057;'>"
                        f"У этого курса уже задано: {saved['total_study_hours']} ч, "
                        f"занятие {saved['lesson_duration_minutes']} мин.</p>"
                    )
                else:
                    saved_schedule.value = (
                        "<p style='margin:8px 0;color:#495057;'>"
                        "Этот курс уже начат. Время для него не меняется.</p>"
                    )
            else:
                start_button.description = "Начать курс"
                schedule_box.layout.display = "flex"
                saved_schedule.value = ""

        def on_course_change(change):
            course = next((c for c in courses if c["id"] == change["new"]), None)
            if course:
                course_description.value = _catalog_html(course)
            _refresh_start_label()

        if courses:
            course_description.value = _catalog_html(courses[0])

        def on_source_change(change):
            custom = change["new"] == "custom"
            custom_box.layout.display = "flex" if custom else "none"
            catalog_box.layout.display = "none" if custom else "flex"
            _refresh_start_label()

        hours_widget = widgets.IntSlider(
            value=10,
            min=1,
            max=100,
            step=1,
            description="Общее время курса (часов):",
            continuous_update=False,
            style={"description_width": "initial"},
            layout=widgets.Layout(width="520px"),
        )
        duration_widget = widgets.IntSlider(
            value=30,
            min=5,
            max=120,
            step=5,
            description="Длительность занятия (минут):",
            continuous_update=False,
            style={"description_width": "initial"},
            layout=widgets.Layout(width="520px"),
        )
        schedule_box = widgets.VBox(
            [hours_widget, duration_widget],
            layout=widgets.Layout(display="flex", gap="8px"),
        )
        saved_schedule = widgets.HTML(value="")

        start_button = widgets.Button(
            description="Начать курс",
            button_style="success",
            tooltip="Начать выбранный или свой курс",
            icon="play",
            layout=widgets.Layout(width="260px", height="40px"),
        )
        # VBox-слот вместо Output: display/clear_output в Output даёт задвоение.
        status_box = widgets.VBox([])

        def _set_status(widget=None) -> None:
            status_box.children = () if widget is None else (widget,)

        def on_start_button_clicked(_b):
            if start_button.disabled:
                return
            start_button.disabled = True
            try:
                _set_status()
                course = _resolve_course(
                    setup,
                    source_radio.value,
                    courses,
                    course_dropdown.value,
                    custom_title.value,
                    custom_desc.value,
                    report=_set_status,
                )
                if course is None:
                    return
                schedule = {
                    "total_study_hours": int(hours_widget.value),
                    "lesson_duration_minutes": int(duration_widget.value),
                }
                if source_radio.value == "custom":
                    from course_domain_ui import gate_custom_course

                    def _switch_to_catalog() -> None:
                        source_radio.value = "catalog"

                    gate_custom_course(
                        setup,
                        course,
                        schedule,
                        _start_course,
                        _switch_to_catalog,
                        status_box=status_box,
                    )
                    return
                clear_output(wait=True)
                _start_course(setup, course, schedule)
            finally:
                # После ухода с экрана кнопка уже не видна; на предупреждении
                # снова можно нажать «Начать» / сменить тему.
                start_button.disabled = False

        start_button.on_click(on_start_button_clicked)
        course_dropdown.observe(on_course_change, names="value")
        source_radio.observe(on_source_change, names="value")
        _refresh_start_label()

        return widgets.VBox(
            [
                header,
                description,
                source_radio,
                catalog_box,
                custom_box,
                schedule_box,
                saved_schedule,
                start_button,
                status_box,
            ],
            layout=widgets.Layout(gap="15px"),
        )
    except Exception as e:
        logger.error("Ошибка при отображении списка курсов: %s", e)
        return setup._create_courses_error_interface(
            f"Произошла ошибка при загрузке списка курсов: {str(e)}"
        )


def _resolve_course(
    setup,
    source: str,
    courses: list,
    catalog_id,
    custom_title: str,
    custom_desc: str,
    report=None,
):
    from custom_course import build_custom_course, validate_custom_course

    def _report(widget) -> None:
        if report is not None:
            report(widget)
        else:
            display(widget)

    if source == "custom":
        error = validate_custom_course(custom_title, custom_desc)
        if error:
            _report(setup.utils.create_styled_message(error, "warning"))
            return None
        return build_custom_course(custom_title, custom_desc)

    course = next((c for c in courses if c["id"] == catalog_id), None)
    if not course:
        _report(
            setup.utils.create_styled_message(
                "Ошибка при выборе курса. Пожалуйста, попробуйте еще раз.",
                "incorrect",
            )
        )
        return None
    course = dict(course)
    course.setdefault("source", "catalog")
    return course


def _open_lesson_after_plan(setup, _course: dict) -> None:
    """Переход к текущему/первому уроку или экрану завершения."""
    section_id, topic_id, lesson_id, _lesson_data = (
        setup.state_manager.get_next_lesson()
    )
    time.sleep(1)
    clear_output(wait=True)

    engine = getattr(setup, "engine", None)
    if section_id and topic_id and lesson_id:
        display(
            setup.utils.create_styled_message("Переход к уроку...", "info")
        )
        from lesson_interface import LessonInterface

        lesson_ui = LessonInterface(
            setup.state_manager,
            setup.content_generator,
            setup.system_logger,
            setup.assessment,
            engine=engine,
        )
        if engine is not None and getattr(engine, "interface", None):
            lesson_ui.interface = engine.interface
        clear_output(wait=True)
        display(lesson_ui.show_lesson(section_id, topic_id, lesson_id))
        return

    if section_id is None and topic_id is None and lesson_id is None:
        display(
            setup.utils.create_styled_message(
                "Курс завершен! Показываем экран завершения...",
                "info",
            )
        )
        from completion_interface import CompletionInterface

        completion_interface = CompletionInterface(
            setup.state_manager,
            setup.system_logger,
            setup.content_generator,
            setup.assessment,
        )
        completion_interface.engine = engine
        clear_output(wait=True)
        display(completion_interface.show_course_completion())
        return

    display(
        setup.utils.create_styled_message(
            "Ошибка: не удалось найти первый урок в плане курса.",
            "incorrect",
        )
    )


def _resume_course(setup, course: dict) -> None:
    from course_portfolio import switch_course

    switch_course(setup.state_manager.state, course["id"])
    setup.state_manager.save_state()
    display(
        setup.utils.create_styled_message(
            f"Продолжаем курс «{course['title']}» (прогресс сохранён).",
            "info",
        )
    )
    _open_lesson_after_plan(setup, course)


def _start_course(setup, course: dict, schedule: dict) -> None:
    try:
        from course_portfolio import begin_new_course, has_course

        if has_course(setup.state_manager.state, course["id"]):
            _resume_course(setup, course)
            return

        display(
            setup.utils.create_styled_message(
                f"Создание персонализированного учебного плана для курса "
                f"'{course['title']}'...",
                "info",
            )
        )
        course_plan = setup.content_generator.generate_course_plan(
            course_data=course,
            total_study_hours=int(schedule["total_study_hours"]),
            lesson_duration_minutes=int(schedule["lesson_duration_minutes"]),
        )
        if course.get("source"):
            course_plan["source"] = course["source"]
        if course.get("domain_override"):
            course_plan["domain_override"] = True

        begin_new_course(setup.state_manager.state)
        success = setup.state_manager.save_course_plan(course_plan)
        setup.state_manager.update_learning_progress(course=course["id"])
        setup.system_logger.log_activity(
            action_type="course_started",
            details={
                "course_id": course["id"],
                "course_title": course["title"],
                "source": course.get("source", "catalog"),
                "total_study_hours": int(schedule["total_study_hours"]),
                "lesson_duration_minutes": int(schedule["lesson_duration_minutes"]),
            },
        )

        if success:
            display(
                setup.utils.create_styled_message(
                    f"Персонализированный учебный план успешно создан! "
                    f"Начинаем курс '{course['title']}'.",
                    "correct",
                )
            )
        else:
            display(
                setup.utils.create_styled_message(
                    "Предупреждение: учебный план создан, но возникли проблемы "
                    "при сохранении.",
                    "warning",
                )
            )

        _open_lesson_after_plan(setup, course)
    except Exception as e:
        logger.debug("Ошибка при генерации учебного плана: %s", e, exc_info=True)
        display(
            setup.utils.create_styled_message(
                setup.utils.format_api_error(
                    e, context="Не удалось создать учебный план"
                ),
                "incorrect",
            )
        )
