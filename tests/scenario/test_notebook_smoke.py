"""Один «честный» прогон ноутбука целиком через nbclient (ячейки выполняются подряд, без кликов)."""
import os
import shutil
from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient

from nbdriver import COPY_GLOBS, ROOT, TESTS, kernel_name_for_tests

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
    NotebookClient(
        nb,
        timeout=120,
        kernel_name=kernel_name_for_tests(),
        resources={"metadata": {"path": str(proj)}},
    ).execute()

    errors = [o for c in nb.cells if c.cell_type == "code" for o in c.get("outputs", []) if o.output_type == "error"]
    assert not errors
    assert "TeachAI" in "".join(o.get("text", "") for c in nb.cells[1:] if c.cell_type == "code" for o in c.get("outputs", []))
    assert log.read_text().strip() == ""  # на первом запуске LLM не вызывается
