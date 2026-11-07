# Задание для Cursor: пакет 7c — усиление course/outside + страховка

Один коммит, один пуш. Работай прямо в `main`. Тесты — в venv текущей машины
(`venv_W_L` на работе, `venv_H_L` дома). Секреты и ключи не трогать и не печатать.

## Зачем
После 7b вопрос «что такое pytorch» на уроке «Операторы и выражения» всё ещё
получил `Вопрос вне курса` и причину «…фокусируется на операторах и выражениях».
Промпт недостаточно сдерживает модель. Делаем два слоя:
1. жёстче промпт (библиотеки/фреймворки курса = course; в outside нельзя
   ссылаться на урок);
2. код-страховка: если модель всё же поставила `outside`, но в `reason`
   объясняет отказ темой урока — поднимаем до `course`.

Без списка «Python / PyTorch» в промпте: правило универсальное.

## Шаг 0
```
git status
git log -1 --oneline   # ожидается 527fc8e или новее
```

## Шаг 1. relevance_checker.py — system
Заменить system-сообщение в `check_question_relevance` на:
```
"Ты преподаватель этого курса. "
"scope=lesson — вопрос про материал этого урока. "
"scope=course — вопрос из предмета курса "
"(язык, библиотеки, фреймворки, инструменты курса), "
"даже если этот урок их не вводит: ответь. "
"scope=outside — только совсем другая область "
"(быт, спорт, погода). "
"Если в причине отказа хочется назвать тему урока — "
"это scope=course, не outside. "
"Отвечай только JSON."
```

## Шаг 2. relevance_checker.py — user-промпт
В `_build_relevance_prompt` заменить блок course/outside/«Не …» на:
```
scope=course — вопрос из предметной области этого курса,
но не из материала этого урока: другая тема курса; язык, библиотеки,
фреймворки и инструменты экосистемы курса; версии, новости и общие
факты о предмете курса. На такой вопрос отвечают.
reason — одна фраза, что это не тема текущего урока.

scope=outside — вопрос вне предмета курса целиком
(другая область: быт, спорт, погода и т.п.).
Только здесь отказ. reason — одно-два предложения ученику о том,
что вопрос вне предмета этого курса.
В reason для outside запрещено: «тема урока», «текущий урок»,
«рамки урока», название текущего урока. Если тянет объяснить отказ
через тему урока — поставь scope=course, а не outside.

Не пиши «не рассматривается в тексте», «отсутствует в материале».
Не ставь scope=course только потому, что вопрос «шире одной фразы» урока:
если ответ в основном опирается на материал этого урока — это scope=lesson.
Не ставь scope=outside только потому, что урок эту тему не вводит:
если вопрос всё ещё про предмет курса (включая его библиотеки
и инструменты) — это scope=course.
```

## Шаг 3. relevance_checker.py — страховка после разбора ответа
Сразу после:
```
result = self._extract_relevance_from_response(relevance_data)
```
добавить:
```
result = self._promote_outside_confused_with_lesson(
    result, lesson_title
)
```

Перед методом `_extract_relevance_from_response` добавить:
```
@staticmethod
def _promote_outside_confused_with_lesson(result, lesson_title):
    """Если модель поставила outside, но объясняет отказ темой урока —
    это путаница lesson/course: поднимаем до course.

    Промпт уже запрещает такие формулировки; страховка нужна, потому
    что модель всё равно иногда пишет «не относится к операторам…».
    """
    if not isinstance(result, dict) or result.get("scope") != "outside":
        return result
    reason = str(result.get("reason") or "").lower()
    title = str(lesson_title or "").strip().lower()
    markers = (
        "тем урока",
        "теме урока",
        "тему урока",
        "текущего урока",
        "текущем уроке",
        "текущий урок",
        "рамки урока",
        "рамках урока",
        "предмет урока",
        "фокусируется на",
    )
    confused = any(m in reason for m in markers)
    if title and len(title) >= 4 and title in reason:
        confused = True
    if not confused:
        return result
    fixed = dict(result)
    fixed["scope"] = "course"
    fixed["is_relevant"] = True
    fixed["on_lesson"] = False
    if not fixed.get("reason"):
        fixed["reason"] = "Это не тема текущего урока."
    return fixed
```

`tests/fake_llm.py` не менять: regex `scope=lesson — вопрос про материал этого урока` по-прежнему совпадает с новым system.

## Шаг 4. tests/legacy_checks/relevance_prompt_checks.py
Заменить блок assert'ов после `"в тексте или коде"` на:
```
    assert "в тексте или коде" in lowered
    assert "предметной области этого курса" in lowered
    assert "библиотеки" in lowered
    assert "фреймворки" in lowered
    assert "понятия, операторы, синтаксис" not in lowered
    assert "3.15" not in lowered
    assert "= и ==" not in lowered
    assert "вне предмета этого курса" in lowered
    assert "название текущего урока" in lowered
    assert "поставь scope=course" in lowered
    assert "включая его библиотеки" in lowered
```

## Шаг 5. Новый файл tests/unit/test_relevance_outside_guard.py
Создать файл целиком (см. прототип в задании ниже — три теста):
- причина про PyTorch + «фокусируется на операторах…» + title урока → course;
- причина про кашу без маркеров урока → outside;
- scope=course не трогаем.

Текст файла:
```python
"""Страховка: outside с причиной про урок → course."""

from relevance_checker import RelevanceChecker


def test_outside_reason_about_lesson_promoted_to_course():
    raw = {
        "scope": "outside",
        "is_relevant": False,
        "on_lesson": False,
        "confidence": 90,
        "reason": (
            "Ваш вопрос о PyTorch не относится к предмету курса, "
            "который фокусируется на операторах и выражениях в Python."
        ),
        "suggestions": [],
    }
    fixed = RelevanceChecker._promote_outside_confused_with_lesson(
        raw, "Операторы и выражения"
    )
    assert fixed["scope"] == "course"
    assert fixed["is_relevant"] is True
    assert fixed["on_lesson"] is False


def test_outside_reason_without_lesson_markers_stays_outside():
    raw = {
        "scope": "outside",
        "is_relevant": False,
        "on_lesson": False,
        "confidence": 90,
        "reason": "Вопрос про готовку каши вне предмета этого курса.",
        "suggestions": [],
    }
    fixed = RelevanceChecker._promote_outside_confused_with_lesson(
        raw, "Операторы и выражения"
    )
    assert fixed["scope"] == "outside"
    assert fixed["is_relevant"] is False


def test_course_untouched():
    raw = {
        "scope": "course",
        "is_relevant": True,
        "on_lesson": False,
        "confidence": 80,
        "reason": "Это не тема текущего урока.",
        "suggestions": [],
    }
    fixed = RelevanceChecker._promote_outside_confused_with_lesson(
        raw, "Операторы и выражения"
    )
    assert fixed is raw
```

## Шаг 6. Тесты
```
python -m pytest -q
```
Ожидается: **166 passed, 1 deselected** (было 163, +3 unit).

## Шаг 7. Коммит и пуш
```
git add relevance_checker.py tests/legacy_checks/relevance_prompt_checks.py tests/unit/test_relevance_outside_guard.py
git commit -m "7c: библиотеки курса = course; страховка от outside с причиной про урок"
bash .secrets/github_ssh/push_origin.sh
```
Не добавлять `TeachAI.ipynb`, `.bak`, сырые логи, файл этого задания.

## Отчёт
SHA, последняя строка pytest, отклонения.
