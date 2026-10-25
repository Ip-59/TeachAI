# Конспект: КЗ, LLM-судья, индикаторы, domain UI (22.10.2026)

**Проект:** `/media/ip-59/64GB/TeachAI` · **Репозиторий:** https://github.com/Ip-59/TeachAI  
**Chat-log:** `docs/chat_logs/1-261022 chat_log.md`  
**Предыдущие:**  
`docs/razgovor-2026-10-21-domain-gate-loading-konspekt.md`,  
`docs/razgovor-2026-10-20-etapy5-6-oblast-python-ml-konspekt.md`

Папки `doc/` и `docs/` в git не входят. Конспект на флешке.

---

## Цель сессии и итог

Довести рамку Python/AI/ML и практику КЗ до честной педагогики: полный текст урока в LLM-запросах, без keyword-угадывания темы, без копипасты примеров и терминальных заданий; починить UI-баги Jupyter (clear_output, индикаторы, задвоение).

**Итог (закоммичено в этой сессии):**

1. Идентичность продукта + баннер + LLM-проверка своей темы (`project_identity`, `course_domain*`).
2. Индикаторы ожидания: dismiss без `clear_output`; загрузка на LLM-вызовах.
3. UI выбора курса: `status_box` вместо Output; КЗ без сноса ячейки.
4. КЗ: полный контекст урока; антикопипаста/терминал/тема — через LLM-судью; starter без готового решения.
5. Убраны keyword-классификаторы предмета/релевантности (примеры, КЗ, relevance).

---

## Принятые решения

| Решение | Почему |
|---------|--------|
| Педагогические вердикты (тема, относится ли, терминал, копипаста) → LLM | Договорённость автора; списки маркеров дырявые |
| Структурная обрезка starter (`# Ваш код здесь`) без LLM | Факт формата строки, не угадывание темы |
| Полный текст урока в Q&A/объяснение/тест/примеры/КЗ | Иначе модель «формалит» и уводит тему |
| `status_box.children` вместо Output+display | Нет задвоений предупреждений в Jupyter |
| Не коммитить ipify в `TeachAI.ipynb` | Отладка VPN, не продукт |

## Отклонённые

| Предложение | Почему нет |
|-------------|------------|
| Оставить regex/token-судью «это быстрее» | Нарушает договор «всё угадывание — у LLM» |
| Хардкод fruits/Igor в промпте судьи | Пример из бага; сбивает модель — убрали |

---

## Коммит

`dea5af9` — Зафиксировать рамку TeachAI, LLM-проверку темы и качество КЗ без keyword-эвристик.

В коммит: код + README/описания + чистый `TeachAI.ipynb` (без ipify).  
Не в коммит: `*.bak_*`, `docs/` (gitignore).

Проверки:

```text
python3 course_domain_checks.py
python3 course_portfolio_checks.py
python3 student_content_checks.py
venv_H_L/bin/python loading_indicators_checks.py
venv_H_L/bin/python learning_prompt_context_checks.py
venv_H_L/bin/python control_task_quality_checks.py
venv_H_L/bin/python control_task_llm_judge_checks.py
```

---

## Ключевые пути

| Файл | Роль |
|------|------|
| `project_identity.py` | титул, баннер, ограничения |
| `course_domain.py` / `_ui` / `_checks` | LLM in_domain |
| `learning_prompt_context.py` | блоки среды/полного урока для промптов |
| `control_task_llm_judge.py` | subject + matches через LLM |
| `control_task_quality.py` | starter без решения; текст антикопипасты |
| `loading_indicators.py` | dismiss виджета |
| `course_selection_ui.py` | status_box |
| `relevance_checker.py` | только LLM |
| `examples_generation.py` | subject через LLM |

---

## Открытые хвосты

1. Ручной Jupyter-прогон: своя тема → out → другой курс; КЗ на уроке типов данных без копипасты.
2. Stacking при первом сохранении профиля (`setup_interface` + Output) — долг.
3. `json_schema` 6B — только по запросу куратора.
4. `content_generator.py` / `control_tasks_generator.py` всё ещё крупные — долг по module-size.
5. Push на origin — по явной просьбе.

---

## Бриф на следующий чат

```
Конспект: docs/razgovor-2026-10-22-kz-llm-judge-loading-konspekt.md
Chat-log: docs/chat_logs/1-261022 chat_log.md
Закоммичены identity/domain/loading/KZ-LLM-judge.
Дальше: ручной прогон Jupyter; push только по просьбе.
Угадывание темы/релевантности — только LLM, не словари.
```
