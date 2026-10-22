#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "jsonschema>=4.18",
# ]
# ///
"""Validate one JSON document against a hella-patent schema.

依赖 jsonschema，已写在本文件顶部。用 `uv run validate_json.py` 执行。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("document", type=Path)
    parser.add_argument("--schema", type=Path, required=True)
    args = parser.parse_args()
    if not args.document.is_file() or not args.schema.is_file():
        print("SCHEMA_VALIDATE: ok=0 missing_input=1")
        return 2
    document = json.loads(args.document.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(
            schema, format_checker=FormatChecker()
        ).iter_errors(document),
        key=lambda error: list(error.path),
    )
    print(f"SCHEMA_VALIDATE: ok={int(not errors)} errors={len(errors)}")
    for error in errors:
        location = "/".join(str(part) for part in error.path) or "$"
        print(f"ERROR: {location}: {error.message}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
