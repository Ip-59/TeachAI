# Конспект: этапы 5–6 куратора, рамка Python/AI/ML (20.10.2026)

**Проект:** `/media/ip-59/64GB/TeachAI` · **Репозиторий:** https://github.com/Ip-59/TeachAI  
**Chat-log:** `docs/chat_logs/1-261020 chat_log.md`  
**План куратора (19.10):** `docs/razgovor-2026-10-19-kurator-dorabotki-plan-konspekt.md`  
**Отчёты этапов:**  
`docs/otchet-etap5-course-portfolio-2026-10-20.md`,  
`docs/otchet-etap6-llm-render-2026-10-20.md`

Папки `doc/` и `docs/` в git не входят. Конспект на флешке.

---

## Цель сессии и итог

Продолжение доработок куратора: считать этап 4 принятым → этап 5 (портфель) → этап 6 (вывод LLM) → честно зафиксировать предметную область Python/AI/ML.

**Итог:**

1. **Этап 5 принят автором.** Портфель курсов в `state.json` (зеркало активного слота + `courses`). Коммит `0b70bda`.
2. **Этап 6 в коде.** Канон `student_content.render_student_content()`. Коммит `ff5ba0a`. Полный `json_schema` на все генераторы **не делали** (сознательно).
3. **Рамка продукта:** не «учитель чего угодно». Название: *TeachAI — интеллектуальная система персонализированного обучения Python и AI/ML на основе языковой модели* (именительный: «система», не «систему»).
4. Баннер области на первом экране (дашборд / профиль). Своя тема курса проверяется **запросом к LLM**, не словарём ключевых слов. Вне области — предупреждение + принудительный старт. **Коммита этой части ещё нет.**

Порядок куратора 5→6→1→3→2→4 по этапам реализации: **1–6 закрыты в коде**; этап 6B-schema отложен.

---

## Принятые решения

| Решение | Почему |
|---------|--------|
| Портфель = зеркало `learning`/`course_plan`/`cache`/`control_tasks` + `state["courses"]` | Не переписывать все обращения к корню state |
| Resume каталожного id, если слот уже есть | Не генерировать план заново |
| Custom id каждый раз новый | Продолжение своего курса — с дашборда, не повторным вводом названия |
| Этап 6 = канон рендера, не React | Согласовано 19.10; Jupyter/ipywidgets |
| Не json_schema на план/тест/КЗ в этом коммите | План уже `json_object`; GPTunnel+schema не проверяли |
| Продукт = Python + данные + ML в Jupyter | Примеры/КЗ = `exec` / AST; C/Java запускать негде |
| Своё название оставить | Требование куратора п.1; внутри рамки («pandas для аналитика») |
| Проверка темы **только LLM** | Автор отверг словарь маркеров в `course_domain.py` как дырявый фильтр |
| Вне области: предупреждение, не запрет | Кнопка «всё равно начать» + перечень, что не гарантируется |
| Если LLM недоступна — ошибка, курс сам не стартует | Это не «нет» и не обход эвристикой |

## Отклонённые

| Предложение | Почему нет |
|-------------|------------|
| «Не навязывать Python» как универсальный учитель | Враньё: практика привязана к Python-ядру |
| Кричать в любом кастомном курсе «это курс Python» | Враньё в другую сторону (шитьё → фейковый Python) |
| Фильтр темы по спискам stem’ов | Автор: надо спрашивать модель да/нет |
| json_schema сразу на все генераторы | Риск GPTunnel, не критерий «читаемый HTML» |
| Движок C++/Java | Вне диплома |

---

## Коммиты и команды

```
0b70bda Сохранить несколько курсов в профиле без взаимного затирания.
ff5ba0a Свести учебный текст LLM к одному HTML-рендеру в Jupyter.
```

Ветка `main` опережает `origin/main` (на момент сессии +7 после двух коммитов; identity/domain ещё не в git).

Проверки без Jupyter:

```text
python3 course_portfolio_checks.py
venv_H_L/bin/python student_content_checks.py
python3 course_domain_checks.py
```

Не коммитили: `.env`, `TeachAI.ipynb` (там ещё ipify из отладки VPN), `*.bak_*`.

---

## Изменённые пути

### Этап 5 (в git)

`course_portfolio.py`, `course_portfolio_ui.py`, `course_portfolio_checks.py`, `state_manager.py`, `course_data_manager.py`, `course_selection_ui.py`, `startup_dashboard.py`, `lesson_navigation.py`, `lesson_utils.py`, `completion_interface.py`, `interface.py`, `engine.py`, `assessment_*.py`, `run_teachai.py`, `ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md`, `DESCRIPTION.md`

### Этап 6 (в git)

`student_content.py`, `student_content_checks.py`, `content_formatter_final.py`, `content_utils.py`, `lesson_display.py`, `lesson_generator.py`, `explanation_generator.py`, `qa_generator.py`, `concepts_generator.py`, `examples_display.py`, `control_tasks_interface.py`, `run_teachai.py`, описания

### Рамка Python/AI/ML (рабочее дерево, без коммита)

| Файл | Роль |
|------|------|
| `project_identity.py` | титул, баннер, список ограничений практики |
| `course_domain.py` | только LLM: JSON `in_domain` true/false |
| `course_domain_ui.py` | предупреждение + force / другой курс |
| `course_domain_checks.py` | разбор ответа (фейковый генератор) |
| `setup_interface.py`, `startup_dashboard.py`, `course_selection_ui.py` | баннер; gate на своём названии |
| `README.md`, `ОПИСАНИЕ_…`, `DESCRIPTION.md` | название и рамка |
| `doc/Доклад_очная_защита_TeachAI.md` | слайд 1 |
| `TeachAI.ipynb` | markdown-ячейка с титулом |

---

## Открытые хвосты

1. **Коммит рамки/баннера/LLM-фильтра темы** — автор не просил; сделать по запросу.
2. Ручная проверка этапа 6 (рендер) и баннера/фильтра в Jupyter.
3. **Отложено с 19.10:** наслоение `display` / тройной loader; кнопка «Показать дашборд» после КЗ (частично должен ожить `engine` на LessonInterface).
4. `json_schema` на план/тест/примеры/КЗ — только если куратор упрётся в машиночитаемый контракт.
5. `format_gate` бенчмарка по-прежнему требует ` ```python ` — это про Python-уроки эксперимента, не менять молча.
6. В `TeachAI.ipynb` остался отладочный `api.ipify.org` — в титульный коммит не тащить.
7. Сохранить чат (этот пункт) — **сделано**.

---

## Бриф на следующий чат

```
Конспект: docs/razgovor-2026-10-20-etapy5-6-oblast-python-ml-konspekt.md
Chat-log: docs/chat_logs/1-261020 chat_log.md
Этапы 1–6 куратора в коде (коммиты aa35e88 … ff5ba0a).
Рамка Python/AI/ML + LLM-проверка своей темы — в дереве, без коммита.

Дальше по запросу автора:
- commit identity/domain;
- ручной прогон Jupyter;
- json_schema только если куратор явно потребует;
- не чинить stacking/дашборд-после-КЗ без сигнала.

Архитектура: inference + оркестрация, без RAG/fine-tuning.
Практика = Python kernel. Не обещать мультиязычную IDE.
```
