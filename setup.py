# setup.py
import ipywidgets as widgets


class SetupWizard:
    def __init__(self, interface, on_complete):
        self.interface = interface
        self.on_complete = on_complete
        self.config = {}

    def start(self):
        self.ask_name()

    def ask_name(self):
        self.interface.prompt_input("Введите ваше имя:", self.ask_level)

    def ask_level(self, name):
        self.config["name"] = name
        self.interface.prompt_select(
            "Выберите уровень знаний:",
            ["Новичок", "Средний", "Продвинутый"],
            self.ask_total_time,
        )

    def ask_total_time(self, level):
        self.config["level"] = level
        self.interface.prompt_input(
            "Введите общее время на обучение (в часах):", self.ask_session_time
        )

    def ask_session_time(self, total):
        self.config["total_hours"] = total
        self.interface.prompt_input(
            "Введите длительность одного занятия (в минутах):", self.ask_style
        )

    def ask_style(self, session):
        self.config["session_minutes"] = session
        self.interface.prompt_select(
            "Выберите формат общения:",
            ["Формальный", "Дружеский", "Непринуждённый", "Краткий"],
            self.finish,
        )

    def finish(self, style):
        self.config["style"] = style
        self.on_complete(self.config)
