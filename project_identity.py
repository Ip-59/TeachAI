"""Идентичность TeachAI: Python и AI/ML в Jupyter, не «учитель чего угодно»."""

from __future__ import annotations

PROJECT_NAME = "TeachAI"

PROJECT_TAGLINE = (
    "интеллектуальная система персонализированного обучения Python и AI/ML "
    "на основе языковой модели"
)

PROJECT_FULL_TITLE = f"{PROJECT_NAME} — {PROJECT_TAGLINE}"

# Винительный для устной речи: «представляю … систему»
PROJECT_FULL_TITLE_ACCUSATIVE = (
    f"{PROJECT_NAME} — интеллектуальную систему персонализированного обучения "
    "Python и AI/ML на основе языковой модели"
)

PRACTICE_LIMITATIONS: tuple[str, ...] = (
    "исполняемые примеры кода в Jupyter (запуск через Python ``exec``)",
    "контрольные задания с проверкой кода",
    "интерактивные учебные ячейки",
    "синтаксическая проверка кода (AST Python)",
    "запуск программ на C, C++, Java и других языках — в системе нет их рантайма",
    "методическое качество уроков и тестов вне Python, анализа данных и ML",
)


def limitations_html_list() -> str:
    """Маркированный список ограничений практики."""
    items = []
    for item in PRACTICE_LIMITATIONS:
        text = item.replace("``exec``", "<code>exec</code>")
        items.append(f"<li>{text}</li>")
    return (
        "<ul style='margin:8px 0 0 20px;line-height:1.5;'>"
        + "".join(items)
        + "</ul>"
    )


def scope_banner_html() -> str:
    """HTML баннера предметной области для первого экрана."""
    return (
        "<div style='background:linear-gradient(135deg,#1a365d 0%,#2c5282 100%);"
        "color:#fff;padding:18px 20px;border-radius:10px;margin:0 0 16px 0;'>"
        f"<h2 style='margin:0 0 8px 0;font-size:22px;color:#fff;'>{PROJECT_NAME}</h2>"
        f"<p style='margin:0 0 10px 0;font-size:16px;line-height:1.45;'>{PROJECT_TAGLINE}.</p>"
        "<p style='margin:0;font-size:14px;line-height:1.5;opacity:0.95;'>"
        "Предметная область — <strong>Python, анализ данных и машинное обучение</strong> "
        "в Jupyter. Система не преподаёт произвольные школьные и бытовые темы "
        "и не запускает код на других языках программирования. "
        "Своё название курса можно ввести, если это тема внутри этой рамки "
        "(например «pandas для аналитика»)."
        "</p></div>"
    )
