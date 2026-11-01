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
