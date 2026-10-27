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
