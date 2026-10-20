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
                        "в Markdown: заголовки, списки, код только в блоках ```lang. "
                        "Не оборачивай весь ответ в один fence. Без прощаний в конце. "
                        "Язык примеров кода — язык темы курса, не Python по умолчанию."
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

        topic_l = f"{topic} {lesson_title} {course}".lower()
        pythonish = any(
            word in topic_l
            for word in (
                "python",
                "pandas",
                "numpy",
                "django",
                "flask",
                "список",
                "словарь",
                "list",
                "dict",
            )
        )
        if pythonish:
            topic_specific = (
                "\n- Если в теме есть списки/словари — покажи append, insert, "
                "remove и операции с ключами.\n"
                "- Примеры кода на Python в блоках ```python, каждая инструкция "
                "на своей строке, отступ 4 пробела."
            )
            code_lang = "python"
        else:
            topic_specific = (
                "\n- Примеры кода — только если они нужны теме, на языке этой темы. "
                "Не подставляй Python, если курс не про программирование на Python. "
                "Если кода нет — в начале явно напиши: "
                "'В этом уроке нет кода для практики.'"
            )
            code_lang = "язык темы (не python, если тема не Python)"

        return f"""
Создай образовательный урок по теме:

Курс: {course}
Раздел: {section}
Тема: {topic}
Урок: {lesson_title}

Пользователь: {user_name}
Стиль общения: {style_description}
{topic_specific}

Урок должен быть подробным:
1. Краткое введение
2. Основные концепции и определения
3. Объяснения с примерами
4. Пошаговые инструкции (если уместно)
5. Применение на практике
6. Частые ошибки
7. Краткое резюме без прощаний

Формат — Markdown, не HTML:
- Заголовки # / ##, списки, **жирный**.
- Код только внутри ```{code_lang} ... ```. Не оборачивай весь урок в один fence.
- Не пиши код в одну строку. Внутри блока — только рабочий код, без комментариев-пояснений снаружи синтаксиса.
- Не используй print() в обычном тексте урока.
"""


