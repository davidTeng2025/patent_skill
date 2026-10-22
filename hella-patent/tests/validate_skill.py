#!/usr/bin/env python3
"""Validate the project skill structure without Cursor internals."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBSKILLS = (
    "idf-review",
    "fto",
    "claim-scope",
    "office-action",
    "idf-drafting",
    "application-drafting",
    "draft-revision",
)
SECTIONS = ("用途", "何时用", "输入", "步骤", "护栏", "产出物")


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def main() -> int:
    errors: list[str] = []
    for relative in (".", *SUBSKILLS):
        path = ROOT / relative / "SKILL.md"
        if not path.is_file():
            errors.append(f"missing: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        meta = frontmatter(text)
        name = meta.get("name", "")
        if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
            errors.append(f"{relative}: invalid name {name!r}")
        if not meta.get("description"):
            errors.append(f"{relative}: missing description")
        if len(text.splitlines()) >= 500:
            errors.append(f"{relative}: SKILL.md must be under 500 lines")
        if relative != ".":
            for section in SECTIONS:
                if f"## {section}" not in text:
                    errors.append(f"{relative}: missing section {section}")
    print(f"SKILL_VALIDATE: ok={int(not errors)} errors={len(errors)}")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
