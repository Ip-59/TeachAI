"""Стили общения для промптов и короткие HTML-префиксы ответа."""
from __future__ import annotations

COMMUNICATION_STYLES = {
    "formal": "Формальный, академический стиль общения с использованием научной терминологии.",
    "friendly": "Дружелюбный стиль общения, использующий простые объяснения и аналогии.",
    "casual": "Непринужденный, разговорный стиль с элементами юмора.",
    "brief": "Краткий и четкий стиль, фокусирующийся только на ключевой информации.",
}


def get_style_prefix(communication_style, content_type="general"):
    """
    Возвращает префикс для контента в зависимости от стиля общения.

    Args:
        communication_style (str): Стиль общения
        content_type (str): Тип контента (examples, explanation, qa, general)

    Returns:
        str: HTML префикс
    """
    if content_type == "examples":
        if communication_style == "formal":
            return "<p style='font-size: 16px; line-height: 1.4;'>Представляем вашему вниманию примеры для данного учебного материала.</p>"
        elif communication_style == "casual":
            return "<p style='font-size: 16px; line-height: 1.4;'>Привет! Вот несколько примеров, которые помогут разобраться с темой! 👍</p>"
        elif communication_style == "brief":
            return "<p style='font-size: 16px; line-height: 1.4;'>Примеры:</p>"
        else:  # friendly по умолчанию
            return "<p style='font-size: 16px; line-height: 1.4;'>Вот несколько полезных примеров, которые помогут вам лучше понять материал урока:</p>"

    elif content_type == "explanation":
        if communication_style == "formal":
            return "<p style='font-size: 16px; line-height: 1.4;'>Уважаемый пользователь! Ниже представлено академическое объяснение материала.</p>"
        elif communication_style == "casual":
            return "<p style='font-size: 16px; line-height: 1.4;'>Привет! Вот более подробное и неформальное объяснение этой темы. 😊</p>"
        elif communication_style == "brief":
            return "<p style='font-size: 16px; line-height: 1.4;'>Краткое дополнительное объяснение:</p>"
        else:  # friendly по умолчанию
            return "<p style='font-size: 16px; line-height: 1.4;'>Добро пожаловать в подробное объяснение! Надеюсь, что этот материал поможет вам лучше понять тему.</p>"

    elif content_type == "qa":
        if communication_style == "formal":
            return "<p style='font-size: 16px; line-height: 1.4;'>Академический ответ на ваш вопрос:</p>"
        elif communication_style == "casual":
            return "<p style='font-size: 16px; line-height: 1.4;'>Отличный вопрос! Вот мой ответ: 😊</p>"
        elif communication_style == "brief":
            return (
                "<p style='font-size: 16px; line-height: 1.4;'>Краткий ответ:</p>"
            )
        else:  # friendly по умолчанию
            return "<p style='font-size: 16px; line-height: 1.4;'>Спасибо за вопрос! Вот подробный ответ:</p>"

    return ""


class ContentUtils:
    """Совместимость: генераторы делают ContentUtils() / ContentUtils.COMMUNICATION_STYLES."""

    COMMUNICATION_STYLES = COMMUNICATION_STYLES

    def get_style_prefix(self, communication_style, content_type="general"):
        return get_style_prefix(communication_style, content_type)
