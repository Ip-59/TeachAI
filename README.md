# TeachAI

Интерактивная система обучения программированию на Python в среде **Jupyter Notebook** с генерацией учебного контента через **OpenAI API**. Пользователь проходит персонализированный курс: план строится LLM, уроки и проверки знаний создаются по запросу, прогресс сохраняется локально.

> **Полное описание проекта** (цели, архитектура, pipeline AI-учителя, модули): [ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md](ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md)  
> **English version**: [DESCRIPTION.md](DESCRIPTION.md)

---

## Назначение

TeachAI реализует роль **AI-учителя**: ведёт обучение по выбранному курсу из каталога, генерирует текст уроков, отвечает на вопросы в рамках темы, предлагает примеры и углублённые объяснения, проводит тесты и практические контрольные задания с автоматической проверкой кода.

Система **не** дообучает собственную модель и **не** использует внешнюю БД: состояние и кэш уроков хранятся в `data/state.json`, логи — в `logs/`.

---

## Быстрый старт

### Требования

- Python 3 (зависимости — в `requirements.txt`)
- Jupyter / IPython kernel
- Файл `.env` с ключом OpenAI и **обязательным** прокси (см. `config.py`)

### Установка

```bash
pip install -r requirements.txt
cp .env.sample .env   # если образец создан ConfigManager
# Заполните OPENAI_API_KEY и OPENAI_PROXY (или HTTPS_PROXY)
```

### Запуск

**Рекомендуемый способ** — notebook `TeachAI.ipynb`:

```python
from run_teachai import start_jupyter
start_jupyter()
```

**Альтернатива** — CLI:

```bash
python run_teachai.py
```

Точка входа: `run_teachai.py` → `TeachAIEngine` (`engine.py`).

---

## Каталог курсов

Пять предметных направлений заданы в `courses.json`:

| ID | Название |
|----|----------|
| `python-basics` | Основы Python |
| `data-analysis` | Анализ данных с Python |
| `machine-learning` | Введение в машинное обучение |
| `web-development` | Веб-разработка на Python (Flask) |
| `python-for-finance` | Python для финансов |

Для курсов в `requirements.txt` указаны библиотеки (pandas, scikit-learn, TensorFlow, Flask, yfinance и др.) — они нужны для **выполнения** сгенерированных примеров и контрольных заданий, а не для работы ядра системы.

---

## Архитектура (кратко)

```
TeachAI.ipynb / run_teachai.py
        │
        ▼
  TeachAIEngine (engine.py)
        │
        ├── ConfigManager (.env, директории logs/, data/)
        ├── StateManager (data/state.json)
        ├── ContentGenerator → специализированные генераторы (OpenAI)
        ├── Assessment (тесты)
        ├── Logger (logs/*.json, lesson_history.md)
        ├── StartupDashboard (повторный запуск)
        └── UserInterface (фасад)
                ├── SetupInterface
                ├── LessonInterface → Display / Navigation / Interaction
                ├── AssessmentInterface
                └── CompletionInterface
```

Подробные диаграммы и сценарии — в [ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md](ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md).

---

## Завершение урока (факты из кода)

Урок считается **завершённым**, если (`learning_progress_manager.py`):

1. Оценка теста **> 40%**, **и**
2. Контрольное задание выполнено верно (`control_tasks` в state),

**или** урок отмечен принудительно (`lesson_completion_status`).

---

## Структура репозитория

| Путь | Назначение |
|------|------------|
| `engine.py` | Инициализация и запуск системы |
| `interface.py`, `*_interface.py` | UI на `ipywidgets` |
| `content_generator.py`, `*_generator.py` | Запросы к OpenAI |
| `content_utils.py` | Базовый клиент API, стили, подготовка текста урока |
| `content_formatter_final.py`, `content_renderer.py` | HTML/Markdown/LaTeX |
| `state_manager.py`, `*_manager.py` | Состояние и прогресс |
| `control_tasks_*.py`, `result_checker.py` | Практические задания |
| `interactive_cell_*.py` | Виджет редактора кода |
| `courses.json` | Статический каталог курсов |
| `data/state.json` | Состояние пользователя (создаётся при работе) |
| `logs/` | Журналы активности |
| `debug_responses/` | Отладочные ответы LLM (при генерации) |
| `archive/` | Устаревшие notebook и презентации (не входят в runtime) |

---

## Конфигурация

| Переменная | Назначение |
|------------|------------|
| `OPENAI_API_KEY` | Ключ API (обязательно) |
| `OPENAI_PROXY` / `HTTPS_PROXY` / `HTTP_PROXY` | Прокси (обязательно, `config.py`) |
| `LLM_MODEL` | Модель чата (по умолчанию `gpt-4o-mini`, `content_utils.py`) |
| `VALIDATION_MODEL` | Модель для валидации контрольных заданий (`control_tasks_generator.py`) |

---

## Различие файлов документации

| Файл | Аудитория | Содержание |
|------|-----------|------------|
| **README.md** (этот файл) | Разработчик, преподаватель | Краткий обзор, установка, структура |
| **ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md** | Комиссия, рецензент | Полный отчёт на русском по коду |
| **DESCRIPTION.md** | Международная аудитория | Тот же отчёт на английском |

---

## Лицензия и авторство

Уточняйте у владельца репозитория — в анализируемых `.py` файлах отдельная лицензия не зафиксирована.
