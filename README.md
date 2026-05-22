# TeachAI - Интеллектуальная система обучения

Система на основе OpenAI API для создания персонализированных учебных курсов с интерактивными уроками, примерами и тестами.

## 🎯 Основные возможности

- **Генерация персонализированных курсов** - автоматическое создание учебного плана на основе выбранной темы
- **Интерактивные уроки** - контент, адаптированный к стилю общения пользователя
- **Практические примеры** - автоматически генерируемые примеры кода и задания
- **Контрольные задания** - тесты для проверки усвоения материала
- **Отслеживание прогресса** - сохранение статуса обучения и оценок
- **Поддержка Jupyter Notebook** - интерактивный интерфейс в окружении Jupyter

## 🚀 Быстрый старт

### Требования

- Python 3.10+
- Jupyter Notebook или JupyterLab
- API ключ OpenAI

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/TeachAI.git
cd TeachAI
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv_home
source venv_home/Scripts/activate  # Windows
# или
source venv_home/bin/activate      # Linux/Mac
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env`:
```bash
cp .env.sample .env
```

5. Добавьте ваш OpenAI API ключ в файл `.env`:
```
OPENAI_API_KEY=your_api_key_here
```

### Запуск

Откройте Jupyter Notebook и выполните:

```python
from engine import TeachAIEngine

# Создаем и запускаем систему
engine = TeachAIEngine()
interface_element = engine.start()

if interface_element:
    display(interface_element)
```

Или используйте предготовленный ноутбук [TeachAI.ipynb](TeachAI.ipynb)

## 📋 Архитектура проекта

### Основные компоненты

- **[engine.py](engine.py)** - главный класс системы, координирует все компоненты
- **[config.py](config.py)** - управление конфигурацией и переменными окружения
- **[state_manager.py](state_manager.py)** - сохранение и загрузка состояния системы
- **[content_generator.py](content_generator.py)** - фасад для генерации контента через OpenAI
- **[interface.py](interface.py)** - создание интерактивного UI с ipywidgets
- **[assessment.py](assessment.py)** - модуль проверки знаний и оценивания
- **[startup_dashboard.py](startup_dashboard.py)** - дашборд статистики обучения

### Специализированные генераторы

- **[course_plan_generator.py](course_plan_generator.py)** - генерация плана курса
- **[lesson_generator.py](lesson_generator.py)** - создание содержания уроков
- **[examples_generator.py](examples_generator.py)** - генерация примеров кода
- **[assessment_generator.py](assessment_generator.py)** - создание тестовых вопросов
- **[qa_generator.py](qa_generator.py)** - генерация вопросов и ответов
- **[concepts_generator.py](concepts_generator.py)** - выделение ключевых концепций
- **[control_tasks_generator.py](control_tasks_generator.py)** - создание контрольных заданий

### Менеджеры состояния

- **[user_profile_manager.py](user_profile_manager.py)** - управление профилем пользователя
- **[learning_progress_manager.py](learning_progress_manager.py)** - отслеживание прогресса обучения
- **[course_data_manager.py](course_data_manager.py)** - управление данными курса

### UI интерфейсы

- **[setup_interface.py](setup_interface.py)** - интерфейс первоначальной настройки
- **[lesson_interface.py](lesson_interface.py)** - отображение урока
- **[assessment_interface.py](assessment_interface.py)** - интерфейс теста
- **[completion_interface.py](completion_interface.py)** - экран завершения

## 🔧 Конфигурация

### Переменные окружения

```env
OPENAI_API_KEY=sk-...       # API ключ OpenAI (обязательный)
LLM_MODEL=gpt-4o-mini       # Модель по умолчанию (gpt-4o — для сложных задач)
OPENAI_PROXY=http://...     # Прокси (обязательный)
```

### Стили общения

Система поддерживает несколько стилей общения:

- **friendly** (по умолчанию) - дружелюбный, с простыми объяснениями
- **formal** - формальный, академический стиль
- **casual** - непринужденный, разговорный
- **brief** - краткий, только ключевая информация

## 📁 Структура файлов

```
TeachAI/
├── engine.py                   # Главный класс системы
├── config.py                   # Конфигурация
├── state_manager.py            # Управление состоянием
├── logger.py                   # Логирование
│
├── Генераторы контента:
│   ├── content_generator.py    # Фасад для генерации контента
│   ├── course_plan_generator.py
│   ├── lesson_generator.py
│   ├── examples_generator.py
│   ├── assessment_generator.py
│   └── ...
│
├── Интерфейсы:
│   ├── interface.py            # Главный интерфейс
│   ├── setup_interface.py
│   ├── lesson_interface.py
│   ├── assessment_interface.py
│   └── ...
│
├── Менеджеры:
│   ├── user_profile_manager.py
│   ├── learning_progress_manager.py
│   └── course_data_manager.py
│
├── Важные документы:
│   ├── ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md   # Полное описание проекта
│   ├── ОТВЕТ_КУРАТОРУ.md              # О подходе к разработке
│   └── README.md                      # Этот файл
│
├── data/                       # Данные приложения (git ignored)
├── logs/                       # Логи системы (git ignored)
├── doc/                        # Отчеты разработки (git ignored)
├── docs/                       # Техническая документация (git ignored)
│
├── requirements.txt            # Зависимости Python
├── TeachAI.ipynb              # Основной notebook для запуска
└── .gitignore                 # Исключения из git
```

## 💻 Зависимости

Основные библиотеки:

- `openai` - OpenAI Python API
- `ipywidgets` - интерактивные виджеты для Jupyter
- `python-dotenv` - управление переменными окружения
- `jupyter` - Jupyter Notebook/Lab

Полный список см. в [requirements.txt](requirements.txt)

## 📚 Документация

### Основная документация

- **[ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md](ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md)** - подробное описание проекта, архитектуры и реализации (1000+ строк)
- **[ОТВЕТ_КУРАТОРУ.md](ОТВЕТ_КУРАТОРУ.md)** - объяснение подхода к разработке и использования GPT без дообучения

### Дополнительные материалы

Папка `doc/` (не включена в репозиторий) содержит:
- Отчеты о разработке
- Логи сессий
- История исправлений

## 🔒 Безопасность

- **Никогда** не коммитьте файл `.env` с API ключом
- API ключи автоматически скрыты в логах (показывается только начало)
- Используйте `.gitignore` для исключения чувствительных файлов

## 📝 Лицензия

[Добавьте информацию о лицензии]

## 👤 Автор

[Ваше имя/организация]

## 🤝 Внесение вклада

Приветствуются pull requests. Для крупных изменений сначала откройте issue для обсуждения.

## 📞 Поддержка

Для сообщения об ошибках и предложений используйте [Issues](https://github.com/your-username/TeachAI/issues)

---

**Статус проекта:** Активная разработка

**Последнее обновление:** 25 января 2026 г.
