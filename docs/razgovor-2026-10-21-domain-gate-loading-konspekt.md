# Конспект: domain-gate, индикаторы ожидания, UI Jupyter (21.10.2026)

**Проект:** `/media/ip-59/64GB/TeachAI` · **Репозиторий:** https://github.com/Ip-59/TeachAI  
**Chat-log:** `docs/chat_logs/1-261021 chat_log.md`  
**Предыдущий конспект:** `docs/razgovor-2026-10-20-etapy5-6-oblast-python-ml-konspekt.md`

Папки `doc/` и `docs/` в git не входят. Конспект на флешке.

---

## Цель сессии и итог

Продолжение после рамки Python/AI/ML (20.10): починить живые баги проверки своей темы и индикаторов ожидания LLM в Jupyter.

**Итог:**

1. **False «нет модели»** при проверке темы: фасад `ContentGenerator` без `make_api_request` — берём API у вложенных генераторов (`resolve_api_generator`).
2. **«Выбрать другой курс» сносило UI:** `clear_output` вне `Output` чистил всю ячейку.
3. **Старт курса/урока из `with output:`** вкладывал следующий экран в форму — старт вынесен с очисткой ячейки.
4. **Индикатор «крутится поверх урока»:** `hide()` звал `clear_output` (виджет не убирался); у lesson-индикатора не ставился `is_active`. Переписан `loading_indicators.py`: скрытие через `dismiss_widget` / `close()`, контекст `displayed_loading`.
5. **Индикаторы добавлены** на план, урок, тест, примеры, Q&A, объяснение, понятия, релевантность, КЗ, проверку темы.
6. **Задвоение предупреждения domain:** `Output`+`display`/`clear_output` — заменены на слот `status_box.children = (widget,)`.
7. Полный интерактивный E2E «всех модулей» в Jupyter **не утверждался** — статика + `*_checks.py`; живой прогон — за автором.

**Коммита этой сессии не было** (автор не просил).

---

## Принятые решения

| Решение | Почему |
|---------|--------|
| `resolve_api_generator` на фасаде | Не ломать архитектуру фасада; API у `lesson_gen` / … |
| Статус domain — `VBox`-слот, не `Output` | Jupyter часто оставляет старые `display` в Output → дубли |
| Скрытие индикатора без `clear_output` | `clear_output` ломает соседний UI / не снимает widget view |
| `displayed_loading` + `finally` | Индикатор всегда снимается при успехе и ошибке |
| Кнопка «Начать» disabled на время gate | Меньше двойных кликов / двойных запросов к LLM |
| Аудит потоков = код + checks, не «всё зелёное E2E» | Без kernel+API нельзя честно закрыть все ветки |

## Отклонённые / не делали

| Предложение | Почему нет |
|-------------|------------|
| Полный клик по каждому модулю со всеми ветками в этой сессии | Нужен живой Jupyter + API; сделан статический обход + checks |
| Словарь ключевых слов для domain (снова) | Уже отвергнуто 20.10; остаётся LLM-only |
| Коммит «заодно» | Только по явной просьбе |

---

## Изменённые пути (рабочее дерево)

| Файл | Роль |
|------|------|
| `course_domain.py` | `resolve_api_generator`, classify через вложенный API |
| `course_domain_ui.py` | gate: status_box, wait-banner, без Output-дублей |
| `course_domain_checks.py` | тест фасада |
| `course_selection_ui.py` | status_box, disabled start, старт вне Output |
| `loading_indicators.py` | dismiss без clear_output; `make_wait_banner`; `displayed_loading` |
| `loading_indicators_checks.py` | автопроверки скрытия |
| `content_generator.py` | loading на план/урок/тест/примеры/Q&A/объяснение/понятия/релевантность |
| `control_tasks_interface.py` | loading на генерацию КЗ |
| `lesson_navigation.py` | wait-banner при примерах |
| `run_teachai.py` | reload `loading_indicators` |

Рамка/баннер/`project_identity` с 20.10 по-прежнему в дереве; отдельного коммита identity+domain+loading всё ещё нет.

---

## Проверки

```text
python3 course_domain_checks.py
python3 course_portfolio_checks.py
python3 student_content_checks.py
venv_H_L/bin/python loading_indicators_checks.py
```

Ручной Jupyter (Restart kernel → `start_jupyter()`):

1. Своя тема вне IT → одно предупреждение → «Выбрать другой курс» → форма выбора жива.
2. Тема in-domain / каталог → план → урок: индикатор исчезает, когда появляется контент.
3. Вопрос / примеры / тест / КЗ — виден баннер ожидания, потом снимается.

---

## Открытые хвосты

1. **Коммит** identity + domain + loading (по запросу).
2. Первый запуск: профиль → выбор курса всё ещё может идти через `Output` в `setup_interface` (класс stacking).
3. Отложено ранее: наслоение display / дашборд после КЗ; `json_schema` 6B.
4. В `TeachAI.ipynb` может оставаться отладочный ipify — в коммит не тащить без чистки.
5. `content_generator.py` ~529 строк — долг по размеру модуля.

---

## Бриф на следующий чат

```
Конспект: docs/razgovor-2026-10-21-domain-gate-loading-konspekt.md
Chat-log: docs/chat_logs/1-261021 chat_log.md
Предыдущий: docs/razgovor-2026-10-20-etapy5-6-oblast-python-ml-konspekt.md

Починены: domain resolve API, «другой курс», stuck loader, задвоение warning (status_box).
Не закоммичено. Дальше по запросу: commit + ручной Jupyter-прогон.
Не обещать полный E2E без прогона автором. Inference + оркестрация, практика = Python kernel.
```
