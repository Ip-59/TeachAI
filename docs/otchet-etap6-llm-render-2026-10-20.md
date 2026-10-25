# Мини-отчёт: этап 6 — канон вывода LLM (6A + узкий 6B)

**Дата:** 2026-10-20  
**План:** `docs/razgovor-2026-10-19-kurator-dorabotki-plan-konspekt.md` (этап 6 / п.4 куратора)

---

## Что сделано (и почему не весь 6B)

Куратор просил «нормальный вывод ответов LLM». Канон рендера уже жил в `content_renderer.py`, но экраны его обходили:

- `lesson_display` **срезал все \`\`\`**, если кэш не в `<div class="lesson-content">`;
- `clean_markdown_code_blocks` снимал **все** fences, не только внешнюю обёртку;
- Q&A клал сырой markdown в `widgets.HTML`;
- форматтер выкидывал пустые строки в коде и ставил язык `python` на безымянный fence.

**6A:** один вход `student_content.render_student_content()`.  
**6B в этом коммите:** промпты урока/Q&A/объяснений — Markdown, не оборачивать весь ответ в fence, язык кода = язык темы (не «это курс Python»).

**Не делал** `json_schema` на все генераторы: план курса уже `json_object`; schema на GPTunnel не проверяли; это отдельный риск и отдельная проверка. `make_api_request(..., response_format=)` уже есть.

Заглушек нет. React не подключался.

---

## Как проверить

1. Restart kernel. Открыть **уже сгенерированный** урок — код с отступами, без сырых \`\`\` на экране.
2. Новый урок (лучше не-Python тема): блоки кода с языком темы, не принудительный Python.
3. «Объяснить подробнее» / «Задать вопрос»: заголовки, списки, код как у урока (светлый pre, не «зелёный терминал»).
4. КЗ: описание/комментарий LLM читаются как текст, не как сырой markdown.

Кэш старых уроков с поломанными CODE_BLOCK_ пересобирается из `raw_content`.

---

## Автопроверка

```text
venv_H_L/bin/python student_content_checks.py
```

---

## Изменённые файлы

| Файл | Роль |
|------|------|
| `student_content.py` | канон `render_student_content` / `unwrap_outer_fence` |
| `student_content_checks.py` | проверки без Jupyter |
| `content_formatter_final.py` | тонкий: fences + markdown, пустые строки кода |
| `lesson_display.py` | без срезания \`\`\` |
| `explanation_generator.py`, `qa_generator.py`, `concepts_generator.py` | канон + Markdown-промпт |
| `lesson_generator.py` | промпт без «это курс Python» |
| `content_utils.py` | `clean_markdown_code_blocks` только внешний fence |
| `examples_display.py`, `control_tasks_interface.py` | описание/feedback через канон |
| `run_teachai.py` | reload |
| `ОПИСАНИЕ_ПРОЕКТА_TEACHAI.md`, `DESCRIPTION.md` | гибрид Markdown + structured (план/тест как были) |

---

## По-прежнему отложено

- Наслоение экранов / тройной loader.
- Кнопка «Показать дашборд» после КЗ.
- `json_schema` на план/тест/примеры/КЗ (6B-остаток).
- `format_gate` бенчмарка по-прежнему требует \`\`\`python — это про Python-уроки бенчмарка, не про швейный курс.

---

## Критерий этапа

Урок / объяснение / Q&A / примеры / КЗ идут в один HTML-пайплайн с кодом и отступами. Полный rewrite генераторов на schema — нет, и это сознательно.
