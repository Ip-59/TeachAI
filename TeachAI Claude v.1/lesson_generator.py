"""
Модуль для генерации основного содержания уроков.
Отвечает за создание структурированных образовательных материалов для каждого урока.
ИСПРАВЛЕНО: Убраны неуместные прощания в конце урока
"""

from content_utils import BaseContentGenerator, ContentUtils


class LessonGenerator(BaseContentGenerator):
    """Генератор основного содержания уроков."""

    def __init__(self, api_key):
        """
        Инициализация генератора уроков.

        Args:
            api_key (str): API ключ OpenAI
        """
        super().__init__(api_key)
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
                    "content": "Ты - опытный преподаватель и эксперт в разных областях знаний. Создавай подробные, информативные и практически полезные уроки БЕЗ финальных прощаний и пожеланий удачи.",
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

            # Формируем полный контент урока с CSS
            full_content = f"{ContentUtils.BASE_CSS_STYLES}{lesson_content}</div>"

            # Создаем результат
            result = {"title": lesson_title, "content": full_content}

            self.logger.info(f"Урок '{lesson_title}' успешно сгенерирован")
            return result

        except Exception as e:
            self.logger.error(f"Критическая ошибка при генерации урока: {str(e)}")
            raise Exception(f"Не удалось сгенерировать урок '{lesson}': {str(e)}")

    def _build_lesson_prompt(
        self, course, section, topic, lesson_title, user_name, communication_style
    ):
        """
        Создает промпт для генерации урока.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson_title (str): Название урока
            user_name (str): Имя пользователя
            communication_style (str): Стиль общения

        Returns:
            str: Промпт для API
        """
        style_description = ContentUtils.COMMUNICATION_STYLES.get(
            communication_style, ContentUtils.COMMUNICATION_STYLES["friendly"]
        )

        return f"""
        Создай образовательный урок по теме:

        Курс: {course}
        Раздел: {section}
        Тема: {topic}
        Урок: {lesson_title}

        Пользователь: {user_name}

        Используй следующий стиль общения: {style_description}

        Урок должен быть ПОДРОБНЫМ и НАСЫЩЕННЫМ, содержать:
        1. Краткое введение в тему с объяснением важности
        2. Основные концепции и определения с четкими объяснениями
        3. Подробные объяснения с МНОЖЕСТВОМ практических примеров
        4. Пошаговые инструкции или алгоритмы (если применимо)
        5. Практические применения в реальной жизни
        6. Частые ошибки и как их избежать
        7. Заключение с КРАТКОЙ сводкой ключевых моментов

        ВАЖНЫЕ ТРЕБОВАНИЯ:
        - Урок должен быть достаточно подробным, чтобы студент мог изучить тему глубоко
        - Включи конкретные примеры кода, формулы или методы (в зависимости от темы)
        - Объясни не только "что", но и "как" и "почему"
        - Добавь практические советы и рекомендации
        - Материал должен быть самодостаточным для понимания темы
        - НЕ ЗАВЕРШАЙ урок прощанием, пожеланиями удачи или фразами типа "до новых встреч"
        - Заключение должно быть КРАТКИМ резюме ключевых точек, без личных пожеланий

        Используй HTML для форматирования ответа. Обязательно используй стандартные размеры шрифта:
        - заголовки h1, h2, h3
        - основной текст - 18px
        - списки с правильными отступами
        - выделяй важные термины жирным шрифтом
        - используй курсив для примеров и пояснений

        Обеспечь хорошую структуру и читаемость текста.
        """
