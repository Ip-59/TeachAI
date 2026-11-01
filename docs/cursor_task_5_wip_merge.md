# Задача для Cursor: пакет 5 — довести WIP judge/время/результат и влить в main

Скопируй файл целиком в чат Cursor. Исполнитель — Cursor-агент в проекте TeachAI на локальном компьютере.

**Ветка работы:** `wip/judge-time-result` (уже на GitHub, коммит **`e7b6a73`**, база **`bf0d467`** / `origin/main`).
Не создавай новую ветку от main — этапы 0/5а/5б/5в делай **на `wip/judge-time-result`**, в конце 5в — обычный merge в `main` (fast-forward или merge-commit). Без rebase и force-push.

Все правки ниже **проверены в прототипе** на копии `e7b6a73` (Linux, Python 3.13, venv_box):

| После этапа | Ожидаемый полный `python -m pytest -q` |
|---|---|
| старт `e7b6a73` | `4 failed, 118 passed, 1 deselected, 21 errors` (все про «Общее время») |
| **0** | scenario ещё red; **+4 unit** `test_check_secrets` → ориентир `122 passed, 4 failed, 21 errors, 1 deselected` |
| **5а** | **`147 passed, 1 deselected`** |
| **5б** | **`154 passed, 1 deselected`** |
| **5в** | тот же зелёный набор; merge в `main` |

Номера строк правок сценариев — по **`e7b6a73`**. Если контекст не совпал — **остановись и напиши**, не подгоняй.

---

## 0. Жёсткие правила

1. Менять только то, что описано в текущем этапе. Без «заодно»-рефакторинга.
2. **Не трогать** `content_utils.py`, `data/`, `.env`, `.env.sample`. Никогда не печатать и не echo **OPENAI_API_KEY** и любые секреты. В тестах — только `sk-test-not-a-real-key`.
3. **Один этап — один коммит — один push** в `origin/wip/judge-time-result` (этап 5в дополнительно пушит `main`). Сообщения коммитов — по-русски.
4. Venv **текущей** машины: `venv_W_L` или `venv_H_L`. Прогон: `python -m pytest -q -rx`.
5. **Не** `git push --force`, **не** rewrite history (`rebase -i`, `commit --amend` уже запушенного).
6. Новых `xfail`/`skip` без согласования не добавлять.
7. После прогона `git status` чист от `data/`, `.env`. В индекс **не** класть `*.bak_*`, `docs/chat_logs/raw/`, `docs/Grok_bot_chat.txt`.
8. Удаление remote `wip/judge-time-result` — **только после явного «да» от Игоря**.

---

## 1. Что уже в WIP и зачем пакет 5

В `e7b6a73` уже есть (не откатывать): судья КЗ, время на курс, блок «Результат запуска» в `examples_display.py`.

Красный pytest: сценарии ищут «Общее время» на профиле, а слайдеры на экране курса — **«Общее время курса (часов):»**, **«Длительность занятия (минут):»**.

Пакет 5: гигиена → починить scenario → фиксы → notebook + merge.

---

## 2. Состав этапов

| Этап | Что | Pytest |
|---|---|---|
| **0** | gitignore, docs, check_secrets + hooks, README «сохрани чат» | secrets unit OK; scenario red |
| **5а** | scenario + `helpers.start_catalog_course` | **147 passed, 1 deselected** |
| **5б** | annotation, schedule_of fallback, validate профиля, NameError hint | **154 passed, 1 deselected** |
| **5в** | чистый notebook, якорь scenarios.md, merge→main | зелёный; wip remote не удалять без Игоря |

---

## ЭТАП 0. Гигиена и проверка секретов

### A. Ветка

```bash
git fetch origin
git switch wip/judge-time-result
git log -1 --oneline   # ожидается e7b6a73 или коммиты только этого пакета поверх него
```

### B. В конец `.gitignore` добавить

```
# Резервные копии и сырые логи чатов (md-логи коммитим выборочно)
*.bak_*
docs/chat_logs/raw/
docs/Grok_bot_chat.txt
```

### C. Создать файлы

**`scripts/__init__.py`** — пустой.

**`scripts/check_secrets.py`** (целиком; затем `chmod +x scripts/check_secrets.py`):

```python
#!/usr/bin/env python3
"""Проверка staged-диффа на секреты (OpenAI-ключ и присваивание OPENAI_API_KEY).

Запуск вручную:
  python scripts/check_secrets.py
  git diff --cached -U0 | python scripts/check_secrets.py --stdin

Хук (на каждой машине один раз):
  git config core.hooksPath hooks
  # файл hooks/pre-commit уже вызывает этот скрипт
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from typing import Iterable, List, Tuple

OPENAI_KEY_RE = re.compile(r"sk-[A-Za-z0-9_-]{20,}")
OPENAI_ASSIGN_RE = re.compile(
    r"(?i)\bOPENAI_API_KEY\s*=\s*['\"][^'\"]+['\"]"
)

ALLOWED_FRAGMENTS = (
    "sk-test-not-a-real-key",
)


def iter_added_lines(diff_text: str) -> Iterable[Tuple[str, str]]:
    """Из unified diff берёт только добавленные строки (+), не +++."""
    path = ""
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            continue
        if line.startswith("+") and not line.startswith("+++"):
            yield path, line[1:]


def find_secret_hits(diff_text: str) -> List[str]:
    hits: List[str] = []
    for path, content in iter_added_lines(diff_text):
        if any(frag in content for frag in ALLOWED_FRAGMENTS):
            continue
        if OPENAI_KEY_RE.search(content):
            hits.append(f"{path}: похоже на OpenAI-ключ в добавленной строке")
        if OPENAI_ASSIGN_RE.search(content):
            hits.append(f"{path}: присваивание литерала OPENAI_API_KEY=...")
    seen: set[str] = set()
    out: List[str] = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def staged_diff() -> str:
    proc = subprocess.run(
        ["git", "diff", "--cached", "-U0"],
        check=False,
        capture_output=True,
        text=True,
    )
    return proc.stdout or ""


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="читать unified diff из stdin вместо git diff --cached",
    )
    args = parser.parse_args(argv)
    diff = sys.stdin.read() if args.stdin else staged_diff()
    hits = find_secret_hits(diff)
    if hits:
        sys.stderr.write(
            "check_secrets: отказ — в индексе есть похожие на секреты строки:\n"
        )
        for h in hits:
            sys.stderr.write(f"  - {h}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

**`hooks/pre-commit`** (затем `chmod +x hooks/pre-commit`):

```bash
#!/usr/bin/env bash
# Отклоняет commit, если в индексе есть похожие на секреты строки.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
exec python "$ROOT/scripts/check_secrets.py"

```

**`tests/unit/test_check_secrets.py`**:

```python
"""Проверка pre-commit скрипта на секреты."""
import pytest

pytestmark = pytest.mark.unit


def _diff(path: str, added: str) -> str:
    return (
        f"diff --git a/{path} b/{path}\n"
        f"--- a/{path}\n"
        f"+++ b/{path}\n"
        f"@@ -0,0 +1,1 @@\n"
        f"+{added}\n"
    )


def test_check_secrets_rejects_openai_key_pattern():
    from scripts.check_secrets import find_secret_hits

    fake = "sk-" + ("a" * 24)
    hits = find_secret_hits(_diff("foo.py", f"KEY = {fake!r}"))
    assert hits and "OpenAI" in hits[0]


def test_check_secrets_rejects_openai_api_key_assignment():
    from scripts.check_secrets import find_secret_hits

    # Конкатенация: иначе сам этот файл в staged-диффе ловит хук.
    payload = "OPENAI_API_" + 'KEY="literally-any-value-here"'
    hits = find_secret_hits(_diff("cfg.py", payload))
    assert any("OPENAI_API_KEY" in h for h in hits)


def test_check_secrets_allows_test_fake_key():
    from scripts.check_secrets import find_secret_hits

    hits = find_secret_hits(
        _diff("tests/unit/x.py", 'ContentGenerator("sk-test-not-a-real-key")')
    )
    assert hits == []


def test_check_secrets_clean_diff():
    from scripts.check_secrets import find_secret_hits

    assert find_secret_hits(_diff("a.py", "x = 1")) == []

```

**`docs/chat_logs/README.md`**:

```markdown
# Логи чатов с агентом

В конце **каждой** сессии Cursor:

1. Попроси агента: **«сохрани чат»** (итог сессии в `docs/chat_logs/`).
2. В начале файла держи блок **«Итог»** — коротко: что сделали, какие коммиты, что осталось.
3. Закоммить `.md` лог **вместе с кодом** этой сессии (один или соседний коммит).

Не коммить:

- `docs/chat_logs/raw/` — сырые jsonl (в `.gitignore`);
- `docs/Grok_bot_chat.txt`;
- `*.bak_*`.

Перед пушем сработает хук `hooks/pre-commit` → `scripts/check_secrets.py` (см. этап 0 пакета 5).

```

### D. Индекс (выборочно)

```bash
git add .gitignore scripts/__init__.py scripts/check_secrets.py hooks/pre-commit \
  tests/unit/test_check_secrets.py docs/chat_logs/README.md
git add docs/chat_logs/*.md
git add docs/cursor_task_*.md 2>/dev/null || true
git status
# В индексе НЕ должно быть: raw/, *.bak_*, docs/Grok_bot_chat.txt
```

Имена с пробелами — добавляй в кавычках по одному, если glob не сработал.

### E. Хук на машине (результат `git config` не коммитить)

```bash
git config core.hooksPath hooks
python scripts/check_secrets.py; echo exit:$?
```

На второй машине после pull — тот же `git config core.hooksPath hooks`.

### F. Тесты, коммит, push

```bash
python -m pytest tests/unit/test_check_secrets.py -q
python -m pytest -q -rx
git commit -m "Гигиена: gitignore для raw/bak, проверка секретов в pre-commit, логи чатов"
git push -u origin wip/judge-time-result
```

**Ожидание:** 4 secrets unit passed; полный прогон — те же ошибки «нет поля Общее время», плюс 4 новых passed.

**Отчёт:** SHA, краткий pytest, `git status`, подтверждение что raw/bak не в коммите.

---

## ЭТАП 5а. Scenario под новый UI

### Контекст на `e7b6a73`

| Файл | Строки | Было |
|---|---|---|
| `tests/scenario/conftest.py` | 20–23 | `Общее время` / `Длительность урока` до «Сохранить» |
| `tests/scenario/test_flow_core.py` | 41–42 | то же в `test_ZAP_01_no_debug_output_on_course_start` |
| `tests/scenario/test_flow_core.py` | 139–144 | то же в `_start_custom_out_of_domain` |
| `tests/scenario/test_followup_flow.py` | 14–18 | то же в `_open_first_lesson` |

После правок: `rg 'Общее время"|Длительность урока' tests/scenario` → пусто.

### A. В конец `tests/helpers.py` добавить

```python
def start_catalog_course(nb, *, name="Тест", hours=3, minutes=30):
    """Профиль (имя) -> экран курса (часы/занятие) -> «Начать курс».

    Время больше не на форме профиля: слайдеры на экране выбора курса.
    Подстроки description: «Общее время курса (часов):», «Длительность занятия (минут):».
    """
    nb.set_value("Имя", name)
    nb.click("Сохранить настройки")
    nb.set_value("Общее время курса", hours)
    nb.set_value("Длительность занятия", minutes)
    nb.click("Начать курс")
```

### B. `tests/scenario/conftest.py`

Заменить содержимое файла так:

- `from helpers import start_catalog_course`
- фикстура `nb` — без изменений по смыслу
- фикстура `lesson`: `nb.start_teachai()` затем `start_catalog_course(nb)` (без `set_value` времени на профиле)

### C. `tests/scenario/test_flow_core.py`

**`test_ZAP_01_no_debug_output_on_course_start`** — тело:

```python
def test_ZAP_01_no_debug_output_on_course_start(nb):
    nb.start_teachai()
    nb.set_value("Имя", "Тест")
    out = nb.click("Сохранить настройки")
    nb.set_value("Общее время курса", 3)
    nb.set_value("Длительность занятия", 30)
    out = out + nb.click("Начать курс")
    assert "ОТЛАДКА" not in out
    assert "Ключи" not in out
```

**`_start_custom_out_of_domain`**:

```python
def _start_custom_out_of_domain(nb):
    nb.start_teachai()
    nb.set_value("Имя", "Тест")
    nb.click("Сохранить настройки")
    nb.choose("Своё название курса")
    nb.llm_use("domain", "domain_out")
    nb.set_value("Название", "Курс кройки и шитья")
    nb.set_value("Общее время курса", 3)
    nb.set_value("Длительность занятия", 30)
    nb.click("Начать курс")
```

### D. `tests/scenario/test_followup_flow.py`

```python
def _open_first_lesson(nb: NotebookSession) -> None:
    from helpers import start_catalog_course

    nb.start_teachai()
    start_catalog_course(nb)
```

### E. Тесты, коммит, push

```bash
python -m pytest -q -rx
git add tests/helpers.py tests/scenario/conftest.py \
  tests/scenario/test_flow_core.py tests/scenario/test_followup_flow.py
git commit -m "Сценарии: время курса задаётся на экране выбора курса"
git push origin wip/judge-time-result
```

**Ожидание:** `147 passed, 1 deselected`.

**Отчёт:** SHA, pytest summary.

---

## ЭТАП 5б. Фиксы

### A. Annotation

В `control_tasks_generator.py` у `_task_matches_subject`: `) -> bool:` заменить на `) -> tuple[bool, str]:`.

### B. Fallback `schedule_of` (старые планы)

**Решение:** минуты = поле плана или длительность первого урока или 30; часы = поле плана или `max(1, total_duration_minutes // 60)`; иначе `None` (UI уже умеет текст без цифр).

В `course_portfolio.py` заменить `schedule_of` / `active_lesson_duration_minutes` и добавить хелпер — целиком:

```python
def _first_lesson_duration_minutes(plan: dict) -> int | None:
    """Длительность первого урока в плане — запасной источник для старых слотов."""
    for section in plan.get("sections") or []:
        for topic in section.get("topics") or []:
            for lesson in topic.get("lessons") or []:
                minutes = lesson.get("duration_minutes")
                if minutes:
                    return int(minutes)
    return None


def schedule_of(state: dict, course_id: str) -> dict[str, int] | None:
    """Часы и длительность занятия, сохранённые в слоте этого курса.

    Для планов до поля total_study_hours / lesson_duration_minutes:
    часы = total_duration_minutes // 60 (минимум 1, если total > 0),
    минуты занятия = lesson_duration_minutes или длительность первого урока
    или 30. Если восстановить нельзя — None (UI пишет «не задано»).
    """
    slot = (state.get("courses") or {}).get(course_id) or {}
    plan = slot.get("course_plan") or {}
    hours = plan.get("total_study_hours")
    minutes = plan.get("lesson_duration_minutes")

    if not minutes:
        minutes = _first_lesson_duration_minutes(plan) or 30
    else:
        minutes = int(minutes)

    if not hours:
        total_mins = plan.get("total_duration_minutes")
        if total_mins:
            hours = max(1, int(total_mins) // 60)
        else:
            return None
    else:
        hours = int(hours)

    return {
        "total_study_hours": hours,
        "lesson_duration_minutes": int(minutes),
    }


def active_lesson_duration_minutes(state: dict) -> int:
    """Длительность занятия активного курса, не общая настройка профиля."""
    plan = state.get("course_plan") or {}
    minutes = plan.get("lesson_duration_minutes")
    if minutes:
        return int(minutes)
    inferred = _first_lesson_duration_minutes(plan)
    if inferred:
        return inferred
    user = state.get("user") or {}
    return int(user.get("lesson_duration_minutes") or 30)

```

### C. `validate_user_profile`

В `user_profile_manager.py` заменить блок обязательных полей и проверок `> 0` на:

```python
            # Имя и стиль — общие. Часы и длительность занятия задаются
            # на экране курса и в профиле могут быть 0.
            required_fields = {
                "name": str,
                "communication_style": str,
            }

            for field, field_type in required_fields.items():
                value = profile.get(field)
                if value is None or value == "" or not isinstance(value, field_type):
                    missing_fields.append(field)

            valid_styles = ["formal", "friendly", "casual", "brief"]
            if profile.get("communication_style") not in valid_styles:
                missing_fields.append(
                    f"communication_style (должно быть одно из: {valid_styles})"
                )

            is_valid = len(missing_fields) == 0

```

Дальше `valid_styles` и `return` — без изменений. Часы/минуты в профиле могут быть 0.

### D. Подсказка NameError

**Единое место:** хелперы в `code_sandbox.py`. Сайты показа вызывают их. В промпт судьи / generator hint не вшивать.

Вставить **перед** `def choose_timeout` в `code_sandbox.py`:

```python
NAME_ERROR_HINT_RU = (
    "Каждый запуск выполняется с нуля: переменные из прошлых запусков "
    "не сохраняются. Вставьте в ячейку весь нужный код."
)


def name_error_student_hint(error: str | None) -> str:
    """Подсказка ученику при NameError; иначе пустая строка.

    Идемпотентно: если подсказка уже есть в тексте, не возвращаем её снова.
    """
    text = (error or "").strip()
    if not text or NAME_ERROR_HINT_RU in text:
        return ""
    first = text.splitlines()[0].strip()
    if first.startswith("NameError:") or first == "NameError":
        return NAME_ERROR_HINT_RU
    return ""


def with_name_error_hint(error: str) -> str:
    """Текст ошибки + подсказка (для print / plain)."""
    hint = name_error_student_hint(error)
    if not hint:
        return error
    return f"{error}\n\n{hint}"


def format_execution_error_html(error: str) -> str:
    """HTML ошибки выполнения: текст + серая подсказка при NameError.

    Единая точка для всех сайтов показа (КЗ, примеры, ячейки).
    """
    import html as html_module

    body = html_module.escape(error or "")
    hint = name_error_student_hint(error)
    parts = [
        "<pre style='white-space:pre-wrap;margin:8px 0;color:#721c24;'>"
        f"{body}</pre>"
    ]
    if hint:
        parts.append(
            "<p style='color:#6c757d;margin:0 0 8px 0;font-size:14px;line-height:1.45;'>"
            f"{html_module.escape(hint)}</p>"
        )
    return "".join(parts)

```

Подключить:

1. `control_tasks_interface.py` — оба пути ошибки кнопки выполнения кода: `format_execution_error_html(msg)` под заголовком «Ошибка выполнения».
2. `examples_display.py` — оба пути ошибки fallback-виджета: внутри «Результат запуска» вызвать `format_execution_error_html(...)`.
3. `cell_widget_base.py` — при fail вернуть `with_name_error_hint(...)`.
4. `interactive_cell_logic.py` — при fail/timeout обернуть msg в `with_name_error_hint(...)`.

Текст: «Каждый запуск выполняется с нуля: переменные из прошлых запусков не сохраняются. Вставьте в ячейку весь нужный код.» В HTML — цвет `#6c757d`.

### E. Unit-тесты

В конец `tests/unit/test_code_sandbox.py`:

```python
def test_name_error_hint_for_student():
    from code_sandbox import (
        NAME_ERROR_HINT_RU,
        format_execution_error_html,
        name_error_student_hint,
        with_name_error_hint,
    )

    msg = "NameError: name 'my_var' is not defined"
    assert name_error_student_hint(msg) == NAME_ERROR_HINT_RU
    assert "с нуля" in with_name_error_hint(msg)
    assert name_error_student_hint("ValueError: x") == ""
    html = format_execution_error_html(msg)
    assert "#6c757d" in html
    assert "my_var" in html
    assert NAME_ERROR_HINT_RU in html
    # идемпотентность
    assert name_error_student_hint(with_name_error_hint(msg)) == ""

```

Новый файл `tests/unit/test_course_schedule.py`:

```python
"""Время курса в слоте плана; профиль без обязательных часов."""
import pytest

pytestmark = pytest.mark.unit


def test_schedule_of_reads_explicit_fields():
    from course_portfolio import schedule_of

    state = {
        "courses": {
            "c1": {
                "course_plan": {
                    "total_study_hours": 4,
                    "lesson_duration_minutes": 20,
                    "total_duration_minutes": 240,
                }
            }
        }
    }
    assert schedule_of(state, "c1") == {
        "total_study_hours": 4,
        "lesson_duration_minutes": 20,
    }


def test_schedule_of_fallback_from_total_duration_and_lesson():
    from course_portfolio import schedule_of

    state = {
        "courses": {
            "old": {
                "course_plan": {
                    "total_duration_minutes": 180,
                    "sections": [
                        {
                            "topics": [
                                {"lessons": [{"duration_minutes": 45}]}
                            ]
                        }
                    ],
                }
            }
        }
    }
    assert schedule_of(state, "old") == {
        "total_study_hours": 3,
        "lesson_duration_minutes": 45,
    }


def test_schedule_of_fallback_default_lesson_30():
    from course_portfolio import schedule_of

    state = {
        "courses": {
            "old": {"course_plan": {"total_duration_minutes": 60}}
        }
    }
    assert schedule_of(state, "old") == {
        "total_study_hours": 1,
        "lesson_duration_minutes": 30,
    }


def test_schedule_of_none_without_hours_source():
    from course_portfolio import schedule_of

    state = {"courses": {"x": {"course_plan": {"sections": []}}}}
    assert schedule_of(state, "x") is None
    assert schedule_of(state, "missing") is None


def test_validate_user_profile_allows_zero_course_time():
    from state_manager import StateManager

    sm = StateManager()
    sm.state["user"]["name"] = "Тест"
    sm.state["user"]["communication_style"] = "friendly"
    sm.state["user"]["total_study_hours"] = 0
    sm.state["user"]["lesson_duration_minutes"] = 0
    ok, missing = sm.user_profile.validate_user_profile()
    assert ok is True
    assert missing == []


def test_validate_user_profile_still_requires_name():
    from state_manager import StateManager

    sm = StateManager()
    sm.state["user"]["name"] = ""
    sm.state["user"]["communication_style"] = "friendly"
    ok, missing = sm.user_profile.validate_user_profile()
    assert ok is False
    assert "name" in missing

```

### F. Тесты, коммит, push

```bash
python -m pytest -q -rx
git add control_tasks_generator.py course_portfolio.py user_profile_manager.py \
  code_sandbox.py control_tasks_interface.py examples_display.py \
  cell_widget_base.py interactive_cell_logic.py \
  tests/unit/test_code_sandbox.py tests/unit/test_course_schedule.py
git commit -m "Фиксы: schedule старых планов, профиль без часов, подсказка NameError"
git push origin wip/judge-time-result
```

**Ожидание:** `154 passed, 1 deselected`.

**Отчёт:** SHA, pytest summary.

---

## ЭТАП 5в. Notebook, якорь docs, merge в main

### A. `TeachAI.ipynb`

```bash
git checkout origin/main -- TeachAI.ipynb
```

Так получаем `execution_count: null`, пустые `outputs`, kernelspec как на main (`display_name: venv_W_L`). Не подставлять `venv_H_L` «для дома».

### B. Якорь в `docs/TeachAI_test_scenarios.md`

Строку **Основа:** с `66ae024` заменить на:

`**Основа:** код после пакета 5 (ветка wip/judge-time-result, merge в main; база WIP e7b6a73 на bf0d467). Решения D1–D9 от 27.10.2026 — в разделе ниже.`

Таблицы сценариев в этом этапе не переписывать.

### C. Коммит на wip

```bash
python -m pytest -q -rx
git add TeachAI.ipynb docs/TeachAI_test_scenarios.md
git commit -m "Notebook без output; актуальный якорь в scenarios.md"
git push origin wip/judge-time-result
```

Ожидание: **`154 passed, 1 deselected`**.

### D. Merge в main

```bash
git switch main
git pull origin main
git merge --no-ff wip/judge-time-result -m "Merge branch 'wip/judge-time-result' — пакет 5 (judge, время курса, результат запуска)"
python -m pytest -q -rx
git push origin main
```

Fast-forward тоже допустим. **Не** force-push.

### E. Remote wip не удалять

Команду только показать Игорю, не выполнять без его «да»:

```bash
# НЕ ЗАПУСКАТЬ без явного согласия:
# git push origin --delete wip/judge-time-result
```

**Отчёт 5в:** SHA на main, pytest на main, remote wip ещё существует.

---

## Чеклист приёмки пакета 5

- [ ] `scripts/check_secrets.py` + `hooks/pre-commit`; на машине `core.hooksPath=hooks`
- [ ] raw/bak/Grok_bot_chat не в git; md-логи и `docs/cursor_task_*.md` — да (если были на диске)
- [ ] Полный pytest на main: **154 passed, 1 deselected**
- [ ] По желанию: NameError → серая подсказка; новый курс → слайдеры на экране курса; «Продолжить» без слайдеров
- [ ] Remote `wip/judge-time-result` жив, пока Игорь не подтвердит удаление
