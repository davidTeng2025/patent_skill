#!/usr/bin/env python3
"""Enforce the drafting fact fence recorded in source_map.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def check(items: list[dict], *, confirmed: bool = False) -> list[str]:
    errors: list[str] = []
    for item in items:
        para = item.get("para_id") or "?"
        status = item.get("status")
        sources = item.get("sources") or []
        if status == "traced" and not sources:
            errors.append(f"{para}: status=traced 但没有 sources")
        elif status == "needs_confirm":
            if not item.get("question"):
                errors.append(f"{para}: needs_confirm 缺少 question")
            if confirmed:
                errors.append(f"{para}: 确认版仍含 needs_confirm")
        elif status == "template_text":
            continue
        elif status not in {"traced", "needs_confirm", "template_text"}:
            errors.append(f"{para}: 未知 status={status!r}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_map", type=Path)
    parser.add_argument("--confirmed", action="store_true")
    args = parser.parse_args()
    if not args.source_map.is_file():
        print(f"SOURCE_TRACE: ok=0 missing={args.source_map}")
        return 2
    data = json.loads(args.source_map.read_text(encoding="utf-8"))
    errors = check(data, confirmed=args.confirmed)
    traced = sum(item.get("status") == "traced" for item in data)
    waiting = sum(item.get("status") == "needs_confirm" for item in data)
    print(
        f"SOURCE_TRACE: ok={int(not errors)} traced={traced} "
        f"needs_confirm={waiting} errors={len(errors)}"
    )
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
