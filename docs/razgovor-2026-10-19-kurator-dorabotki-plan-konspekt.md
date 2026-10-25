# Конспект: замечания куратора — разбор, план, этап 1 (19.10.2026)

**Проект:** `/media/ip-59/64GB/TeachAI` · **Репозиторий:** https://github.com/Ip-59/TeachAI  
**Chat-log:** `docs/chat_logs/1-261019 chat_log.md`  
**Отчёт этапа 1:** `docs/otchet-etap1-test-answers-2026-10-19.md`  
**Вводные по формату LLM:**  
`docs/Mistral форматы-ответов-llm-по-api-гарантии-качество-и-вывод-на-экран.md`,  
`docs/Perplexiti о формате ответов и выводе на экран.txt`  
**Предыдущий контекст сдачи:** этап 7 / очная защита; inference + оркестрация, без fine-tuning/RAG.

Папки `doc/` и `docs/` в git не входят. Конспект на флешке.

---

## Цель сессии и итог

Куратор указал 6 недоработок. Нужны: экспертная оценка, план по файлам, старт поэтапной реализации с стопом после каждого этапа, правилами module-size / no-stubs.

**Итог сессии:**
1. Вердикт и план 0–6 зафиксированы (см. ниже).
2. Правила Cursor: `module-size.mdc`, `no-stubs.mdc`.
3. **Этап 1 (п.5) выполнен** — снимок `RadioButtons.value`, unlock Submit; модуль `assessment_questions_ui.py`.
4. Коммит: `aa35e88`. Этапы 2–6 не начаты; ждёт ручной проверки теста в Jupyter.

Порядок работ: 5→6→1→3→2→4; п.4 = гибрид Markdown + structured в ipywidgets, без React.

---

## Вердикт по требованиям куратора

| # | Требование | Вердикт | Gap в коде |
|---|------------|---------|------------|
| 1 | Ввод своего названия курса | Справедливо | Только dropdown из `courses.json` (`setup_interface.py`) |
| 2 | Несколько курсов, switch, delete | Справедливо, самое тяжёлое | Один `current_course` + один `course_plan` |
| 3 | Перемещение по урокам внутри курса | Справедливо | Есть `get_next_lesson`, нет outline/jump |
| 4 | Нормальный вывод ответов LLM везде | Суть да; «полный rewrite» — нет | Разные пути рендера; самописные очистки; нет единого контракта |
| 5 | Не перекликивать ответ в тесте | Справедливо, баг UX | Submit читает `current_answers` из `observe`, не снимки `.value` виджетов |
| 6 | Принудительный переход к КЗ | Справедливо | Кнопка КЗ `disabled=not test_passed`; force completion ≠ force entry |

### Принятые решения

1. **Порядок реализации:** 5 → 6 → 1 → 3 → 2 → 4 (не наоборот).
2. **П.4 = гибрид из Mistral-дока:** учебный текст = Markdown + единый рендерер; машиночитаемое (план, тест, метаданные примеров) = Structured Outputs / schema. Адаптация под **ipywidgets**, не react-markdown.
3. **П.2 = портфель курсов в `state.json`**, не «вторая LMS».
4. **П.3:** outline + переход; политика доступа — завершённые + текущий + следующий (или все с предупреждением) — зафиксировать при старте этапа.
5. **П.6:** отдельный bypass входа в КЗ с пометкой в прогрессе; не путать с `mark_lesson_completed_forced`.
6. **Вне scope сдачи (пока куратор явно не потребует):** image-generation, Mermaid-рендер, стриминг токенов, смена UI-стека.
7. **Процесс:** после каждого этапа — стоп, мини-отчёт в `docs/otchet-etap…`, коммит; автор проверяет в Jupyter.
8. **Правила агента:** дробить модули (~300–400 строк); заглушки только с явным согласием (`no-stubs.mdc`).

### Отклонённые / суженные формулировки

- «Серьёзно и глубоко переработать всё с современными технологиями» → **унификация контракта + один рендер-путь**.
- Perplexity-вариант «всё в JSON-конверте» как единственный подход → только для structured-частей; длинный урок оставляем Markdown (налог на качество / экранирование).
- Полное открытие всех уроков без правил прогресса → риск размыть демо и статистику.

### Красные флаги

- Патчить multi-course поверх одного `course_plan` без миграции state.
- Тянуть фронтовый стек из docs в Jupyter.
- Обещать «гарантию красивого текста» через JSON schema (формат ≠ содержание).

---

## Текущая архитектура (якорь)

| Что | Где |
|-----|-----|
| Выбор курса | `setup_interface.py` → `get_all_courses()` / `courses.json` |
| Один слот прогресса | `state["learning"]`, `state["course_plan"]` — `state_manager.py`, `learning_progress_manager.py`, `course_data_manager.py` |
| Навигация урока | `lesson_navigation.py`, `course_data_manager.get_next_lesson()` |
| Тест | `assessment_interface.py`, `assessment_results_handler.py` |
| КЗ | `control_tasks_interface.py`; кнопка в `lesson_navigation.py` |
| Рендер урока | `content_formatter_final.py`, `content_renderer.py`, `lesson_display.py` |
| Примеры | `examples_*.py` (структурированные данные уже есть) |
| Точка входа | `run_teachai.py`, `engine.py`, `startup_dashboard.py` |

---

## План изменений по этапам и файлам

### Этап 0 — подготовка (до кода)

**Цель:** бэкап и фиксация контрактов, чтобы не ломать демо.

| Действие | Файлы / артефакты |
|----------|-------------------|
| Бэкап | копия `data/state.json`, при крупных правках — `.bak` ключевых модулей |
| Зафиксировать целевую схему state для п.2 (черновик) | этот конспект + комментарий в `state_manager.py` при старте этапа 2 |
| Чеклист ручной проверки | сценарии: тест без переклика; force КЗ; свой курс; jump по уроку; 2 курса + delete |

Критерий готовности: согласован порядок этапов (ниже) и политика доступа к урокам (п.3).

---

### Этап 1 — тест без перекликивания (п.5)

**Цель:** «Завершить тест» принимает уже выбранные ответы без повторного клика.

| Файл | Изменение |
|------|-----------|
| `assessment_interface.py` | Перед `handle_test_submission`: собрать ответы из `self.question_widgets[i].value` в список; fallback на `current_answers`. Убрать зависимость только от `observe`. |
| `assessment_results_handler.py` | При необходимости уточнить сообщения «не отвечены вопросы» (если `None` после снимка). |
| Ручной тест | Выбрать все варианты один раз → Submit → нет ложного «ответьте на вопросы». |

**Критерий:** однократный выбор каждого варианта достаточен.

**Оценка:** ~0.5–1 ч.

---

### Этап 2 — принудительный вход в контрольное (п.6)

**Цель:** КЗ доступно не только после успешного теста.

| Файл | Изменение |
|------|-----------|
| `lesson_navigation.py` | Кнопка КЗ всегда активна **или** вторая кнопка/меню «К практике без теста». Tooltip честный. |
| `lesson_navigation.py` / обработчик | При force-входе писать флаг в learning (например `control_task_bypass[lesson_id]=True` или `test_skipped`). |
| `learning_progress_manager.py` | API: `mark_test_bypassed(lesson_id)` / чтение флага; **не** смешивать с `mark_lesson_completed_forced`. |
| `state_manager.py` | Проброс методов; дефолты в `learning`. |
| `assessment_results_handler.py` | После успешного теста по-прежнему unlock; bypass не ломает обычный путь. |
| `ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md` | Одна фраза: педагогический bypass входа в КЗ. |

**Критерий:** без прохождения теста можно открыть КЗ; факт bypass виден в state/логах.

**Оценка:** ~1–2 ч.

---

### Этап 3 — своё название курса (п.1)

**Цель:** ученик выбирает из каталога **или** вводит свою тему.

| Файл | Изменение |
|------|-----------|
| `setup_interface.py` | UI: Radio/Toggle «из списка» / «свой курс»; `widgets.Text` для названия; описание опционально. Валидация: непустое, разумная длина. |
| `setup_interface.py` | Сборка объекта курса: `{id: "custom_<slug>", title, description, prerequisites, difficulty, source: "user"}`. |
| `course_plan_generator.py` | Убедиться, что план строится по `title`/`description` без обязательного id из каталога (уже так — проверить промпт). |
| `course_data_manager.py` | При необходимости: не искать custom-id в `courses.json` при отображении заголовка (брать из `course_plan` / портфеля). |
| `logger.py` / activity | Лог `course_started` с `source: user|catalog`. |

**Критерий:** «Основы pandas для аналитика» → план → первый урок без записи в `courses.json`.

**Оценка:** ~2–3 ч.

---

### Этап 4 — навигация по урокам внутри курса (п.3)

**Цель:** видеть план и переходить между уроками, не только «следующий».

| Файл | Изменение |
|------|-----------|
| **Новый** `lesson_outline.py` (предпочтительно) **или** расширение `lesson_navigation.py` | Построить дерево sections/topics/lessons из `course_plan`; статусы (done / current / locked) из `learning_progress_manager`. |
| `lesson_interface.py` / `lesson_display.py` | Вставить outline (Accordion/Select/кнопки) на экран урока. |
| `course_data_manager.py` | `get_lesson_data` + новый `set_current_lesson(section, topic, lesson)` / `open_lesson(...)` с обновлением progress. |
| `learning_progress_manager.py` | Политика: разрешённые переходы (рекомендация: completed ∪ current ∪ next; опционально «открыть любой» с warning). |
| `startup_dashboard.py` / `engine.py` | При resume открывать `current_*`, outline согласован. |
| `lesson_utils.py` | Хелперы заголовков/breadcrumb при hop. |

**Критерий:** из урока 1.2 перейти на завершённый 1.1 и обратно на текущий без потери state.

**Оценка:** ~4–6 ч.

---

### Этап 5 — портфель курсов (п.2)

**Цель:** несколько курсов в профиле; старт нового без удаления старых; switch; delete.

#### 5A. Модель данных

Целевая схема (миграция из текущего single-slot):

```text
state = {
  "user": {...},
  "active_course_id": "<id>|\"\"",
  "courses": {
    "<course_id>": {
      "meta": { "title", "source", "created_at", "status": "active|completed" },
      "course_plan": {...},
      "learning": {
        "current_section", "current_topic", "current_lesson",
        "completed_lessons" / assessment scores / control results /
        "lesson_completion_status", bypass-флаги, ...
      },
      "lesson_content_cache": { ... }   # или общий кэш с префиксом course_id:
    }
  },
  # совместимость на 1 релиз:
  "learning": ..., "course_plan": ...   # зеркало active или удалить после миграции
}
```

| Файл | Изменение |
|------|-----------|
| `state_manager.py` | Дефолты; `migrate_state_to_multi_course()` при load; getters/setters active course. |
| `course_data_manager.py` | `save/get_course_plan` относительно **active**; `list_user_courses()`, `switch_course(id)`, `delete_course(id)`. |
| `learning_progress_manager.py` | Все update/get читают/пишут слот active (или явный `course_id`). |
| `state_manager.py` (кэш уроков) | Ключи кэша с префиксом `course_id:` **или** кэш внутри слота курса. |

#### 5B. UI

| Файл | Изменение |
|------|-----------|
| `setup_interface.py` | «Начать ещё один курс» не wipe’ает предыдущий. |
| `startup_dashboard.py` | Список «Мои курсы»: продолжить / переключить / удалить (с confirm). |
| `lesson_navigation.py` | «Назад к курсам» → дашборд портфеля, не только выбор из каталога. |
| `completion_interface.py` | Завершение курса → status completed; остаться в портфеле. |
| `interface.py` | Фасад: маршрутизация к portfolio UI. |

#### 5C. Документация

| Файл | Изменение |
|------|-----------|
| `ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md` | Раздел про портфель курсов. |
| `DESCRIPTION.md` | Кратко, если используется на защите EN. |

**Критерий:** курс A на уроке 3 → старт B → switch на A → тот же урок 3; delete B не трогает A.

**Оценка:** ~1–2 дня (главный объём).

---

### Этап 6 — контракт LLM и вывод на экран (п.4)

**Цель:** один понятный пайплайн «запрос → формат → рендер» на всех учебных экранах; убрать хрупкие самописные фильтры где возможно.

#### 6A. Единый рендер (Jupyter)

| Файл | Изменение |
|------|-----------|
| `content_renderer.py` | Канон: `render_markdown_to_html`, code fences, таблицы, LaTeX→MathML; публичный API `render_student_content(md) -> html`. |
| `content_formatter_final.py` | Свести к тонкой обёртке над каноном; вычистить дублирующие «очистки», которые ломают разметку. |
| `lesson_display.py` | Только канон; меньше эвристик «уже HTML / ещё markdown». |
| `lesson_interaction.py` / ответы Q&A | Прогон через тот же рендер. |
| `explanation_generator.py` + UI показа | Markdown → канон. |
| `examples_display.py` | Уже structured — выровнять стили под канон CSS. |
| `control_tasks_interface.py` | Описание задания / feedback LLM через канон. |
| `interface_utils.py` | Общий CSS класс `.lesson-content` / explanations. |

#### 6B. Контракт запросов

| Файл | Изменение |
|------|-----------|
| `content_utils.py` | Хелпер API: `response_format` json_schema где поддерживается провайдером; проверка `finish_reason`. |
| `course_plan_generator.py` | Structured / строгая schema + Pydantic/jsonschema (усилить то, что уже есть). |
| `assessment_generator.py` | Schema вопросов/вариантов/correct index. |
| `lesson_generator.py` | Остаётся Markdown; системный промпт: русский, ```python, не оборачивать весь ответ в fence. |
| `qa_generator.py`, `explanation_generator.py` | Markdown + лёгкие правила промпта. |
| `examples_generator.py` / `examples_validation.py` | Сохранить structured blocks; при возможности schema на API. |
| `control_tasks_generator.py` | Structured поля задачи; prose-описание можно markdown. |
| `model_benchmark/format_gate.py` | При желании — регрессия формата после изменений. |

#### 6C. Документы

| Файл | Изменение |
|------|-----------|
| `ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md` | Гибридный контракт Markdown + Structured Outputs. |
| Этот конспект | Отметить выполненное по чеклисту. |

**Критерий:** урок / объяснение / Q&A / примеры / КЗ — читаемый HTML с кодом и отступами; план и тест парсятся без regex-«спасения» (кроме снятия fence вокруг JSON при необходимости).

**Вне этапа:** React, Streamdown, image-gen, Mermaid UI.

**Оценка:** ~2–4 дня итерациями; не блокировать этапы 1–5.

---

## Сводка порядка и зависимостей

```text
[1] п.5 тест          ── независим
[2] п.6 force КЗ      ── независим (слегка трогает learning flags)
[3] п.1 свой курс     ── лучше до или параллельно с п.2; после п.2 custom id кладётся в портфель
[4] п.3 outline       ── удобнее после стабильного get_lesson; до или после п.2 (после п.2 — outline внутри active)
[5] п.2 портфель      ── зависит от аккуратной миграции state; делать отдельным PR/коммитом
[6] п.4 LLM pipeline ── параллельно после 1–2; не ждать п.2 обязательно, но единый рендер нужен всем экранам
```

Рекомендуемые коммиты (когда попросите): по одному на этап 1, 2, 3; отдельно 4; отдельно 5A+5B; отдельно 6A затем 6B.

---

## Статус этапов

- **Этап 1 (п.5):** выполнен 19.10.2026 — отчёт `docs/otchet-etap1-test-answers-2026-10-19.md`, коммит `aa35e88`. Проверен после GPTunnel.
- **Маршрут LLM:** GPTunnel на рабочем ПК — `7445f4c`, отчёт `docs/otchet-gptunnel-route-2026-10-20.md`.
- **Этап 2 (п.6):** выполнен 20.10.2026 — отчёт `docs/otchet-etap2-kz-bypass-2026-10-20.md`.
- **Этап 3 (п.1):** выполнен 20.10.2026 — отчёт `docs/otchet-etap3-custom-course-2026-10-20.md`. Подтверждён автором.
- **Этап 4 (п.3):** выполнен 20.10.2026 — отчёт `docs/otchet-etap4-lesson-outline-2026-10-20.md`. Политика: completed ∪ current ∪ next. Ждёт ручной проверки.
- Этапы 5–6: не начаты.

## Изменённые файлы (этап 1 + правила)

| Путь | Что |
|------|-----|
| `assessment_questions_ui.py` | новый: RadioButtons + снимок ответов |
| `assessment_interface.py` | Submit / unlock |
| `assessment_results_handler.py` | return bool |
| `.cursor/rules/module-size.mdc` | лимит размера модулей |
| `.cursor/rules/no-stubs.mdc` | запрет заглушек без согласия |

## Открытые хвосты

1. Ручная проверка этапа 4: оглавление, jump, 🔒 на далёких уроках.
2. **Отложено:** наслоение экранов / повтор loader (`display` в Output + `loading_manager.show_loading`). Автор разрешил не чинить сразу.
3. **Отложено:** кнопка «Показать дашборд» после КЗ.
4. **Отложено:** Python-примеры на не-Python курсе (промпты).
5. Этап 5: портфель курсов.
4. Миграция старых `data/state.json` — в этапе 5A.
5. Согласовать с куратором сужение п.4 (гибрид Jupyter), если формулировка в отзыве жёсткая.

---

## Бриф на следующий чат

```
Конспект: docs/razgovor-2026-10-19-kurator-dorabotki-plan-konspekt.md
Chat-log: docs/chat_logs/1-261019 chat_log.md
Отчёты: docs/otchet-etap1…etap5-course-portfolio-2026-10-20.md

Этапы 1–6 в коде (20.10: портфель `0b70bda`, рендер `ff5ba0a`).
Продолжение 20.10: `docs/razgovor-2026-10-20-etapy5-6-oblast-python-ml-konspekt.md`, chat-log `1-261020`.
Рамка Python/AI/ML + LLM-проверка своей темы — в дереве, без коммита. json_schema отложен.

Отложено: наслоение display; кнопка дашборда после КЗ; Python-примеры на не-Python курсе.

Правила: module-size.mdc, no-stubs.mdc. После этапа — стоп, otchet, commit.
Не менять UI-стек. П.4 = гибрид Markdown + structured в ipywidgets.
Архитектура: inference + оркестрация, без RAG/fine-tuning.
```
