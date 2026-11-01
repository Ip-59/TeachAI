import pytest
from helpers import start_catalog_course
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
    start_catalog_course(nb)
    return nb
