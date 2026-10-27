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


def kernel_name_for_tests() -> str:
    """Имя ядра из того же виртуального окружения, что и pytest.

    На работе это ``venv_w_l`` (``venv_W_L``). Сравнивать ``realpath``
    нельзя: ``venv_W_L/bin/python`` — ссылка на ``/usr/bin/python3.12``,
    и тогда выбирается системное ядро ``python3``. ``TEACHAI_KERNEL``
    перекрывает выбор.
    """
    forced = os.environ.get("TEACHAI_KERNEL")
    if forced:
        return forced
    prefix = Path(sys.prefix).resolve()
    matches: list[str] = []
    roots = (
        Path.home() / ".local/share/jupyter/kernels",
        prefix / "share/jupyter/kernels",
    )
    for root in roots:
        if not root.is_dir():
            continue
        for spec in root.glob("*/kernel.json"):
            try:
                argv = json.loads(spec.read_text(encoding="utf-8")).get("argv") or []
            except (OSError, json.JSONDecodeError):
                continue
            if not argv:
                continue
            exe = Path(argv[0])
            if not exe.is_absolute():
                continue
            # Не resolve() самого файла: в venv это ссылка на /usr/bin/python3.12.
            try:
                exe.parent.resolve().relative_to(prefix)
            except ValueError:
                continue
            matches.append(spec.parent.name)
    if matches:
        return sorted(matches)[0]
    return "python3"


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
        self.km = KernelManager(kernel_name=kernel_name_for_tests())
        self.km.start_kernel(cwd=str(self.proj), env=full_env)
        self.kc = self.km.client()
        self.kc.start_channels()
        self.kc.wait_for_ready(timeout=60)
        kernel_prefix = self.run("import sys; print(sys.prefix)").strip()
        assert os.path.realpath(kernel_prefix) == os.path.realpath(sys.prefix), (
            f"ядро Jupyter из другого окружения: {kernel_prefix} (тесты: {sys.prefix}). "
            "Запускайте pytest интерпретатором venv_W_L на работе и venv_H_L дома."
        )
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
