# Задание для Cursor: пакет 7 — текст отказа на вопрос вне курса

Один коммит, один пуш. Работай прямо в `main`. Тесты запускай в venv текущей машины
(`venv_W_L` на работе, `venv_H_L` дома). Секреты и ключи не трогать и не печатать.

## Зачем
На вопрос «как сварить кашу» плашка показывает:
- «Это **уже** 1-й вопрос…» — «уже» на первом вопросе звучит странно;
- причину от модели «не относится к теме урока по гистограмме», хотя заголовок
  «Вопрос вне курса». Для scope=outside причина должна говорить про курс, а не про урок.

Классификация lesson / course / outside уже есть и работает; меняем только тексты.

## Шаг 0. Проверка старта
```
git status        # чисто (не считая неотслеживаемых логов/bak)
git log -1 --oneline   # efb533a или новее
```

## Шаг 1. lesson_interaction.py (около строки 469)
Было:
```
<p>Это уже {n}-й вопрос не в тему урока и не в тему курса.</p>
```
Стало:
```
<p>Это {n}-й вопрос не в тему урока и не в тему курса.</p>
```
Больше в файле ничего не менять.

## Шаг 2. relevance_checker.py, промпт (блок «scope=outside», около строки 388)
Было:
```
scope=outside — вопрос вне курса.
Только здесь отказ. reason — одно-два предложения ученику.
```
Стало:
```
scope=outside — вопрос вне курса.
Только здесь отказ. reason — одно-два предложения ученику о том,
что вопрос вне тем курса (Python, данные, машинное обучение).
Для scope=outside не пиши, что вопрос «не относится к теме урока»:
он не относится к курсу целиком.
```
Остальной промпт (scope=lesson, scope=course, JSON) не трогать.

## Шаг 3. tests/legacy_checks/relevance_prompt_checks.py
После строки `assert "= и ==" not in lowered` добавить:
```
    assert "вне тем курса" in lowered
    assert "не относится к курсу целиком" in lowered
```

## Шаг 4. tests/scenario/test_flow_core.py, тест test_LSN_10_outside_question_not_counted_as_answered
После строки `assert lesson.state()["learning"]["offtopic_count"].get(L1, 0) == 1` добавить:
```
    page = " ".join(lesson.html_texts())
    assert "Вопрос вне курса" in page
    assert "Это 1-й вопрос не в тему" in page
    assert "Это уже" not in page
```

## Шаг 5. Тесты
```
python -m pytest -q
```
Ожидается: **163 passed, 1 deselected** (число тестов не меняется, добавлены только assert).

## Шаг 6. Коммит и пуш
```
git add lesson_interaction.py relevance_checker.py tests/legacy_checks/relevance_prompt_checks.py tests/scenario/test_flow_core.py
git commit -m "7: отказ вне курса — без «уже», причина про курс, а не урок"
bash .secrets/github_ssh/push_origin.sh
```
Не добавлять `TeachAI.ipynb` с выводами, `.bak`, сырые логи.

## Отчёт
SHA коммита, вывод последней строки pytest, отклонения от задания (если были).
