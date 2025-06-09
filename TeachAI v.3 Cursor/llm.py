import os
import json
from openai import OpenAI


class LLMGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.log_path = "log_openai.jsonl"

    def _log(self, role, content):
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(
                json.dumps({"role": role, "content": content}, ensure_ascii=False)
                + "\n"
            )

    def generate_course(self, config):
        prompt = f"""
Создай учебный план по теме "Искусственный интеллект и машинное обучение" для уровня: {config['level']}.
Курс рассчитан на {config['total_hours']} часов, с занятиями по {config['session_minutes']} минут.
Верни структуру в JSON: список тем с полями title и content (анонс).
        """
        self._log("prompt", prompt)
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()
        self._log("response", content)
        try:
            return json.loads(content)
        except Exception as e:
            raise ValueError(f"Ошибка парсинга плана курса: {e}")

    def generate_lesson_text(self, topic_title, config):
        prompt = f"""
Сформируй подробный текст урока на тему: "{topic_title}" для уровня: {config['level']}.
Объём должен соответствовать времени {config['session_minutes']} минут. Напиши на русском языке, стиль: {config['style']}.
        """
        self._log("prompt", prompt)
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()
        self._log("response", content)
        return content

    def generate_quiz_for_lesson(self, topic_title, lesson_text):
        prompt = f"""
Составь 3 вопроса викторины с 3 вариантами ответов каждый по теме: "{topic_title}".
Используй следующий текст урока как источник: {lesson_text}
Ответ верни в JSON-формате:
[
  {{"question": "...", "options": ["A", "B", "C"], "answer": "A"}},
  ...
]
        """
        self._log("prompt", prompt)
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()
        self._log("response", content)
        try:
            return json.loads(content)
        except Exception as e:
            raise ValueError(f"Ошибка парсинга викторины: {e}")
