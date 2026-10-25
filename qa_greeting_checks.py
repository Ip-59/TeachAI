"""Снятие приветствия не должно съедать первое предложение и ссылку."""

from __future__ import annotations

from qa_generator import QAGenerator

_ANSWER = (
    "Актуальная версия Python в момент установки может варьироваться, "
    "так как разработка языка продолжается. "
    "Для проверки текущей версии Python, установленной в вашей среде, "
    "выполните следующий код:\n\n"
    "```python\nimport sys\nprint(sys.version)\n```\n\n"
    "Рекомендуется всегда загружать последнюю стабильную версию с "
    "официального сайта [python.org](https://www.python.org), так как она "
    "будет содержать последние обновления и исправления."
)


def test_answer_keeps_version_sentence_and_link() -> None:
    cleaned = QAGenerator._remove_greetings(_ANSWER)
    assert cleaned.startswith("Актуальная версия")
    assert "[python.org](https://www.python.org)" in cleaned
    assert "сайта [python.org]" in cleaned


def test_real_greeting_is_removed() -> None:
    text = "Привет, Игорь!\n\nАктуальная версия указана на сайте."
    cleaned = QAGenerator._remove_greetings(text)
    assert not cleaned.startswith("Привет")
    assert cleaned.startswith("Актуальная версия")


def main() -> None:
    test_answer_keeps_version_sentence_and_link()
    print("OK test_answer_keeps_version_sentence_and_link")
    test_real_greeting_is_removed()
    print("OK test_real_greeting_is_removed")


if __name__ == "__main__":
    main()
