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
            from learning_prompt_context import FULL_LESSON_MAX_CHARS

            lesson_title = str(lesson) if lesson is not None else "Урок"
            user_name_str = str(user_name) if user_name is not None else "Пользователь"
            full_lesson = self.prepare_lesson_text_for_analysis(
                lesson_content,
                max_chars=FULL_LESSON_MAX_CHARS,
                lesson_title=lesson_title,
            )

            prompt = self._build_qa_prompt(
                course,
                section,
                topic,
                lesson_title,
                user_question,
                full_lesson,
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

            styled_answer = self._apply_answer_styles(answer, communication_style)

            self.logger.info("Ответ на вопрос успешно сгенерирован")
            return styled_answer

        except Exception as e:
            self.logger.error(
                f"Критическая ошибка при генерации ответа на вопрос: {str(e)}"
            )
            raise Exception(f"Не удалось сгенерировать ответ на вопрос: {str(e)}")

    def _apply_answer_styles(self, answer, communication_style):
        """Прогоняет ответ через канон рендера (``.qa-answer``)."""
        from student_content import render_student_content

        cleaned_answer = self._remove_greetings(answer)
        utils = ContentUtils()
        prefix = utils.get_style_prefix(communication_style, "qa")
        return render_student_content(
            cleaned_answer,
            wrapper="qa-answer",
            lead_html=prefix,
        )

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

        from learning_prompt_context import (
            lesson_context_block,
            practice_runtime_rules_ru,
        )

        return f"""
        Ответь на вопрос пользователя {user_name_str} по следующему уроку:

        Курс: {course}
        Раздел: {section}
        Тема: {topic}
        Урок: {lesson_title}

        {practice_runtime_rules_ru()}
        {lesson_context_block(lesson_content)}

        Вопрос пользователя:
        {user_question}

        Используй следующий стиль общения: {style_description}

        ВАЖНЫЕ ТРЕБОВАНИЯ:
        1. НЕ начинай ответ с приветствий типа "Привет, {user_name_str}!" или подобных
        2. Сразу переходи к сути ответа
        3. Ответ должен быть содержательным по материалу урока выше, не формальным
        4. Если в уроке не хватает факта — скажи об этом явно; не выдумывай шаги для терминала ОС
        5. Примеры кода — только то, что можно выполнить в Python Jupyter TeachAI
        6. Форматируй код в отдельных блоках с подсветкой синтаксиса
        7. Добавляй практические советы, согласованные с уроком и средой TeachAI

        Формат: Markdown (заголовки, списки). Код только в блоках ```.
        Не оборачивай весь ответ в один fence. Не используй HTML.
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
