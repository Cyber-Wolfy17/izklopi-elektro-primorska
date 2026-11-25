"""Fail if protected personal terms appear in the repository.

Terms are read from a file (one per line) or from the PRIVACY_TERMS environment
variable. The terms themselves are never stored in this repository. A line
starting with "re:" is treated as a regular expression. Blank lines and lines
starting with "#" are ignored. Matching is case-insensitive.

Modes:
  --staged   scan lines being added in the current git index (pre-commit)
  --tracked  scan every tracked file at HEAD (CI)
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def load_terms(terms_file: str | None) -> list[re.Pattern[str]]:
    if terms_file:
        raw = Path(terms_file).read_text(encoding="utf-8")
    else:
        raw = os.environ.get("PRIVACY_TERMS", "")
    patterns: list[re.Pattern[str]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("re:"):
            patterns.append(re.compile(line[3:], re.IGNORECASE))
        else:
            patterns.append(re.compile(re.escape(line), re.IGNORECASE))
    return patterns


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
    ).stdout


def staged_added_lines() -> list[tuple[str, int, str]]:
    results: list[tuple[str, int, str]] = []
    current = ""
    lineno = 0
    for line in git("diff", "--cached", "--unified=0", "--no-color").splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else line[4:]
        elif line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            lineno = int(match.group(1)) if match else 0
        elif line.startswith("+") and not line.startswith("+++"):
            results.append((current, lineno, line[1:]))
            lineno += 1
    return results


def tracked_lines() -> list[tuple[str, int, str]]:
    results: list[tuple[str, int, str]] = []
    for name in git("ls-files").splitlines():
        path = Path(name)
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            results.append((name, number, line))
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true")
    mode.add_argument("--tracked", action="store_true")
    parser.add_argument("--terms-file")
    args = parser.parse_args()

    patterns = load_terms(args.terms_file)
    if not patterns:
        print("privacy_check: no terms configured, nothing to check", file=sys.stderr)
        return 2

    lines = staged_added_lines() if args.staged else tracked_lines()
    hits = [
        (name, number)
        for name, number, text in lines
        if any(p.search(text) for p in patterns)
    ]
    if hits:
        print("privacy_check: protected term found (content not shown):", file=sys.stderr)
        for name, number in hits:
            print(f"  {name}:{number}", file=sys.stderr)
        return 1
    print(f"privacy_check: OK ({len(patterns)} terms checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
