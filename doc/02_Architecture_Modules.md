# TeachAI — Архитектура: Модули, Классы, Методы и Взаимосвязи

## Оглавление
1. [Точка входа](#1-точка-входа)
2. [Ядро системы](#2-ядро-системы)
3. [Конфигурация](#3-конфигурация)
4. [Управление состоянием](#4-управление-состоянием)
5. [LLM-интеграция](#5-llm-интеграция)
6. [Генерация контента](#6-генерация-контента)
7. [Интерфейс пользователя](#7-интерфейс-пользователя)
8. [Оценка знаний](#8-оценка-знаний)
9. [Утилиты и вспомогательные модули](#9-утилиты)
10. [Граф вызовов](#10-граф-вызовов)

---

## 1. Точка входа

### `TeachAI.ipynb`
Jupyter-ноутбук, единственная точка входа для пользователя.

```python
from engine import TeachAIEngine
engine = TeachAIEngine()
engine.start()
```

**Логика:** Создаёт экземпляр `TeachAIEngine`, который инициализирует все подсистемы, затем вызывает `start()` для запуска UI.

---

## 2. Ядро системы

### `engine.py` → класс `TeachAIEngine`

Центральный оркестратор. Создаёт и связывает все компоненты.

| Метод | Назначение | Вызывает |
|-------|-----------|----------|
| `__init__()` | Инициализация всех компонентов | `ConfigManager`, `StateManager`, `SystemLogger`, `LLMProvider`, `ContentGenerator`, `Assessment`, `UserInterface`, `StartupDashboard` |
| `start()` | Запуск приложения | `_show_startup_or_setup()` |
| `_show_startup_or_setup()` | Решает: показать дашборд или форму настройки | `StartupDashboard.show_dashboard()` или `SetupInterface.show_initial_setup()` |
| `_init_components()` | Создание зависимостей между компонентами | Передаёт ссылки между модулями |

**Цепочка вызовов при запуске:**
```
TeachAIEngine.__init__()
  → ConfigManager().load_config()
  → StateManager(config)
  → SystemLogger(config)
  → LLMProvider(config)
  → ContentGenerator(api_key)
  → Assessment(content_generator, logger)
  → UserInterface(state_manager, content_generator, logger, assessment)
  → StartupDashboard(state_manager, engine)

TeachAIEngine.start()
  → проверка: есть ли user_profile и course_plan?
    ДА  → StartupDashboard.show_dashboard()
    НЕТ → SetupInterface.show_initial_setup()
```

---

## 3. Конфигурация

### `config.py` → класс `ConfigManager`

| Метод | Назначение |
|-------|-----------|
| `load_config()` | Загружает `.env`, создаёт директории (`data/`, `logs/`, `debug_responses/`) |
| `get_api_key()` | Возвращает `OPENAI_API_KEY` из окружения |
| `get_llm_config()` | Возвращает словарь с provider, model, proxy |
| `ensure_directories()` | Создаёт необходимые папки |

---

## 4. Управление состоянием

### `state_manager.py` → класс `StateManager` (Facade)

Фасад, делегирующий работу трём специализированным менеджерам. Единственный компонент, который читает/пишет `data/state.json`.

| Делегат | Модуль | Ответственность |
|---------|--------|----------------|
| `UserProfileManager` | `user_profile_manager.py` | Профиль пользователя (имя, стиль, часы) |
| `LearningProgressManager` | `learning_progress_manager.py` | Прогресс обучения, оценки, завершённость |
| `CourseDataManager` | `course_data_manager.py` | Учебный план, навигация по урокам |

#### 4.1 `user_profile_manager.py` → `UserProfileManager`

| Метод | Назначение |
|-------|-----------|
| `get_user_profile()` | Возвращает словарь профиля |
| `save_user_profile(name, style, hours)` | Сохраняет настройки пользователя |
| `is_profile_configured()` | Проверяет наличие профиля |
| `validate_profile(data)` | Валидация полей профиля |

#### 4.2 `learning_progress_manager.py` → `LearningProgressManager`

| Метод | Назначение |
|-------|-----------|
| `save_lesson_assessment(lesson_id, score, passed)` | Сохраняет результат теста |
| `is_test_passed(lesson_id)` | Проверяет, пройден ли тест (>40%) |
| `is_control_task_completed(lesson_id)` | Проверяет выполнение контрольного задания |
| `is_lesson_completed(lesson_id)` | Тест пройден + задание выполнено |
| `mark_lesson_complete_manually(lesson_id)` | Принудительное завершение урока |
| `calculate_course_progress()` | Считает % прогресса курса |
| `get_detailed_course_statistics()` | Расширенная статистика |
| `recalculate_statistics()` | Пересчёт средних баллов |
| `save_control_task_result(lesson_id, title, correct)` | Сохраняет результат контрольного задания |

#### 4.3 `course_data_manager.py` → `CourseDataManager`

| Метод | Назначение |
|-------|-----------|
| `get_course_plan()` | Возвращает текущий учебный план |
| `save_course_plan(plan)` | Сохраняет сгенерированный план |
| `get_lesson_data(section, topic, lesson)` | Данные конкретного урока |
| `get_next_lesson()` | Находит следующий незавершённый урок |
| `get_all_courses()` | Загружает каталог из `courses.json` |
| `get_cached_lesson_content(key)` | Кэшированный контент урока |
| `save_lesson_content(key, title, content)` | Сохраняет кэш урока |

---

## 5. LLM-интеграция

### `llm.py` → класс `LLMProvider`

Обёртка для OpenAI API с поддержкой нескольких провайдеров.

| Метод | Назначение |
|-------|-----------|
| `__init__(config)` | Настраивает клиент OpenAI с прокси |
| `chat_completion(messages, **kwargs)` | Выполняет запрос к LLM |
| `_setup_proxy()` | Настраивает HTTP-прокси через `httpx` |

**Поддерживаемые провайдеры:** OpenAI, Azure, OpenRouter, Local.

### `content_utils.py` → класс `BaseContentGenerator`

Базовый класс для **всех** генераторов контента.

| Метод | Назначение |
|-------|-----------|
| `__init__(api_key)` | Создаёт `OpenAI` клиент с прокси |
| `make_api_request(messages, temp, tokens)` | Единый запрос к API |
| `make_api_request_with_retries(...)` | Запрос с retry (3 попытки, экспоненциальная задержка) |
| `save_debug_response(type, prompt, response)` | Сохранение ответа API в `debug_responses/` |
| `clean_markdown_code_blocks(text)` | Очистка markdown-меток из ответа |

---

## 6. Генерация контента

### `content_generator.py` → класс `ContentGenerator` (Facade)

Фасад, проксирующий вызовы к специализированным генераторам.

| Метод фасада | Делегирует в | Модуль |
|-------------|-------------|--------|
| `generate_course_plan()` | `CoursePlanGenerator.generate()` | `course_plan_generator.py` |
| `generate_lesson()` | `LessonGenerator.generate()` | `lesson_generator.py` |
| `generate_assessment()` | `AssessmentGenerator.generate()` | `assessment_generator.py` |
| `generate_examples()` | `ExamplesGenerator.generate()` | `examples_generator.py` |
| `generate_explanation()` | `ExplanationGenerator.generate()` | `explanation_generator.py` |
| `generate_qa_answer()` | `QAGenerator.generate()` | `qa_generator.py` |

#### Специализированные генераторы (все наследуют `BaseContentGenerator`):

**`course_plan_generator.py` → `CoursePlanGenerator`**
- `generate(course_id, course_title, ...)` → JSON-план: sections → topics → lessons
- Ответ в формате `json_object`, парсинг и валидация обязательных полей

**`lesson_generator.py` → `LessonGenerator`**
- `generate(course, section, topic, lesson, user_name, style)` → `{title, content}`
- Промпт требует HTML-форматирование, примеры кода Python, без прощаний

**`assessment_generator.py` → `AssessmentGenerator`**
- `generate_questions(course, section, topic, lesson, content, num=5)` → список вопросов с вариантами ответов и правильным ответом

**`examples_generator.py` → `ExamplesGenerator`**
- Генерирует дополнительные примеры кода по теме урока
- Использует `examples_generation.py`, `examples_utils.py`, `examples_validation.py`

**`explanation_generator.py` → `ExplanationGenerator`**
- Генерирует расширенные объяснения материала

**`qa_generator.py` → `QAGenerator`**
- Отвечает на вопросы пользователя в контексте урока
- Проверяет релевантность вопроса через `RelevanceChecker`

**`control_tasks_generator.py` → `ControlTasksGenerator`**
- `generate_control_task(lesson_data, content, style)` → задание с эталонным решением
- `validate_task_execution(user_code, expected_output)` → выполняет `exec()` кода пользователя, сравнивает вывод
- Автоматическая проверка соответствия `solution_code` ↔ `expected_output`

---

## 7. Интерфейс пользователя

### `interface.py` / `interface_facade.py` → класс `UserInterface` (Facade)

Фасад для всех UI-компонентов. Координирует переключение между экранами.

#### 7.1 `setup_interface.py` → `SetupInterface`

| Метод | Назначение |
|-------|-----------|
| `show_initial_setup()` | Форма: имя, стиль общения, часы обучения |
| `show_course_selection()` | Выбор курса из каталога |
| `_on_start_course()` | Запускает генерацию плана курса и переход к первому уроку |

#### 7.2 `lesson_interface.py` → `LessonInterface` (Facade)

Координатор отображения урока. Делегирует в три под-модуля:

| Под-модуль | Класс | Ответственность |
|-----------|-------|----------------|
| `lesson_display.py` | `LessonDisplay` | Генерация и рендеринг урока |
| `lesson_navigation.py` | `LessonNavigation` | Кнопки: тест, примеры, объяснение, Q&A, контрольные, след.урок |
| `lesson_interaction.py` | `LessonInteraction` | Обработка интерактивных действий (вопросы, примеры) |

**`LessonDisplay.show_lesson(section_id, topic_id, lesson_id)`:**
1. Проверяет кэш в `state.json` → если есть, использует
2. Если кэша нет → `ContentGenerator.generate_lesson()` → сохраняет в кэш
3. Форматирует HTML (markdown → HTML, очистка стилей)
4. Собирает виджет: заголовок + контент + навигация + контейнеры для расширений

**`LessonNavigation.create_enhanced_navigation_buttons()`:**
Создаёт кнопки с обработчиками:
- 📝 **Тест** → `AssessmentInterface.show_assessment()`
- 📖 **Примеры** → `ExamplesGenerator.generate()`
- 💡 **Объяснение** → `ExplanationGenerator.generate()`
- ❓ **Вопрос ИИ** → `QAGenerator.generate()`
- 🛠️ **Контрольные задания** → `ControlTasksInterface.show_control_task()` (доступна после теста)
- ➡️ **Следующий урок** → `CourseDataManager.get_next_lesson()`

#### 7.3 `assessment_interface.py` → `AssessmentInterface`

| Метод | Назначение |
|-------|-----------|
| `show_assessment(course, section, topic, lesson, content)` | Генерирует вопросы, показывает RadioButtons |
| `_create_compact_questions_interface(questions)` | Создаёт виджеты вопросов |
| `on_submit_button_clicked()` | Делегирует в `AssessmentResultsHandler` |

#### 7.4 `assessment_results_handler.py` → `AssessmentResultsHandler`

| Метод | Назначение |
|-------|-----------|
| `handle_test_submission(...)` | Расчёт баллов, сохранение результата, показ детальных результатов |
| `display_enhanced_test_results(...)` | HTML с оценкой, прогрессом, детализацией по вопросам |
| `_activate_control_tasks_button()` | Разблокирует кнопку контрольных заданий |

**Логика после теста:**
- Балл > 40% → тест пройден → доступны контрольные задания
- Балл ≤ 40% → предлагается повторить урок или продолжить с текущей оценкой

#### 7.5 `control_tasks_interface.py` → `ControlTasksInterface`

| Метод | Назначение |
|-------|-----------|
| `show_control_task(lesson_data, content)` | Генерирует задание, показывает поле ввода кода |
| `_check_solution(user_code, task_data, output)` | Вызывает `validate_task_execution()`, показывает результат |
| `_save_task_result(task_data, is_correct)` | Сохраняет результат → если тест + задание пройдены → урок завершён |
| `_navigate_to_next_lesson()` | Переход к следующему уроку через `get_next_lesson()` |

#### 7.6 `completion_interface.py` → `CompletionInterface`

| Метод | Назначение |
|-------|-----------|
| `show_course_completion()` | Экран завершения: статистика + сертификат + рекомендации |
| `_create_certificate_widget()` | HTML-сертификат с именем, курсом, баллом, датой |
| `_create_recommendations_widget()` | Рекомендации следующих курсов |

#### 7.7 `startup_dashboard.py` → `StartupDashboard`

| Метод | Назначение |
|-------|-----------|
| `show_dashboard()` | Дашборд: приветствие, прогресс, статистика, кнопка «Продолжить» |
| `_create_progress_section()` | Прогресс-бар и статистика по секциям |
| `_create_statistics_section()` | Средний балл, количество тестов, время |

---

## 8. Оценка знаний

### `assessment.py` → класс `Assessment`

| Метод | Назначение |
|-------|-----------|
| `generate_questions(course, section, topic, lesson, content, num)` | Делегирует в `AssessmentGenerator` |
| `calculate_score(questions, user_answers)` | Считает баллы: правильные/всего × 100% |
| `log_assessment_results(...)` | Логирует результаты через `SystemLogger` |

---

## 9. Утилиты

### `content_utils.py` → `ContentUtils`
- `COMMUNICATION_STYLES` — словарь 4 стилей общения
- `BASE_CSS_STYLES` / `EXAMPLES_CSS_STYLES` / `EXPLANATION_CSS_STYLES` — HTML+CSS шаблоны
- `get_style_prefix(style, content_type)` — персонализированные приветствия

### `interface_utils.py`
- `InterfaceState` (Enum) — состояния UI: INITIAL_SETUP, LESSON_VIEW, ASSESSMENT и т.д.
- `InterfaceStyles` — CSS для тестов (вопросы, варианты, результаты)
- `InterfaceUtils` — утилиты: навигация, прогресс-бар, стилизованные сообщения

### `content_formatter_final.py` → `ContentFormatterFinal`
- Конвертирует Markdown → HTML с CSS-стилями
- Извлекает блоки кода через placeholder-механизм
- Подсвечивает комментарии в коде

### `loading_indicators.py`
- `LoadingIndicator` — базовый спиннер
- `OpenAIAPILoadingIndicator` — спиннер с типом операции
- `LessonLoadingIndicator` — спиннер с прогрессом загрузки урока
- `LoadingManager` — фабрика индикаторов

### `logger.py` → `SystemLogger`
- `log_activity(action_type, status, details)` — общий лог
- `log_lesson(course, section, topic, title, content)` — лог уроков
- `log_assessment(...)` — лог тестов

### `relevance_checker.py` → `RelevanceChecker`
- Проверяет, относится ли вопрос пользователя к теме курса через LLM

---

## 10. Граф вызовов

### Запуск нового пользователя
```
TeachAI.ipynb
  └→ TeachAIEngine()
       └→ start()
            └→ _show_startup_or_setup()
                 └→ SetupInterface.show_initial_setup()
                      └→ [пользователь заполняет форму]
                           └→ UserProfileManager.save_user_profile()
                                └→ SetupInterface.show_course_selection()
                                     └→ [пользователь выбирает курс]
                                          └→ CoursePlanGenerator.generate()
                                               └→ OpenAI API
                                          └→ CourseDataManager.save_course_plan()
                                          └→ LessonDisplay.show_lesson()
                                               └→ LessonGenerator.generate()
                                                    └→ OpenAI API
```

### Прохождение урока
```
LessonDisplay.show_lesson()
  └→ [пользователь читает урок]
       └→ [нажимает «Тест»]
            └→ AssessmentInterface.show_assessment()
                 └→ AssessmentGenerator.generate_questions()
                      └→ OpenAI API
                 └→ [пользователь отвечает, нажимает «Завершить»]
                      └→ AssessmentResultsHandler.handle_test_submission()
                           └→ Assessment.calculate_score()
                           └→ LearningProgressManager.save_lesson_assessment()
                           └→ [если тест пройден: кнопка контрольных заданий]
                                └→ ControlTasksInterface.show_control_task()
                                     └→ ControlTasksGenerator.generate_control_task()
                                          └→ OpenAI API
                                     └→ [пользователь пишет код, нажимает «Проверить»]
                                          └→ ControlTasksGenerator.validate_task_execution()
                                          └→ _save_task_result()
                                               └→ LearningProgressManager (тест + задание → урок завершён)
                                          └→ _navigate_to_next_lesson()
                                               └→ CourseDataManager.get_next_lesson()
                                               └→ LessonDisplay.show_lesson() [следующий урок]
```

### Интерактивные функции урока
```
[Кнопка «Примеры»]  → LessonInteraction → ExamplesGenerator → OpenAI API → HTML в examples_container
[Кнопка «Объяснение»] → LessonInteraction → ExplanationGenerator → OpenAI API → HTML в explain_container
[Кнопка «Вопрос ИИ»] → LessonInteraction → RelevanceChecker → QAGenerator → OpenAI API → HTML в qa_container
```

---

## Сводная таблица всех модулей

| Модуль | Класс | Тип | Зависит от |
|--------|-------|-----|-----------|
| `engine.py` | `TeachAIEngine` | Оркестратор | Все модули |
| `config.py` | `ConfigManager` | Конфигурация | `dotenv` |
| `state_manager.py` | `StateManager` | Facade состояния | 3 под-менеджера |
| `user_profile_manager.py` | `UserProfileManager` | Менеджер | — |
| `learning_progress_manager.py` | `LearningProgressManager` | Менеджер | — |
| `course_data_manager.py` | `CourseDataManager` | Менеджер | `courses.json` |
| `llm.py` | `LLMProvider` | LLM-обёртка | `openai`, `httpx` |
| `content_utils.py` | `BaseContentGenerator` | Базовый класс | `openai`, `httpx` |
| `content_generator.py` | `ContentGenerator` | Facade контента | 6 генераторов |
| `course_plan_generator.py` | `CoursePlanGenerator` | Генератор | `BaseContentGenerator` |
| `lesson_generator.py` | `LessonGenerator` | Генератор | `BaseContentGenerator` |
| `assessment_generator.py` | `AssessmentGenerator` | Генератор | `BaseContentGenerator` |
| `examples_generator.py` | `ExamplesGenerator` | Генератор | `BaseContentGenerator` |
| `explanation_generator.py` | `ExplanationGenerator` | Генератор | `BaseContentGenerator` |
| `qa_generator.py` | `QAGenerator` | Генератор | `BaseContentGenerator` |
| `control_tasks_generator.py` | `ControlTasksGenerator` | Генератор | `BaseContentGenerator` |
| `assessment.py` | `Assessment` | Координатор тестов | `ContentGenerator` |
| `interface.py` | `UserInterface` | Facade UI | Все интерфейсы |
| `setup_interface.py` | `SetupInterface` | UI настройки | `StateManager` |
| `lesson_interface.py` | `LessonInterface` | Facade урока | 3 под-модуля |
| `lesson_display.py` | `LessonDisplay` | Рендеринг урока | `ContentGenerator` |
| `lesson_navigation.py` | `LessonNavigation` | Навигация | `StateManager` |
| `lesson_interaction.py` | `LessonInteraction` | Интерактив | Генераторы |
| `assessment_interface.py` | `AssessmentInterface` | UI тестов | `Assessment` |
| `assessment_results_handler.py` | `AssessmentResultsHandler` | Обработчик | `StateManager` |
| `control_tasks_interface.py` | `ControlTasksInterface` | UI заданий | `ControlTasksGenerator` |
| `completion_interface.py` | `CompletionInterface` | UI завершения | `StateManager` |
| `startup_dashboard.py` | `StartupDashboard` | Дашборд | `StateManager` |
| `content_formatter_final.py` | `ContentFormatterFinal` | Форматирование | `re` |
| `loading_indicators.py` | `LoadingManager` | Индикаторы | `ipywidgets` |
| `logger.py` | `SystemLogger` | Логирование | `logging` |
| `interface_utils.py` | `InterfaceUtils` | UI-утилиты | `ipywidgets` |
| `relevance_checker.py` | `RelevanceChecker` | Проверка | `BaseContentGenerator` |
