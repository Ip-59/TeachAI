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
