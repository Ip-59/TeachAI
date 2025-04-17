import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from IPython.display import display, clear_output, Markdown
import ipywidgets as widgets
import textwrap
from datetime import datetime


class TeachAIEngine:
    def __init__(self):
        """Инициализация движка TeachAI."""
        self.state_file = "state.json"
        self.plan_file = "personal_learning_plan.json"
        self.log_file = "lesson_history.md"
        self.debug_log_file = "debug_openai_responses.log"
        self.state = {}
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Ошибка: отсутствует ключ OpenAI API. Добавьте его в файл `.env` как `OPENAI_API_KEY`."
            )
        self.client = OpenAI(api_key=self.api_key)

        # Создаём лог-файл, если он ещё не существует
        self.initialize_log_file()

    def initialize_log_file(self):
        """Создаёт лог-файл взаимодействий, если его ещё нет."""
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", encoding="utf-8") as file:
                file.write("# Лог взаимодействий TeachAI\n")
                file.write(
                    f"Создан: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )
            print(f"Лог-файл {self.log_file} создан.")

    def log_interaction(self, entry):
        """Записывает взаимодействие в лог-файл."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as file:
            file.write(f"[{timestamp}] {entry}\n")
        print(f"Лог записан: {entry}")

    def load_state(self):
        """Загрузка состояния пользователя из файла."""
        if os.path.exists(self.state_file):
            with open(self.state_file, "r", encoding="utf-8") as file:
                self.state = json.load(file)
        else:
            self.state = {}

    def save_state(self):
        """Сохранение состояния пользователя в файл."""
        try:
            with open(self.state_file, "w", encoding="utf-8") as file:
                json.dump(self.state, file, ensure_ascii=False, indent=4)
            print(f"Состояние сохранено в {self.state_file}")
        except Exception as e:
            print(f"Ошибка при сохранении состояния: {e}")

    def save_learning_plan(self, plan_data):
        """Сохранение плана обучения в файл."""
        try:
            with open(self.plan_file, "w", encoding="utf-8") as file:
                json.dump(plan_data, file, ensure_ascii=False, indent=4)
            print(f"План обучения сохранён в {self.plan_file}")
        except Exception as e:
            print(f"Ошибка при сохранении плана обучения: {e}")

    def clean_json_response(self, response_text):
        """Удаляет Markdown-обёртку из JSON-ответа."""
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Удаляем начальную строку ```json
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Удаляем завершающую строку ```
        return response_text.strip()

    def generate_personal_plan(self):
        """Генерация персонального учебного плана на основе данных пользователя."""
        course = self.state.get("course", "Машинное обучение")
        total_hours = self.state.get("total_hours", 10)
        session_duration = self.state.get("session_duration", 2)

        # Формулировка запроса
        prompt = (
            f"Создай учебный план по курсу '{course}' на {total_hours} часов. "
            f"Разбей план на части, каждая из которых соответствует занятиям по {session_duration} часа. "
            "Ответ должен быть строго в формате JSON и содержать только JSON-объект. Никакого дополнительного текста. "
            "Формат ответа:\n\n"
            "{\n"
            '  "Учебный_план": [\n'
            "    {\n"
            '      "Тема": "Название темы",\n'
            '      "Подтемы": [\n'
            '        {"Подтема": "Название подтемы", "Текст_занятия": "Описание занятия"}\n'
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Пример:\n"
            "{\n"
            '  "Учебный_план": [\n'
            "    {\n"
            '      "Тема": "Основы машинного обучения",\n'
            '      "Подтемы": [\n'
            '        {"Подтема": "Введение в машинное обучение", "Текст_занятия": "Объяснение основных концепций"}\n'
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        try:
            # Отправка запроса к OpenAI
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Ты помощник, создающий учебные программы.",
                    },
                    {"role": "user", "content": prompt},
                ],
                model="gpt-4o",  # Используем современную модель
            )

            # Получаем текст ответа
            full_response = response.choices[0].message.content.strip()

            # Логируем полный ответ для анализа
            self.log_debug_response(full_response)

            # Очищаем JSON от Markdown-обёртки
            cleaned_response = self.clean_json_response(full_response)

            # Проверяем и загружаем JSON
            plan_data = json.loads(cleaned_response)  # Загружаем JSON без ключевых слов
            self.state["plan"] = plan_data["Учебный_план"]
            self.state["current_topic_index"] = 0
            self.state["current_subtopic_index"] = 0
            self.save_state()
            self.save_learning_plan(plan_data)  # Сохраняем план обучения

            # Логируем учебный план
            self.log_interaction(
                f"Сгенерирован учебный план: {json.dumps(plan_data, ensure_ascii=False, indent=4)}"
            )

        except json.JSONDecodeError as e:
            raise ValueError(
                f"Ошибка: неверный формат JSON. {e}\nПолученный текст: {cleaned_response}"
            )
        except Exception as e:
            print(f"Ошибка при генерации плана: {e}")
            raise

    def log_debug_response(self, response_text):
        """Сохранение исходного ответа OpenAI для анализа."""
        try:
            with open(self.debug_log_file, "a", encoding="utf-8") as file:
                file.write("=== Новый ответ OpenAI ===\n")
                file.write(response_text + "\n\n")
            print(f"Ответ OpenAI логирован в файл: {self.debug_log_file}")
        except Exception as e:
            print(f"Ошибка при логировании ответа: {e}")

    def start_interface(self):
        """Запуск интерфейса взаимодействия с пользователем."""
        self.load_state()
        if not self.state.get("initialized", False):
            self.initialize_user()
        else:
            self.lesson_interface()

    def initialize_user(self):
        """Инициализация профиля пользователя."""
        print("Добро пожаловать в TeachAI!")

        # Ввод имени, уровня подготовки и формата общения
        name_input = widgets.Text(description="Имя:")
        level_input = widgets.RadioButtons(
            options=["Начальный", "Средний", "Продвинутый"], description="Уровень:"
        )

        # Формат общения
        communication_format_input = widgets.RadioButtons(
            options=[
                "Простой дружелюбный",
                "Вежливый официальный деловой",
                "Нейтральный",
            ],
            description="Формат общения:",
        )

        # Выбор курса
        course_input = widgets.RadioButtons(
            options=["Машинное обучение (Machine Learning)"],
            description="Курс:",
        )

        # Ввод времени обучения
        total_hours_input = widgets.BoundedIntText(
            value=10, min=1, max=100, step=1, description="Всего часов:"
        )
        session_duration_input = widgets.BoundedIntText(
            value=2, min=1, max=8, step=1, description="Часов за занятие:"
        )

        start_button = widgets.Button(description="Сохранить")

        def save_user_data(_):
            self.state["name"] = name_input.value
            self.state["level"] = level_input.value
            self.state["communication_format"] = communication_format_input.value
            self.state["course"] = course_input.value
            self.state["total_hours"] = total_hours_input.value
            self.state["session_duration"] = session_duration_input.value
            self.state["initialized"] = True
            self.save_state()

            # Логируем данные пользователя
            self.log_interaction(
                f"Пользователь ввёл данные: {json.dumps(self.state, ensure_ascii=False, indent=4)}"
            )

            clear_output()
            print(self.get_greeting())
            self.generate_personal_plan()
            self.lesson_interface()

        start_button.on_click(save_user_data)
        display(
            widgets.VBox(
                [
                    name_input,
                    level_input,
                    communication_format_input,
                    course_input,
                    total_hours_input,
                    session_duration_input,
                    start_button,
                ]
            )
        )

    def get_greeting(self):
        """Формирование приветствия в зависимости от выбранного формата общения."""
        format = self.state.get("communication_format", "Нейтральный")
        if format == "Простой дружелюбный":
            return f"Привет, {self.state['name']}! Давай начнём!"
        elif format == "Вежливый официальный деловой":
            return f"Здравствуйте, {self.state['name']}! Готовы приступить к обучению?"
        else:
            return f"Добрый день, {self.state['name']}! Начнём обучение."

    def lesson_interface(self):
        """Интерфейс уроков."""
        clear_output()
        content_area = widgets.Output(
            layout={"border": "1px solid black", "padding": "10px"}
        )

        def render_next_content():
            """Отображает следующую часть учебного плана."""
            content_area.clear_output()
            topic, subtopic, lesson_text = self.get_current_lesson_details()

            if topic is None:
                with content_area:
                    print("Учебный план завершён. Поздравляем с прохождением курса!")
            else:
                # Форматирование текста темы, подтемы и текста занятия
                formatted_topic = f"**Тема:** {topic}"
                formatted_subtopic = f"**Подтема:** {subtopic}"
                formatted_lesson = f"**Текст занятия:** {lesson_text}"

                # Генерация реплики на основе текста занятия
                reply = self.generate_reply(lesson_text)

                # Логирование взаимодействий
                self.log_interaction(f"Тема: {topic}")
                self.log_interaction(f"Подтема: {subtopic}")
                self.log_interaction(f"Текст занятия: {lesson_text}")
                self.log_interaction(f"Реплика TeachAI: {reply}")

                with content_area:
                    display(Markdown(formatted_topic))
                    display(Markdown(formatted_subtopic))
                    display(Markdown(formatted_lesson))
                    display(Markdown(reply))  # Реплика с учётом Markdown-разметки

        def handle_continue(_):
            """Обрабатывает нажатие кнопки 'Продолжить'."""
            self.log_interaction("Студент нажал кнопку: 'Продолжить'")
            if not self.next_lesson_step():
                with content_area:
                    print("Все темы завершены!")
            else:
                render_next_content()

        # Кнопка "Продолжить"
        continue_button = widgets.Button(description="Продолжить")
        continue_button.on_click(handle_continue)

        # Первоначальная отрисовка
        render_next_content()
        display(widgets.VBox([content_area, continue_button]))

    def get_current_lesson_details(self):
        """Возвращает текущие тему, подтему и текст занятия."""
        try:
            plan = self.state.get("plan", [])
            current_topic_index = self.state.get("current_topic_index", 0)
            current_subtopic_index = self.state.get("current_subtopic_index", 0)

            if not plan or current_topic_index >= len(plan):
                return None, None, None  # План завершён

            topic = plan[current_topic_index]
            subtopics = topic["Подтемы"]

            if current_subtopic_index >= len(subtopics):
                return None, None, None  # Все подтемы завершены

            subtopic = subtopics[current_subtopic_index]
            return topic["Тема"], subtopic["Подтема"], subtopic["Текст_занятия"]

        except Exception as e:
            print(f"Ошибка получения текущего урока: {e}")
            return None, None, None

    def next_lesson_step(self):
        """Переход к следующему этапу учебного плана."""
        try:
            current_topic_index = self.state.get("current_topic_index", 0)
            current_subtopic_index = self.state.get("current_subtopic_index", 0)
            plan = self.state.get("plan", [])

            if not plan or current_topic_index >= len(plan):
                return False  # Все темы завершены

            topic = plan[current_topic_index]
            subtopics = topic["Подтемы"]

            if current_subtopic_index + 1 < len(subtopics):
                self.state["current_subtopic_index"] += 1
            elif current_topic_index + 1 < len(plan):
                self.state["current_topic_index"] += 1
                self.state["current_subtopic_index"] = 0
            else:
                return False  # Все темы и подтемы завершены

            self.save_state()
            return True

        except Exception as e:
            print(f"Ошибка перехода к следующему шагу: {e}")
            return False

    def generate_reply(self, lesson_text):
        """Генерация реплики TeachAI на основе текста занятия."""
        try:
            prompt = (
                f"Объясни понятия, содержащиеся в следующем тексте занятия:\n\n"
                f"{lesson_text}\n\n"
                "Верни ясное и понятное объяснение с использованием Markdown для форматирования."
            )
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Ты помощник, объясняющий учебный материал.",
                    },
                    {"role": "user", "content": prompt},
                ],
                model="gpt-4o",  # Используем современную модель
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Ошибка генерации реплики: {e}")
            return "Не удалось сгенерировать ответ."
