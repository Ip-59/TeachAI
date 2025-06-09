"""
Модуль для генерации ответов на вопросы пользователей.
Отвечает за создание персонализированных ответов на основе материалов урока и контекста.
ИСПРАВЛЕНО: Красивое форматирование ответов на вопросы
"""

from content_utils import BaseContentGenerator, ContentUtils


class QAGenerator(BaseContentGenerator):
    """Генератор ответов на вопросы пользователей."""

    def __init__(self, api_key):
        """
        Инициализация генератора вопросов и ответов.

        Args:
            api_key (str): API ключ OpenAI
        """
        super().__init__(api_key)
        self.logger.info("QAGenerator инициализирован")

    def answer_question(
        self,
        course,
        section,
        topic,
        lesson,
        user_question,
        lesson_content,
        user_name,
        communication_style="friendly",
    ):
        """
        Генерирует ответ на вопрос пользователя по уроку.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson (str): Название урока
            user_question (str): Вопрос пользователя
            lesson_content (str): Содержание урока
            user_name (str): Имя пользователя
            communication_style (str): Стиль общения

        Returns:
            str: Ответ на вопрос

        Raises:
            Exception: Если не удалось сгенерировать ответ
        """
        try:
            lesson_title = str(lesson) if lesson is not None else "Урок"
            user_name_str = str(user_name) if user_name is not None else "Пользователь"

            prompt = self._build_qa_prompt(
                course,
                section,
                topic,
                lesson_title,
                user_question,
                lesson_content,
                user_name_str,
                communication_style,
            )

            messages = [
                {
                    "role": "system",
                    "content": "Ты - опытный преподаватель, который отвечает на вопросы студентов по учебным материалам. Отвечай профессионально, четко и по существу, БЕЗ приветствий в начале ответа.",
                },
                {"role": "user", "content": prompt},
            ]

            answer = self.make_api_request(
                messages=messages, temperature=0.7, max_tokens=2000
            )

            # Сохраняем отладочную информацию
            self.save_debug_response(
                "question_answer",
                prompt,
                answer,
                {
                    "course": course,
                    "section": section,
                    "topic": topic,
                    "lesson": lesson_title,
                    "user_question": user_question,
                    "user_name": user_name_str,
                    "communication_style": communication_style,
                },
            )

            # ИСПРАВЛЕНО: Применяем красивое форматирование ответов
            styled_answer = self._apply_answer_styles(answer, communication_style)

            self.logger.info("Ответ на вопрос успешно сгенерирован")
            return styled_answer

        except Exception as e:
            self.logger.error(
                f"Критическая ошибка при генерации ответа на вопрос: {str(e)}"
            )
            raise Exception(f"Не удалось сгенерировать ответ на вопрос: {str(e)}")

    def _apply_answer_styles(self, answer, communication_style):
        """
        ИСПРАВЛЕНО: Применяет красивые CSS стили к ответу.

        Args:
            answer (str): Исходный ответ
            communication_style (str): Стиль общения

        Returns:
            str: Стилизованный ответ
        """
        # Очищаем ответ от возможных приветствий
        cleaned_answer = self._remove_greetings(answer)

        # Получаем префикс в зависимости от стиля общения
        utils = ContentUtils()
        prefix = utils.get_style_prefix(communication_style, "qa")

        # ИСПРАВЛЕНО: Красивые CSS стили для ответов на вопросы
        answer_css = """
        <style>
        .qa-answer {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 16px;
            line-height: 1.4;
            padding: 20px;
            background: linear-gradient(135deg, #e7f3ff 0%, #cce7ff 100%);
            border-radius: 10px;
            margin: 15px 0;
            border-left: 4px solid #007bff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .qa-answer h1, .qa-answer h2, .qa-answer h3, .qa-answer h4 {
            color: #495057;
            margin-top: 15px;
            margin-bottom: 8px;
            line-height: 1.2;
            border-bottom: 2px solid #007bff;
            padding-bottom: 4px;
        }
        .qa-answer h1 { font-size: 20px; }
        .qa-answer h2 { font-size: 18px; }
        .qa-answer h3 { font-size: 17px; }
        .qa-answer h4 { font-size: 16px; }
        .qa-answer p {
            margin-bottom: 8px;
            line-height: 1.3;
            text-align: justify;
        }
        .qa-answer ul, .qa-answer ol {
            margin-bottom: 10px;
            padding-left: 25px;
            line-height: 1.3;
        }
        .qa-answer li {
            margin-bottom: 4px;
        }
        .qa-answer code {
            background-color: #f8f9fa;
            color: #d63384;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            font-weight: 600;
            border: 1px solid #dee2e6;
        }
        .qa-answer pre {
            background-color: #f8f9fa;
            color: #212529;
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.05;
            border: 2px solid #dee2e6;
        }
        .qa-answer pre code {
            background: none;
            color: inherit;
            padding: 0;
            font-size: inherit;
            border: none;
        }
        .qa-answer .answer-block {
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 12px;
            margin: 10px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .qa-answer strong {
            color: #495057;
            font-weight: 600;
        }
        .qa-answer em {
            color: #6c757d;
            font-style: italic;
        }
        </style>
        <div class="qa-answer">
        """

        return f"{answer_css}{prefix}{cleaned_answer}</div>"

    def _build_qa_prompt(
        self,
        course,
        section,
        topic,
        lesson_title,
        user_question,
        lesson_content,
        user_name_str,
        communication_style,
    ):
        """
        Создает промпт для генерации ответа на вопрос.

        Args:
            course (str): Название курса
            section (str): Название раздела
            topic (str): Название темы
            lesson_title (str): Название урока
            user_question (str): Вопрос пользователя
            lesson_content (str): Содержание урока
            user_name_str (str): Имя пользователя
            communication_style (str): Стиль общения

        Returns:
            str: Промпт для API
        """
        style_description = ContentUtils.COMMUNICATION_STYLES.get(
            communication_style, ContentUtils.COMMUNICATION_STYLES["friendly"]
        )

        return f"""
        Ответь на вопрос пользователя {user_name_str} по следующему уроку:

        Курс: {course}
        Раздел: {section}
        Тема: {topic}
        Урок: {lesson_title}

        Содержание урока:
        {lesson_content[:2000]}  # Ограничиваем длину для запроса

        Вопрос пользователя:
        {user_question}

        Используй следующий стиль общения: {style_description}

        ВАЖНЫЕ ТРЕБОВАНИЯ:
        1. НЕ начинай ответ с приветствий типа "Привет, {user_name_str}!" или подобных
        2. Сразу переходи к сути ответа
        3. Давай подробный и информативный ответ, основываясь на материале урока
        4. Если информации в материале урока недостаточно, используй свои знания по теме, но укажи это явно
        5. Используй четкую структуру ответа с заголовками и примерами
        6. Форматируй код в отдельных блоках с подсветкой синтаксиса
        7. Добавляй практические советы и рекомендации

        Ответ должен быть профессиональным, структурированным и легко читаемым.
        Используй HTML-форматирование для улучшения читаемости.
        """

    def _remove_greetings(self, answer):
        """
        Убирает приветствия из начала ответа.

        Args:
            answer (str): Исходный ответ

        Returns:
            str: Ответ без приветствий
        """
        import re

        # Паттерны для удаления приветствий
        greeting_patterns = [
            r"^Привет[^!]*!\s*",
            r"^Здравствуй[^!]*!\s*",
            r"^Добро пожаловать[^!]*!\s*",
            r"^Рад[^!]*!\s*",
            r"^[А-Я][а-я]+[^.!]*[!.]\s*",  # Общий паттерн для предложений-приветствий
        ]

        cleaned_answer = answer
        for pattern in greeting_patterns:
            cleaned_answer = re.sub(
                pattern, "", cleaned_answer, flags=re.IGNORECASE | re.MULTILINE
            )

        return cleaned_answer.strip()
