"""Ориентир для заданий: предыдущие уроки, без выдуманного синтаксиса."""

from __future__ import annotations

from student_knowledge import (
    attach_concepts_to_lesson,
    knowledge_brief_ru,
    mark_lesson_concepts_passed,
    remember_lesson_concepts,
)


class _State:
    def __init__(self) -> None:
        self.state = {
            "learning": {},
            "course_plan": {
                "sections": [
                    {
                        "id": "section-1",
                        "title": "Введение",
                        "topics": [
                            {
                                "id": "topic-1",
                                "title": "Старт",
                                "lessons": [
                                    {
                                        "id": "lesson-1",
                                        "title": "Установка Python",
                                        "description": "Как поставить интерпретатор.",
                                        "keywords": ["установка"],
                                    },
                                    {
                                        "id": "lesson-2",
                                        "title": "Настройка среды разработки",
                                        "description": "Выбор IDE.",
                                        "keywords": ["IDE"],
                                    },
                                ],
                            }
                        ],
                    }
                ]
            },
        }
        self.saved = 0

    def get_course_plan(self):
        return self.state["course_plan"]

    def save_state(self) -> bool:
        self.saved += 1
        return True


def test_second_lesson_without_passed_concepts() -> None:
    state = _State()
    text = knowledge_brief_ru(state, "section-1:topic-1:lesson-2")
    assert "урок 2 из 2" in text
    assert "Установка Python" in text
    assert "понятия ещё не засчитаны" in text


def test_first_lesson_has_no_prior_code() -> None:
    state = _State()
    text = knowledge_brief_ru(state, "section-1:topic-1:lesson-1")
    assert "урок 1 из 2" in text
    assert "ещё не изучал, как писать код" in text


def test_concepts_are_stored() -> None:
    state = _State()
    remember_lesson_concepts(
        state,
        "section-1:topic-1:lesson-1",
        [{"title": "Интерпретатор", "description": "Программа, которая выполняет код."}],
    )
    text = knowledge_brief_ru(state, "section-1:topic-1:lesson-2")
    assert "Интерпретатор" in text
    assert state.saved == 1


def test_passed_lesson_copies_concepts_from_cache() -> None:
    state = _State()
    state.state["learning"]["lesson_scores"] = {"section-1:topic-1:lesson-1": 80}
    attach_concepts_to_lesson(
        state,
        "section-1:topic-1:lesson-1",
        [{"title": "Интерпретатор", "description": "Запускает код."}],
    )
    mark_lesson_concepts_passed(state, "section-1:topic-1:lesson-1")
    text = knowledge_brief_ru(state, "section-1:topic-1:lesson-2")
    assert "пройденные понятия Интерпретатор" in text


def main() -> None:
    test_second_lesson_without_passed_concepts()
    print("OK test_second_lesson_without_passed_concepts")
    test_passed_lesson_copies_concepts_from_cache()
    print("OK test_passed_lesson_copies_concepts_from_cache")
    test_first_lesson_has_no_prior_code()
    print("OK test_first_lesson_has_no_prior_code")
    test_concepts_are_stored()
    print("OK test_concepts_are_stored")


if __name__ == "__main__":
    main()
