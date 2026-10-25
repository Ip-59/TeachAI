"""Генерация схем-картинок для презентации TeachAI.

Рисует точные блок-схемы (matplotlib), чтобы отдать их Gamma готовыми PNG,
а не надеяться на авто-рисование. Запуск:

    ./venv_H_L/bin/python doc/build_shemy.py

Результат: doc/shemy/shema_6_arhitektura.png и др.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

plt.rcParams["font.family"] = "DejaVu Sans"

OUT = Path(__file__).resolve().parent / "shemy"
OUT.mkdir(exist_ok=True)

NAVY = "#1A365D"
BLUE = "#2B6CB0"
LIGHT = "#EAF1FA"
LIGHT2 = "#F3F7FC"
TEXT = "#1A202C"
MUTED = "#4A5568"
GREEN = "#2F855A"
AMBER = "#B7791F"
WHITE = "#FFFFFF"


def new_ax(w=16.0, h=9.0):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    ax.set_aspect("equal")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig, ax


def box(ax, cx, cy, w, h, text, fill=LIGHT, edge=BLUE, tcolor=TEXT,
        fontsize=15, bold=False, lw=2.0):
    patch = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=lw, edgecolor=edge, facecolor=fill, zorder=2,
    )
    ax.add_patch(patch)
    ax.text(cx, cy, text, ha="center", va="center", color=tcolor,
            fontsize=fontsize, fontweight="bold" if bold else "normal",
            zorder=3, wrap=True)
    return (cx, cy, w, h)


def arrow(ax, p1, p2, color=NAVY, lw=2.0, style="-|>", both=False):
    connection = "arc3,rad=0"
    astyle = "<|-|>" if both else style
    a = FancyArrowPatch(
        p1, p2, arrowstyle=astyle, mutation_scale=18,
        color=color, lw=lw, connectionstyle=connection, zorder=1,
    )
    ax.add_patch(a)


def edge_point(b, side):
    cx, cy, w, h = b
    return {
        "top": (cx, cy + h / 2),
        "bottom": (cx, cy - h / 2),
        "left": (cx - w / 2, cy),
        "right": (cx + w / 2, cy),
    }[side]


def save(fig, name):
    path = OUT / name
    fig.savefig(path, dpi=150, facecolor=WHITE, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("saved", path)


# ---------- Схема 6: архитектура «звезда» ----------
def shema_arhitektura():
    fig, ax = new_ax(16, 10)
    ax.text(8, 9.5, "Архитектура TeachAI: движок координирует подсистемы",
            ha="center", va="center", fontsize=18, fontweight="bold", color=NAVY)

    engine = box(ax, 8, 5.5, 3.4, 1.3, "Движок\n(TeachAIEngine)",
                 fill=NAVY, edge=NAVY, tcolor=WHITE, fontsize=17, bold=True)

    ui = box(ax, 2.9, 7.5, 3.0, 1.1, "Интерфейс\nвиджеты Jupyter", fontsize=14)
    cfg = box(ax, 2.9, 3.6, 3.0, 1.1, "Конфигурация\nключ, модель, сеть (.env)", fontsize=13)
    state = box(ax, 13.1, 7.5, 3.0, 1.1, "Состояние\nпрофиль · план · прогресс", fontsize=13)
    assess = box(ax, 13.1, 3.6, 3.0, 1.1, "Оценивание\nтесты и проверка", fontsize=14)
    gen = box(ax, 8, 3.0, 3.2, 1.0, "Генерация\nфасад запросов к LLM", fontsize=14)

    # внешние ресурсы
    api = box(ax, 8, 1.55, 2.6, 0.8, "LLM API", fill=LIGHT2, edge=GREEN,
              tcolor=GREEN, fontsize=14, bold=True)
    js = box(ax, 13.1, 8.9, 2.6, 0.75, "data/state.json", fill=LIGHT2,
             edge=MUTED, tcolor=MUTED, fontsize=13)

    # связи движок <-> подсистемы
    arrow(ax, edge_point(engine, "left"), edge_point(ui, "right"), both=True)
    arrow(ax, edge_point(engine, "left"), edge_point(cfg, "right"), both=True)
    arrow(ax, edge_point(engine, "right"), edge_point(state, "left"), both=True)
    arrow(ax, edge_point(engine, "right"), edge_point(assess, "left"), both=True)
    arrow(ax, edge_point(engine, "bottom"), edge_point(gen, "top"), both=True)
    # внешние направления
    arrow(ax, edge_point(gen, "bottom"), edge_point(api, "top"), color=GREEN)
    arrow(ax, edge_point(state, "top"), edge_point(js, "bottom"), color=MUTED)

    ax.text(8, 8.5, "Интерфейс → Движок → Генерация → LLM;  Состояние ↔ JSON",
            ha="center", va="center", fontsize=12.5, color=MUTED, style="italic")
    ax.text(8, 0.5, "Четыре слоя:  Ядро  ·  LLM  ·  UI  ·  Сервис",
            ha="center", va="center", fontsize=13, color=NAVY, fontweight="bold")
    save(fig, "shema_6_arhitektura.png")


# ---------- Схема 7: генерация контента ----------
def shema_generaciya():
    fig, ax = new_ax()
    ax.text(8, 8.6, "Генерация контента: фасад делегирует отдельным генераторам",
            ha="center", va="center", fontsize=18, fontweight="bold", color=NAVY)

    facade = box(ax, 2.7, 4.3, 3.0, 1.6, "ContentGenerator\n(единый фасад)",
                 fill=NAVY, edge=NAVY, tcolor=WHITE, fontsize=15, bold=True)

    items = [
        "План курса (JSON)",
        "Урок",
        "Примеры (код)",
        "Тест",
        "Вопрос → релевантность",
        "Понятия / объяснение",
        "Контрольное задание",
    ]
    ys = [7.6, 6.5, 5.4, 4.3, 3.2, 2.1, 1.0]
    mid_boxes = []
    for y, label in zip(ys, items):
        b = box(ax, 8.0, y, 3.8, 0.78, label, fontsize=13)
        mid_boxes.append(b)
        arrow(ax, edge_point(facade, "right"), edge_point(b, "left"), color=BLUE, lw=1.6)

    api = box(ax, 13.6, 4.3, 2.2, 7.3, "LLM\nAPI", fill=LIGHT2, edge=GREEN,
              tcolor=GREEN, fontsize=18, bold=True)
    for b in mid_boxes:
        arrow(ax, edge_point(b, "right"), (edge_point(api, "left")[0], b[1]),
              color=GREEN, lw=1.4)

    ax.text(8, 0.1, "У каждого генератора — свой промпт и параметры (temperature, формат ответа)",
            ha="center", va="bottom", fontsize=12.5, color=MUTED, style="italic")
    save(fig, "shema_7_generaciya.png")


# ---------- Схема 9: сценарий работы ----------
def shema_scenariy():
    fig, ax = new_ax(16, 7)
    ax.text(8, 6.4, "Сценарий работы: путь глазами ученика",
            ha="center", va="center", fontsize=18, fontweight="bold", color=NAVY)

    steps = [
        ("1. Профиль", "имя, часы,\nстиль"),
        ("2. План курса", "LLM → JSON"),
        ("3. Урок", "кэш или\nгенерация"),
        ("4. Действия", "примеры · вопрос\nтест · практика"),
        ("5. Прогресс", "сохранён\nв JSON"),
    ]
    xs = [1.9, 4.9, 7.9, 10.9, 13.9]
    boxes = []
    for x, (title, sub) in zip(xs, steps):
        b = box(ax, x, 3.5, 2.5, 1.8, f"{title}\n\n{sub}",
                fill=LIGHT, edge=BLUE, fontsize=13.5, bold=False)
        boxes.append(b)
    for i in range(len(boxes) - 1):
        arrow(ax, edge_point(boxes[i], "right"), edge_point(boxes[i + 1], "left"),
              color=NAVY, lw=2.2)

    ax.text(8, 1.2, "Повторный вход → дашборд с прогрессом (тяжёлая загрузка по кнопке)",
            ha="center", va="center", fontsize=13, color=MUTED, style="italic")
    save(fig, "shema_9_scenariy.png")


# ---------- Схема 11: методика бенчмарка ----------
def shema_metodika():
    fig, ax = new_ax()
    ax.text(8, 8.6, "Сравнение моделей: методика эксперимента (13.09.2026)",
            ha="center", va="center", fontsize=18, fontweight="bold", color=NAVY)

    prompt = box(ax, 2.2, 4.5, 2.8, 1.4, "Единый\nпромпт урока\n(5 тем)",
                 fill=NAVY, edge=NAVY, tcolor=WHITE, fontsize=14, bold=True)

    models = ["gpt-4o-mini", "gpt-5.6-luna", "gpt-5.6-terra",
              "claude-5-sonnet", "gemini-3.5-flash"]
    mys = [7.4, 6.2, 5.0, 3.8, 2.6]
    mboxes = []
    for y, m in zip(mys, models):
        b = box(ax, 6.0, y, 3.1, 0.82, m, fontsize=12.5)
        mboxes.append(b)
        arrow(ax, edge_point(prompt, "right"), edge_point(b, "left"), color=BLUE, lw=1.4)

    gate = box(ax, 9.6, 5.0, 2.4, 2.1,
               "Format gate\nобъём · заголовки\nблок Python\n25 / 25",
               fill=LIGHT2, edge=AMBER, tcolor=AMBER, fontsize=12.5, bold=True)
    gate_in = edge_point(gate, "left")  # единая точка схода стрелок от моделей
    for b in mboxes:
        arrow(ax, edge_point(b, "right"), gate_in, color=AMBER, lw=1.3)

    judges = ["gpt-5.6-sol", "claude-opus-5", "gemini-3.1-pro"]
    jys = [6.1, 5.0, 3.9]
    jboxes = []
    for y, j in zip(jys, judges):
        b = box(ax, 12.9, y, 2.6, 0.78, j, fontsize=12)
        jboxes.append(b)
        arrow(ax, edge_point(gate, "right"), edge_point(b, "left"), color=BLUE, lw=1.3)

    rating = box(ax, 12.9, 1.7, 3.0, 1.5, "Рейтинг\nбалл 0–10 · ₽ · latency · балл/₽",
                 fill=LIGHT, edge=GREEN, tcolor=GREEN, fontsize=12.5, bold=True)
    rating_in = edge_point(rating, "top")  # единая точка схода стрелок от судей
    for b in jboxes:
        arrow(ax, edge_point(b, "bottom"), rating_in, color=GREEN, lw=1.2)

    ax.text(8, 0.6, "3 судьи разных семейств · слепые метки A–E · рубрика 0–10 "
            "(тема, полнота, плотность, педагогика, соответствие)",
            ha="center", va="center", fontsize=11.5, color=MUTED, style="italic")
    ax.text(8, 0.1, "Оговорка: судьям текст обрезан до ~3500 символов; цена и скорость — по полному ответу",
            ha="center", va="center", fontsize=11, color=MUTED, style="italic")
    save(fig, "shema_11_metodika.png")


def shema_put():
    """Полный путь ученика для заочной версии."""
    fig, ax = new_ax(16, 8.2)
    ax.text(8, 7.7, "Путь ученика: от профиля до завершённого урока",
            ha="center", va="center", fontsize=18, fontweight="bold", color=NAVY)

    steps = [
        ("1. Профиль", "имя, часы,\nстиль"),
        ("2. Курс", "выбор\nиз каталога"),
        ("3. План", "LLM → JSON,\nпроверка структуры"),
        ("4. Урок", "кэш или\nновая генерация"),
        ("5. Действия", "примеры, вопрос,\nтест, практика"),
    ]
    xs = [1.7, 4.7, 7.7, 10.7, 13.7]
    boxes = []
    for x, (title, sub) in zip(xs, steps):
        b = box(ax, x, 5.5, 2.6, 1.7, f"{title}\n\n{sub}", fontsize=13)
        boxes.append(b)
    for i in range(len(boxes) - 1):
        arrow(ax, edge_point(boxes[i], "right"), edge_point(boxes[i + 1], "left"),
              color=NAVY, lw=2.0)

    done = box(
        ax, 8, 2.7, 10.5, 1.5,
        "Урок завершён, когда выполнены оба условия:\n"
        "тест больше 40%  и  контрольное задание принято\n"
        "→ прогресс пишется в JSON  →  при следующем входе дашборд",
        fill=LIGHT2, edge=GREEN, tcolor=GREEN, fontsize=14, bold=True,
    )
    arrow(ax, edge_point(boxes[-1], "bottom"), edge_point(done, "top"), color=GREEN, lw=2.0)
    save(fig, "shema_put_uchenika.png")


def shema_vopros():
    """Два запроса: проверка темы, затем ответ."""
    fig, ax = new_ax(16, 9)
    ax.text(8, 8.55, "Вопрос ученика: два разных запроса к модели",
            ha="center", va="center", fontsize=18, fontweight="bold", color=NAVY)

    student = box(ax, 2.3, 6.5, 2.8, 1.15, "Ученик\nвводит вопрос", fontsize=14)
    screen = box(ax, 6.0, 6.5, 3.0, 1.15, "Экран урока\nполе вопроса", fontsize=14)
    check = box(
        ax, 10.6, 6.5, 3.6, 1.35,
        "Проверка темы урока\nсначала правила по тексту,\nпри необходимости — LLM (JSON)",
        fontsize=13,
    )
    arrow(ax, edge_point(student, "right"), edge_point(screen, "left"), color=NAVY, lw=2.0)
    arrow(ax, edge_point(screen, "right"), edge_point(check, "left"), color=NAVY, lw=2.0)

    counter = box(
        ax, 6.0, 4.55, 3.2, 1.05,
        "Счётчик вопросов\nзаписывается в state.json",
        fill=LIGHT2, edge=MUTED, tcolor=MUTED, fontsize=13,
    )
    arrow(ax, edge_point(screen, "bottom"), edge_point(counter, "top"), color=MUTED, lw=1.6)

    stop = box(
        ax, 7.9, 2.35, 4.0, 1.5,
        "Не по теме\nжёлтое предупреждение\nответ по существу не запрашивается",
        fill=LIGHT2, edge=AMBER, tcolor=AMBER, fontsize=13, bold=True,
    )
    go = box(
        ax, 12.9, 2.35, 4.0, 1.5,
        "По теме — второй запрос\nгенератор ответа: урок, стиль, вопрос\nответ показывается в том же виджете",
        fill=LIGHT2, edge=GREEN, tcolor=GREEN, fontsize=13, bold=True,
    )
    arrow(ax, edge_point(check, "bottom"), edge_point(stop, "top"), color=AMBER, lw=1.8)
    arrow(ax, edge_point(check, "bottom"), edge_point(go, "top"), color=GREEN, lw=1.8)

    ax.text(
        8, 0.45,
        "Напоминание «больше трёх вопросов» на этом экране не показывается, хотя счётчик пишется.",
        ha="center", va="center", fontsize=12, color=MUTED, style="italic",
    )
    save(fig, "shema_vopros.png")


if __name__ == "__main__":
    shema_arhitektura()
    shema_generaciya()
    shema_scenariy()
    shema_metodika()
    shema_put()
    shema_vopros()
    print("done")
