#!/usr/bin/env python3
"""Проверка staged-диффа на секреты (OpenAI-ключ и присваивание OPENAI_API_KEY).

Запуск вручную:
  python scripts/check_secrets.py
  git diff --cached -U0 | python scripts/check_secrets.py --stdin

Хук (на каждой машине один раз):
  git config core.hooksPath hooks
  # файл hooks/pre-commit уже вызывает этот скрипт
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from typing import Iterable, List, Tuple

OPENAI_KEY_RE = re.compile(r"sk-[A-Za-z0-9_-]{20,}")
OPENAI_ASSIGN_RE = re.compile(
    r"(?i)\bOPENAI_API_KEY\s*=\s*['\"][^'\"]+['\"]"
)

ALLOWED_FRAGMENTS = (
    "sk-test-not-a-real-key",
)


def iter_added_lines(diff_text: str) -> Iterable[Tuple[str, str]]:
    """Из unified diff берёт только добавленные строки (+), не +++."""
    path = ""
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            continue
        if line.startswith("+") and not line.startswith("+++"):
            yield path, line[1:]


def find_secret_hits(diff_text: str) -> List[str]:
    hits: List[str] = []
    for path, content in iter_added_lines(diff_text):
        if any(frag in content for frag in ALLOWED_FRAGMENTS):
            continue
        if OPENAI_KEY_RE.search(content):
            hits.append(f"{path}: похоже на OpenAI-ключ в добавленной строке")
        if OPENAI_ASSIGN_RE.search(content):
            hits.append(f"{path}: присваивание литерала OPENAI_API_KEY=...")
    seen: set[str] = set()
    out: List[str] = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def staged_diff() -> str:
    proc = subprocess.run(
        ["git", "diff", "--cached", "-U0"],
        check=False,
        capture_output=True,
        text=True,
    )
    return proc.stdout or ""


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="читать unified diff из stdin вместо git diff --cached",
    )
    args = parser.parse_args(argv)
    diff = sys.stdin.read() if args.stdin else staged_diff()
    hits = find_secret_hits(diff)
    if hits:
        sys.stderr.write(
            "check_secrets: отказ — в индексе есть похожие на секреты строки:\n"
        )
        for h in hits:
            sys.stderr.write(f"  - {h}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
