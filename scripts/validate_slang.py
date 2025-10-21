#!/usr/bin/env python3
"""Validate a slang mapping JSON file.

Usage: python scripts/validate_slang.py path/to/slang.json

This checks that the file is valid JSON, that the top-level value is an
object/dict, and that every value is either a string or list of strings.
"""
import json
import sys
from pathlib import Path


def validate(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf8")
    except Exception as e:
        print(f"ERROR: cannot read file: {e}")
        return 2
    try:
        obj = json.loads(text)
    except Exception as e:
        print(f"ERROR: invalid JSON: {e}")
        return 2
    if not isinstance(obj, dict):
        print("ERROR: top-level JSON value must be an object/dictionary")
        return 2
    problems = 0
    for k, v in obj.items():
        if not isinstance(k, str):
            print(f"ERROR: key {k!r} is not a string")
            problems += 1
            continue
        if isinstance(v, str):
            continue
        if isinstance(v, list):
            if not all(isinstance(x, str) for x in v):
                print(f"ERROR: value for key {k!r} contains non-string entries")
                problems += 1
            continue
        print(f"ERROR: value for key {k!r} must be a string or list of strings")
        problems += 1

    if problems:
        print(f"Found {problems} problem(s)")
        return 1
    print("OK: mapping looks valid")
    return 0


def main(argv):
    if len(argv) < 2:
        print("Usage: validate_slang.py path/to/slang.json")
        return 2
    path = Path(argv[1])
    return validate(path)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
