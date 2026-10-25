"""
Модуль для генерации основного содержания уроков.
Отвечает за создание структурированных образовательных материалов для каждого урока.
ИСПРАВЛЕНО: Убраны неуместные прощания в конце урока
"""

from content_utils import BaseContentGenerator, ContentUtils
from content_formatter_final import ContentFormatterFinal


class LessonGenerator(BaseContentGenerator):
    """Генератор основного содержания уроков."""

    def __init__(self, api_key):
        """
        Инициализация генератора уроков.

        Args:
            api_key (str): API ключ OpenAI
        """
        super().__init__(api_key)
        self.content_formatter = ContentFormatterFinal()
        self.logger.info("LessonGenerator инициализирован")

    def generate_lesson(
        self, course, section, topic, lesson, user_name, communication_style="friendly"
    ):
        """
        Генерирует содержание урока.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson (str): Название урока
            user_name (str): Имя пользователя
            communication_style (str): Стиль общения

        Returns:
            dict: Словарь с заголовком и содержанием урока

        Raises:
            Exception: Если не удалось сгенерировать урок
        """
        try:
            lesson_title = str(lesson) if lesson is not None else "Урок"

            self.logger.info(f"Генерация содержания урока '{lesson_title}'")

            prompt = self._build_lesson_prompt(
                course, section, topic, lesson_title, user_name, communication_style
            )

            messages = [
                {
                    "role": "system",
                    "content": (
                        "Ты опытный преподаватель. Пиши подробный урок на русском "
                        "строго по названию этого занятия. "
                        "В Markdown: заголовки, списки, код только в блоках ```lang. "
                        "Не оборачивай весь ответ в один fence. Без прощаний в конце. "
                        "Примеры только те, которым учит этот урок. "
                        "Не добавляй соседние темы курса."
                    ),
                },
                {"role": "user", "content": prompt},
            ]

            self.logger.info("Отправка запроса к OpenAI API...")

            lesson_content = self.make_api_request(
                messages=messages, temperature=0.7, max_tokens=3500  # Безопасный лимит
            )

            self.logger.info("Получен ответ от OpenAI API")
            


            # Сохраняем отладочную информацию
            self.save_debug_response(
                "lesson",
                prompt,
                lesson_content,
                {
                    "course": course,
                    "section": section,
                    "topic": topic,
                    "lesson": lesson_title,
                    "user_name": user_name,
                    "communication_style": communication_style,
                },
            )

            # ИСПРАВЛЕНО: Используем единый ContentFormatter для форматирования
            formatted_content = self.content_formatter.format_lesson_content(
                lesson_content, lesson_title
            )

            # Сохраняем и сырой текст от LLM (до CSS/HTML-обёртки) — он нужен
            # для проверки релевантности, ключевых понятий и QA, чтобы CSS
            # форматтера не попадал в промпт вместо материала урока.
            result = {
                "title": lesson_title,
                "content": formatted_content,
                "raw_content": lesson_content,
            }

            self.logger.info(f"Урок '{lesson_title}' успешно сгенерирован")
            return result

        except Exception as e:
            self.logger.error(f"Критическая ошибка при генерации урока: {str(e)}")
            raise Exception(f"Не удалось сгенерировать урок '{lesson}': {str(e)}")

    def _build_lesson_prompt(
        self, course, section, topic, lesson_title, user_name, communication_style
    ):
        style_description = ContentUtils.COMMUNICATION_STYLES.get(
            communication_style, ContentUtils.COMMUNICATION_STYLES["friendly"]
        )

        return f"""
Создай образовательный урок строго по этому занятию:

Курс: {course}
Раздел: {section}
Тема: {topic}
Урок: {lesson_title}

Пользователь: {user_name}
Стиль общения: {style_description}

О чём писать:
- Только этот урок: его название, раздел и тема. Название курса не повод добавлять другие занятия курса.
- Объясняй понятия и шаги, которые нужны именно здесь.
- Примеры и код — только если без них этот урок не объяснить. Не переноси сюда приёмы из других уроков.
- Если урок не учит писать код, не вставляй учебные программы. Напиши это прямо.
- Если код нужен, он на том языке, которому посвящён урок. Каждая инструкция с новой строки, отступ как принято в этом языке.

Урок должен быть подробным:
1. Краткое введение
2. Основные концепции и определения
3. Объяснения с примерами по этому уроку
4. Пошаговые инструкции (если уместно)
5. Применение на практике
6. Частые ошибки
7. Краткое резюме без прощаний

Формат — Markdown, не HTML:
- Заголовки # / ##, списки, **жирный**.
- Код только внутри ``` с указанием языка. Не оборачивай весь урок в один fence.
- Внутри блока — только код. Пояснения — снаружи блока.
- Не используй print() в обычном тексте урока.
"""


