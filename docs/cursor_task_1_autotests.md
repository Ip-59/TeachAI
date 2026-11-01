# Задача для Cursor: пакет 1 — автотесты TeachAI на текущее поведение

Скопируй этот файл целиком в чат Cursor (или положи в проект и сделай `@`-ссылку). Исполнитель — Cursor-агент в проекте TeachAI на локальном компьютере. Всё нужное для работы написано ниже; код стенда **проверен в прототипе** (Linux, Python 3.13, ipykernel/ipywidgets/openai последних версий): эталонный набор давал `64 passed, 1 skipped, 23 xfailed` примерно за 60 секунд. Нужно воспроизвести его в проекте, не меняя код приложения.

## 0. Жёсткие правила

1. **Код приложения не менять.** Ни один существующий `*.py`, `TeachAI.ipynb`, `courses.json`, `requirements.txt` не правится. Допустимо менять только: добавить `tests/`, `pytest.ini`, `requirements-dev.txt`, и поправить `.gitignore` (п. 2).
2. **Не делать `git push`, не коммитить без моей команды.** Результат — файлы в рабочей папке; показать `git status`.
3. **Реальный ключ и сеть не нужны и не используются.** Везде фальшивый ключ `sk-test-not-a-real-key`. Не печатать, не читать и не копировать мой настоящий `.env`.
4. **Тесты не трогают реальные `data/`, `logs/`, `.env`, `.env.sample`** проекта (см. п. 1 «как изолируем»; в `conftest.py` есть страховка).
5. Известные баги **не чинить**, а фиксировать тестом `xfail(strict=True, raises=AssertionError, reason="<ID сценария>: <суть бага (файл:строка)>")`. Так, когда баг будет исправлен, тест покраснеет и подскажет снять `xfail`. `raises=AssertionError` обязателен: иначе `xfail` скроет посторонние ошибки стенда (опечатку, `KeyError`). Поэтому в `xfail`-тестах проверки пишутся через `assert` и `.get(...)`, а не через прямое индексирование.
6. Тест, который при падении зависнет (бесконечный цикл), нельзя оставлять даже как `xfail`: ставь `@pytest.mark.skip(reason=...)` (пример: `KZ-16`).
7. Если что-то из описанного ниже не сходится с кодом (другая строка, другое имя), **остановиться и написать, что именно не сходится**, а не подгонять тест под баг.

## 1. Что выяснено про код (проверено чтением и прогоном)

**Единственная точка подмены LLM.** Все генераторы наследуют `ContentBase` из `content_utils.py` и создают клиента в `ContentBase.__init__` строкой `self.client, self.http_client, self.llm_meta = create_openai_client(...)` (`content_utils.py:272`; имя импортировано в `content_utils.py:13` из `llm_route.py:225`). Все запросы идут через `ContentBase.make_api_request` → `self.client.chat.completions.create(**kwargs)` (`content_utils.py:~582`). Поэтому тест подменяет **`content_utils.create_openai_client`** и возвращает клиент с методом `chat.completions.create(**kwargs)`, отдающий объект с `.choices[0].message.content`. `self.http_client` нигде больше не используется, ему можно давать `None`. Подмена на уровне `llm_route` не годится: `content_utils` держит свою ссылку на имя.

**Ответ определяется по типу запроса.** Типов 16, различаются по system-сообщению (и, для двух классификаторов, по user-сообщению): таблица `RULES` в `fake_llm.py` ниже. Если правило не нашлось или нет фикстуры, стенд пишет «ошибку стенда» в журнал и бросает исключение: приложение глотает такие исключения, поэтому в фикстуре `nb` на выходе проверяется, что ошибок стенда не было.

**Изоляция состояния.** Одного `chdir` во временную папку недостаточно:
- `StateManager` строит путь как `<папка модуля state_manager.py>/<state_file>` (`state_manager.py:30-31`). Абсолютный `state_file` обходит это (`Path / абсолютный путь` = абсолютный путь). Поэтому в unit-тестах подменяется значение аргумента по умолчанию: `monkeypatch.setattr(StateManager.__init__, "__defaults__", (<abs path>,))`.
- `engine.py:126,285,334` создаёт `StateManager()` без аргументов, поэтому сценарные тесты работают в **копии проекта** (все `*.py`, `courses.json`, `TeachAI.ipynb`) во временной папке: ядро запускается с рабочей папкой = копия, `from run_teachai import start_jupyter` импортируется оттуда.
- Копия нужна ещё и потому, что `run_teachai.start_jupyter` делает `load_dotenv(override=True)` (`run_teachai.py:90`): `find_dotenv` ищет `.env` рядом с `run_teachai.py`, то есть нашёл бы **настоящий** `.env` проекта и перезаписал бы им переменные. В копии лежит только фальшивый `.env`.
- Относительные пути (`logs/`, `data/llm_route_preference.json` — `llm_route.py:24`, `debug_responses/`) изолируются через `chdir`.
- `ConfigManager.ensure_directories` создаёт `logs/` и `data/` рядом с модулем (`config.py:201-206`): в реальной папке проекта могут появиться пустые каталоги, это безвредно (они в `.gitignore`).
- Тесты меняют `os.environ` (`set_llm_route` пишет `OPENAI_API_ROUTE`, чистит прокси-переменные, `llm_route.py:~100`): поэтому только `monkeypatch.setenv/delenv`.

**Управление ядром.** Нужно нажимать кнопки между ячейками, а `nbclient.NotebookClient.execute()` выполняет ячейки пакетом. Поэтому интерактивные сценарии идут через `jupyter_client` (запуск ядра, `execute`, чтение `stdout`), а виджеты находятся и нажимаются через реестр `ipywidgets.Widget.widgets` внутри ядра (`.click()`, `.value = …`). `nbclient` используется для одного smoke-теста всего ноутбука. Известная хрупкость: «старые» виджеты после `clear_output` остаются в реестре, поэтому хелперы по умолчанию берут **последнюю созданную** подходящую кнопку/поле и пропускают скрытые (`layout.display == 'none'`). Если когда-нибудь это начнёт ломаться, запасной вариант — вызывать интерфейсные объекты напрямую в процессе pytest; но `display()`/`clear_output()` без ядра ничего не показывают, поэтому основной путь именно через ядро.

**Варианты в тесте перемешаны** (`assessment_generator._force_randomize_questions`): верный ответ в тесте выбирается по тексту варианта (`верно N` / `неверно N…`), а не по номеру.

**`.gitignore` блокирует тесты.** Строка `tests/` (`.gitignore:35`) и строка `*.json` (с белым списком исключений) спрячут и `tests/`, и фикстуры `tests/fixtures/llm/*.json`. Нужно: удалить строку `tests/` и добавить после блока исключений для JSON строку `!tests/fixtures/llm/*.json`. Проверить: `git status` показывает `tests/` и файлы фикстур как неотслеживаемые, а не игнорируемые (`git check-ignore -v tests/fixtures/llm/plan.json` ничего не выводит).

## 2. Что создать

```
pytest.ini
requirements-dev.txt
.gitignore                 (правка: п. 1)
tests/
  conftest.py              # изоляция, нет сети, фикстура fake_llm
  fake_llm.py              # подмена LLM + журнал вызовов
  kernel_boot.py           # то же внутри ядра Jupyter
  nbdriver.py              # запуск ядра, клики, чтение state.json
  helpers.py               # make_state(): StateManager с планом из 3 уроков
  fixtures/llm/*.json|md   # записанные ответы LLM (п. 4)
  unit/
    test_progress_state.py
    test_misc_bugs.py
    test_llm_and_domain.py
    test_legacy_checks.py  # запуск существующих *_checks.py как есть
  scenario/
    conftest.py            # фикстуры nb и lesson
    test_flow_core.py
    test_notebook_smoke.py
  live/
    test_live_smoke.py     # @pytest.mark.live, по умолчанию выключен
```

### `requirements-dev.txt`

```
-r requirements.txt
pytest>=8.0
jupyter_client>=8.0
nbclient>=0.10
nbformat>=5.9
ipykernel>=6.30
```

(`ipykernel`, `ipywidgets`, `openai`, `httpx`, `python-dotenv` уже есть в `requirements.txt`.) Установить в то же окружение, из которого запускаются тесты (то самое, где работает TeachAI): `pip install -r requirements-dev.txt`. Ядро Jupyter для тестов должно быть из **этого же** окружения: `NotebookSession` проверяет это и подсказывает `python -m ipykernel install --user --name python3`.

### `pytest.ini`

```ini
[pytest]
pythonpath = .
testpaths = tests
addopts = -m "not live" -p no:cacheprovider
markers =
    unit: быстрые тесты без Jupyter и сети
    scenario: сценарии в настоящем ядре Jupyter, LLM подменён записанными ответами
    live: настоящая модель, нужен OPENAI_API_KEY, по умолчанию выключены
```

## 3. Код стенда (эталонная реализация, проверена)

Создай файлы **ровно такими**, затем запусти п. 6. Менять можно, если упрётся в различие окружения (Windows: пути, кодировка — все чтения файлов уже с `encoding="utf-8"`).

#### `tests/fake_llm.py`

```python
"""Подмена LLM: клиент с тем же интерфейсом, что у openai.OpenAI (chat.completions.create).

Работает и в процессе pytest, и внутри ядра Jupyter (см. tests/kernel_boot.py).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

FIXTURES = Path(__file__).parent / "fixtures" / "llm"

# (kind, regex по system, regex по user | None). Порядок важен: первое совпадение.
RULES: list[tuple[str, str, str | None]] = [
    ("domain", r"классификатор учебной темы", r"Относится ли тема курса"),
    ("subject", r"классификатор учебной темы", r"Определи предметную область"),
    ("code_practice", r"решаешь, есть ли у урока практика кодом", None),
    ("task_matches", r"проверяешь соответствие практики уроку", None),
    ("plan", r"методист образовательных программ", None),
    ("lesson", r"Пиши подробный урок", None),
    ("concepts", r"выделяет ключевые понятия", None),
    ("concept_explain", r"подробные и понятные объяснения сложных понятий", None),
    ("explanation", r"эксперт в данной области", None),
    ("examples", r"Сначала реши, есть ли у этого урока", None),
    ("examples_repair", r"генерируешь только JSON с рабочими Python-примерами", None),
    ("assessment", r"создающий тесты для проверки знаний", None),
    ("relevance", r"scope=lesson, если вопрос", None),
    ("qa", r"отвечает на вопросы студентов", None),
    ("task_gen", r"Создавай однозначные контрольные задания", None),
    ("task_validate", r"Проверяешь контрольные задания по смыслу решения", None),
]


@dataclass
class Call:
    kind: str
    messages: list
    kwargs: dict


def classify(messages: list) -> str:
    system = "\n".join(m["content"] for m in messages if m.get("role") == "system")
    user = "\n".join(m["content"] for m in messages if m.get("role") == "user")
    for kind, sys_re, user_re in RULES:
        if re.search(sys_re, system) and (user_re is None or re.search(user_re, user)):
            return kind
    raise AssertionError(
        "Неизвестный запрос к LLM (нет правила в tests/fake_llm.py RULES):\n"
        + system[:200]
    )


@dataclass
class FakeLLM:
    """Выбирает записанный ответ по типу запроса и ведёт журнал вызовов."""

    fixtures: Path = FIXTURES
    calls: list[Call] = field(default_factory=list)
    overrides: dict[str, list[Any]] = field(default_factory=dict)
    log_path: Path | None = None  # для ядра: журнал в JSONL, читает pytest

    # --- настройка ---------------------------------------------------------
    def use(self, kind: str, *responses: Any) -> None:
        """Следующие ответы на ``kind``: имя фикстуры (str без пробелов и '{'),
        dict/list (будет JSON), готовая строка, Exception или callable(messages).
        Последний элемент повторяется, пока не заменён."""
        self.overrides[kind] = list(responses)

    # --- ответ -------------------------------------------------------------
    def _load(self, kind_or_name: str) -> str:
        for ext in (".json", ".md", ".txt"):
            p = self.fixtures / f"{kind_or_name}{ext}"
            if p.exists():
                return p.read_text(encoding="utf-8")
        raise FileNotFoundError(f"нет фикстуры {kind_or_name} в {self.fixtures}")

    def _log(self, row: dict) -> None:
        if self.log_path:
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def answer(self, messages: list, kwargs: dict) -> str:
        try:
            return self._answer(messages, kwargs)
        except (AssertionError, FileNotFoundError) as exc:  # ошибки самого стенда, а не приложения
            self._log({"harness_error": str(exc)})
            raise

    def _answer(self, messages: list, kwargs: dict) -> str:
        kind = classify(messages)
        self.calls.append(Call(kind, messages, kwargs))
        self._log({"kind": kind})
        queue = self.overrides.get(kind)
        item: Any = self._load(kind)
        if queue:
            item = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(item, BaseException):
            raise item
        if callable(item):
            item = item(messages)
        if isinstance(item, (dict, list)):
            return json.dumps(item, ensure_ascii=False)
        if isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9_\-]+", item):
            return self._load(item)
        return str(item)

    def count(self, kind: str | None = None) -> int:
        return sum(1 for c in self.calls if kind is None or c.kind == kind)

    # --- интерфейс клиента OpenAI -------------------------------------------
    def client(self) -> Any:
        fake = self

        def create(**kwargs: Any) -> Any:
            text = fake.answer(kwargs["messages"], kwargs)
            msg = SimpleNamespace(content=text)
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)])

        completions = SimpleNamespace(create=create)
        return SimpleNamespace(chat=SimpleNamespace(completions=completions))

    def create_openai_client(self, api_key: str | None = None, **_: Any):
        meta = {"route": "fake", "use_wallet_balance": False, "base_url": None}
        return self.client(), None, meta

    def install(self) -> None:
        """Подменяет единственную точку создания клиента: content_utils.create_openai_client."""
        import content_utils

        content_utils.create_openai_client = self.create_openai_client
```

#### `tests/conftest.py`

```python
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

FAKE_KEY = "sk-test-not-a-real-key"


@pytest.fixture(autouse=True, scope="session")
def real_data_untouched():
    """Страховка: реальные data/state.json и .env проекта тестами не меняются."""
    def snap():
        return {p: (p.stat().st_mtime_ns, p.stat().st_size) for p in
                [ROOT / "data" / "state.json", ROOT / ".env", ROOT / ".env.sample"] if p.exists()}
    before = snap()
    yield
    assert snap() == before, "тесты изменили реальные файлы проекта"


@pytest.fixture(autouse=True)
def no_network(monkeypatch, request):
    """Любой реальный HTTP-запрос в тесте — ошибка (кроме тестов с маркером live)."""
    if request.node.get_closest_marker("live"):
        return
    import httpx

    def boom(*a, **k):
        raise AssertionError("тест пытался выйти в сеть")

    monkeypatch.setattr(httpx.Client, "send", boom)


@pytest.fixture(autouse=True)
def isolated_project(tmp_path, monkeypatch):
    """Каждый тест живёт во временной папке: ни data/state.json, ни logs, ни .env проекта не трогаются."""
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)  # logs/, data/llm_route_preference.json, debug_responses/ — относительные пути
    (work / ".env").write_text(f"OPENAI_API_KEY={FAKE_KEY}\nOPENAI_API_ROUTE=direct\n", encoding="utf-8")
    for var in ("OPENAI_PROXY", "HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy",
                "ALL_PROXY", "all_proxy", "GPTUNNEL_API_KEY", "OPENAI_USE_PROXY", "OPENAI_CONNECTION_MODE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    monkeypatch.setenv("OPENAI_API_ROUTE", "direct")
    # StateManager строит путь как <папка модуля>/<state_file>; абсолютный путь это обходит.
    import state_manager

    state_file = str(work / "data" / "state.json")
    monkeypatch.setattr(state_manager.StateManager.__init__, "__defaults__", (state_file,))
    yield work


@pytest.fixture
def fake_llm():
    from fake_llm import FakeLLM

    fake = FakeLLM()
    fake.install()
    return fake
```

#### `tests/helpers.py`

```python
"""Общие помощники для unit-тестов."""
from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "llm"
SEC, TOP = "section-1", "topic-1-1"
L1, L2, L3 = (f"{SEC}:{TOP}:lesson-1-1-{i}" for i in (1, 2, 3))


def load_plan() -> dict:
    return json.loads((FIXTURES / "plan.json").read_text(encoding="utf-8"))


def make_state(plan_id: str = "python-basics"):
    """StateManager во временной папке с готовым планом из 3 уроков и активным курсом."""
    from state_manager import StateManager
    from course_portfolio import bind_new_plan

    sm = StateManager()
    plan = load_plan()
    plan["id"] = plan_id
    sm.state["course_plan"] = plan
    bind_new_plan(sm.state, plan)
    sm.state["learning"]["current_section"] = SEC
    sm.state["learning"]["current_topic"] = TOP
    sm.state["learning"]["current_lesson"] = "lesson-1-1-1"
    sm.save_state()
    return sm
```

#### `tests/kernel_boot.py`

```python
"""Выполняется ВНУТРИ ядра Jupyter до ячейки TeachAI: подменяет LLM и ведёт журнал вызовов."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fake_llm import FakeLLM  # noqa: E402

import content_utils  # noqa: E402  (грузится из копии проекта — рабочая папка ядра)

FAKE = FakeLLM(log_path=Path(os.environ["TEACHAI_FAKE_LOG"]))
FAKE.install()

# Страховка: из ядра теста нельзя выйти в сеть.
import httpx  # noqa: E402


def _no_network(*args, **kwargs):
    raise AssertionError("тест пытался выйти в сеть из ядра")


httpx.Client.send = _no_network
```

#### `tests/nbdriver.py`

```python
"""Управление настоящим ядром Jupyter: запуск ячейки TeachAI.ipynb, чтение и нажатие виджетов."""
from __future__ import annotations

import json
import os
import queue
import shutil
import sys
from pathlib import Path

from jupyter_client.manager import KernelManager

ROOT = Path(__file__).resolve().parents[1]
TESTS = Path(__file__).parent
MARK = "<<J>>"

# что копируем в временный проект: код, каталог курсов, ноутбук
COPY_GLOBS = ("*.py", "courses.json", "TeachAI.ipynb")


class NotebookSession:
    def __init__(self, workdir: Path, key: str = "sk-test-not-a-real-key"):
        self.proj = workdir / "project"
        self.proj.mkdir()
        for pattern in COPY_GLOBS:
            for src in ROOT.glob(pattern):
                shutil.copy2(src, self.proj / src.name)
        (self.proj / ".env").write_text(f"OPENAI_API_KEY={key}\nOPENAI_API_ROUTE=direct\n", encoding="utf-8")
        self.llm_log = workdir / "llm_calls.jsonl"
        self.llm_log.write_text("", encoding="utf-8")
        env = {"TEACHAI_FAKE_LOG": str(self.llm_log), "OPENAI_API_KEY": key, "OPENAI_API_ROUTE": "direct",
               "PYTHONPATH": str(self.proj)}
        full_env = {k: v for k, v in os.environ.items()
                    if k.upper() not in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")}
        full_env.update(env)
        self.km = KernelManager(kernel_name="python3")
        self.km.start_kernel(cwd=str(self.proj), env=full_env)
        self.kc = self.km.client()
        self.kc.start_channels()
        self.kc.wait_for_ready(timeout=60)
        kernel_python = self.run("import sys; print(sys.executable)").strip()
        assert os.path.realpath(kernel_python) == os.path.realpath(sys.executable) or \
            Path(kernel_python).parent.parent == Path(sys.prefix), (
            f"ядро Jupyter запущено другим Python: {kernel_python} (тесты: {sys.executable}). "
            "Установите ядро из текущего окружения: python -m ipykernel install --user --name python3")
        self.run(f"import sys; sys.path.insert(0, {str(TESTS)!r}); import kernel_boot")

    # --- выполнение ---------------------------------------------------------
    def run(self, code: str, timeout: float = 120) -> str:
        """Выполняет код в ядре, возвращает stdout; при ошибке — исключение с traceback."""
        msg_id = self.kc.execute(code)
        out, err = [], None
        while True:
            try:
                msg = self.kc.get_iopub_msg(timeout=timeout)
            except queue.Empty:
                raise TimeoutError(f"ядро не ответило за {timeout} с: {code[:80]}")
            if msg["parent_header"].get("msg_id") != msg_id:
                continue
            t, c = msg["msg_type"], msg["content"]
            if t == "stream" and c["name"] == "stdout":
                out.append(c["text"])
            elif t == "error":
                err = "\n".join(c["traceback"])
            elif t == "status" and c["execution_state"] == "idle":
                break
        if err:
            raise RuntimeError(err)
        return "".join(out)

    def eval(self, expr: str):
        """Значение выражения, переданное через JSON."""
        text = self.run(f"import json as _j; print({MARK!r} + _j.dumps({expr}, ensure_ascii=False, default=str))")
        return json.loads(text.split(MARK, 1)[1])

    def start_teachai(self) -> str:
        """Выполняет ячейку TeachAI.ipynb: from run_teachai import start_jupyter; start_jupyter()"""
        import nbformat
        nb = nbformat.read(self.proj / "TeachAI.ipynb", as_version=4)
        code = next(c.source for c in nb.cells if c.cell_type == "code")
        return self.run(code)

    # --- виджеты ------------------------------------------------------------
    def buttons(self, text: str = "") -> list[dict]:
        """Кнопки (в порядке создания), чьё описание содержит text и которые видимы и не отключены."""
        return self.eval(
            "[{'i': i, 'd': w.description, 'dis': w.disabled} "
            "for i, w in enumerate(__import__('ipywidgets').Widget.widgets.values()) "
            f"if type(w).__name__ == 'Button' and {text!r} in w.description "
            "and w.layout.display != 'none']"
        )

    def click(self, text: str, nth: int = -1) -> None:
        """Нажимает nth-ую (по умолчанию последнюю созданную) подходящую кнопку."""
        found = [b for b in self.buttons(text) if not b["dis"]]
        assert found, f"нет активной кнопки «{text}». Есть: {[b['d'] for b in self.buttons()]}"
        idx = found[nth]["i"]
        self.run(f"list(__import__('ipywidgets').Widget.widgets.values())[{idx}].click()")

    def set_value(self, description: str, value) -> None:
        """Меняет value у поля ввода/слайдера/списка по подписи (description содержит текст); берёт последнее созданное."""
        idx = self.eval(
            "[i for i, w in enumerate(__import__('ipywidgets').Widget.widgets.values()) "
            f"if {description!r} in getattr(w, 'description', '') and hasattr(w, 'value') "
            "and type(w).__name__ != 'Button']")
        assert idx, f"нет поля «{description}»"
        self.run(f"list(__import__('ipywidgets').Widget.widgets.values())[{idx[-1]}].value = {value!r}")

    def dump(self) -> list:
        """Диагностика: все интерактивные виджеты (для отладки теста)."""
        return self.eval(
            "[(i, type(w).__name__, getattr(w, 'description', ''), str(getattr(w, 'value', ''))[:40]) "
            "for i, w in enumerate(__import__('ipywidgets').Widget.widgets.values()) "
            "if type(w).__name__ in ('Button','Text','IntSlider','Dropdown','RadioButtons','Textarea')]")

    def type_into(self, placeholder: str, value: str) -> None:
        """Вводит текст в поле по подсказке (placeholder), например «Введите ваш вопрос»."""
        idx = self.eval(
            "[i for i, w in enumerate(__import__('ipywidgets').Widget.widgets.values()) "
            f"if {placeholder!r} in getattr(w, 'placeholder', '')]")
        assert idx, f"нет поля с подсказкой «{placeholder}»"
        self.run(f"list(__import__('ipywidgets').Widget.widgets.values())[{idx[-1]}].value = {value!r}")

    def choose(self, option_label: str) -> None:
        """Выбирает пункт RadioButtons по подписи, например «Своё название курса»."""
        self.run(
            "_w = [w for w in __import__('ipywidgets').Widget.widgets.values() "
            "if type(w).__name__ == 'RadioButtons' "
            f"and any(o[0] == {option_label!r} for o in w.options)][-1]\n"
            f"_w.value = dict(_w.options)[{option_label!r}]")

    def answer_test(self, correct: int) -> None:
        """Отвечает на 5 вопросов теста: первые `correct` — верно (вариант «верно N»), остальные — неверно.
        Варианты в тесте перемешаны, поэтому ответ выбирается по тексту, а не по номеру."""
        groups = self.eval(
            "[[o[0] for o in w.options] for w in __import__('ipywidgets').Widget.widgets.values() "
            "if type(w).__name__ == 'RadioButtons' and len(w.options) == 3 "
            "and str(w.options[0][0]).startswith(('верно', 'неверно'))][-5:]")
        assert len(groups) == 5, groups
        for q, labels in enumerate(groups):
            want_ok = q < correct
            pick = next(i for i, t in enumerate(labels) if t.startswith("верно") == want_ok) + 1
            self.run(
                "_w = [w for w in __import__('ipywidgets').Widget.widgets.values() "
                "if type(w).__name__ == 'RadioButtons' and len(w.options) == 3 "
                "and str(w.options[0][0]).startswith(('верно', 'неверно'))][-5:]\n"
                f"_w[{q}].value = {pick}")

    def llm_use(self, kind: str, *responses) -> None:
        """Подменяет ответы LLM внутри ядра (как FakeLLM.use). Значения — только JSON-совместимые."""
        args = ", ".join(repr(r) for r in responses)
        self.run(f"kernel_boot.FAKE.use({kind!r}, {args})")

    def set_code(self, code: str) -> None:
        """Вставляет код в редактор контрольного задания (Textarea «Код:»)."""
        self.set_value("Код:", code)

    def html_texts(self) -> list[str]:
        """Тексты всех HTML-виджетов (для проверки сообщений)."""
        return self.eval("[w.value for w in __import__('ipywidgets').Widget.widgets.values() "
                         "if type(w).__name__ == 'HTML']")

    def llm_calls(self) -> list[str]:
        lines = self.llm_log.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(x) for x in lines if x.strip()]
        return [r["kind"] for r in rows if "kind" in r]

    def harness_errors(self) -> list[str]:
        """Ошибки стенда (нет фикстуры / нет правила в RULES): приложение их глотает, тест обязан их увидеть."""
        lines = self.llm_log.read_text(encoding="utf-8").splitlines()
        return [json.loads(x)["harness_error"] for x in lines if x.strip() and "harness_error" in x]

    def state(self) -> dict:
        return json.loads((self.proj / "data" / "state.json").read_text(encoding="utf-8"))

    def close(self) -> None:
        try:
            self.kc.stop_channels()
        finally:
            self.km.shutdown_kernel(now=True)
```

#### `tests/scenario/conftest.py`

```python
import pytest
from nbdriver import NotebookSession


@pytest.fixture
def nb(tmp_path):
    """Ядро Jupyter в копии проекта во временной папке; LLM подменён."""
    session = NotebookSession(tmp_path)
    yield session
    errors = session.harness_errors()
    session.close()
    assert not errors, f"стенд LLM: {errors}"  # приложение глотает такие ошибки — ловим здесь


@pytest.fixture
def lesson(nb):
    """Профиль сохранён, курс «Основы Python» начат, открыт урок 1 (LLM: plan, lesson, concepts)."""
    nb.start_teachai()
    nb.set_value("Имя", "Тест")
    nb.set_value("Общее время", 3)
    nb.set_value("Длительность урока", 30)
    nb.click("Сохранить настройки")
    nb.click("Начать курс")
    return nb
```

## 4. Фикстуры ответов LLM

Содержимое — ровно такое. Имя файла = вид запроса (`kind` из `RULES`); `kind.json` — ответ по умолчанию, `kind_<вариант>.json` — альтернативный, выбирается в тесте через `fake_llm.use("kind", "kind_<вариант>")` (в ядре: `nb.llm_use(...)`). Перемешанные варианты и `correct_option` в `assessment.json` — как в реальном ответе модели.

#### `tests/fixtures/llm/assessment.json`

```json
{
  "questions": [
    {
      "text": "Вопрос 1?",
      "options": [
        "верно 1",
        "неверно 1a",
        "неверно 1b"
      ],
      "correct_option": 1,
      "explanation": "Потому что."
    },
    {
      "text": "Вопрос 2?",
      "options": [
        "верно 2",
        "неверно 2a",
        "неверно 2b"
      ],
      "correct_option": 1,
      "explanation": "Потому что."
    },
    {
      "text": "Вопрос 3?",
      "options": [
        "верно 3",
        "неверно 3a",
        "неверно 3b"
      ],
      "correct_option": 1,
      "explanation": "Потому что."
    },
    {
      "text": "Вопрос 4?",
      "options": [
        "верно 4",
        "неверно 4a",
        "неверно 4b"
      ],
      "correct_option": 1,
      "explanation": "Потому что."
    },
    {
      "text": "Вопрос 5?",
      "options": [
        "верно 5",
        "неверно 5a",
        "неверно 5b"
      ],
      "correct_option": 1,
      "explanation": "Потому что."
    }
  ]
}
```

#### `tests/fixtures/llm/code_practice.json`

```json
{
  "code_practice": true,
  "reason": ""
}
```

#### `tests/fixtures/llm/code_practice_no.json`

```json
{
  "code_practice": false,
  "reason": "Этот урок не учит писать код."
}
```

#### `tests/fixtures/llm/concept_explain.md`

```markdown
Переменная — это имя, под которым хранится значение.
```

#### `tests/fixtures/llm/concepts.json`

```json
{
  "concepts": [
    {
      "name": "Переменная",
      "brief_description": "Имя для значения"
    },
    {
      "name": "Функция print",
      "brief_description": "Вывод на экран"
    }
  ]
}
```

#### `tests/fixtures/llm/domain.json`

```json
{
  "in_domain": true,
  "reason": "Тема про Python."
}
```

#### `tests/fixtures/llm/domain_out.json`

```json
{
  "in_domain": false,
  "reason": "Кройка и шитьё — не Python и не AI/ML."
}
```

#### `tests/fixtures/llm/examples.json`

```json
{
  "practice_possible": true,
  "examples": [
    {
      "title": "Переменная",
      "description": "Сохраняем число.",
      "code": "x = 5\nprint(x)"
    },
    {
      "title": "Две переменные",
      "description": "Складываем.",
      "code": "a = 2\nb = 3\nprint(a + b)"
    }
  ]
}
```

#### `tests/fixtures/llm/examples_oneline.json`

```json
{
  "practice_possible": true,
  "examples": [
    {
      "title": "Тип",
      "description": "Тип числа.",
      "code": "print(type(3.5))"
    }
  ]
}
```

#### `tests/fixtures/llm/explanation.md`

```markdown
Простыми словами: переменная — это коробка с именем.
```

#### `tests/fixtures/llm/lesson.md`

```markdown
# Переменные и вывод

Переменная хранит значение. Вывод делает `print`.

## Пример

```python
x = 5
print(x)
```

## Правила имён

Имя переменной начинается с буквы или `_`.
```

#### `tests/fixtures/llm/plan.json`

```json
{
  "title": "Основы Python",
  "description": "Тестовый курс",
  "total_duration_minutes": 90,
  "sections": [
    {
      "id": "section-1",
      "title": "Введение",
      "description": "Раздел",
      "duration_minutes": 90,
      "topics": [
        {
          "id": "topic-1-1",
          "title": "Основы",
          "description": "Тема",
          "duration_minutes": 90,
          "lessons": [
            {
              "id": "lesson-1-1-1",
              "title": "Урок 1: переменные и вывод",
              "description": "Описание урока 1",
              "duration_minutes": 30,
              "keywords": [
                "переменные",
                "print"
              ]
            },
            {
              "id": "lesson-1-1-2",
              "title": "Урок 2: числа и строки",
              "description": "Описание урока 2",
              "duration_minutes": 30,
              "keywords": [
                "переменные",
                "print"
              ]
            },
            {
              "id": "lesson-1-1-3",
              "title": "Урок 3: числа и строки",
              "description": "Описание урока 3",
              "duration_minutes": 30,
              "keywords": [
                "переменные",
                "print"
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

#### `tests/fixtures/llm/qa.md`

```markdown
Переменная — это имя для значения в памяти.
```

#### `tests/fixtures/llm/relevance.json`

```json
{
  "scope": "lesson",
  "is_relevant": true,
  "confidence": 95,
  "reason": "По теме урока.",
  "suggestions": []
}
```

#### `tests/fixtures/llm/relevance_course.json`

```json
{
  "scope": "course",
  "is_relevant": true,
  "confidence": 80,
  "reason": "Это из другого урока курса.",
  "suggestions": []
}
```

#### `tests/fixtures/llm/relevance_outside.json`

```json
{
  "scope": "outside",
  "is_relevant": false,
  "confidence": 99,
  "reason": "Вопрос про погоду не относится к курсу.",
  "suggestions": []
}
```

#### `tests/fixtures/llm/subject.json`

```json
{
  "subject": "основы Python",
  "reason": "Урок про переменные."
}
```

#### `tests/fixtures/llm/task_gen.json`

```json
{
  "title": "Сумма чисел",
  "description": "Сложите два числа.",
  "student_steps": [
    "Используйте a и b из заготовки",
    "Запишите сумму в total"
  ],
  "condition_rule": "",
  "task_code": "a = 2\nb = 3\n# Ваш код здесь",
  "solution_code": "a = 2\nb = 3\ntotal = a + b",
  "validation_mode": "llm",
  "check_variables": [
    "total"
  ],
  "output_format": "",
  "hints": [
    "Используйте оператор +"
  ],
  "is_needed": true,
  "skip_reason": ""
}
```

#### `tests/fixtures/llm/task_matches.json`

```json
{
  "matches": true,
  "reason": "Практика по теме урока."
}
```

#### `tests/fixtures/llm/task_validate.json`

```json
{
  "is_correct": true,
  "score": 100,
  "feedback": "Верно.",
  "failure_reason": ""
}
```

#### `tests/fixtures/llm/task_validate_wrong.json`

```json
{
  "is_correct": false,
  "score": 0,
  "feedback": "Сумма посчитана неверно.",
  "failure_reason": "total не равно 5"
}
```

Чего в фикстурах **нет**: плана на 8 уроков (хватает 3), кривых ответов (битый JSON, ```json-обёртка) — их добавить во втором проходе (сценарии LLM-04/05, см. п. 7).

## 5. Тесты (эталонный набор, проверен)

Каждый тест называется по ID из `docs/TeachAI_test_scenarios.md`. Ожидаемый результат эталонного набора — в п. 8.

#### `tests/unit/test_progress_state.py`

```python
"""Прогресс, завершённость урока, результаты КЗ (сценарии ST, TST, KZ, LSN, PRF)."""
import logging
from types import SimpleNamespace

import pytest

from helpers import L1, L2, L3, SEC, TOP, make_state

pytestmark = pytest.mark.unit


def test_ST_02_test_passed_without_task_is_not_completed():
    sm = make_state()
    sm.save_lesson_assessment(L1, 60, True)
    assert sm.is_test_passed(L1)
    assert not sm.is_lesson_completed(L1)


def test_ST_03_test_and_correct_task_complete_lesson():
    sm = make_state()
    sm.save_lesson_assessment(L1, 60, True)
    sm.save_control_task_result(L1, "Сумма", True)
    assert sm.is_lesson_completed(L1)


def test_ST_04_bypass_and_correct_task_complete_lesson():
    sm = make_state()
    sm.mark_test_bypassed(L1)
    sm.save_control_task_result(L1, "Сумма", True)
    assert sm.is_lesson_completed(L1)


def test_TST_06_forty_percent_is_not_passed():
    sm = make_state()
    sm.state["learning"]["lesson_scores"] = {L1: 40}
    assert not sm.is_test_passed(L1)
    sm.state["learning"]["lesson_scores"] = {L1: 60}
    assert sm.is_test_passed(L1)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="ST-01: открытие урока кладёт его в completed_lessons (learning_progress_manager.py:47-56)")
def test_ST_01_opening_lesson_does_not_complete_it():
    sm = make_state()
    sm.update_learning_progress(section=SEC, topic=TOP, lesson="lesson-1-1-1")
    assert L1 not in sm.state["learning"]["completed_lessons"]



@pytest.mark.xfail(strict=True, raises=AssertionError, reason="KZ-12: верный результат КЗ затирается неверной пересдачей (state_manager.py:368-372)")
def test_KZ_12_wrong_resubmission_keeps_best_result():
    sm = make_state()
    sm.save_control_task_result(L1, "Сумма", True)
    sm.save_control_task_result(L1, "Сумма", False)
    assert sm.state["control_tasks"][L1]["is_correct"] is True


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="TST-08: «Повторить урок» удаляет лучший балл (learning_progress_manager.py:316-320)")
def test_TST_08_repeat_lesson_keeps_best_score():
    sm = make_state()
    sm.save_lesson_assessment(L1, 80, True)
    sm.mark_lesson_incomplete(L1)
    assert sm.get_lesson_score(L1) == 80


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="LSN-13: следующий урок ищется по позиции, а не первый незавершённый (course_data_manager.py:177)")
def test_LSN_13_next_lesson_is_first_unfinished():
    sm = make_state()
    for lid in (L1, L2):
        sm.mark_lesson_complete_manually(lid)
    sm.state["learning"]["current_lesson"] = "lesson-1-1-1"
    section, topic, lesson, _ = sm.get_next_lesson()
    assert lesson == "lesson-1-1-3"


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="PRF-05: верное КЗ добавляет лишнюю «попытку теста» (control_tasks_interface.py:535)")
def test_PRF_05_correct_task_does_not_add_test_attempt():
    from control_tasks_interface import ControlTasksInterface

    sm = make_state()
    sm.save_lesson_assessment(L1, 40, False)
    sm.save_lesson_assessment(L1, 100, True)
    li = SimpleNamespace(current_lesson_id=L1, state_manager=sm)
    fake_self = SimpleNamespace(lesson_interface=li, logger=logging.getLogger("t"))
    ControlTasksInterface._save_task_result(fake_self, {"title": "Сумма"}, True)
    assert len(sm.state["learning"]["lesson_attempts"][L1]) == 2


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="D2: понятия записываются в профиль уже при тесте >40% (learning_progress_manager.py:119-122); по D2 — только при переходе")
def test_D2_concepts_not_counted_on_test_pass():
    sm = make_state()
    sm.state["lesson_content_cache"] = {L1: {"concepts": [{"name": "Переменная", "description": "x"}]}}
    sm.save_lesson_assessment(L1, 80, True)
    assert L1 not in (sm.state["learning"].get("lesson_concepts") or {})


def test_D2_concepts_counted_on_forced_transition():
    sm = make_state()
    sm.state["lesson_content_cache"] = {L1: {"concepts": [{"name": "Переменная", "description": "x"}]}}
    sm.mark_lesson_complete_manually(L1)
    assert L1 in sm.state["learning"]["lesson_concepts"]


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="PRF-04: дашборд считает открытые уроки как пройденные (startup_dashboard.py:300-316, learning_progress_manager.py:47-56)")
def test_PRF_04_dashboard_progress_ignores_opened_lessons():
    from startup_dashboard import StartupDashboard

    sm = make_state()
    sm.update_learning_progress(section="section-1", topic="topic-1-1", lesson="lesson-1-1-1")
    stats = StartupDashboard(sm, None)._get_progress_statistics()
    assert stats["completed_lessons_count"] == 0
    assert stats["progress_percent"] == 0


def test_PRF_03_dashboard_counts_completed_lesson():
    from startup_dashboard import StartupDashboard

    sm = make_state()
    sm.save_lesson_assessment(L1, 60, True)
    sm.save_control_task_result(L1, "Сумма", True)
    sm.mark_lesson_complete_manually(L1)
    stats = StartupDashboard(sm, None)._get_progress_statistics()
    assert stats["total_lessons_count"] == 3
```

#### `tests/unit/test_misc_bugs.py`

```python
"""Известные баги без Jupyter: конфиг, парсинг примеров, ретраи LLM, выполнение кода (ZAP, LSN, LLM, SEC, KZ)."""
import os
import pytest

pytestmark = pytest.mark.unit


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="ZAP-02: create_sample_env перезаписывает существующий .env.sample (config.py:139-149)")
def test_ZAP_02_sample_env_not_overwritten(isolated_project):
    from config import ConfigManager

    sample = isolated_project / ".env.sample"
    sample.write_text("МОЁ СОДЕРЖИМОЕ", encoding="utf-8")
    ConfigManager().create_sample_env()
    assert sample.read_text(encoding="utf-8") == "МОЁ СОДЕРЖИМОЕ"


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="LSN-06: однострочный пример отбрасывается (examples_html_utils.py:158)")
def test_LSN_06_one_line_example_is_kept():
    from examples_html_utils import executable_examples

    payload = {"examples": [{"title": "Тип", "description": "", "code": "print(type(3.5))"}]}
    assert len(executable_examples(payload)) == 1


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="LLM-01: 401 повторяется 3 раза и объясняется «прокси» (content_utils.py:588-632)")
def test_LLM_01_401_is_not_retried(fake_llm, monkeypatch):
    import time
    from course_plan_generator import CoursePlanGenerator

    monkeypatch.setattr(time, "sleep", lambda *_: None)
    fake_llm.use("plan", Exception("Error code: 401 - invalid_api_key"))
    gen = CoursePlanGenerator("sk-test-not-a-real-key")
    with pytest.raises(Exception) as err:
        gen.make_api_request_with_retries(
            messages=[{"role": "system", "content": "Ты - опытный методист образовательных программ."},
                      {"role": "user", "content": "x"}])
    assert fake_llm.count("plan") == 1
    assert "прокси" not in str(err.value).lower()


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="SEC-04: eval на выводе программы (result_checker.py:358)")
def test_SEC_04_no_eval_on_program_output():
    from result_checker import extract_numpy_arrays

    extract_numpy_arrays("[__import__('os').__setattr__('TEACHAI_EVAL_PROBE', 1)]")
    try:
        assert not hasattr(os, "TEACHAI_EVAL_PROBE")
    finally:
        if hasattr(os, "TEACHAI_EVAL_PROBE"):
            del os.TEACHAI_EVAL_PROBE


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="SEC-02: код ученика читает OPENAI_API_KEY (control_tasks_generator.py:64, exec в процессе ядра)")
def test_SEC_02_student_code_cannot_read_api_key():
    from control_tasks_generator import ControlTasksGenerator

    out, _ = ControlTasksGenerator.execute_code("import os\nprint(os.environ.get('OPENAI_API_KEY', 'НЕТ КЛЮЧА'))")
    assert "sk-test" not in out


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="SEC-01: код ученика пишет в файлы текущей папки (control_tasks_generator.py:64)")
def test_SEC_01_student_code_cannot_touch_project_files(isolated_project):
    from control_tasks_generator import ControlTasksGenerator

    marker = isolated_project / "student_wrote_this.txt"
    ControlTasksGenerator.execute_code("open('student_wrote_this.txt', 'w').write('x')")
    assert not marker.exists()


@pytest.mark.skip(reason="KZ-16: `while True` повесит тест, пока нет таймаута (пакет 4, D9). После D9 снять skip и ожидать сообщение «Код выполнялся слишком долго…»")
def test_KZ_16_infinite_loop_is_stopped():
    from control_tasks_generator import ControlTasksGenerator

    ControlTasksGenerator.execute_code("while True:\n    pass")
```

#### `tests/unit/test_llm_and_domain.py`

```python
"""Проверка темы курса, разбор ответов LLM, число вызовов (CRS, LLM, LSN)."""
import pytest

pytestmark = pytest.mark.unit


def _generator():
    from content_generator import ContentGenerator
    return ContentGenerator("sk-test-not-a-real-key")


def test_CRS_03_in_domain_topic(fake_llm):
    from course_domain import classify_course_topic
    v = classify_course_topic("Основы pandas для аналитика", generator=_generator())
    assert v.status == "in"


def test_CRS_04_out_of_domain_topic(fake_llm):
    from course_domain import classify_course_topic
    fake_llm.use("domain", "domain_out")
    v = classify_course_topic("Курс кройки и шитья", generator=_generator())
    assert v.status == "out"


def test_CRS_08_garbage_answer_is_error_not_in(fake_llm):
    from course_domain import classify_course_topic
    fake_llm.use("domain", "это не JSON")
    v = classify_course_topic("Курс кройки и шитья", generator=_generator())
    assert v.status == "error"


@pytest.mark.parametrize("title,ok", [("ab", False), ("x" * 121, False), ("Основы pandas", True)])
def test_CRS_02_custom_title_validation(title, ok):
    from custom_course import validate_custom_course
    assert (validate_custom_course(title) is None) is ok
```

#### `tests/unit/test_legacy_checks.py`

```python
"""Существующие проверки в корне проекта (*_checks.py) запускаются как есть, но в изолированной среде.

Файлы *_checks.py не двигаем и не правим — только вызываем их функции test_*.
"""
import importlib
import inspect
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.unit

# Устаревшие проверки (сами проверки правит пакет 2, здесь они помечены xfail).
STALE = {
    "relevance_prompt_checks::test_relevance_prompt_is_a_teacher_judgment":
        "LEGACY: в промпте релевантности больше нет фразы «как преподаватель» (промпт переписан на scope, relevance_checker.py)",
}


def _cases():
    for path in sorted(ROOT.glob("*_checks.py")):
        mod = importlib.import_module(path.stem)
        for name, fn in inspect.getmembers(mod, inspect.isfunction):
            if name.startswith("test_") and fn.__module__ == path.stem:
                case_id = f"{path.stem}::{name}"
                marks = []
                if case_id in STALE:
                    marks.append(pytest.mark.xfail(strict=True, raises=AssertionError, reason=STALE[case_id]))
                yield pytest.param(fn, id=case_id, marks=marks)


@pytest.mark.parametrize("fn", list(_cases()))
def test_legacy_check(fn):
    fn()
```

#### `tests/scenario/test_flow_core.py`

```python
"""Основной путь ученика в настоящем ядре Jupyter (ZAP, CRS, LSN, TST, KZ, ST)."""
import pytest

from helpers import L1

pytestmark = pytest.mark.scenario


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="ZAP-01: при запуске печатается отладка «🔍 ОТЛАДКА» (interface.py:65-67)")
def test_ZAP_01_no_debug_output_on_start(nb):
    out = nb.start_teachai()
    assert "Traceback" not in out
    assert "ОТЛАДКА" not in out


def test_PRF_01_empty_name_does_not_create_profile(nb):
    nb.start_teachai()
    nb.click("Сохранить настройки")
    assert nb.llm_calls() == []
    assert not (nb.proj / "data" / "state.json").exists() or not nb.state()["user"].get("name")


def test_CRS_01_start_catalog_course(lesson):
    assert lesson.llm_calls() == ["plan", "lesson", "concepts"]
    st = lesson.state()
    assert st["active_course_id"] == "python-basics"
    assert "python-basics" in st["courses"]


def test_TST_07_sixty_percent_passes_but_does_not_complete(lesson):
    lesson.click("Пройти тест")
    lesson.answer_test(3)
    lesson.click("Завершить тест")
    learn = lesson.state()["learning"]
    assert learn["lesson_scores"][L1] == 60
    assert not learn.get("lesson_completion_status", {}).get(L1)
    assert lesson.buttons("Перейти к контрольным заданиям")


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="TST-02: в тесте заранее выбран первый вариант (assessment_questions_ui.py:94)")
def test_TST_02_no_option_preselected(lesson):
    lesson.click("Пройти тест")
    values = lesson.eval(
        "[w.value for w in __import__('ipywidgets').Widget.widgets.values() "
        "if type(w).__name__ == 'RadioButtons' and len(w.options) == 3][-5:]")
    assert values == [None] * 5


def test_KZ_08_wrong_solution_is_recorded_and_lesson_not_completed(lesson):
    lesson.click("Пройти тест"); lesson.answer_test(3); lesson.click("Завершить тест")
    lesson.click("Контрольные задания")
    lesson.llm_use("task_validate", "task_validate_wrong")
    lesson.set_code("a = 2\nb = 3\ntotal = 1")
    lesson.click("Проверить решение")
    st = lesson.state()
    assert st["control_tasks"][L1]["is_correct"] is False
    assert not st["learning"]["lesson_completion_status"].get(L1)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="KZ-09/D4: эталонное решение показывается автоматически после первой ошибки (control_tasks_interface.py:482-490)")
def test_KZ_09_reference_solution_not_shown_after_wrong_attempt(lesson):
    lesson.click("Пройти тест"); lesson.answer_test(3); lesson.click("Завершить тест")
    lesson.click("Контрольные задания")
    lesson.llm_use("task_validate", "task_validate_wrong")
    lesson.set_code("a = 2\nb = 3\ntotal = 1")
    lesson.click("Проверить решение")
    assert not any("Эталонное решение" in t for t in lesson.html_texts())


def test_KZ_10_correct_solution_completes_lesson(lesson):
    lesson.click("Пройти тест"); lesson.answer_test(3); lesson.click("Завершить тест")
    lesson.click("Контрольные задания")
    lesson.set_code("a = 2\nb = 3\ntotal = a + b")
    lesson.click("Проверить решение")
    st = lesson.state()
    assert st["control_tasks"][L1]["is_correct"] is True
    assert st["learning"]["lesson_completion_status"][L1] is True


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="D3: нет поля lesson_pass_mode — «Продолжить с текущей оценкой» неотличим от обычного прохождения")
def test_TST_09_continue_after_failed_test_marks_no_test(lesson):
    lesson.click("Пройти тест"); lesson.answer_test(1); lesson.click("Завершить тест")
    lesson.click("Продолжить с текущей оценкой")
    learn = lesson.state()["learning"]
    assert learn["lesson_completion_status"][L1] is True
    assert learn.get("lesson_pass_mode", {}).get(L1) == "no_test"


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="LSN-04/D2: понятия попадают в профиль при открытии списка «Ключевые понятия» (lesson_interaction.py:139,291)")
def test_LSN_04_opening_concepts_does_not_count_them(lesson):
    lesson.click("Объяснить подробнее")
    lesson.click("Ключевые понятия")
    assert L1 not in (lesson.state()["learning"].get("lesson_concepts") or {})


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="LSN-10/D8: отклонённый вопрос увеличивает questions_count (lesson_interaction.py:434-438)")
def test_LSN_10_outside_question_not_counted_as_answered(lesson):
    lesson.click("Задать вопрос")
    lesson.llm_use("relevance", "relevance_outside")
    lesson.type_into("Введите ваш вопрос", "Какая завтра погода?")
    lesson.click("Отправить вопрос")
    assert "qa" not in lesson.llm_calls()
    assert lesson.state()["learning"]["questions_count"].get(L1, 0) == 0


def test_LSN_08_relevant_question_is_answered_and_counted(lesson):
    lesson.click("Задать вопрос")
    lesson.type_into("Введите ваш вопрос", "Что такое переменная?")
    lesson.click("Отправить вопрос")
    assert lesson.llm_calls()[-2:] == ["relevance", "qa"]
    assert lesson.state()["learning"]["questions_count"][L1] == 1


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="LSN-15: после «Повторить урок» «← Назад к курсам» не открывает дашборд (lesson_interface.py:93-96, assessment_results_handler.py:324)")
def test_LSN_15_back_to_courses_works_after_repeat_lesson(lesson):
    lesson.click("Пройти тест"); lesson.answer_test(1); lesson.click("Завершить тест")
    lesson.click("Повторить урок")
    before = len(lesson.buttons("Продолжить обучение"))
    lesson.click("Назад к курсам")
    assert len(lesson.buttons("Продолжить обучение")) == before + 1


def _start_custom_out_of_domain(nb):
    nb.start_teachai()
    nb.set_value("Имя", "Тест"); nb.set_value("Общее время", 3); nb.set_value("Длительность урока", 30)
    nb.click("Сохранить настройки")
    nb.choose("Своё название курса")
    nb.llm_use("domain", "domain_out")
    nb.set_value("Название", "Курс кройки и шитья")
    nb.click("Начать курс")


def test_CRS_04_out_of_domain_course_is_blocked_with_choice(nb):
    _start_custom_out_of_domain(nb)
    assert nb.buttons("Всё равно начать")
    assert nb.buttons("Выбрать другой курс")
    assert "plan" not in nb.llm_calls()
    assert not nb.state().get("courses")


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="CRS-05/D7: пометка «вне области» не сохраняется в state (course_domain_ui.py:146 пишет domain_override только в локальный dict)")
def test_CRS_05_forced_out_of_domain_course_is_marked_in_state(nb):
    _start_custom_out_of_domain(nb)
    nb.click("Всё равно начать")
    st = nb.state()
    assert "plan" in nb.llm_calls()
    meta = st["courses"][st["active_course_id"]]["meta"]
    assert meta.get("domain_override") is True


def test_KZ_01_open_task_without_test_asks_confirmation_then_records_bypass(lesson):
    lesson.click("Контрольные задания")
    assert lesson.buttons("Перейти к практике без теста")
    assert "task_gen" not in lesson.llm_calls()
    lesson.click("Перейти к практике без теста")
    assert lesson.state()["learning"]["control_task_bypass"][L1] is True
    assert "task_gen" in lesson.llm_calls()


def test_KZ_02_cancel_bypass_records_nothing(lesson):
    lesson.click("Контрольные задания")
    lesson.click("Отмена")
    assert not lesson.state()["learning"].get("control_task_bypass")
    assert "task_gen" not in lesson.llm_calls()


def test_KZ_13_bypass_and_task_not_required_passes_lesson(lesson):
    """D6: тест обойдён + «Задание не требуется» => урок пройден."""
    lesson.llm_use("code_practice", "code_practice_no")
    lesson.click("Контрольные задания")
    lesson.click("Перейти к практике без теста")
    lesson.click("Перейти к следующему уроку")
    learn = lesson.state()["learning"]
    assert learn["control_task_bypass"][L1] is True
    assert learn["lesson_completion_status"][L1] is True


def test_ZAP_07_second_start_in_same_kernel_makes_no_llm_calls(lesson):
    calls_before = len(lesson.llm_calls())
    lesson.start_teachai()
    assert len(lesson.llm_calls()) == calls_before
    assert lesson.buttons("Продолжить обучение")


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="TST-03: «Завершить тест» без единого ответа принимается и оценивается (assessment_questions_ui.py:94, нет value=None)")
def test_TST_03_empty_test_is_not_accepted(lesson):
    lesson.click("Пройти тест")
    lesson.click("Завершить тест")
    assert L1 not in lesson.state()["learning"].get("lesson_attempts", {})
```

#### `tests/scenario/test_notebook_smoke.py`

```python
"""Один «честный» прогон ноутбука целиком через nbclient (ячейки выполняются подряд, без кликов)."""
import os
import shutil
from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient

from nbdriver import COPY_GLOBS, ROOT, TESTS

pytestmark = pytest.mark.scenario


def test_ZAP_00_notebook_runs_without_errors(tmp_path, monkeypatch):
    proj = tmp_path / "project"
    proj.mkdir()
    for pattern in COPY_GLOBS:
        for src in ROOT.glob(pattern):
            shutil.copy2(src, proj / src.name)
    (proj / ".env").write_text("OPENAI_API_KEY=sk-test-not-a-real-key\nOPENAI_API_ROUTE=direct\n", encoding="utf-8")
    log = tmp_path / "llm.jsonl"
    log.write_text("")
    monkeypatch.setenv("TEACHAI_FAKE_LOG", str(log))
    monkeypatch.setenv("PYTHONPATH", str(proj))
    for var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy"):
        monkeypatch.delenv(var, raising=False)

    nb = nbformat.read(proj / "TeachAI.ipynb", as_version=4)
    boot = nbformat.v4.new_code_cell(f"import sys; sys.path.insert(0, {str(TESTS)!r}); import kernel_boot")
    nb.cells.insert(0, boot)
    NotebookClient(nb, timeout=120, kernel_name="python3", resources={"metadata": {"path": str(proj)}}).execute()

    errors = [o for c in nb.cells if c.cell_type == "code" for o in c.get("outputs", []) if o.output_type == "error"]
    assert not errors
    assert "TeachAI" in "".join(o.get("text", "") for c in nb.cells[1:] if c.cell_type == "code" for o in c.get("outputs", []))
    assert log.read_text().strip() == ""  # на первом запуске LLM не вызывается
```

#### `tests/live/test_live_smoke.py`

```python
"""Живой тест: настоящая модель. Выключен по умолчанию; запуск: TEACHAI_LIVE_KEY=sk-... pytest -m live"""
import os

import pytest

pytestmark = pytest.mark.live


@pytest.mark.skipif(not os.environ.get("TEACHAI_LIVE_KEY"), reason="нужен TEACHAI_LIVE_KEY")
def test_live_domain_classifier(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", os.environ["TEACHAI_LIVE_KEY"])
    from content_generator import ContentGenerator
    from course_domain import classify_course_topic

    verdict = classify_course_topic("Основы pandas для аналитика", generator=ContentGenerator(os.environ["TEACHAI_LIVE_KEY"]))
    assert verdict.status == "in"
```

## 6. Запуск

```
pip install -r requirements-dev.txt
pytest                      # unit + scenario, live выключен (addopts: -m "not live")
pytest tests/unit           # секунды
pytest tests/scenario       # ~1 мин: каждый тест поднимает своё ядро
pytest -rx                  # показать причины xfail
pytest -m live              # вручную; нужен TEACHAI_LIVE_KEY=<настоящий ключ>, платный вызов
```

## 7. Что дописать после эталонного набора (по образцу, **не проверено прототипом**)

Дописывай, только когда эталонный набор зелёный. Каждый тест — по тем же правилам (п. 0.5–0.6). Приоритет сверху вниз.

| ID | Уровень | Что проверить | Подсказка |
|---|---|---|---|
| TST-05 | scenario | Двойной «Завершить тест» → одна запись в `lesson_attempts` | `lesson.click("Завершить тест")` дважды; вторая кнопка может быть disabled — тогда `click` упадёт: обернуть в `try` и проверить число записей |
| LSN-02 | scenario | Урок в кэше: после перезапуска ядра 0 LLM-вызовов | второй `NotebookSession` на **той же** папке `project` (скопировать `data/state.json`) |
| ST-05 | unit | Два курса: прогресс у каждого свой | `course_portfolio.switch_course`; образец — `course_portfolio_checks.py` |
| LSN-09 | scenario | Вопрос scope=course → ответ с пометкой «не тема этого урока»; `questions_count` +1 | `nb.llm_use("relevance", "relevance_course")`; искать в `html_texts()` текст «Не тема этого урока» |
| KZ-14 | scenario | LLM-проверка КЗ падает → резервная проверка | `nb.llm_use("task_validate", ...)` нельзя передать исключение через ядро: добавить в `kernel_boot` режим «ошибка», например фикстуру `task_validate_broken.txt` с текстом без JSON |
| LLM-04/05 | unit | Кривые ответы: битый JSON, ```json-обёртка для плана, теста, понятий, судьи, домена | добавить `broken_*.txt` в фикстуры; ожидание — понятная ошибка или fallback, без трассировки |
| LLM-06 | unit | `correct_option` = 0 → 1; = 4 → ошибка | `assessment_generator._extract_questions_from_response` |
| CRS-10 | unit | План с другим `id` — один слот в портфеле | `course_portfolio` + `course_selection_ui._start_course` (строка 307) |
| ST-11/12 | unit | Битый `state.json` не роняет запуск; атомарная запись | записать мусор в `state.json`, создать `StateManager()` |
| LSN-12 | unit | Клик по закрытому уроку отклонён | `lesson_outline.py` |

Пакет 1 **не** содержит тестов на D1–D9 (их ещё нет в коде): достаточно тех, что перечислены в эталоне со ссылками на D-пункты и `xfail`. Тесты на `visited_lessons`, `lesson_pass_mode`, «Показать решение», `offtopic_count`, историю КЗ и дочерний процесс пишутся в пакетах 3 и 4 вместе с реализацией.

## 8. Критерии приёмки

1. `pytest` (из корня проекта, без реального `.env`-ключа в окружении) завершается с кодом 0.
2. Эталонный набор даёт **`64 passed, 1 skipped, 23 xfailed`** (допустимо больше тестов при тех же правилах; допустимо отличие на 1–2 теста, если оно объяснено: например, `xfail`, который на твоей машине неожиданно проходит, — повод остановиться и написать, а не «чинить»).
3. Красных (`failed`) и «неожиданно прошедших» (`XPASS(strict)`) нет.
4. Время: `tests/unit` < 5 с, весь `pytest` ≲ 90 с (каждый сценарный тест ≈ 3 с, из них около 1 с запуск ядра).
5. `git status`: изменены только `.gitignore`; новые — `pytest.ini`, `requirements-dev.txt`, `tests/`. Файлы приложения не изменены (`git diff --stat` показывает один `.gitignore`).
6. Реальные `data/state.json`, `.env`, `.env.sample` не изменились (страховка `real_data_untouched` в `conftest.py` проверяет это).
7. Сети нет: `no_network` в `conftest.py` и `kernel_boot.py` превращает любой HTTP-запрос в ошибку; убедись, что тесты проходят при отключённом интернете.
8. `pytest -rx` печатает у каждого `xfail` причину в формате `<ID>: <суть> (файл:строка)`.
9. Старые проверки `*_checks.py` запускаются через `tests/unit/test_legacy_checks.py` без правок; одна из них (`relevance_prompt_checks::test_relevance_prompt_is_a_teacher_judgment`) устарела относительно кода и помечена `xfail` (её исправляет пакет 2).

## 9. Что вернуть мне

Короткий отчёт: итоговая строка `pytest`, список `xfail` с причинами (`pytest -rx`), время прогона, и всё, что отличалось от описания выше (другие номера строк, ломкие места, тесты, которые пришлось менять), чтобы я исправил инструкцию и сценарии.
