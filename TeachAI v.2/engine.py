import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from IPython.display import display, clear_output, Markdown
import ipywidgets as widgets
from datetime import datetime


class TeachAIEngine:
    def __init__(self):
        self.state_file = "state.json"
        self.log_file = "lesson_history.md"
        self.debug_log_file = "debug_openai_responses.log"
        self.state = {}
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY отсутствует в .env")
        self.client = OpenAI(api_key=self.api_key)
        self.initialize_log_file()

    def initialize_log_file(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", encoding="utf-8") as file:
                file.write("# Лог взаимодействий TeachAI\n")
                file.write(
                    f"Создан: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

    def log_interaction(self, entry):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as file:
            file.write(f"[{timestamp}] {entry}\n")

    def log_debug_response(self, response_text):
        with open(self.debug_log_file, "a", encoding="utf-8") as file:
            file.write("=== Новый ответ OpenAI ===\n")
            file.write(response_text + "\n\n")

    def save_state(self):
        with open(self.state_file, "w", encoding="utf-8") as file:
            json.dump(self.state, file, ensure_ascii=False, indent=4)

    def load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r", encoding="utf-8") as file:
                self.state = json.load(file)
        else:
            self.state = {}

    def clean_json_response(self, response_text):
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        return response_text.strip()

    def generate_prompted_reply(self, base_text, mode="explain"):
        instructions = {
            "explain": "Объясни подробнее следующий материал:",
            "example": "Приведи пример к следующему материалу:",
            "summary": "Сделай краткое резюме следующего материала в сжатой форме:",
        }
        prompt = f"{instructions[mode]}\n\n{base_text}\n\nИспользуй Markdown."
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Ты помощник, объясняющий учебный материал.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        reply = response.choices[0].message.content.strip()
        self.log_debug_response(reply)
        return reply

    def get_current_lesson_details(self):
        plan = self.state.get("plan", [])
        i, j = self.state.get("current_topic_index", 0), self.state.get(
            "current_subtopic_index", 0
        )
        if i >= len(plan):
            return None, None, None
        topic = plan[i]
        if j >= len(topic["Подтемы"]):
            return None, None, None
        subtopic = topic["Подтемы"][j]
        return topic["Тема"], subtopic["Подтема"], subtopic["Текст_занятия"]

    def next_lesson_step(self):
        i, j = self.state.get("current_topic_index", 0), self.state.get(
            "current_subtopic_index", 0
        )
        plan = self.state.get("plan", [])
        if i >= len(plan):
            return False
        subtopics = plan[i]["Подтемы"]
        if j + 1 < len(subtopics):
            self.state["current_subtopic_index"] += 1
        elif i + 1 < len(plan):
            self.state["current_topic_index"] += 1
            self.state["current_subtopic_index"] = 0
        else:
            return False
        self.save_state()
        return True

    def lesson_interface(self):
        clear_output()
        content_area = widgets.Output(
            layout={"border": "1px solid black", "padding": "10px"}
        )
        spinner = widgets.Label(value="")

        def render_content(reply_text=None):
            content_area.clear_output()
            spinner.value = ""
            topic, subtopic, lesson = self.get_current_lesson_details()
            if topic is None:
                with content_area:
                    print("Учебный план завершён.")
            else:
                if reply_text is None:
                    spinner.value = "⏳ Формируется ответ..."
                    reply_text = self.generate_prompted_reply(lesson, "explain")
                self.log_interaction(
                    f"Тема: {topic}\nПодтема: {subtopic}\nТекст: {lesson}\nРеплика: {reply_text}"
                )
                with content_area:
                    display(Markdown(f"**Тема:** {topic}"))
                    display(Markdown(f"**Подтема:** {subtopic}"))
                    display(Markdown(f"**Текст занятия:** {lesson}"))
                    display(Markdown(reply_text.replace("```", "")))
                spinner.value = ""

        def handle_continue(_):
            self.log_interaction("Кнопка: Продолжить")
            if not self.next_lesson_step():
                with content_area:
                    print("Все темы завершены!")
            else:
                render_content()

        def handle_explain(_):
            spinner.value = "⏳ Поясняем подробнее..."
            self.log_interaction("Кнопка: Объяснить подробнее")
            _, _, lesson = self.get_current_lesson_details()
            render_content(self.generate_prompted_reply(lesson, "explain"))

        def handle_example(_):
            spinner.value = "⏳ Ищем пример..."
            self.log_interaction("Кнопка: Привести пример")
            _, _, lesson = self.get_current_lesson_details()
            render_content(self.generate_prompted_reply(lesson, "example"))

        def handle_finish(_):
            spinner.value = "⏳ Формируем итог..."
            self.log_interaction("Кнопка: Закончить урок")
            _, _, lesson = self.get_current_lesson_details()
            summary = self.generate_prompted_reply(lesson, "summary")
            self.log_interaction(f"Краткое резюме: {summary}")
            with content_area:
                display(Markdown("**Краткое резюме:**"))
                display(Markdown(summary.replace("```", "")))
                display(Markdown("**Урок завершён. До новых встреч!**"))
            self.save_state()
            spinner.value = ""

        btn_continue = widgets.Button(
            description="Продолжить",
            style={"button_color": "#cce6ff"},
            layout=widgets.Layout(font_weight="bold", border="1px solid black"),
        )
        btn_explain = widgets.Button(
            description="Объяснить подробнее",
            style={"button_color": "#cce6ff"},
            layout=widgets.Layout(font_weight="bold", border="1px solid black"),
        )
        btn_example = widgets.Button(
            description="Привести пример",
            style={"button_color": "#cce6ff"},
            layout=widgets.Layout(font_weight="bold", border="1px solid black"),
        )
        btn_finish = widgets.Button(
            description="Закончить урок",
            style={"button_color": "#cce6ff"},
            layout=widgets.Layout(font_weight="bold", border="1px solid black"),
        )

        btn_continue.on_click(handle_continue)
        btn_explain.on_click(handle_explain)
        btn_example.on_click(handle_example)
        btn_finish.on_click(handle_finish)

        buttons = widgets.HBox([btn_continue, btn_explain, btn_example, btn_finish])
        render_content()
        display(widgets.VBox([content_area, buttons, spinner]))

    def initialize_user(self):
        clear_output()
        name = widgets.Text(description="Имя:")
        level = widgets.Dropdown(
            options=["Начальный", "Средний", "Продвинутый"], description="Уровень"
        )
        format_ = widgets.Dropdown(
            options=["Простой дружелюбный", "Нейтральный", "Официальный"],
            description="Формат",
        )
        hours = widgets.BoundedIntText(value=10, min=1, max=100, description="Часов")
        per_session = widgets.BoundedIntText(
            value=2, min=1, max=8, description="За занятие"
        )
        button = widgets.Button(description="Начать обучение")

        def on_start(_):
            self.state = {
                "name": name.value,
                "level": level.value,
                "communication_format": format_.value,
                "total_hours": hours.value,
                "session_duration": per_session.value,
                "initialized": True,
            }
            self.save_state()
            self.generate_personal_plan()
            self.lesson_interface()

        display(widgets.VBox([name, level, format_, hours, per_session, button]))
        button.on_click(on_start)

    def generate_personal_plan(self):
        course = self.state.get("course", "Машинное обучение")
        total_hours = self.state.get("total_hours", 10)
        session_duration = self.state.get("session_duration", 2)
        prompt = (
            f"Создай учебный план по курсу '{course}' на {total_hours} часов. Разбей на занятия по {session_duration} часа.\n"
            "Ответ в формате JSON, строго без лишнего текста:\n"
            '{"Учебный_план": [{"Тема": "...", "Подтемы": [{"Подтема": "...", "Текст_занятия": "..."}]}]}'
        )
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты помощник, создающий учебные планы."},
                {"role": "user", "content": prompt},
            ],
        )
        raw = response.choices[0].message.content.strip()
        self.log_debug_response(raw)
        cleaned = self.clean_json_response(raw)
        parsed = json.loads(cleaned)
        self.state["plan"] = parsed["Учебный_план"]
        self.state["current_topic_index"] = 0
        self.state["current_subtopic_index"] = 0
        self.save_state()

    def start_interface(self):
        self.load_state()
        if not self.state.get("initialized") or "plan" not in self.state:
            self.initialize_user()
        else:
            self.lesson_interface()
