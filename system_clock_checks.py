"""Часы этапа берутся из datetime, не из файла."""

from __future__ import annotations

from datetime import datetime

from system_clock import format_clock_ru, mark_stage, read_clock


def test_clock_comes_from_datetime() -> None:
    moment = read_clock()
    assert moment.tzinfo is not None
    text = format_clock_ru(moment)
    assert str(moment.year) in text
    assert moment.strftime("%H:%M") in text
    marked = mark_stage("проверка")
    assert str(datetime.now().astimezone().year) in marked


def main() -> None:
    test_clock_comes_from_datetime()
    print("OK test_clock_comes_from_datetime")


if __name__ == "__main__":
    main()
