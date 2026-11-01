"""Мелкие правки HTML-ответов ученику (напоминания и т.п.)."""
from __future__ import annotations


def append_question_reminder(answer_html: str, questions_count: int) -> str:
    """
    Добавляет напоминание к ответу, если вопросов больше 3.
    Args:
        answer_html (str): HTML-ответ
        questions_count (int): Количество заданных вопросов
    Returns:
        str: HTML-ответ с напоминанием (если нужно)
    """
    if questions_count > 3:
        reminder = (
            "<div style='margin-top: 16px; color: #0c5460; background: #e2f0fb; border-left: 4px solid #007bff; "
            "padding: 12px; border-radius: 8px; font-size: 15px;'>"
            "Мы несколько увлеклись вопросами, давайте продолжим обучение по плану курса."
            "</div>"
        )
        return answer_html + reminder
    return answer_html
